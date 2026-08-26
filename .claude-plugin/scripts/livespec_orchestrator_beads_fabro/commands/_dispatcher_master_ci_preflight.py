"""Host-side master-CI preflight for Fabro dispatch admission safety."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    CommandRunner,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import InvokerIdentity
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile

__all__: list[str] = [
    "MasterCiRefusal",
    "journal_master_ci_refusal",
    "master_ci_preflight_refusal",
]

_GH_PREFLIGHT_TIMEOUT_SECONDS = 30.0
_STAGE = "master-ci-preflight"
_REASON_RED = "master-ci-red"
_REASON_UNPROVABLE = "master-ci-unprovable"
_CI_GREEN_JOB = "ci-green"
_GREEN_CONCLUSIONS: frozenset[str] = frozenset({"success"})
_PENDING_STATUSES: frozenset[str] = frozenset(
    {"queued", "in_progress", "waiting", "pending", "requested"},
)
_RED_CONCLUSIONS: frozenset[str] = frozenset(
    {"failure", "cancelled", "timed_out", "action_required", "stale", "startup_failure"},
)


class _CiRun(TypedDict, total=False):
    status: str | None
    conclusion: str | None
    databaseId: int | str | None


class _CiJob(TypedDict, total=False):
    name: str | None
    conclusion: str | None
    status: str | None


@dataclass(frozen=True, kw_only=True)
class MasterCiRefusal:
    """Terminal master-CI preflight refusal, ready to emit and journal."""

    detail: str
    record: dict[str, object]


def master_ci_preflight_refusal(*, repo: Path, runner: CommandRunner) -> MasterCiRefusal | None:
    """Refuse dispatch when the latest master CI run's `ci-green` job is red.

    Hosts that cannot check at all fail open: no `gh` binary, no stored `gh`
    credential, or no master CI runs yet. A credentialed GitHub call that fails
    is different: the caller could have checked and got no proof of green, so
    dispatch refuses before admission and before any sandbox work is spent.
    """
    latest = _latest_master_ci_run(repo=repo, runner=runner)
    refusal: MasterCiRefusal | None = None
    if isinstance(latest, CommandResult):
        refusal = _credentialed_call_failure_refusal(result=latest)
    elif latest is not None:
        refusal = _classify_latest_run(repo=repo, runner=runner, run=latest)
    return refusal


def journal_master_ci_refusal(
    *, journal_path: Path, identity: InvokerIdentity, refusal: MasterCiRefusal
) -> None:
    """Persist the distinct terminal preflight outcome in the dispatch journal.

    The refusing invocation's own resolved identity is threaded in rather than
    re-derived, so a dispatch that asserted `--invoker` is not downgraded to the
    environment or the fallback mark on the one record that says it refused.
    """
    JournalFile(path=journal_path, identity=identity).append(record=refusal.record)


def _classify_latest_run(
    *, repo: Path, runner: CommandRunner, run: _CiRun
) -> MasterCiRefusal | None:
    status = run.get("status")
    if isinstance(status, str) and status in _PENDING_STATUSES:
        return None
    run_id = _run_id(run=run)
    ci_green = _ci_green_job(repo=repo, runner=runner, run_id=run_id)
    return _classify_ci_green(run_id=run_id, ci_green=ci_green)


def _classify_ci_green(
    *, run_id: str, ci_green: _CiJob | CommandResult | None
) -> MasterCiRefusal | None:
    refusal: MasterCiRefusal | None = None
    if isinstance(ci_green, CommandResult):
        refusal = _unprovable_refusal(run_id=run_id, detail_reason="ci-green job lookup failed")
    elif ci_green is None:
        refusal = _unprovable_refusal(run_id=run_id, detail_reason="ci-green job missing")
    else:
        refusal = _classify_ci_green_job(run_id=run_id, ci_green=ci_green)
    return refusal


def _classify_ci_green_job(*, run_id: str, ci_green: _CiJob) -> MasterCiRefusal | None:
    conclusion = ci_green.get("conclusion")
    job_status = ci_green.get("status")
    refusal: MasterCiRefusal | None = None
    if isinstance(job_status, str) and job_status in _PENDING_STATUSES:
        refusal = _unprovable_refusal(run_id=run_id, detail_reason="ci-green job still pending")
    elif conclusion in _RED_CONCLUSIONS:
        refusal = _red_refusal(run_id=run_id, conclusion=conclusion)
    elif conclusion not in _GREEN_CONCLUSIONS:
        refusal = _unprovable_refusal(
            run_id=run_id,
            detail_reason="ci-green conclusion unrecognized",
        )
    return refusal


def _latest_master_ci_run(*, repo: Path, runner: CommandRunner) -> _CiRun | CommandResult | None:
    result = _gh(
        repo=repo,
        runner=runner,
        argv=[
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
        ],
    )
    if result.exit_code != 0:
        if not _gh_has_stored_credential(repo=repo, runner=runner):
            return None
        return result
    parsed: object = json.loads(result.stdout)
    if not isinstance(parsed, list) or not parsed:
        return None
    payload = cast("list[object]", parsed)
    first = payload[0]
    if not isinstance(first, dict):
        return _malformed_payload(result=result, detail="unexpected gh run list shape")
    return cast("_CiRun", first)


def _gh_has_stored_credential(*, repo: Path, runner: CommandRunner) -> bool:
    result = _gh(repo=repo, runner=runner, argv=["auth", "token"])
    return result.exit_code == 0


def _ci_green_job(
    *, repo: Path, runner: CommandRunner, run_id: str
) -> _CiJob | CommandResult | None:
    result = _gh(repo=repo, runner=runner, argv=["run", "view", run_id, "--json", "jobs"])
    if result.exit_code != 0:
        return result
    parsed: object = json.loads(result.stdout)
    if not isinstance(parsed, dict):
        return _malformed_payload(result=result, detail="unexpected gh run view shape")
    payload = cast("dict[str, object]", parsed)
    jobs_raw = payload.get("jobs")
    if not isinstance(jobs_raw, list):
        return _malformed_payload(result=result, detail="unexpected gh jobs shape")
    jobs = cast("list[object]", jobs_raw)
    return _find_ci_green_job(jobs=jobs)


def _find_ci_green_job(*, jobs: list[object]) -> _CiJob | None:
    found: _CiJob | None = None
    for raw_job in jobs:
        if isinstance(raw_job, dict):
            job_payload = cast("dict[str, object]", raw_job)
            if job_payload.get("name") == _CI_GREEN_JOB:
                found = cast("_CiJob", raw_job)
    return found


def _malformed_payload(*, result: CommandResult, detail: str) -> CommandResult:
    return CommandResult(exit_code=1, stdout=result.stdout, stderr=detail)


def _gh(*, repo: Path, runner: CommandRunner, argv: list[str]) -> CommandResult:
    return runner.run(
        argv=["gh", *argv],
        cwd=repo,
        timeout_seconds=_GH_PREFLIGHT_TIMEOUT_SECONDS,
    )


def _run_id(*, run: _CiRun) -> str:
    raw = run.get("databaseId")
    return str(raw) if raw is not None else "<unknown>"


def _red_refusal(*, run_id: str, conclusion: str) -> MasterCiRefusal:
    return MasterCiRefusal(
        detail=_refusal_detail(run_id=run_id, reason=f"ci-green concluded {conclusion}"),
        record=_refusal_record(run_id=run_id, reason=_REASON_RED, detail=conclusion),
    )


def _credentialed_call_failure_refusal(*, result: CommandResult) -> MasterCiRefusal:
    stderr = result.stderr.strip()[:200]
    return MasterCiRefusal(
        detail=(
            "ERROR: latest master CI could not be read by credentialed gh; "
            "refusing dispatch before sandbox work. GitHub API state is unprovable. "
            f"stderr: {stderr or '<empty stderr>'}\n"
        ),
        record={
            "stage": _STAGE,
            "terminal": True,
            "status": "failed",
            "reason": _REASON_UNPROVABLE,
            "detail": "credentialed gh call failed",
            "gh_exit_code": result.exit_code,
            "gh_stderr": result.stderr,
        },
    )


def _unprovable_refusal(*, run_id: str, detail_reason: str) -> MasterCiRefusal:
    return MasterCiRefusal(
        detail=_refusal_detail(run_id=run_id, reason=detail_reason),
        record=_refusal_record(run_id=run_id, reason=_REASON_UNPROVABLE, detail=detail_reason),
    )


def _refusal_detail(*, run_id: str, reason: str) -> str:
    return (
        "ERROR: latest master CI is not proven green at required check `ci-green`; "
        "refusing dispatch before sandbox work.\n"
        f"Run databaseId: {run_id}\n"
        f"Reason: {reason}\n"
        "Recovery: if this is a master-health-restoration item parked behind red "
        "master, drive it in-session through worktree -> PR -> merge; PR CI is "
        "independent of master. See AGENTS.md and .claude-plugin/prose/implement.md "
        "Step 0. For repeat-flakes, rerun attempts are diagnostic only and may not "
        "produce a green master.\n"
    )


def _refusal_record(*, run_id: str, reason: str, detail: str) -> dict[str, object]:
    return {
        "stage": _STAGE,
        "terminal": True,
        "status": "failed",
        "reason": reason,
        "run_database_id": run_id,
        "required_job": _CI_GREEN_JOB,
        "detail": detail,
        "recovery": [
            " ".join(
                (
                    "For a master-health-restoration item parked behind red master, drive it",
                    "in-session through worktree -> PR -> merge; PR CI is independent of master.",
                )
            ),
            " ".join(
                (
                    "See AGENTS.md and .claude-plugin/prose/implement.md Step 0 for the",
                    "documented escape hatch and the repeat-flake caveat.",
                )
            ),
        ],
    }
