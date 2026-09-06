"""Coverage for the one attention row a merge-held item produces."""

import importlib
import json
from pathlib import Path

from livespec_orchestrator_beads_fabro.types import WorkItem

_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec_orchestrator_beads_fabro"
    / "commands"
    / "_needs_attention_merge_hold.py"
)
_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._needs_attention_merge_hold"


def _item(*, id_: str, status: str = "active") -> WorkItem:
    return WorkItem(
        id=id_,
        type="task",
        status=status,  # type: ignore[arg-type]
        title=f"{id_} title",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee="fabro",
        depends_on=(),
        captured_at="2026-05-19T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )


def _write_journal(project_root: Path, *, records: list[object]) -> None:
    journal = project_root / "tmp" / "fabro-dispatch-journal.jsonl"
    journal.parent.mkdir(parents=True, exist_ok=True)
    lines = [record if isinstance(record, str) else json.dumps(record) for record in records]
    _ = journal.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _merge_hold_items(**kwargs: object) -> list[object]:
    module = importlib.import_module(_MODULE_NAME)
    return module.merge_hold_items(**kwargs)


def test_a_held_active_item_gets_exactly_one_row_naming_its_pr_and_its_release(
    tmp_path: Path,
) -> None:
    """The whole visibility clause in one case: one row, the PR, the release action."""
    assert _MODULE_PATH.is_file()
    _write_journal(
        tmp_path,
        records=[
            {"stage": "ledger-admit", "work_item_id": "bd-held"},
            {
                "stage": "outcome",
                "outcome": {"work_item_id": "bd-held", "status": "green", "pr_number": 2211},
            },
        ],
    )

    attention = _merge_hold_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-held")],
        held_work_item_ids=frozenset({"bd-held"}),
    )

    assert [item.id for item in attention] == ["hygiene:merge-hold:bd-held"]
    row = attention[0]
    assert row.kind == "hygiene"
    assert "pull request #2211" in row.summary
    assert row.handoff.action_id == "set-merge-hold:bd-held:off"
    assert "--action set-merge-hold:bd-held:off" in row.handoff.command
    assert row.source_ref.work_item == "bd-held"


def test_an_unheld_item_and_a_held_item_outside_active_produce_nothing(tmp_path: Path) -> None:
    """The row's two retractions: releasing the hold, and leaving `active`."""
    assert _MODULE_PATH.is_file()
    _write_journal(tmp_path, records=[])

    attention = _merge_hold_items(
        project_root=tmp_path,
        repo="repo",
        items=[
            _item(id_="bd-free"),
            _item(id_="bd-accepted", status="acceptance"),
        ],
        held_work_item_ids=frozenset({"bd-accepted"}),
    )

    assert attention == []


def test_a_hold_with_no_journaled_pull_request_is_still_reported(tmp_path: Path) -> None:
    """A hold MUST NOT become invisible, so an unnameable PR costs the row nothing."""
    assert _MODULE_PATH.is_file()

    attention = _merge_hold_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-early")],
        held_work_item_ids=frozenset({"bd-early"}),
    )

    assert [item.id for item in attention] == ["hygiene:merge-hold:bd-early"]
    assert "no pull request named by the dispatch journal" in attention[0].summary


def test_the_newest_journaled_pull_request_wins_over_unusable_records(tmp_path: Path) -> None:
    """Newest-wins across both record shapes; a malformed number names nothing."""
    assert _MODULE_PATH.is_file()
    _write_journal(
        tmp_path,
        records=[
            "not-json",
            {"stage": "dispatch-id", "work_item_id": "bd-held", "pr_number": 11},
            {"stage": "outcome", "outcome": ["not-a-mapping"]},
            {"stage": "pr", "work_item_id": "bd-held", "pr_number": True},
            {"stage": "pr", "work_item_id": None, "pr_number": 99},
            {"stage": "outcome", "outcome": {"work_item_id": "bd-held", "pr_number": 12}},
        ],
    )

    attention = _merge_hold_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-held")],
        held_work_item_ids=frozenset({"bd-held"}),
    )

    assert "pull request #12" in attention[0].summary
