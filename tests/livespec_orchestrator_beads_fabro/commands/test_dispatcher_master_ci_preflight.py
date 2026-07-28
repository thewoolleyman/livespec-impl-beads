"""Focused tests for the host-side master-CI dispatch preflight."""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, cast

import pytest
from livespec_orchestrator_beads_fabro.commands import _dispatcher_run_checks
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult

_MODULE_PATH = (
    Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
    / "_dispatcher_master_ci_preflight.py"
)
_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._dispatcher_master_ci_preflight"
_EXIT_PRECONDITION_ERROR = 3
_RED_CONCLUSIONS = (
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
    "stale",
    "startup_failure",
)
_PENDING_STATUSES = ("queued", "in_progress", "waiting", "pending", "requested")


class _MasterCiRefusal(Protocol):
    detail: str
    record: dict[str, object]


class _PreflightModule(Protocol):
    def master_ci_preflight_refusal(
        self, *, repo: Path, runner: _Runner
    ) -> _MasterCiRefusal | None:
        """Return the master-CI refusal or None."""


@dataclass(kw_only=True)
class _Runner:
    results: dict[tuple[str, ...], CommandResult]
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env, stdin)
        key = tuple(argv)
        self.calls.append(key)
        return self.results[key]


def _module() -> _PreflightModule:
    assert _MODULE_PATH.is_file()
    return cast("_PreflightModule", importlib.import_module(_MODULE_NAME))


def _result(*, exit_code: int = 0, stdout: str = "", stderr: str = "") -> CommandResult:
    return CommandResult(exit_code=exit_code, stdout=stdout, stderr=stderr)


def _run_list_payload(
    *, status: str = "completed", conclusion: str | None = "success", database_id: int = 303
) -> str:
    return json.dumps(
        [
            {
                "status": status,
                "conclusion": conclusion,
                "databaseId": database_id,
            }
        ]
    )


def _jobs_payload(
    *, ci_green_conclusion: str | None = "success", ci_green_status: str = "completed"
) -> str:
    jobs: list[dict[str, str | None]] = [{"name": "export-telemetry", "conclusion": "failure"}]
    if ci_green_conclusion is not None:
        jobs.append(
            {
                "name": "ci-green",
                "conclusion": ci_green_conclusion,
                "status": ci_green_status,
            }
        )
    return json.dumps({"jobs": jobs})


def _results(
    *,
    run_list: CommandResult | None = None,
    jobs: CommandResult | None = None,
    auth: CommandResult | None = None,
    view_run_id: str = "303",
) -> dict[tuple[str, ...], CommandResult]:
    return {
        ("gh", "auth", "token"): auth if auth is not None else _result(stdout="secret\n"),
        (
            "gh",
            "run",
            "list",
            "--branch",
            "master",
            "--limit",
            "1",
            "--workflow",
            "CI",
            "--json",
            "status,conclusion,databaseId",
        ): run_list if run_list is not None else _result(stdout=_run_list_payload()),
        ("gh", "run", "view", view_run_id, "--json", "jobs"): (
            jobs if jobs is not None else _result(stdout=_jobs_payload())
        ),
    }


@pytest.mark.parametrize("conclusion", _RED_CONCLUSIONS)
def test_red_ci_green_conclusions_refuse(tmp_path: Path, conclusion: str) -> None:
    module = _module()
    runner = _Runner(
        results=_results(jobs=_result(stdout=_jobs_payload(ci_green_conclusion=conclusion)))
    )

    refusal = module.master_ci_preflight_refusal(repo=tmp_path, runner=runner)

    assert refusal is not None


def test_run_rollup_failure_proceeds_when_ci_green_succeeded(tmp_path: Path) -> None:
    module = _module()
    runner = _Runner(
        results=_results(run_list=_result(stdout=_run_list_payload(conclusion="failure")))
    )

    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=runner) is None


def test_ci_green_failure_refuses_even_when_run_payload_matches(tmp_path: Path) -> None:
    module = _module()
    runner = _Runner(
        results=_results(
            run_list=_result(stdout=_run_list_payload(conclusion="failure")),
            jobs=_result(stdout=_jobs_payload(ci_green_conclusion="failure")),
        )
    )

    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=runner) is not None


def test_missing_ci_green_job_refuses_as_unprovable(tmp_path: Path) -> None:
    module = _module()
    runner = _Runner(results=_results(jobs=_result(stdout=_jobs_payload(ci_green_conclusion=None))))

    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=runner) is not None


def test_ci_green_pending_or_unknown_refuses_as_unprovable(tmp_path: Path) -> None:
    module = _module()
    pending = _Runner(
        results=_results(
            jobs=_result(
                stdout=_jobs_payload(ci_green_conclusion="success", ci_green_status="in_progress")
            )
        )
    )
    unknown = _Runner(
        results=_results(jobs=_result(stdout=_jobs_payload(ci_green_conclusion="neutral")))
    )

    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=pending) is not None
    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=unknown) is not None


def test_success_pending_statuses_and_empty_run_list_do_not_refuse(tmp_path: Path) -> None:
    module = _module()
    assert (
        module.master_ci_preflight_refusal(repo=tmp_path, runner=_Runner(results=_results()))
        is None
    )
    empty = _Runner(results=_results(run_list=_result(stdout="[]")))
    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=empty) is None
    for status in _PENDING_STATUSES:
        runner = _Runner(
            results=_results(
                run_list=_result(stdout=_run_list_payload(status=status, conclusion="failure")),
                jobs=_result(stdout=_jobs_payload(ci_green_conclusion="failure")),
            )
        )
        assert module.master_ci_preflight_refusal(repo=tmp_path, runner=runner) is None


