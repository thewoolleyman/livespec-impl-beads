"""Tests for the loop probe's report vocabulary (v076).

The rendering group asserts the delta line carries the words "reported, not
asserted". That phrasing is not decoration: the contract's whole residue design
turns on unrelated movement being reported rather than graded, and an operator
reading a probe's output is the only place that distinction becomes visible.
"""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_report import (
    PASSED_OUTCOME,
    PROBE_OUTCOME_STAGE,
    PROBE_START_STAGE,
    STAGE_FAILED_OUTCOME,
    STAGE_REMEDY,
    ProbeResult,
    emit_probe_result,
    probe_failure,
    probe_result_record,
    probe_run_identifier,
    probe_start_record,
)

_ITEM = "bd-ib-probe"
_STARTED = "2026-08-28T00:00:00Z"


def test_the_run_identifier_is_probe_item_timestamp() -> None:
    assert (
        probe_run_identifier(work_item_id=_ITEM, started_at=_STARTED) == f"probe:{_ITEM}:{_STARTED}"
    )


def test_the_start_record_carries_the_reserved_identifier_set() -> None:
    run_id = probe_run_identifier(work_item_id=_ITEM, started_at=_STARTED)

    record = probe_start_record(work_item_id=_ITEM, probe_run_id=run_id)

    assert record["stage"] == PROBE_START_STAGE
    assert record["probe_run_id"] == run_id
    assert record["reserved_identifiers"] == [run_id, _ITEM]


def test_a_failure_verdict_defaults_to_the_stage_outcome_and_remedy() -> None:
    result = probe_failure(
        probe_run_id="probe:x:y", stage="merge", detail="a detail", item_status="active"
    )

    assert not result.passed
    assert result.outcome == STAGE_FAILED_OUTCOME
    assert result.remedy == STAGE_REMEDY
    assert result.item_status == "active"


def test_the_result_record_carries_the_stage_reached_and_the_delta() -> None:
    result = probe_failure(
        probe_run_id="probe:x:y", stage="residue", detail="a detail", item_status="acceptance"
    )

    record = probe_result_record(
        result=replace(result, unrelated_delta=("appeared attention:other",))
    )

    assert record["stage"] == PROBE_OUTCOME_STAGE
    assert record["probe_stage"] == "residue"
    assert record["item_status"] == "acceptance"
    assert record["unrelated_delta"] == ["appeared attention:other"]


def test_the_json_rendering_is_the_journal_record(capsys: pytest.CaptureFixture[str]) -> None:
    result = probe_failure(
        probe_run_id="probe:x:y", stage="merge", detail="a detail", item_status="active"
    )

    emit_probe_result(result=result, as_json=True)

    assert json.loads(capsys.readouterr().out) == probe_result_record(result=result)


def test_the_human_rendering_names_the_stage_the_state_and_the_remedy(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = probe_failure(
        probe_run_id="probe:x:y", stage="merge", detail="a detail", item_status="active"
    )

    emit_probe_result(result=result, as_json=False)

    out = capsys.readouterr().out
    assert "stage=merge" in out
    assert "item_status=active" in out
    assert f"Remedy: {STAGE_REMEDY}" in out


def test_a_passing_rendering_omits_the_remedy_and_reports_the_delta(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = ProbeResult(
        passed=True,
        outcome=PASSED_OUTCOME,
        stage="residue",
        detail="every stage assertion passed",
        remedy="",
        probe_run_id="probe:x:y",
        item_status="done",
        unrelated_delta=("appeared attention:other",),
    )

    emit_probe_result(result=result, as_json=False)

    out = capsys.readouterr().out
    assert "Remedy:" not in out
    assert "unrelated (reported, not asserted): appeared attention:other" in out
