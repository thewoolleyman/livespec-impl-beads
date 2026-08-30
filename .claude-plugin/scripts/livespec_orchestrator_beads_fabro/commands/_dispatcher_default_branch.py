"""The ONE default-branch resolution every dispatch-path stage shares.

Ratified in `SPECIFICATION/contracts.md`, the default-branch-resolution clause:
a dispatch-path stage that references the target's primary branch MUST resolve
it -- `git symbolic-ref refs/remotes/origin/HEAD` first, `gh repo view --json
defaultBranchRef` when git has no answer -- and MUST NOT hardcode `master`,
because an adopter whose primary branch is `main` does not have the branch a
literal names, and gets a clean, plausible, wrong answer for it.

This lives in a module of its own rather than beside any one caller because the
clause says the dispatch path reuses a SINGLE resolution rather than carrying
its own ref constant. The master-CI preflight and the factory workflow-file
guard both ask this question; a second copy is how the two would come to answer
it differently.

The module also carries NO runtime import from `_dispatcher_engine` -- it names
`CommandRunner` under `TYPE_CHECKING` only. That is load-bearing, not
fastidiousness: the engine reaches the workflow guard transitively
(`_dispatcher_engine` -> `_dispatcher_plan` -> `_dispatcher_goal` ->
`_dispatcher_workflow_guard`), so a resolver the guard imports must not import
the engine back or the cycle closes and every one of those modules stops
importing at all.

NEITHER ROUTE FALLS BACK TO A CONSTANT. When both are silent the caller gets
`None` and refuses. A branch nobody could name is not a branch a diff range can
be built on or a green pipeline proven for, and defaulting to `master` there
would quietly reinstate exactly the hardcoding this clause retires.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandRunner

__all__: list[str] = [
    "ORIGIN_HEAD_ARGV",
    "REPO_VIEW_ARGV",
    "resolve_default_branch",
]

# The two routes, named so a refusal can quote what it asked and a caller can
# assert the ratified argv rather than a paraphrase of it.
ORIGIN_HEAD_ARGV: tuple[str, ...] = (
    "git",
    "symbolic-ref",
    "--short",
    "refs/remotes/origin/HEAD",
)
REPO_VIEW_ARGV: tuple[str, ...] = (
    "gh",
    "repo",
    "view",
    "--json",
    "defaultBranchRef",
    "--jq",
    ".defaultBranchRef.name",
)

_RESOLUTION_TIMEOUT_SECONDS = 30.0


def resolve_default_branch(*, repo: Path, runner: CommandRunner) -> str | None:
    """The target's default branch by the ratified two-route rule; None when silent."""
    head = runner.run(
        argv=list(ORIGIN_HEAD_ARGV),
        cwd=repo,
        timeout_seconds=_RESOLUTION_TIMEOUT_SECONDS,
    )
    if head.exit_code == 0:
        resolved = head.stdout.strip().removeprefix("origin/")
        if resolved != "":
            return resolved
    view = runner.run(
        argv=list(REPO_VIEW_ARGV),
        cwd=repo,
        timeout_seconds=_RESOLUTION_TIMEOUT_SECONDS,
    )
    if view.exit_code != 0:
        return None
    return view.stdout.strip() or None
