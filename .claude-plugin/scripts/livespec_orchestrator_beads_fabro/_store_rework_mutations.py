"""Rework-pending marker mutation for the beads-backed work-item store.

Split from `_store_mutations` because the mutations file is at its LLOC
ceiling; this owns the whole `rework:pending` vocabulary — the label name, the
stamp/clear write behind the two rework entries the ratified rework-pending
re-dispatch contract in `SPECIFICATION/contracts.md` permits to stamp it, and
the removal list every lifecycle write seam carries so the standing invariant
holds: an item whose status is not `active` MUST NOT carry the marker.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "LABEL_REWORK_PENDING",
    "rework_pending_label_removals",
    "update_work_item_rework_pending",
]

LABEL_REWORK_PENDING = "rework:pending"
_ACTIVE_STATUS = "active"


def update_work_item_rework_pending(
    *,
    path: StoreConfig,
    item_id: str,
    value: bool,
) -> None:
    """Stamp or clear the `rework:pending` marker without changing status.

    Exactly two entries MAY stamp it — the under-cap dispositive FAIL of the
    post-merge acceptance valve and the human `reject:<id>:rework` valve — so
    the write is label-only and deliberately sends no status or assignee
    mutation: routing the item to `active` is the caller's half of the same
    disposition, and no other machinery may stamp the marker at all.
    """
    client = make_beads_client(config=path)
    if value:
        client.update_issue(issue_id=item_id, add_labels=[LABEL_REWORK_PENDING])
    else:
        client.update_issue(issue_id=item_id, remove_labels=[LABEL_REWORK_PENDING])


def rework_pending_label_removals(*, status: str) -> list[str]:
    """The marker removals a lifecycle write landing on `status` must carry.

    Rework-pending is an `active`-lane condition, so a write to any OTHER
    status clears the marker in the same mutation. Routing the clear through
    the write seams rather than through each disposition is what makes "an
    item leaving `active` has the label cleared" structural — a new
    disposition cannot forget it.
    """
    return [] if status == _ACTIVE_STATUS else [LABEL_REWORK_PENDING]
