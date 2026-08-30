"""Tests for the file-scoped check's vacuous-match outcome and the gate rule.

Covers the scoped-check vacuity clause ratified in v091
(`SPECIFICATION/contracts.md`) and its scenario in
`SPECIFICATION/scenarios.md`: a file-scoped check that matched zero files
reports vacuity, not success.
"""

from __future__ import annotations

import importlib
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult

_VACUITY_MODULE = "livespec_orchestrator_beads_fabro.commands._dispatcher_scoped_check_vacuity"
_GUARD_MODULE = "livespec_orchestrator_beads_fabro.commands._dispatcher_workflow_guard"


class RecordingRunner:
    def __init__(self, *, result: CommandResult) -> None:
        self.result = result
        self.calls: list[tuple[list[str], Path]] = []

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (timeout_seconds, env, stdin)
        self.calls.append((argv, cwd))
        return self.result


def test_scoped_check_vacuity_module_exists_before_import() -> None:
    module_path = (
        Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
        / "_dispatcher_scoped_check_vacuity.py"
    )
    assert module_path.is_file()


def test_zero_matched_files_is_a_vacuous_match_never_a_pass() -> None:
    vacuity = importlib.import_module(_VACUITY_MODULE)

    # The scope matched nothing, so the check observed nothing — whichever way
    # its own verdict would have leaned had it observed something.
    assert vacuity.scoped_check_outcome(matched_file_count=0, failing=False) == "vacuous-match"
    assert vacuity.scoped_check_outcome(matched_file_count=0, failing=True) == "vacuous-match"


def test_one_or_more_matched_files_yields_the_normal_pass_or_fail_outcome() -> None:
    vacuity = importlib.import_module(_VACUITY_MODULE)

    assert vacuity.scoped_check_outcome(matched_file_count=2, failing=False) == "pass"
    assert vacuity.scoped_check_outcome(matched_file_count=1, failing=True) == "fail"


def test_gate_counts_a_vacuous_match_toward_neither_passing_nor_failing() -> None:
    vacuity = importlib.import_module(_VACUITY_MODULE)

    tally = vacuity.gate_tally(outcomes=("pass", "fail", "vacuous-match", "vacuous-match"))

    # Four outcomes, but only two of them are evidence a gate may count.
    assert tally.passing == 1
    assert tally.failing == 1
    assert tally.vacuous == 2


def test_gate_reading_only_vacuous_matches_has_no_evidence_either_way() -> None:
    vacuity = importlib.import_module(_VACUITY_MODULE)

    tally = vacuity.gate_tally(outcomes=("vacuous-match",))

    assert tally.passing == 0
    assert tally.failing == 0
    assert tally.vacuous == 1
    # Not failing evidence either: vacuity moves the gate's verdict nowhere.
    assert vacuity.gate_exit_code(tally=tally) == 0


def test_gate_exit_code_is_non_zero_only_on_observed_failing_evidence() -> None:
    vacuity = importlib.import_module(_VACUITY_MODULE)

    assert vacuity.gate_exit_code(tally=vacuity.gate_tally(outcomes=("fail",))) == 1
    assert vacuity.gate_exit_code(tally=vacuity.gate_tally(outcomes=("pass",))) == 0
    assert vacuity.gate_exit_code(tally=vacuity.gate_tally(outcomes=())) == 0


def test_workflow_guard_over_an_empty_diff_reports_vacuous_match() -> None:
    guard = importlib.import_module(_GUARD_MODULE)
    runner = RecordingRunner(result=CommandResult(exit_code=0, stdout="", stderr=""))

    result = guard.check_no_workflow_changes(repo=Path(), runner=runner)

    # A file-scoped check over a zero-change diff matches zero files BY
    # CONSTRUCTION — the shape that let this very check pass vacuously over an
    # empty merge for all four review rounds.
    assert result.outcome == "vacuous-match"
    assert result.outcome != "pass"
    assert "vacuous-match" in result.message
    assert result.exit_code == 0


def test_workflow_guard_vacuous_match_is_neither_pass_nor_fail_evidence_to_a_gate() -> None:
    guard = importlib.import_module(_GUARD_MODULE)
    vacuity = importlib.import_module(_VACUITY_MODULE)
    runner = RecordingRunner(
        result=CommandResult(exit_code=0, stdout="src/app.py\ndocs/readme.md\n", stderr="")
    )

    result = guard.check_no_workflow_changes(repo=Path(), runner=runner)
    tally = vacuity.gate_tally(outcomes=(result.outcome,))

    assert result.outcome == "vacuous-match"
    assert tally.passing == 0
    assert tally.failing == 0
    assert tally.vacuous == 1


def test_workflow_guard_with_matched_files_reports_fail_not_vacuous_match() -> None:
    guard = importlib.import_module(_GUARD_MODULE)
    vacuity = importlib.import_module(_VACUITY_MODULE)
    runner = RecordingRunner(
        result=CommandResult(
            exit_code=0,
            stdout=".github/workflows/ci.yml\nsrc/app.py\n",
            stderr="",
        )
    )

    result = guard.check_no_workflow_changes(repo=Path(), runner=runner)
    tally = vacuity.gate_tally(outcomes=(result.outcome,))

    assert result.outcome == "fail"
    assert result.exit_code == 1
    assert tally.failing == 1
    assert tally.vacuous == 0


def test_workflow_guard_unreadable_diff_carries_no_scoped_check_outcome() -> None:
    guard = importlib.import_module(_GUARD_MODULE)

    runner = RecordingRunner(
        result=CommandResult(exit_code=128, stdout="", stderr="fatal: no merge base")
    )

    result = guard.check_no_workflow_changes(repo=Path(), runner=runner)

    # The scope was never resolved, so there is no matched-file count to call
    # vacuous — this is the older "could not inspect" arm, kept distinct.
    assert result.outcome is None
    assert result.exit_code == 2
