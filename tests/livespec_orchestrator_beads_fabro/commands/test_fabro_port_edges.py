"""Edge coverage for the Fabro port parsers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._fabro_port import (
    FabroPort,
    FabroRunSummary,
    FabroTarget,
)


@dataclass(kw_only=True)
class _Runner:
    results: list[CommandResult]

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (argv, cwd, timeout_seconds, env, stdin)
        return self.results.pop(0)


def test_fabro_port_handles_absent_factory_target_and_missing_run_id(tmp_path: Path) -> None:
    runner = _Runner(results=[CommandResult(exit_code=0, stdout="started\n", stderr="")])
    port = FabroPort(fabro_bin="fabro", target=FabroTarget(), runner=runner, cwd=tmp_path)

    assert port.auth_login(timeout_seconds=1.0) is None
    assert (
        port.run(
            workflow_toml=tmp_path / "workflow.toml",
            goal_file=tmp_path / "goal.md",
            inputs=(),
            timeout_seconds=2.0,
        ).run_id
        is None
    )


def test_fabro_port_handles_unusable_json_and_status_shapes(tmp_path: Path) -> None:
    runner = _Runner(
        results=[
            CommandResult(exit_code=1, stdout='{"status": "blocked"}', stderr="failed"),
            CommandResult(exit_code=0, stdout="not json", stderr=""),
            CommandResult(exit_code=0, stdout='{"status": "done"}', stderr=""),
            CommandResult(exit_code=0, stdout='{"status": {"detail": "missing kind"}}', stderr=""),
            CommandResult(exit_code=0, stdout='{"status": 7}', stderr=""),
            CommandResult(exit_code=0, stdout="[]", stderr=""),
        ]
    )
    port = FabroPort(
        fabro_bin="fabro",
        target=FabroTarget(server_url="http://factory"),
        runner=runner,
        cwd=tmp_path,
    )

    assert port.inspect(run_id="01A", timeout_seconds=1.0).payload is None
    assert port.events(run_id="01A", timeout_seconds=1.0).payload is None
    assert port.inspect(run_id="01A", timeout_seconds=1.0).status_kind == "done"
    assert port.inspect(run_id="01A", timeout_seconds=1.0).status_kind is None
    assert port.inspect(run_id="01A", timeout_seconds=1.0).status_kind is None
    assert port.inspect(run_id="01A", timeout_seconds=1.0).status_kind is None


def test_fabro_port_ps_accepts_top_level_lists_and_skips_unusable_runs(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        results=[
            CommandResult(
                exit_code=0,
                stdout=(
                    '[7, {"run_id": ""}, '
                    '{"run_id": "01A", "status": "done", '
                    '"goal": 7, "total_usd_micros": "unknown"}]'
                ),
                stderr="",
            ),
            CommandResult(exit_code=0, stdout='{"runs": "not a list"}', stderr=""),
            CommandResult(exit_code=0, stdout='"not an envelope"', stderr=""),
        ]
    )
    port = FabroPort(fabro_bin="fabro", target=FabroTarget(), runner=runner, cwd=tmp_path)

    assert port.ps(timeout_seconds=1.0).runs == (
        FabroRunSummary(
            run_id="01A",
            status_kind="done",
            goal=None,
            total_usd_micros=None,
        ),
    )
    assert port.ps(timeout_seconds=1.0).runs == ()
    assert port.ps(timeout_seconds=1.0).runs == ()
