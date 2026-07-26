"""Tests for dispatch-claim WIP-cap accounting."""

import json
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_claim_reclaim import (
    claimed_active_count,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.types import WorkItem


def test_claimed_active_count_reclaims_non_green_terminal_outcome(tmp_path: Path) -> None:
    item = _item(item_id="bd-failed", status="active")
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    journal.append(record={"stage": "ledger-admit", "work_item_id": item.id})
    journal.append(
        record={
            "stage": "outcome",
            "outcome": {"work_item_id": item.id, "status": "failed", "stage": "fabro-run"},
        }
    )

    count = claimed_active_count(repo=tmp_path, items=[item], journal=journal)

    assert count == 0
    records = _records(path=journal.path)
    abandoned = records[-1]
    assert abandoned["stage"] == "dispatch-claim-abandoned"
    assert abandoned["work_item_id"] == item.id
    assert abandoned["reason"] == "terminal-outcome-non-green"


def test_claimed_active_count_reclaims_when_latest_admit_has_no_outcome(
    tmp_path: Path,
) -> None:
    item = _item(item_id="bd-killed", status="active")
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    journal.append(
        record={
            "stage": "outcome",
            "outcome": {"work_item_id": item.id, "status": "green", "stage": "done"},
        }
    )
    journal.append(record={"stage": "ledger-admit", "work_item_id": item.id})

    count = claimed_active_count(repo=tmp_path, items=[item], journal=journal)

    assert count == 0
    last_record = json.loads(journal.path.read_text(encoding="utf-8").splitlines()[-1])
    assert last_record["reason"] == "no-outcome-since-ledger-admit"


def test_claimed_active_count_reclaims_active_claim_with_missing_journal(
    tmp_path: Path,
) -> None:
    item = _item(item_id="bd-missing-journal", status="active")
    journal = JournalFile(path=tmp_path / "missing-journal.jsonl")

    count = claimed_active_count(repo=tmp_path, items=[item], journal=journal)

    assert count == 0
    assert _records(path=journal.path)[-1]["reason"] == "no-outcome-since-ledger-admit"


def test_claimed_active_count_tolerates_malformed_journal_for_active_items(
    tmp_path: Path,
) -> None:
    item = _item(item_id="bd-malformed-active", status="active")
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    journal_text = "\n".join(
        (
            "not-json",
            "[]",
            json.dumps({"stage": "ledger-admit", "work_item_id": 7}),
            json.dumps({"stage": "outcome", "outcome": "not-an-object"}),
            json.dumps({"stage": "outcome", "outcome": {"work_item_id": item.id}}),
        )
    )
    _ = journal.path.write_text(journal_text + "\n", encoding="utf-8")

    count = claimed_active_count(repo=tmp_path, items=[item], journal=journal)

    assert count == 0
    last_record = json.loads(journal.path.read_text(encoding="utf-8").splitlines()[-1])
    assert last_record["reason"] == "no-outcome-since-ledger-admit"


def test_claimed_active_count_reuses_loaded_history_for_multiple_dead_claims(
    tmp_path: Path,
) -> None:
    green = _item(item_id="bd-green-park", status="active")
    failed = _item(item_id="bd-failed-claim", status="active")
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    journal.append(record={"stage": "ledger-admit", "work_item_id": green.id})
    journal.append(
        record={
            "stage": "outcome",
            "outcome": {"work_item_id": green.id, "status": "green", "stage": "done"},
        }
    )
    journal.append(record={"stage": "ledger-admit", "work_item_id": failed.id})
    journal.append(
        record={
            "stage": "outcome",
            "outcome": {"work_item_id": failed.id, "status": "failed", "stage": "fabro-run"},
        }
    )

    count = claimed_active_count(repo=tmp_path, items=[green, failed], journal=journal)

    assert count == 1
    assert _records(path=journal.path)[-1]["work_item_id"] == failed.id


def test_claimed_active_count_ignores_malformed_journal_for_inactive_items(
    tmp_path: Path,
) -> None:
    item = _item(item_id="bd-ready", status="ready")
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    journal_text = "\n".join(
        (
            "not-json",
            "[]",
            json.dumps({"stage": "ledger-admit", "work_item_id": 7}),
            json.dumps({"stage": "outcome", "outcome": "not-an-object"}),
            json.dumps({"stage": "outcome", "outcome": {"work_item_id": item.id}}),
        )
    )
    _ = journal.path.write_text(journal_text, encoding="utf-8")

    count = claimed_active_count(repo=tmp_path, items=[item], journal=journal)

    assert count == 0
    assert journal.path.read_text(encoding="utf-8") == journal_text


def _item(*, item_id: str, status: str) -> WorkItem:
    return WorkItem(
        id=item_id,
        type="task",
        status=status,
        title="Claim",
        description="Dispatch claim fixture.",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee=None,
        depends_on=(),
        captured_at="2026-07-26T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy="ai-only",
    )


def _records(*, path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
