"""The git/forge reads the master-CI preflight makes, and the shapes they return.

Split out of `_dispatcher_master_ci_preflight` along the seam between ASKING —
which argv, which timeout, which payload key — and CLASSIFYING what came back,
which stays there. The two change for different reasons: a `gh` output-shape
change touches only this module, and a policy change about what counts as proof
touches only the classifier.

THE DEFAULT-BRANCH RESOLUTION IS THE POINT OF THIS MODULE'S EXISTENCE. It is the
ratified two-route rule -- `git symbolic-ref refs/remotes/origin/HEAD` first,
`gh repo view --json defaultBranchRef` when git has no answer -- and it replaces
a hard-coded branch literal that quietly asked the forge about a branch adopters
whose primary branch is `main` do not have. Neither route is a fallback to a
CONSTANT: when both are silent the caller gets `None` and refuses, because a
branch nobody could name is not a branch that can be proven green.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    # Deferred deliberately: the post-merge janitor's VENUE resolution reuses
    # `resolve_default_branch`, and `_dispatcher_engine` imports that janitor
    # slice at module scope. A runtime import of the engine here would close
    # that ring and break the import, while these two names are only ever
    # annotations.
    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
        CommandResult,
        CommandRunner,
    )

__all__: list[str] = [
    "UNKNOWN_RUN",
    "CiJob",
    "CiRun",
    "find_job",
    "has_stored_credential",
    "job_records",
    "list_runs",
    "resolve_default_branch",
    "run_id_of",
    "run_records",
    "view_run_jobs",
]

_PREFLIGHT_TIMEOUT_SECONDS = 30.0

# The id a refusal names when no run was read at all — the same mark the journal
# record carries, so "which run?" has one answer across text and record.
UNKNOWN_RUN = "<none>"


class CiRun(TypedDict, total=False):
    """One `gh run list` record, as loosely as the forge actually returns it."""

    status: str | None
    conclusion: str | None
    databaseId: int | str | None


class CiJob(TypedDict, total=False):
    """One job of a `gh run view --json jobs` payload."""

    name: str | None
    conclusion: str | None
    status: str | None


def resolve_default_branch(*, repo: Path, runner: CommandRunner) -> str | None:
    """The target's default branch by the ratified two-route rule; None when silent."""
    head = runner.run(
        argv=["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        cwd=repo,
        timeout_seconds=_PREFLIGHT_TIMEOUT_SECONDS,
    )
    if head.exit_code == 0:
        resolved = head.stdout.strip().removeprefix("origin/")
        if resolved != "":
            return resolved
    view = _gh(
        repo=repo,
        runner=runner,
        argv=["repo", "view", "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"],
    )
    if view.exit_code != 0:
        return None
    return view.stdout.strip() or None


def has_stored_credential(*, repo: Path, runner: CommandRunner) -> bool:
    """Whether this host holds a `gh` credential it could have checked with."""
    return _gh(repo=repo, runner=runner, argv=["auth", "token"]).exit_code == 0


def list_runs(*, repo: Path, runner: CommandRunner, workflow: str, branch: str) -> CommandResult:
    """The latest run of `workflow` on `branch`, as `gh` reports it."""
    return _gh(
        repo=repo,
        runner=runner,
        argv=[
            "run",
            "list",
            "--branch",
            branch,
            "--limit",
            "1",
            "--workflow",
            workflow,
            "--json",
            "status,conclusion,databaseId",
        ],
    )


def view_run_jobs(*, repo: Path, runner: CommandRunner, run_id: str) -> CommandResult:
    """The jobs of one run, as `gh` reports them."""
    return _gh(repo=repo, runner=runner, argv=["run", "view", run_id, "--json", "jobs"])


def run_records(*, result: CommandResult) -> list[object] | None:
    """The `gh run list` records, or None when the payload is not the listed shape."""
    parsed: object = json.loads(result.stdout)
    if not isinstance(parsed, list):
        return None
    return cast("list[object]", parsed)


def job_records(*, result: CommandResult) -> list[object] | None:
    """The `gh run view` job records, or None when the payload is not that shape."""
    parsed: object = json.loads(result.stdout)
    if not isinstance(parsed, dict):
        return None
    jobs_raw = cast("dict[str, object]", parsed).get("jobs")
    if not isinstance(jobs_raw, list):
        return None
    return cast("list[object]", jobs_raw)


def find_job(*, jobs: list[object], name: str) -> CiJob | None:
    """The named job among `jobs`, ignoring records that are not objects."""
    found: CiJob | None = None
    for raw_job in jobs:
        if isinstance(raw_job, dict):
            job_payload = cast("dict[str, object]", raw_job)
            if job_payload.get("name") == name:
                found = cast("CiJob", raw_job)
    return found


def run_id_of(*, run: CiRun) -> str:
    """The run's database id as a string, or the unknown-run mark."""
    raw = run.get("databaseId")
    return str(raw) if raw is not None else UNKNOWN_RUN


def _gh(*, repo: Path, runner: CommandRunner, argv: list[str]) -> CommandResult:
    return runner.run(
        argv=["gh", *argv],
        cwd=repo,
        timeout_seconds=_PREFLIGHT_TIMEOUT_SECONDS,
    )
