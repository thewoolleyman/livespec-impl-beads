"""The approval record a groom cut is filed under, and where it is stamped.

`file_approved_slices` performs a maintainer-tier mutation: it files N
replacement work-items AND closes the original with a regroomed-out
disposition. `SPECIFICATION/contracts.md` therefore requires that filing seam
to carry an approval record naming the approver identity and how the approval
was obtained, to stamp it on every filed slice and on the regroomed-out
original in a field a later reader can query, and to refuse a call carrying
none.

WHY A STAMPED FIELD RATHER THAN A PROSE OBLIGATION. The requirement already
existed as prose the calling agent was asked to honour, and prose leaves no
forensic difference behind: a closed original beside N filed slices reads
identically whether the maintainer approved, a peer session approved, or the
agent approved itself, and the ledger is append-only, so no later reader can
recover which it was. The 2026-08-22 near miss on `overseer-ulyv` was caught
only because the answering peer volunteered that it had answered. The stamp
is what makes the three cases distinguishable without that courtesy.

It lives beside `_store_dispatch_workflow`'s pin rather than inside it, and
is read through this module directly rather than re-exported from
`store.py`, for the reason that module states: one plain single-shape key
written at one moment does not need the broad facade widened for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro.errors import GroomApprovalRequiredError

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro._beads_client import BeadsRecord
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "GroomApproval",
    "groom_approval_for",
    "groom_approval_from_record",
    "record_groom_approval",
    "require_groom_approval",
]

_META_GROOM_APPROVAL = "groom_approval"
_APPROVER_KEY = "approver"
_ROUTE_KEY = "route"


@dataclass(frozen=True, kw_only=True)
class GroomApproval:
    """Who approved a groom cut, and the route the approval arrived on.

    `approver` is the approving invoker's identity — the operator or agent
    whose answer authorized the filing, not the seat that drafted it.
    `route` is HOW the approval was obtained: under the ratified two-phase
    groom variant that is the `resolve-blocked:<work-item-id>:ready` valve
    plus the ledger comment the answer landed as, which is exactly the pair
    the answer route already supplies mechanically.

    Both fields are plain strings because the record must survive into the
    beads metadata JSON column and be read back by a later reader with no
    access to whatever object the approving front-end held.
    """

    approver: str
    route: str


def require_groom_approval(*, approval: GroomApproval | None) -> GroomApproval:
    """Return the approval record, refusing an absent or unattributed one.

    Refusal is the whole point: a filing seam that RECORDS an approval but
    proceeds without one still files N slices and closes the original on any
    caller's say-so. The three refused shapes are the three ways a caller
    arrives carrying nothing usable — no record at all, a record naming no
    approver, and a record naming no route.
    """
    if approval is None:
        raise GroomApprovalRequiredError(detail="no approval record was supplied")
    if approval.approver.strip() == "":
        raise GroomApprovalRequiredError(detail="the approval record names no approver identity")
    if approval.route.strip() == "":
        raise GroomApprovalRequiredError(detail="the approval record names no approval route")
    return approval


def record_groom_approval(*, path: StoreConfig, work_item_id: str, approval: GroomApproval) -> None:
    """Stamp the approval record onto one work-item's metadata.

    The key lands at the metadata TOP LEVEL, and the whole existing mapping
    is read back and re-sent with it. `bd update --metadata` MERGES
    top-level keys but REPLACES a nested object wholesale, so a record
    tucked under an existing object would destroy every sibling sub-key this
    payload did not happen to resend — and what survives a write is exactly
    what the payload carries.

    Stamped on a CLOSED original as readily as on a freshly filed slice: the
    regroomed-out original is precisely the record whose provenance a later
    reader cannot otherwise recover.
    """
    client = make_beads_client(config=path)
    metadata = _metadata_of(record=client.show_issue(issue_id=work_item_id))
    metadata[_META_GROOM_APPROVAL] = {
        _APPROVER_KEY: approval.approver,
        _ROUTE_KEY: approval.route,
    }
    client.update_issue(issue_id=work_item_id, metadata=metadata)


def groom_approval_for(*, path: StoreConfig, work_item_id: str) -> GroomApproval | None:
    """Return the approval record a groom filing stamped on a work-item."""
    client = make_beads_client(config=path)
    return groom_approval_from_record(record=client.show_issue(issue_id=work_item_id))


def groom_approval_from_record(*, record: BeadsRecord) -> GroomApproval | None:
    """Return the approval record carried by an issue record, if any.

    A record filed before this stamp existed, or one whose metadata column
    holds something other than the two-string object, reads back as `None`
    rather than as a half-built approval: an unattributable filing must not
    be able to masquerade as an attributed one.
    """
    raw = _metadata_of(record=record).get(_META_GROOM_APPROVAL)
    if not isinstance(raw, dict):
        return None
    stored = cast("dict[str, Any]", raw)
    approver = stored.get(_APPROVER_KEY)
    route = stored.get(_ROUTE_KEY)
    if not isinstance(approver, str) or not isinstance(route, str):
        return None
    return GroomApproval(approver=approver, route=route)


def _metadata_of(*, record: BeadsRecord) -> dict[str, Any]:
    raw = record.get("metadata")
    if isinstance(raw, dict):
        return dict(cast("dict[str, Any]", raw))
    return {}
