"""Grading what the loop probe's driven cycle produced.

This is the second half of the probe's stage order: the drive proves the change
was published, confined and merged; this module grades what came back. The three
assertions run in the contract's order -- journaled step outcomes, then the
acceptance verdict, then the scoped residue -- and the ordering matters here for
the same reason it does earlier. A residue read is only meaningful once the
cycle it is measuring has actually completed, so grading residue before the
verdict would report on a cycle that had not finished happening.

The residue leg is where the contract's two populations meet the verdict.
Unavailability outranks a hard failure: a source that could not be read tells
you nothing about whether residue remains, so reporting `stage-failed` from it
would name a finding the probe never actually made. And the unrelated delta
rides EVERY outcome, pass or fail, because it is information for the operator
rather than an input to the grade.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_report import (
    PASSED_OUTCOME,
    SOURCE_REMEDY,
    STAGE_FAILED_OUTCOME,
    STAGE_REMEDY,
    ProbeResult,
    probe_failure,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_residue import (
    SOURCE_UNAVAILABLE_OUTCOME,
    ResidueSnapshot,
    ResidueSource,
    reserved_identifiers,
    residue_report,
    unavailable_detail,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_stages import (
    RESIDUE_STAGE,
    STEP_OUTCOME_STAGE,
    VERDICT_STAGE,
    step_outcome_stage_failure,
    verdict_stage_failure,
)

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_cycle import (
        ProbeObservation,
    )

__all__: list[str] = [
    "graded_observation",
]


def graded_observation(
    *,
    work_item_id: str,
    observation: ProbeObservation,
    before: Sequence[ResidueSnapshot],
    sources: Sequence[ResidueSource],
    probe_run_id: str,
) -> ProbeResult:
    """Grade the observed cycle: step outcomes, then the verdict, then the residue."""
    steps = step_outcome_stage_failure(outcomes=observation.step_outcomes)
    if steps is not None:
        return probe_failure(
            probe_run_id=probe_run_id,
            stage=STEP_OUTCOME_STAGE,
            detail=steps,
            item_status=observation.item_status,
        )
    verdict = verdict_stage_failure(
        verdict=observation.verdict, absent_evidence=observation.absent_evidence
    )
    if verdict is not None:
        return probe_failure(
            probe_run_id=probe_run_id,
            stage=VERDICT_STAGE,
            detail=verdict,
            item_status=observation.item_status,
        )
    return _residue_verdict(
        work_item_id=work_item_id,
        before=before,
        sources=sources,
        probe_run_id=probe_run_id,
        item_status=observation.item_status,
    )


def _residue_verdict(
    *,
    work_item_id: str,
    before: Sequence[ResidueSnapshot],
    sources: Sequence[ResidueSource],
    probe_run_id: str,
    item_status: str,
) -> ProbeResult:
    report = residue_report(
        before=before,
        after=tuple(source.snapshot() for source in sources),
        reserved=reserved_identifiers(work_item_id=work_item_id, probe_run_id=probe_run_id),
        item_status=item_status,
    )
    if report.unavailable:
        return _residue_result(
            probe_run_id=probe_run_id,
            item_status=item_status,
            outcome=SOURCE_UNAVAILABLE_OUTCOME,
            detail=unavailable_detail(unavailable=report.unavailable),
            remedy=SOURCE_REMEDY,
            delta=report.unrelated_delta,
        )
    if report.hard_failures:
        return _residue_result(
            probe_run_id=probe_run_id,
            item_status=item_status,
            outcome=STAGE_FAILED_OUTCOME,
            detail="; ".join(report.hard_failures),
            remedy=STAGE_REMEDY,
            delta=report.unrelated_delta,
        )
    return _residue_result(
        probe_run_id=probe_run_id,
        item_status=item_status,
        outcome=PASSED_OUTCOME,
        detail="every stage assertion passed",
        remedy="",
        delta=report.unrelated_delta,
    )


def _residue_result(
    *,
    probe_run_id: str,
    item_status: str,
    outcome: str,
    detail: str,
    remedy: str,
    delta: tuple[str, ...],
) -> ProbeResult:
    return ProbeResult(
        passed=outcome == PASSED_OUTCOME,
        outcome=outcome,
        stage=RESIDUE_STAGE,
        detail=detail,
        remedy=remedy,
        probe_run_id=probe_run_id,
        item_status=item_status,
        unrelated_delta=delta,
    )
