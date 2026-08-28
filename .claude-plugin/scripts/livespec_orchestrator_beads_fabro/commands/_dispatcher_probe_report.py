"""The loop probe's report vocabulary: its verdict, its records, and its rendering.

The failure leg of the loop-probe clause in `SPECIFICATION/contracts.md` is what
shapes this module. A failed probe MUST report the stage it reached, the item's
CURRENT lifecycle state, and the named remedy -- and it must leave the item
wherever the ordinary machinery put it, visible and disposable through the
normal valves. So `item_status` is a REQUIRED field of the verdict rather than
an optional decoration: a `ProbeResult` that could be built without it would let
a failure report go silent on the one fact an operator needs to act.

The remedies are constants here rather than prose composed at each raise site,
because the operator-facing instruction for an escape that has not merged
("stop; nothing merged") and one that has ("the operator reverts the named
commit") are OPPOSITE actions. Two call sites composing that text independently
is how they eventually come to say the same thing about different situations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_residue import (
    reserved_identifiers,
)
from livespec_orchestrator_beads_fabro.io import write_stdout

__all__: list[str] = [
    "CONFINEMENT_ESCAPE_OUTCOME",
    "MERGED_ESCAPE_OUTCOME",
    "PASSED_OUTCOME",
    "PROBE_OUTCOME_STAGE",
    "PROBE_START_STAGE",
    "REVERT_REMEDY",
    "SOURCE_REMEDY",
    "STAGE_FAILED_OUTCOME",
    "STAGE_REMEDY",
    "STOP_REMEDY",
    "ProbeResult",
    "emit_probe_result",
    "probe_failure",
    "probe_result_record",
    "probe_run_identifier",
    "probe_start_record",
]

PROBE_START_STAGE = "probe-start"
PROBE_OUTCOME_STAGE = "probe-outcome"

PASSED_OUTCOME = "pass"
STAGE_FAILED_OUTCOME = "stage-failed"
CONFINEMENT_ESCAPE_OUTCOME = "confinement-escape"
MERGED_ESCAPE_OUTCOME = "merged-escape"

STOP_REMEDY = (
    "stop; nothing merged. Confine the designated item's change to the"
    " sanctioned probe directory and re-run the probe."
)
REVERT_REMEDY = (
    "the operator reverts the named merged commit; the probe reverts nothing"
    " itself. Then confine the change and re-run the probe."
)
SOURCE_REMEDY = (
    "restore the unreadable source and re-run the probe; do not read the"
    " unavailability as emptiness or resolution."
)
STAGE_REMEDY = (
    "the item is left wherever the ordinary machinery put it; dispose of it"
    " through the normal valves and recovery surfaces."
)


@dataclass(frozen=True, kw_only=True)
class ProbeResult:
    """One probe cycle's verdict plus everything the failure leg must report."""

    passed: bool
    outcome: str
    stage: str
    detail: str
    remedy: str
    probe_run_id: str
    item_status: str
    unrelated_delta: tuple[str, ...] = ()


def probe_run_identifier(*, work_item_id: str, started_at: str) -> str:
    """The reserved run identifier the probe journals at start."""
    return f"probe:{work_item_id}:{started_at}"


def probe_start_record(*, work_item_id: str, probe_run_id: str) -> dict[str, object]:
    """The record the probe journals at start, carrying its reserved identifiers."""
    return {
        "stage": PROBE_START_STAGE,
        "work_item_id": work_item_id,
        "probe_run_id": probe_run_id,
        "reserved_identifiers": list(
            reserved_identifiers(work_item_id=work_item_id, probe_run_id=probe_run_id)
        ),
    }


def probe_result_record(*, result: ProbeResult) -> dict[str, object]:
    """The terminal probe record: the verdict, the stage reached, and the delta."""
    return {
        "stage": PROBE_OUTCOME_STAGE,
        "probe_run_id": result.probe_run_id,
        "outcome": result.outcome,
        "probe_stage": result.stage,
        "passed": result.passed,
        "item_status": result.item_status,
        "detail": result.detail,
        "remedy": result.remedy,
        "unrelated_delta": list(result.unrelated_delta),
    }


def probe_failure(
    *,
    probe_run_id: str,
    stage: str,
    detail: str,
    item_status: str,
    outcome: str = STAGE_FAILED_OUTCOME,
    remedy: str = STAGE_REMEDY,
) -> ProbeResult:
    """One failed probe verdict, always carrying the item's current lifecycle state."""
    return ProbeResult(
        passed=False,
        outcome=outcome,
        stage=stage,
        detail=detail,
        remedy=remedy,
        probe_run_id=probe_run_id,
        item_status=item_status,
    )


def emit_probe_result(*, result: ProbeResult, as_json: bool) -> None:
    """Render the verdict, and render the unrelated delta as REPORTED, not asserted."""
    if as_json:
        payload = probe_result_record(result=result)
        _ = write_stdout(text=json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return
    _ = write_stdout(
        text=(
            f"{result.outcome}  {result.probe_run_id}  stage={result.stage}"
            f"  item_status={result.item_status}\n{result.detail}\n"
        )
    )
    if result.remedy:
        _ = write_stdout(text=f"Remedy: {result.remedy}\n")
    for line in result.unrelated_delta:
        _ = write_stdout(text=f"unrelated (reported, not asserted): {line}\n")
