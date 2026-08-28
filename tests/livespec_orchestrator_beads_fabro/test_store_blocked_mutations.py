"""Tests for clearing the blocked-reason on every exit from `blocked`.

The escalation INTO `blocked` has a writer; these cover its converse. Both
measured exit paths are asserted — the terminal close and the valve move —
because the defect is a single missing obligation that surfaced identically on
two unrelated exits, not two separate bugs.
"""

from __future__ import annotations

from livespec_orchestrator_beads_fabro._beads_client import FakeBeadsClient, make_beads_client
from livespec_orchestrator_beads_fabro._store_mutations import (
    append_work_item,
    update_work_item_status,
)
from livespec_orchestrator_beads_fabro.store import read_work_items
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem, WorkItemStatus

# The wire vocabulary, stated literally rather than imported from the code
# under test: a test that reuses the implementation's own constant cannot
# catch a change to the label the ledger actually carries.
_BLOCKED_REASON_PREFIX = "blocked-reason:"


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="livespec-impl-beads",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _fake() -> FakeBeadsClient:
    client = make_beads_client(config=_config())
    assert isinstance(client, FakeBeadsClient)
    return client


def _item(*, id_: str, status: WorkItemStatus) -> WorkItem:
    return WorkItem(
        id=id_,
        type="task",
        status=status,
        title="t",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a0",
        assignee="alice",
        depends_on=(),
        captured_at="2026-08-28T00:00:00Z",
        resolution="completed" if status == "done" else None,
        reason=None,
        audit=None,
        superseded_by=None,
        blocked_reason="needs-human" if status == "blocked" else None,
    )


def _reason_labels(*, item_id: str) -> list[str]:
    labels = _fake().show_issue(issue_id=item_id)["labels"]
    return [label for label in labels if label.startswith(_BLOCKED_REASON_PREFIX)]


def _park_blocked(*, item_id: str) -> None:
    """Land an item in the parked state the exits below must clear.

    Asserted rather than assumed: every test here reads as a vacuous pass if
    the reason label was never written in the first place.
    """
    append_work_item(path=_config(), item=_item(id_=item_id, status="blocked"))
    assert _reason_labels(item_id=item_id) == [f"{_BLOCKED_REASON_PREFIX}needs-human"]


def test_closing_straight_out_of_blocked_clears_the_blocked_reason() -> None:
    """The close exit path — the measured homelab instances left `blocked` this way."""
    _park_blocked(item_id="li-blk-closed")

    append_work_item(path=_config(), item=_item(id_="li-blk-closed", status="done"))

    [read_back] = list(read_work_items(path=_config()))
    assert (read_back.status, read_back.blocked_reason) == ("done", None)
    assert _reason_labels(item_id="li-blk-closed") == []


def test_a_valve_move_out_of_blocked_clears_the_blocked_reason() -> None:
    """The valve exit path — the measured `bd-ib-tsna` instance left `blocked` this way."""
    _park_blocked(item_id="li-blk-moved")

    update_work_item_status(
        path=_config(),
        item_id="li-blk-moved",
        status="ready",
        clear_assignee=True,
    )

    [read_back] = list(read_work_items(path=_config()))
    assert (read_back.status, read_back.blocked_reason) == ("ready", None)
    assert _reason_labels(item_id="li-blk-moved") == []


def test_a_write_landing_on_blocked_keeps_the_blocked_reason() -> None:
    """The control for the clears above: a write that does NOT exit must not clear."""
    _park_blocked(item_id="li-blk-kept")

    update_work_item_status(path=_config(), item_id="li-blk-kept", status="blocked")

    [read_back] = list(read_work_items(path=_config()))
    assert (read_back.status, read_back.blocked_reason) == ("blocked", "needs-human")
    assert _reason_labels(item_id="li-blk-kept") == [f"{_BLOCKED_REASON_PREFIX}needs-human"]
