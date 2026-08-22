"""Tests for the thin Fabro CLI port."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult

_MODULE_PATH = Path(
    ".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_fabro_port.py"
)
_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._fabro_port"


@dataclass(kw_only=True)
class _Call:
    argv: list[str]
    cwd: Path
    timeout_seconds: float
    env: dict[str, str] | None


@dataclass(kw_only=True)
class _Runner:
    results: list[CommandResult]
    calls: list[_Call]

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = stdin
        self.calls.append(_Call(argv=argv, cwd=cwd, timeout_seconds=timeout_seconds, env=env))
        return self.results.pop(0)


def _port_module() -> Any:
    assert _MODULE_PATH.is_file()
    return importlib.import_module(_MODULE_NAME)


def test_fabro_port_is_the_only_public_fabro_cli_and_response_surface() -> None:
    """Legacy dispatcher modules must not keep duplicate Fabro readers."""
    argv_module = importlib.import_module(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_argv"
    )
    run_status_module = importlib.import_module(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_run_status"
    )
    stale_sweep_module = importlib.import_module(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_stale_run_sweep"
    )

    assert not any(name.startswith("fabro_") for name in argv_module.__all__)
    assert "parse_run_id" not in run_status_module.__all__
    assert "parse_run_status" not in run_status_module.__all__
    assert not hasattr(stale_sweep_module, "_watchable_fabro_run")


def test_fabro_port_run_builds_livespec_run_argv_and_parses_run_id(tmp_path: Path) -> None:
    module = _port_module()
    login_value = "fixture-login-value"
    runner = _Runner(
        results=[CommandResult(exit_code=0, stdout="\x1b[2mRun: 01ABC\x1b[0m\n", stderr="")],
        calls=[],
    )
    port = module.FabroPort(
        fabro_bin="/opt/fabro-254",
        target=module.FabroTarget(
            server_url="http://127.0.0.1:32276",
            dev_token=login_value,
        ),
        runner=runner,
        cwd=tmp_path,
    )

    result = port.run(
        workflow_toml=tmp_path / "workflow.toml",
        goal_file=tmp_path / "goal.md",
        inputs=("acp_adapter=codex-acp", "review_fix_visit_cap=2"),
        timeout_seconds=42.0,
    )

    assert result.run_id == "01ABC"
    assert runner.calls == [
        _Call(
            argv=[
                "/opt/fabro-254",
                "run",
                str(tmp_path / "workflow.toml"),
                "--goal-file",
                str(tmp_path / "goal.md"),
                "--input",
                "acp_adapter=codex-acp",
                "--input",
                "review_fix_visit_cap=2",
                "--no-upgrade-check",
                "--server",
                "http://127.0.0.1:32276",
            ],
            cwd=tmp_path,
            timeout_seconds=42.0,
            env={"FABRO_SERVER": "http://127.0.0.1:32276"},
        )
    ]


def test_fabro_port_auth_login_uses_dev_token_and_server_as_subcommand_flags(
    tmp_path: Path,
) -> None:
    module = _port_module()
    login_value = "fixture-login-value"
    runner = _Runner(results=[CommandResult(exit_code=0, stdout="", stderr="")], calls=[])
    port = module.FabroPort(
        fabro_bin="fabro-candidate",
        target=module.FabroTarget(server_url="http://factory", dev_token=login_value),
        runner=runner,
        cwd=tmp_path,
    )

    result = port.auth_login(timeout_seconds=5.0)

    assert result.command.exit_code == 0
    assert runner.calls == [
        _Call(
            argv=[
                "fabro-candidate",
                "auth",
                "login",
                "--dev-token",
                login_value,
                "--server",
                "http://factory",
            ],
            cwd=tmp_path,
            timeout_seconds=5.0,
            env=None,
        )
    ]


def test_fabro_port_json_operations_parse_payloads_and_run_summaries(tmp_path: Path) -> None:
    module = _port_module()
    runner = _Runner(
        results=[
            CommandResult(exit_code=0, stdout='{"status": {"kind": "blocked"}}', stderr=""),
            CommandResult(exit_code=0, stdout='{"events": [{"timestamp": 12}]}', stderr=""),
            CommandResult(
                exit_code=0,
                stdout=(
                    '{"runs": [{"run_id": "01RUN", "status": {"kind": "running"}, '
                    '"goal": "Work-item: bd-ib-okr5ru", "total_usd_micros": 1250}]}'
                ),
                stderr="",
            ),
            CommandResult(exit_code=0, stdout='{"valid": true}', stderr=""),
        ],
        calls=[],
    )
    port = module.FabroPort(
        fabro_bin="fabro",
        target=module.FabroTarget(server_url="http://factory"),
        runner=runner,
        cwd=tmp_path,
    )

    inspect = port.inspect(run_id="01RUN", timeout_seconds=1.0)
    events = port.events(run_id="01RUN", timeout_seconds=2.0)
    ps = port.ps(timeout_seconds=3.0)
    validate = port.validate(workflow_toml=tmp_path / "workflow.toml", timeout_seconds=4.0)

    assert inspect.status_kind == "blocked"
    assert events.payload == {"events": [{"timestamp": 12}]}
    assert ps.runs == (
        module.FabroRunSummary(
            run_id="01RUN",
            status_kind="running",
            goal="Work-item: bd-ib-okr5ru",
            total_usd_micros=1250,
        ),
    )
    assert getattr(ps.runs[0], "work_item_id", None) == "bd-ib-okr5ru"
    assert validate.payload == {"valid": True}
    assert [call.argv for call in runner.calls] == [
        ["fabro", "inspect", "01RUN", "--json", "--server", "http://factory"],
        ["fabro", "events", "01RUN", "--json", "--server", "http://factory"],
        ["fabro", "ps", "-a", "--json", "--server", "http://factory"],
        ["fabro", "validate", str(tmp_path / "workflow.toml"), "--json"],
    ]


def test_fabro_port_preflight_builds_livespec_run_configuration_argv(tmp_path: Path) -> None:
    module = _port_module()
    runner = _Runner(
        results=[CommandResult(exit_code=0, stdout='{"ok": true}', stderr="")],
        calls=[],
    )
    port = module.FabroPort(
        fabro_bin="fabro",
        target=module.FabroTarget(server_url="http://factory"),
        runner=runner,
        cwd=tmp_path,
    )

    result = port.preflight(
        workflow_toml=tmp_path / "workflow.toml",
        goal_file=tmp_path / "goal.md",
        inputs=("acp_adapter=codex-acp",),
        timeout_seconds=4.0,
    )

    assert result.payload == {"ok": True}
    assert runner.calls == [
        _Call(
            argv=[
                "fabro",
                "preflight",
                str(tmp_path / "workflow.toml"),
                "--goal-file",
                str(tmp_path / "goal.md"),
                "--input",
                "acp_adapter=codex-acp",
                "--no-upgrade-check",
                "--json",
                "--server",
                "http://factory",
            ],
            cwd=tmp_path,
            timeout_seconds=4.0,
            env={"FABRO_SERVER": "http://factory"},
        )
    ]


def test_fabro_port_rm_and_version_stay_on_the_declared_surface(tmp_path: Path) -> None:
    module = _port_module()
    runner = _Runner(
        results=[
            CommandResult(exit_code=0, stdout="", stderr=""),
            CommandResult(exit_code=0, stdout="fabro 0.254.0 (8de6611)\n", stderr=""),
        ],
        calls=[],
    )
    port = module.FabroPort(
        fabro_bin="fabro",
        target=module.FabroTarget(),
        runner=runner,
        cwd=tmp_path,
    )

    rm = port.rm(run_id="01RUN", timeout_seconds=6.0)
    version = port.version(timeout_seconds=7.0)

    assert rm.command.exit_code == 0
    assert version.text == "fabro 0.254.0 (8de6611)\n"
    assert [call.argv for call in runner.calls] == [
        ["fabro", "rm", "-f", "01RUN"],
        ["fabro", "version"],
    ]


def test_fabro_port_can_probe_top_level_server_parse_rejection(tmp_path: Path) -> None:
    module = _port_module()
    runner = _Runner(
        results=[CommandResult(exit_code=2, stdout="", stderr="unexpected argument '--server'")],
        calls=[],
    )
    port = module.FabroPort(
        fabro_bin="fabro",
        target=module.FabroTarget(server_url="http://factory"),
        runner=runner,
        cwd=tmp_path,
    )

    result = port.top_level_server_parse_probe(
        subcommand=("ps", "-a", "--json"),
        timeout_seconds=8.0,
    )

    assert result.command.exit_code == 2
    assert runner.calls == [
        _Call(
            argv=["fabro", "--server", "http://factory", "ps", "-a", "--json"],
            cwd=tmp_path,
            timeout_seconds=8.0,
            env=None,
        )
    ]
