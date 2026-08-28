"""Blocked-state transition and blocked-reason vocabulary for the store.

Split from `_store_mutations` because the mutations file is at its LLOC
ceiling; this owns the whole `blocked-reason:` vocabulary — the label prefix,
the two STORED reasons the field map permits, the dispatch-time escalation that
writes one, the full replace set that escalation rewrites, and the removal list
every lifecycle write seam carries so the standing invariant holds: an item
whose status is not `blocked` MUST NOT carry a blocked-reason label.

The escalation INTO `blocked` already had a writer; its converse — the clear on
the way OUT — had no owner, which is why it failed identically on two unrelated
exit paths (a valve move and a terminal close). Both halves live here, at one
layer, rather than the clear being patched onto each exit site: that is what
keeps an exit path added later from leaking by default.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro._store_rework_mutations import (
    rework_pending_label_removals,
)
from livespec_orchestrator_beads_fabro._store_statuses import beads_status_for

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "LABEL_BLOCKED_REASON_PREFIX",
    "blocked_reason_label_removals",
    "blocked_reason_labels",
    "update_work_item_blocked_state",
]

LABEL_BLOCKED_REASON_PREFIX = "blocked-reason:"

# The escalation replaces the admission policy alongside the reason, so this
# module carries the `admission:` prefix too. `_store_mutations` keeps its own
# copy for the create-time label build, the same read-facade/write-facade
# duplication `store.py` already uses for every bridge-owned label prefix.
_LABEL_ADMISSION = "admission:"
_ADMISSION_POLICIES = ("auto", "manual")

# The two STORED reasons. The third rendered lane reason, `dependency`, is
# DERIVED from unresolved dependency edges and is NEVER written as a label, so
# it is deliberately absent here.
_STORED_BLOCKED_REASONS = ("needs-human", "infra-external")

_BLOCKED_STATUS = "blocked"


def blocked_reason_labels() -> list[str]:
    """Every stored blocked-reason label — the full set a replace must remove.

    The dispatch-time escalation REPLACES the reason rather than clearing it, so
    it removes the whole set unconditionally and adds the one it is writing back.
    """
    return [f"{LABEL_BLOCKED_REASON_PREFIX}{reason}" for reason in _STORED_BLOCKED_REASONS]


def blocked_reason_label_removals(*, status: str) -> list[str]:
    """The reason removals a lifecycle write landing on `status` must carry.

    A blocked-reason is a `blocked`-lane condition, so a write to any OTHER
    status clears it in the same mutation. Routing the clear through the write
    seams rather than through each exit path is what makes "an item leaving
    `blocked` carries no blocked_reason" structural — a valve move, a terminal
    close, or an exit path added later cannot forget it.
    """
    return [] if status == _BLOCKED_STATUS else blocked_reason_labels()


def update_work_item_blocked_state(
    *,
    path: StoreConfig,
    item_id: str,
    status: str,
    blocked_reason: str | None,
    admission_policy: str | None = None,
) -> None:
    """Transition an item and replace its dispatcher blocked-reason label.

    This is the dispatch-time escalation seam for Fabro human gates: the
    Dispatcher writes `status=blocked` plus `blocked-reason:needs-human` in one
    in-place ledger mutation. The same seam is used by the human valve to clear
    that label when an operator moves the item out of `blocked`.

    The removal is the FULL reason set rather than `blocked_reason_label_removals`
    because this seam REPLACES the reason: it removes every reason label
    unconditionally and adds back only the one it was asked to write, so landing
    on `blocked` with a new reason cannot leave the previous one alongside it.
    """
    remove_labels = blocked_reason_labels() + rework_pending_label_removals(status=status)
    add_labels: list[str] = []
    if blocked_reason is not None:
        add_labels.append(f"{LABEL_BLOCKED_REASON_PREFIX}{blocked_reason}")
    if admission_policy is not None:
        remove_labels.extend(f"{_LABEL_ADMISSION}{value}" for value in _ADMISSION_POLICIES)
        add_labels.append(f"{_LABEL_ADMISSION}{admission_policy}")
    client = make_beads_client(config=path)
    client.update_issue(
        issue_id=item_id,
        status=beads_status_for(status=status),
        remove_labels=remove_labels,
    )
    if add_labels:
        client.update_issue(issue_id=item_id, add_labels=add_labels)
