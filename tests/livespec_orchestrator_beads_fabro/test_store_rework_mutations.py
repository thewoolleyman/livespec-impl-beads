"""Tests for the rework-pending marker store mutation."""

from __future__ import annotations

from livespec_orchestrator_beads_fabro._beads_client import FakeBeadsClient, make_beads_client
from livespec_orchestrator_beads_fabro._store_mutations import append_work_item
from livespec_orchestrator_beads_fabro._store_rework_mutations import (
    LABEL_REWORK_PENDING,
    rework_pending_label_removals,
    update_work_item_rework_pending,
)
from livespec_orchestrator_beads_fabro.store import read_work_items
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem


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


def _item(*, id_: str) -> WorkItem:
    return WorkItem(
        id=id_,
        type="task",
        status="active",
        title="t",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a0",
        assignee="alice",
        depends_on=(),
        captured_at="2026-08-28T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )


def test_update_work_item_rework_pending_stamps_and_clears_the_marker() -> None:
    append_work_item(path=_config(), item=_item(id_="li-rework"))

    update_work_item_rework_pending(path=_config(), item_id="li-rework", value=True)

    [marked] = list(read_work_items(path=_config()))
    assert marked.rework_pending is True
    assert LABEL_REWORK_PENDING in _fake().show_issue(issue_id="li-rework")["labels"]

    update_work_item_rework_pending(path=_config(), item_id="li-rework", value=False)

    [cleared] = list(read_work_items(path=_config()))
    assert cleared.rework_pending is False
    assert LABEL_REWORK_PENDING not in _fake().show_issue(issue_id="li-rework")["labels"]


def test_update_work_item_rework_pending_leaves_the_status_alone() -> None:
    """The stamp is label-only: routing the item is the caller's half."""
    append_work_item(path=_config(), item=_item(id_="li-rework-status"))

    update_work_item_rework_pending(path=_config(), item_id="li-rework-status", value=True)

    [marked] = list(read_work_items(path=_config()))
    assert (marked.status, marked.assignee) == ("active", "alice")


def test_rework_pending_label_removals_carries_the_marker_off_active_only() -> None:
    assert rework_pending_label_removals(status="active") == []
    for status in ("acceptance", "backlog", "ready", "blocked", "done", "pending-approval"):
        assert rework_pending_label_removals(status=status) == [LABEL_REWORK_PENDING]
