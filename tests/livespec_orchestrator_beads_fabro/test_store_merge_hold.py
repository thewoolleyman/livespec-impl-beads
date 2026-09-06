"""Coverage for the narrow merge-hold raw read.

The hold is a label, and `store._record_to_work_item` decodes labels into the
named fields the shared `WorkItem` model declares — a model this repository
does not own and cannot extend. So the surfaces the ratified hold binds read
the marker here, from the raw record, and this file pins the fail-soft shape
that read has to hold: a record with no usable id, or with labels that are not
a list of strings, contributes nothing rather than blanking the enumeration.
"""

from __future__ import annotations

import pytest
from livespec_orchestrator_beads_fabro import _store_merge_hold
from livespec_orchestrator_beads_fabro._beads_client import IssueDraft, make_beads_client
from livespec_orchestrator_beads_fabro._store_merge_hold import (
    MERGE_HOLD_LABEL_PREFIX,
    read_merge_held_work_item_ids,
    update_work_item_merge_hold,
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


def _seed(*, issue_id: str, labels: list[str]) -> None:
    client = make_beads_client(config=_config())
    _ = client.create_issue(
        draft=IssueDraft(
            issue_id=issue_id,
            issue_type="task",
            title=f"{issue_id} title",
            description="d",
            priority=2,
            assignee=None,
            created_at="2026-05-19T00:00:00Z",
            labels=list(labels),
            metadata={},
            spec_id=None,
            parent_id=None,
        )
    )


def test_only_the_labelled_ids_read_back_as_held() -> None:
    _seed(issue_id="bd-held", labels=[f"{MERGE_HOLD_LABEL_PREFIX}on"])
    _seed(issue_id="bd-free", labels=["intake:triaged"])
    _seed(issue_id="bd-bare", labels=[])

    assert read_merge_held_work_item_ids(path=_config()) == frozenset({"bd-held"})


def test_the_release_write_removes_the_id_from_the_held_set() -> None:
    """The set tracks the valve, so a released hold cannot linger on any surface."""
    _seed(issue_id="bd-held", labels=[])
    update_work_item_merge_hold(path=_config(), item_id="bd-held", value=True)
    assert read_merge_held_work_item_ids(path=_config()) == frozenset({"bd-held"})

    update_work_item_merge_hold(path=_config(), item_id="bd-held", value=False)

    assert read_merge_held_work_item_ids(path=_config()) == frozenset()


class _StubClient:
    """A read-only stand-in returning a fixed raw record set.

    Mirrors `test_store`'s stub, and for the same reason: the shapes below —
    a non-string id, labels that are not a list, a label list holding a
    non-string — are ones the fake tenant's own write surface never produces,
    while a live tenant read through a mismatched or truncated record can.
    """

    def __init__(self, *, records: list[dict[str, object]]) -> None:
        self._records = records

    def list_issues(self) -> list[dict[str, object]]:
        return [dict(record) for record in self._records]


def test_an_unusable_record_contributes_nothing_rather_than_failing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-soft over every unusable shape, while the usable rows still read."""
    held_label = f"{MERGE_HOLD_LABEL_PREFIX}on"
    stub = _StubClient(
        records=[
            {"id": "bd-held", "labels": [held_label]},
            {"id": 17, "labels": [held_label]},
            {"id": "bd-odd-labels", "labels": "not-a-list"},
            {"id": "bd-mixed-labels", "labels": [7, held_label]},
        ]
    )
    monkeypatch.setattr(_store_merge_hold, "make_beads_client", lambda **_: stub)

    held = read_merge_held_work_item_ids(path=_config())

    assert held == frozenset({"bd-held", "bd-mixed-labels"})
