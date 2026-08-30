"""Merged-diff acquisition for the Dispatcher acceptance pass."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    CommandRunner,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_merge_pr_association import (
    associated_pr_numbers_for_merge,
)
from livespec_orchestrator_beads_fabro.effects import JsonParseFailure, parse_json

__all__: list[str] = [
    "DiffResult",
    "read_merged_diff",
]

_DIFF_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True, kw_only=True)
class DiffResult:
    """One merged-diff read: its text when there is one, and why when there is not.

    `empty` separates "the diff was READ and it changes zero files" from every
    other reason `merged_diff` is `None` — a command that failed, a merge sha
    that was never recorded, output that is not a patch at all. Both look like an
    absent diff here, but only the first is the subject of the empty-merged-diff
    refusal in the post-merge acceptance evidence rule of
    `SPECIFICATION/contracts.md`: a zero-change merge is an OBSERVATION, and the
    acceptance pass decides what it means from the item's change classification.
    Collapsing the two would make the refusal unable to fire on the one case it
    exists for, and would route an unobservable diff into the change-optional
    bypass, which is the fail-OPEN direction.
    """

    merged_diff: str | None
    reason: str
    gradeable: bool
    empty: bool = False


def read_merged_diff(*, repo: Path, outcome: DispatchOutcome, runner: CommandRunner) -> DiffResult:
    merge_sha = outcome.merge_sha
    if merge_sha is None:
        return DiffResult(merged_diff=None, reason="merge sha unavailable", gradeable=True)
    pr_number = outcome.pr_number
    if pr_number is not None:
        pr_result = runner.run(
            argv=["gh", "pr", "diff", str(pr_number), "--patch"],
            cwd=repo,
            timeout_seconds=_DIFF_TIMEOUT_SECONDS,
        )
        diff = _diff_from_command(
            result=pr_result,
            read_reason="pull request diff read",
            empty_reason="pull request diff is empty",
            failed_reason="pull request diff failed",
            no_file_changes_reason="pull request diff has no file changes",
        )
        if diff.merged_diff is not None:
            return diff
        if not diff.gradeable:
            associated = associated_pr_numbers_for_merge(
                repo=repo,
                merge_sha=merge_sha,
                runner=runner,
            )
            if associated is not None and pr_number not in associated:
                return DiffResult(
                    merged_diff=None,
                    reason=_pr_mismatch_reason(
                        pr_number=pr_number,
                        merge_sha=merge_sha,
                        associated=associated,
                    ),
                    gradeable=False,
                )
            return diff
    result = runner.run(
        argv=["git", "show", "--format=", "--find-renames", merge_sha],
        cwd=repo,
        timeout_seconds=_DIFF_TIMEOUT_SECONDS,
    )
    diff = _diff_from_command(
        result=result,
        read_reason="merged diff read",
        empty_reason="merged diff is empty",
        failed_reason="git show failed",
        no_file_changes_reason="merged diff has no file changes",
    )
    if pr_number is not None and diff.merged_diff is None and not diff.empty:
        return DiffResult(
            merged_diff=None,
            reason="pull request diff failed; git show failed",
            gradeable=diff.gradeable,
        )
    # A `git show` that succeeded and reported zero file changes keeps its own
    # reason: the merge genuinely delivered nothing, and reporting that as two
    # failed commands would describe the refusal's one real case as a tooling
    # fault, which is the reading an operator cannot act on.
    return diff


def _diff_from_command(
    *,
    result: CommandResult,
    read_reason: str,
    empty_reason: str,
    failed_reason: str,
    no_file_changes_reason: str,
) -> DiffResult:
    if result.exit_code != 0:
        return DiffResult(merged_diff=None, reason=failed_reason, gradeable=True)
    if not result.stdout.strip():
        return DiffResult(merged_diff=None, reason=empty_reason, gradeable=True, empty=True)
    if "diff --git " not in result.stdout:
        if _looks_like_pr_metadata_json(stdout=result.stdout):
            # Metadata where a patch belongs is the wrong OUTPUT, not a merge
            # that changed nothing, so it is deliberately NOT `empty`: routing
            # it into the change-optional bypass would grade an item against a
            # diff nobody ever read.
            return DiffResult(merged_diff=None, reason=empty_reason, gradeable=True)
        return DiffResult(
            merged_diff=None,
            reason=no_file_changes_reason,
            gradeable=False,
        )
    return DiffResult(merged_diff=result.stdout, reason=read_reason, gradeable=True)


def _looks_like_pr_metadata_json(*, stdout: str) -> bool:
    parsed_raw = parse_json(text=stdout)
    if isinstance(parsed_raw, JsonParseFailure) or not isinstance(parsed_raw, dict):
        return False
    parsed = cast("dict[str, object]", parsed_raw)
    return "mergeCommit" in parsed and "number" in parsed


def _pr_mismatch_reason(*, pr_number: int, merge_sha: str, associated: tuple[int, ...]) -> str:
    associated_text = ", ".join(f"#{number}" for number in associated) if associated else "none"
    return (
        f"recorded PR #{pr_number} does not contain merge sha {merge_sha}; "
        f"associated PRs: {associated_text}"
    )
