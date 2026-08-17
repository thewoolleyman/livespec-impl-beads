"""Tests for dispatcher outcome emission helpers."""

from __future__ import annotations

import json

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import emit_outcomes


def test_emit_outcomes_json_includes_present_fabro_failure_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    outcome = DispatchOutcome(
        work_item_id="bd-ib-rdbtzo.3",
        status="failed",
        stage="fabro-run",
        pr_number=None,
        merge_sha=None,
        detail="script failed with exit 2",
        fabro_run_id="01RUNCAUSE",
        fabro_failure_cause="script failed with exit 2",
        fabro_failure_category="deterministic",
        fabro_failure_signature="fix|deterministic|script failed",
    )

    emit_outcomes(outcomes=[outcome], as_json=True)

    payload = json.loads(capsys.readouterr().out)
    assert payload == [
        {
            "detail": "script failed with exit 2",
            "fabro_failure_cause": "script failed with exit 2",
            "fabro_failure_category": "deterministic",
            "fabro_failure_signature": "fix|deterministic|script failed",
            "fabro_run_id": "01RUNCAUSE",
            "merge_sha": None,
            "pr_number": None,
            "stage": "fabro-run",
            "status": "failed",
            "work_item_id": "bd-ib-rdbtzo.3",
        }
    ]
