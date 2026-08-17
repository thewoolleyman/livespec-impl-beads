"""Focused dispatch-factory marker tests."""

from __future__ import annotations

from livespec_orchestrator_beads_fabro._beads_client import (
    FakeBeadsClient,
    IssueDraft,
    make_beads_client,
)
from livespec_orchestrator_beads_fabro.store import (
    dispatch_factory_for,
    dispatch_factory_from_record,
)
from livespec_orchestrator_beads_fabro.types import StoreConfig


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


def _issue(*, issue_id: str) -> None:
    _ = _fake().create_issue(
        draft=IssueDraft(
            issue_id=issue_id,
            issue_type="task",
            title="title",
            description="description",
            assignee=None,
            created_at="2026-05-19T00:00:00Z",
        )
    )


def test_dispatch_factory_falls_back_to_legacy_comments() -> None:
    _issue(issue_id="li-aaa111")
    _fake().seed_comment(issue_id="li-aaa111", text="livespec-dispatch-factory: ")
    _fake().seed_comment(issue_id="li-aaa111", text="livespec-dispatch-factory: hp")

    assert dispatch_factory_for(path=_config(), work_item_id="li-aaa111") == "hp"


def test_dispatch_factory_from_record_ignores_malformed_metadata() -> None:
    assert dispatch_factory_from_record(record={"metadata": "not-json-object"}) is None
