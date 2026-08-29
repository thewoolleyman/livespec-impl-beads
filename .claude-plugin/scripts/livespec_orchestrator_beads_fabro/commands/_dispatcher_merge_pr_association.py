"""Which pull request actually carries a work-item's merge sha.

The Dispatcher discovers a work-item's pull request BY BRANCH NAME
(`gh pr view <branch>`), and a branch name is not the same identity as
"the pull request whose commits carry the merge sha". A reused, stale or
recreated branch can resolve to a pull request that never produced the
merge commit the outcome goes on to record, so the recorded number and
the recorded sha can name two different pieces of work.

This module owns the merge-sha side of that identity. It asks the forge
which pull requests it associates with a commit, and CORRECTS the
recorded number when the branch-resolved one demonstrably is not among
them.

The correction is deliberately CONSERVATIVE. It rewrites the number only
when the forge names exactly ONE associated pull request — an
unambiguous answer to "which pull request contains this commit". When
the forge names several, or names none, or cannot be reached, the
branch-resolved number is left standing so the acceptance pass's own
cross-check still routes the mismatch to a non-gradeable needs-attention
outcome. Guessing between candidates would trade a detectable wrong
answer for an undetectable one.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_run_status import PrView
from livespec_orchestrator_beads_fabro.effects import JsonParseFailure, parse_json

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
        CommandRunner,
        JournalWriter,
    )

__all__: list[str] = [
    "associated_pr_numbers_for_merge",
    "pr_view_for_merge_sha",
]

_ASSOCIATION_TIMEOUT_SECONDS = 30.0
_RECORDING_STAGE = "pr-merge-sha-recording"


def associated_pr_numbers_for_merge(
    *, repo: Path, merge_sha: str, runner: CommandRunner
) -> tuple[int, ...] | None:
    """The pull requests the forge associates with `merge_sha`.

    None means the question could not be asked (the forge call failed, or
    answered in a shape this cannot read) — which is NOT the same as the
    empty tuple, which means the forge answered "no pull request contains
    this commit". Callers must keep the two apart: only the second is
    evidence about the commit.
    """
    result = runner.run(
        argv=[
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            f"/repos/{{owner}}/{{repo}}/commits/{merge_sha}/pulls",
        ],
        cwd=repo,
        timeout_seconds=_ASSOCIATION_TIMEOUT_SECONDS,
    )
    if result.exit_code != 0:
        return None
    parsed_raw = parse_json(text=result.stdout)
    if isinstance(parsed_raw, JsonParseFailure) or not isinstance(parsed_raw, list):
        return None
    parsed = cast("list[Any]", parsed_raw)
    numbers: list[int] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        record = cast("dict[str, object]", item)
        number = record.get("number")
        if isinstance(number, int) and not isinstance(number, bool):
            numbers.append(number)
    return tuple(numbers)


def pr_view_for_merge_sha(
    *,
    repo: Path,
    work_item_id: str,
    merged: PrView,
    runner: CommandRunner,
    journal: JournalWriter,
) -> PrView:
    """Return `merged` with its number re-resolved from its own merge sha.

    Every outcome is journaled under a single stage so the recorded number
    can always be traced back to how it was chosen — a correction, an
    ambiguous or absent association left standing, or an unreachable forge.
    """
    merge_sha = merged.merge_sha
    if merge_sha is None:
        return merged
    associated = associated_pr_numbers_for_merge(repo=repo, merge_sha=merge_sha, runner=runner)
    if associated is None:
        _journal(
            journal=journal,
            work_item_id=work_item_id,
            outcome="unavailable",
            branch_pr_number=merged.number,
            merge_sha=merge_sha,
            associated=(),
        )
        return merged
    if merged.number in associated:
        _journal(
            journal=journal,
            work_item_id=work_item_id,
            outcome="confirmed",
            branch_pr_number=merged.number,
            merge_sha=merge_sha,
            associated=associated,
        )
        return merged
    if len(associated) != 1:
        _journal(
            journal=journal,
            work_item_id=work_item_id,
            outcome="uncorrected",
            branch_pr_number=merged.number,
            merge_sha=merge_sha,
            associated=associated,
        )
        return merged
    _journal(
        journal=journal,
        work_item_id=work_item_id,
        outcome="corrected",
        branch_pr_number=merged.number,
        merge_sha=merge_sha,
        associated=associated,
    )
    return replace(merged, number=associated[0])


def _journal(
    *,
    journal: JournalWriter,
    work_item_id: str,
    outcome: str,
    branch_pr_number: int,
    merge_sha: str,
    associated: tuple[int, ...],
) -> None:
    journal.append(
        record={
            "work_item_id": work_item_id,
            "stage": _RECORDING_STAGE,
            "outcome": outcome,
            "branch_pr_number": branch_pr_number,
            "merge_sha": merge_sha,
            "associated_pr_numbers": list(associated),
        }
    )