def test_gh_absent_and_no_stored_credential_proceed(tmp_path: Path) -> None:
    module = _module()
    absent = _Runner(
        results=_results(
            auth=_result(exit_code=127, stderr="gh: command not found\n"),
            run_list=_result(exit_code=127, stderr="gh: command not found\n"),
        )
    )
    no_credential = _Runner(
        results=_results(
            auth=_result(exit_code=1, stderr="not logged in\n"),
            run_list=_result(exit_code=1, stderr="HTTP 401\n"),
        )
    )

    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=absent) is None
    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=no_credential) is None


def test_credentialed_gh_failure_refuses(tmp_path: Path) -> None:
    module = _module()
    runner = _Runner(
        results=_results(run_list=_result(exit_code=1, stderr="GitHub API unavailable\n"))
    )

    refusal = module.master_ci_preflight_refusal(repo=tmp_path, runner=runner)

    assert refusal is not None


def test_credentialed_gh_run_view_failure_refuses(tmp_path: Path) -> None:
    module = _module()
    runner = _Runner(results=_results(jobs=_result(exit_code=1, stderr="view failed\n")))

    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=runner) is not None


def test_malformed_credentialed_payloads_refuse_as_unprovable(tmp_path: Path) -> None:
    module = _module()
    malformed_run = _Runner(results=_results(run_list=_result(stdout=json.dumps(["bad"]))))
    malformed_view = _Runner(results=_results(jobs=_result(stdout=json.dumps([]))))
    malformed_jobs = _Runner(results=_results(jobs=_result(stdout=json.dumps({"jobs": {}}))))

    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=malformed_run) is not None
    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=malformed_view) is not None
    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=malformed_jobs) is not None


def test_non_dict_jobs_are_ignored_while_finding_ci_green(tmp_path: Path) -> None:
    module = _module()
    runner = _Runner(
        results=_results(
            jobs=_result(
                stdout=json.dumps({"jobs": ["bad", {"name": "ci-green", "conclusion": "success"}]})
            )
        )
    )

    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=runner) is None


def test_refusal_text_names_run_and_recovery_order(tmp_path: Path) -> None:
    module = _module()
    runner = _Runner(
        results=_results(
            run_list=_result(stdout=_run_list_payload(database_id=30316766663)),
            jobs=_result(stdout=_jobs_payload(ci_green_conclusion="failure")),
            view_run_id="30316766663",
        )
    )

    refusal = module.master_ci_preflight_refusal(repo=tmp_path, runner=runner)

    assert refusal is not None
    detail = refusal.detail
    failed = "gh run rerun 30316766663 --failed"
    full = "gh run rerun 30316766663"
    assert "30316766663" in detail
    assert detail.index(failed) < detail.index(full, detail.index(failed) + len(failed))


def test_lever_env_cannot_make_red_master_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    monkeypatch.setenv("LIVESPEC_SKIP_MASTER_CI_PREFLIGHT", "1")
    monkeypatch.setenv("CHECK_MASTER_CI_GREEN_SEVERITY", "warning")
    runner = _Runner(
        results=_results(jobs=_result(stdout=_jobs_payload(ci_green_conclusion="failure")))
    )

    assert module.master_ci_preflight_refusal(repo=tmp_path, runner=runner) is not None


def test_dispatch_preamble_refuses_before_receiver_or_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _MODULE_PATH.is_file()
    journal = tmp_path / "journal.jsonl"
    args = argparse.Namespace(fabro_bin=str(tmp_path / "fabro"), janitor=None, journal=str(journal))
    runner = _Runner(
        results=_results(jobs=_result(stdout=_jobs_payload(ci_green_conclusion="failure")))
    )
    _ = (tmp_path / "fabro").write_text("#!/bin/sh\n", encoding="utf-8")
    (tmp_path / "fabro").chmod(0o755)
    monkeypatch.setattr(_dispatcher_run_checks, "ShellCommandRunner", lambda: runner)

    def source_preflight_passes(*, repo: Path, runner: _Runner) -> None:
        _ = (repo, runner)

    monkeypatch.setattr(
        _dispatcher_run_checks,
        "source_checkout_preflight_refusal",
        source_preflight_passes,
    )

    assert _dispatcher_run_checks.dispatch_preamble(args=args, repo=tmp_path) == (
        None,
        _EXIT_PRECONDITION_ERROR,
    )
    assert json.loads(journal.read_text(encoding="utf-8"))["stage"] == "master-ci-preflight"


def test_existing_in_sandbox_master_ci_gate_and_janitor_aggregate_are_unchanged() -> None:
    master_ci_gate = Path(
        ".venv/lib/python3.10/site-packages/livespec_dev_tooling/checks/master_ci_green.py"
    ).read_text(encoding="utf-8")
    justfile = Path("justfile").read_text(encoding="utf-8")

    assert '"failure", "cancelled", "timed_out", "action_required", "stale"' in master_ci_gate
    assert "startup_failure" in master_ci_gate
    assert "check-master-ci-green" in justfile
