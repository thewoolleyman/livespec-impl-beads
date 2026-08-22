"""Post-merge AI acceptance pass for Dispatcher completions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_acceptance_criteria import (
    CriterionCheck,
    criteria_checks,
    criteria_lines,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    CommandRunner,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "NO_CHANGE_NEEDED_VERDICT",
    "AcceptancePassResult",
    "CriterionCheck",
    "run_acceptance_pass",
]

NO_CHANGE_NEEDED_VERDICT = "NO_CHANGE_NEEDED"

_DIFF_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True, kw_only=True)
class AcceptancePassResult:
    """The post-merge acceptance verdict and the inputs that produced it."""

    verdict: str
    merged_diff: str | None
    diff_reason: str
    telemetry_passed: bool
    telemetry_reason: str
    criteria: tuple[CriterionCheck, ...]

    def journal_record(self, *, work_item_id: str, policy: str) -> dict[str, object]:
        return {
            "stage": "acceptance-ai-pass",
            "work_item_id": work_item_id,
            "verdict": self.verdict,
            "acceptance_policy": policy,
            "diff": {
                "observed": self.merged_diff is not None,
                "bytes": 0 if self.merged_diff is None else len(self.merged_diff.encode()),
                "reason": self.diff_reason,
            },
            "criteria": {
                "observed": bool(self.criteria),
                "checks": [check.as_record() for check in self.criteria],
            },
            "telemetry": {
                "observed": True,
                "passed": self.telemetry_passed,
                "reason": self.telemetry_reason,
            },
        }


def run_acceptance_pass(
    *,
    repo: Path,
    item: WorkItem,
    outcome: DispatchOutcome,
    runner: CommandRunner | None = None,
) -> AcceptancePassResult:
    """Read the merged diff, judge criteria, watch telemetry, and return PASS/FAIL."""
    active_runner = ShellCommandRunner() if runner is None else runner
    diff_result = _read_merged_diff(repo=repo, outcome=outcome, runner=active_runner)
    telemetry_passed, telemetry_reason = _telemetry_verdict(outcome=outcome)
    checks = criteria_checks(
        criteria_text=_effective_criteria_text(item=item),
        merged_diff=diff_result.merged_diff,
        telemetry_passed=telemetry_passed,
    )
    verdict = _verdict(diff=diff_result, telemetry=telemetry_passed, checks=checks)
    return AcceptancePassResult(
        verdict=verdict,
        merged_diff=diff_result.merged_diff,
        diff_reason=diff_result.reason,
        telemetry_passed=telemetry_passed,
        telemetry_reason=telemetry_reason,
        criteria=checks,
    )


@dataclass(frozen=True, kw_only=True)
class _DiffResult:
    merged_diff: str | None
    reason: str


def _read_merged_diff(
    *, repo: Path, outcome: DispatchOutcome, runner: CommandRunner
) -> _DiffResult:
    merge_sha = outcome.merge_sha
    if merge_sha is None:
        return _DiffResult(merged_diff=None, reason="merge sha unavailable")
    result = runner.run(
        argv=["git", "show", "--format=", "--find-renames", merge_sha],
        cwd=repo,
        timeout_seconds=_DIFF_TIMEOUT_SECONDS,
    )
    return _diff_from_command(result=result)


def _diff_from_command(*, result: CommandResult) -> _DiffResult:
    if result.exit_code != 0:
        return _DiffResult(merged_diff=None, reason="git show failed")
    if not result.stdout.strip():
        return _DiffResult(merged_diff="", reason="merged diff is empty")
    return _DiffResult(merged_diff=result.stdout, reason="merged diff read")


def _telemetry_verdict(*, outcome: DispatchOutcome) -> tuple[bool, str]:
    if outcome.status != "green":
        return False, f"dispatch outcome status was {outcome.status!r}"
    if outcome.pr_number is None:
        return False, "merged PR number unavailable"
    if outcome.merge_sha is None:
        return True, "green merged dispatch with PR; merge sha unavailable"
    return True, "green merged dispatch with PR and merge sha"


def _effective_criteria_text(*, item: WorkItem) -> str | None:
    if criteria_lines(criteria_text=item.acceptance_criteria):
        return item.acceptance_criteria
    return _description_exit_criteria(description=item.description)


def _description_exit_criteria(*, description: str) -> str | None:
    lines = description.splitlines()
    section_lines: list[str] = []
    in_section = False
    section_level = 0
    for raw in lines:
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw)
        if heading is not None:
            level = len(heading.group(1))
            title = heading.group(2).strip().casefold()
            if in_section and level <= section_level:
                break
            if title == "exit criteria":
                in_section = True
                section_level = level
                continue
        if in_section:
            section_lines.append(raw)
    text = "\n".join(section_lines).strip()
    if not text:
        return None
    return text


def _passes(*, diff: _DiffResult, telemetry: bool, checks: tuple[CriterionCheck, ...]) -> bool:
    if not telemetry:
        return False
    if diff.merged_diff is None:
        return False
    return bool(checks) and all(check.passed for check in checks)


def _verdict(*, diff: _DiffResult, telemetry: bool, checks: tuple[CriterionCheck, ...]) -> str:
    if telemetry and diff.merged_diff == "":
        return NO_CHANGE_NEEDED_VERDICT
    if _passes(diff=diff, telemetry=telemetry, checks=checks):
        return "PASS"
    return "FAIL"
