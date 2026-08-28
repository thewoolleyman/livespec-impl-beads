"""Tests for the loop probe's ordered stage assertions (v076).

The step-outcome group carries the load. A probe that accepted a
warn-and-proceed record would certify the very degradation it exists to find,
so the negative cases enumerate each non-pass shape the dispatch vocabulary can
write rather than testing `failed` alone.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_stages import (
    PASSED_STATUS,
    PASSED_VERDICT,
    criteria_stage_failure,
    step_outcome_stage_failure,
    verdict_stage_failure,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

_TWO_ASSERTIONS = "The probe refuses without an item.\nThe probe never files one.\n"


def _item(**overrides: object) -> WorkItem:
    base = WorkItem(
        id="bd-ib-probe",
        type="task",
        status="ready",
        title="A probe fixture",
        description="Drive the loop.",
        origin="freeform",
        gap_id=None,
        rank="a2",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-28T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy="ai-only",
        acceptance_criteria=_TWO_ASSERTIONS,
    )
    return replace(base, **overrides)


def test_gradeable_effective_criteria_clear_the_pre_dispatch_stage() -> None:
    assert criteria_stage_failure(item=_item()) is None


def test_ungradeable_effective_criteria_fail_before_dispatch() -> None:
    failure = criteria_stage_failure(item=_item(acceptance_criteria=None))

    assert failure is not None
    assert "bd-ib-probe" in failure
    assert "before dispatch" in failure


def test_clean_step_outcomes_clear_the_stage() -> None:
    outcomes = [
        {"step": "source-checkout", "status": PASSED_STATUS},
        {"step": "master-ci", "status": PASSED_STATUS},
    ]

    assert step_outcome_stage_failure(outcomes=outcomes) is None


def test_no_step_outcomes_at_all_clears_the_stage() -> None:
    assert step_outcome_stage_failure(outcomes=[]) is None


@pytest.mark.parametrize("status", ["failed", "warn", "skipped", "waived"])
def test_any_non_pass_step_outcome_fails_the_probe(status: str) -> None:
    failure = step_outcome_stage_failure(outcomes=[{"step": "master-ci", "status": status}])

    assert failure is not None
    assert f"master-ci={status}" in failure


def test_a_step_outcome_missing_its_fields_still_names_what_it_can() -> None:
    failure = step_outcome_stage_failure(outcomes=[{}])

    assert failure is not None
    assert "<unnamed step>=<no status>" in failure


def test_a_passing_verdict_grounded_in_observed_evidence_clears_the_stage() -> None:
    assert verdict_stage_failure(verdict=PASSED_VERDICT, absent_evidence=()) is None


def test_absent_evidence_fails_the_verdict_stage_even_on_a_passing_verdict() -> None:
    failure = verdict_stage_failure(verdict=PASSED_VERDICT, absent_evidence=("telemetry",))

    assert failure is not None
    assert "not grounded in observed" in failure
    assert "telemetry" in failure


def test_a_non_passing_verdict_fails_the_verdict_stage() -> None:
    failure = verdict_stage_failure(verdict="NEEDS_ATTENTION", absent_evidence=())

    assert failure is not None
    assert "NEEDS_ATTENTION" in failure
