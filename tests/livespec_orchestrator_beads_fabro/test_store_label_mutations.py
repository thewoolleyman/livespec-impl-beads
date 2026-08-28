"""Tests for the label-only store field mutations.

Moved verbatim from `test_store_mutations` with the primitives they cover,
when `_store_mutations` was decomposed along its label-only-writes seam.
"""

from __future__ import annotations

from livespec_orchestrator_beads_fabro._beads_client import FakeBeadsClient, make_beads_client
from livespec_orchestrator_beads_fabro._store_label_mutations import (
    update_work_item_awaits_scope_override,
    update_work_item_policy,
    update_work_item_workflow_scope_override,
)
from livespec_orchestrator_beads_fabro._store_mutations import append_work_item
from livespec_orchestrator_beads_fabro.store import read_work_items
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem
from livespec_runtime.work_items.types import AcceptancePolicy, AdmissionPolicy


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


def _item(
    *,
    id_: str,
    admission_policy: AdmissionPolicy | None = None,
    acceptance_policy: AcceptancePolicy | None = None,
) -> WorkItem:
    return WorkItem(
        id=id_,
        type="task",
        status="ready",
        title="t",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a0",
        assignee=None,
        depends_on=(),
        captured_at="2026-05-19T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy=admission_policy,
        acceptance_policy=acceptance_policy,
    )


def test_update_work_item_policy_replaces_requested_labels_only() -> None:
    append_work_item(
        path=_config(),
        item=_item(id_="li-pol", admission_policy="manual", acceptance_policy="ai-only"),
    )
    update_work_item_policy(
        path=_config(),
        item_id="li-pol",
        admission_policy="auto",
        acceptance_policy="human-only",
    )
    record = _fake().show_issue(issue_id="li-pol")
    assert "admission:auto" in record["labels"]
    assert "acceptance:human-only" in record["labels"]
    assert "admission:manual" not in record["labels"]
    assert "acceptance:ai-only" not in record["labels"]


def test_update_work_item_policy_noop_leaves_item_unchanged() -> None:
    append_work_item(
        path=_config(),
        item=_item(
            id_="li-pol-noop",
            admission_policy="manual",
            acceptance_policy="ai-then-human",
        ),
    )
    update_work_item_policy(path=_config(), item_id="li-pol-noop")
    [read_back] = list(read_work_items(path=_config()))
    assert (read_back.admission_policy, read_back.acceptance_policy) == (
        "manual",
        "ai-then-human",
    )


def test_update_work_item_awaits_scope_override_sets_and_clears_label() -> None:
    append_work_item(path=_config(), item=_item(id_="li-awaits"))
    update_work_item_awaits_scope_override(path=_config(), item_id="li-awaits", value=True)
    [with_signal] = list(read_work_items(path=_config()))
    assert with_signal.awaits_scope_override is True
    assert "awaits-scope-override" in _fake().show_issue(issue_id="li-awaits")["labels"]

    update_work_item_awaits_scope_override(path=_config(), item_id="li-awaits", value=False)

    [without_signal] = list(read_work_items(path=_config()))
    assert without_signal.awaits_scope_override is False
    assert "awaits-scope-override" not in _fake().show_issue(issue_id="li-awaits")["labels"]


def test_update_work_item_workflow_scope_override_replaces_the_awaiting_signal() -> None:
    append_work_item(path=_config(), item=_item(id_="li-scope"))
    update_work_item_awaits_scope_override(path=_config(), item_id="li-scope", value=True)

    update_work_item_workflow_scope_override(
        path=_config(), item_id="li-scope", value="citation-only"
    )

    labels = _fake().show_issue(issue_id="li-scope")["labels"]
    assert "workflow-scope-override:citation-only" in labels
    assert "awaits-scope-override" not in labels
