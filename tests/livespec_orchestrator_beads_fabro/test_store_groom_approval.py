"""The groom-cut approval record: what it refuses, and where it is stamped.

Two properties carry the weight here.

The REFUSAL arm is what separates this from a seam that merely records an
approval: `require_groom_approval` must reject an absent record and a record
naming no approver or no route, because a filing seam that records without
refusing still files N slices and closes the original on any caller's
say-so.

The STAMP arm pins the key at the metadata TOP LEVEL and proves a nested
neighbour survives the write. `bd update --metadata` MERGES top-level keys
but REPLACES a nested object wholesale, so a record tucked under an existing
object would silently destroy every sub-key the payload did not resend.

The module is reached through `importlib` rather than a top-level import so
this file's first assertion is a genuine one about the module's existence,
not a collection error.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest
from livespec_orchestrator_beads_fabro._beads_client import (
    FakeBeadsClient,
    IssueDraft,
    make_beads_client,
)
from livespec_orchestrator_beads_fabro.errors import GroomApprovalRequiredError
from livespec_orchestrator_beads_fabro.types import StoreConfig

_MODULE_NAME = "livespec_orchestrator_beads_fabro._store_groom_approval"
_MODULE_PATH = Path(
    ".claude-plugin/scripts/livespec_orchestrator_beads_fabro/_store_groom_approval.py"
)


def _approval_module() -> Any:
    """Import the approval-record module, proving the file exists first."""
    assert _MODULE_PATH.is_file()
    return importlib.import_module(_MODULE_NAME)


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
            created_at="2026-09-06T00:00:00Z",
        )
    )


def _metadata_of(*, issue_id: str) -> dict[str, Any]:
    raw = _fake().show_issue(issue_id=issue_id).get("metadata")
    assert isinstance(raw, dict)
    return dict(raw)


def _approval(*, approver: str = "thewoolleyman", route: str = "resolve-blocked comment 41") -> Any:
    return _approval_module().GroomApproval(approver=approver, route=route)


def test_an_approval_record_names_the_approver_and_the_route() -> None:
    """The record carries both halves the contract requires of it."""
    approval = _approval(approver="thewoolleyman", route="resolve-blocked:bd-ib-ouoq:ready")

    assert approval.approver == "thewoolleyman"
    assert approval.route == "resolve-blocked:bd-ib-ouoq:ready"


def test_an_absent_approval_record_is_refused() -> None:
    """The near-miss shape: a filing that carries no approval evidence at all."""
    with pytest.raises(GroomApprovalRequiredError, match="no approval record was supplied"):
        _ = _approval_module().require_groom_approval(approval=None)


def test_an_approval_record_naming_no_approver_is_refused() -> None:
    """A blank identity is absence, not an approver named ''."""
    with pytest.raises(GroomApprovalRequiredError, match="names no approver identity"):
        _ = _approval_module().require_groom_approval(approval=_approval(approver="   "))


def test_an_approval_record_naming_no_route_is_refused() -> None:
    """How the approval was obtained is required too, not merely by whom."""
    with pytest.raises(GroomApprovalRequiredError, match="names no approval route"):
        _ = _approval_module().require_groom_approval(approval=_approval(route=""))


def test_a_complete_approval_record_is_returned_unchanged() -> None:
    """The accepting arm hands the caller back the record it will stamp."""
    approval = _approval()

    assert _approval_module().require_groom_approval(approval=approval) is approval


def test_an_unstamped_item_reports_no_approval() -> None:
    """The unconfigured case: nothing stamped reads back as nothing."""
    _issue(issue_id="li-ga-none")

    assert _approval_module().groom_approval_for(path=_config(), work_item_id="li-ga-none") is None


def test_the_record_is_written_and_read_back_as_a_top_level_key() -> None:
    """The stamp lands at `metadata.groom_approval` and reads back whole."""
    _issue(issue_id="li-ga-stamp")
    module = _approval_module()

    module.record_groom_approval(
        path=_config(),
        work_item_id="li-ga-stamp",
        approval=_approval(approver="thewoolleyman", route="ledger comment 41"),
    )

    assert _metadata_of(issue_id="li-ga-stamp")["groom_approval"] == {
        "approver": "thewoolleyman",
        "route": "ledger comment 41",
    }
    read_back = module.groom_approval_for(path=_config(), work_item_id="li-ga-stamp")
    assert read_back.approver == "thewoolleyman"
    assert read_back.route == "ledger comment 41"


def test_the_stamp_preserves_every_other_metadata_key_including_nested_ones() -> None:
    """A nested neighbour survives the write, sub-key by sub-key."""
    _issue(issue_id="li-ga-sib")
    _fake().update_issue(
        issue_id="li-ga-sib",
        metadata={"rank": "a1", "audit": {"actor": "operator", "note": "kept"}},
    )

    _approval_module().record_groom_approval(
        path=_config(), work_item_id="li-ga-sib", approval=_approval()
    )

    metadata = _metadata_of(issue_id="li-ga-sib")
    assert metadata["rank"] == "a1"
    assert metadata["audit"] == {"actor": "operator", "note": "kept"}
    assert metadata["groom_approval"]["approver"] == "thewoolleyman"


def test_a_malformed_metadata_column_reads_back_as_no_approval() -> None:
    """A record whose metadata is not an object carries no approval, and does not raise."""
    record: dict[str, Any] = {"metadata": "not-an-object"}

    assert _approval_module().groom_approval_from_record(record=record) is None


def test_a_record_without_the_key_reads_back_as_no_approval() -> None:
    """A slice filed before the stamp existed is unattributed, not half-attributed."""
    assert (
        _approval_module().groom_approval_from_record(record={"metadata": {"rank": "a1"}}) is None
    )


def test_a_half_built_stored_record_reads_back_as_no_approval() -> None:
    """Neither missing half may masquerade as an attributed filing."""
    module = _approval_module()

    no_route = module.groom_approval_from_record(
        record={"metadata": {"groom_approval": {"approver": "thewoolleyman"}}}
    )
    no_approver = module.groom_approval_from_record(
        record={"metadata": {"groom_approval": {"route": "ledger comment 41"}}}
    )

    assert no_route is None
    assert no_approver is None
