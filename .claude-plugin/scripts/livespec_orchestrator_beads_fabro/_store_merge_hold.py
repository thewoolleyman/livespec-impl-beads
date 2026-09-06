"""Merge-hold marker mutation for the beads-backed work-item store.

Owns the whole `merge-hold:` vocabulary — the label the ratified per-item
merge-hold contract in `SPECIFICATION/contracts.md` names, the set/release write
behind the `set-merge-hold:<work-item-id>:on|off` human valve, and the predicate
every reader uses to answer "is this item held?" from raw labels. It sits beside
`_store_rework_mutations` for the reason that module gives: `_store_mutations`
is at its LLOC ceiling, and a one-marker vocabulary is cohesive on its own.

The hold has NO repository-level default and no value space of its own: it is
set on one item, by a person, for one merge, so the label's PRESENCE is the
hold. One canonical label is written, and every read keys on the `merge-hold:`
PREFIX the contract names, so the writer and the reader cannot come to disagree
about what counts as held.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro._store_cap_mutations import update_work_item_cap

if TYPE_CHECKING:
    from collections.abc import Iterable

    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "MERGE_HOLD_LABEL_PREFIX",
    "merge_hold_from_labels",
    "update_work_item_merge_hold",
]

MERGE_HOLD_LABEL_PREFIX = "merge-hold:"
_HELD_VALUE = "on"


def update_work_item_merge_hold(*, path: StoreConfig, item_id: str, value: bool) -> None:
    """Set or release an item's merge hold, sending no status or assignee mutation.

    Delegates to the prefixed-label store write the per-item cap overrides
    already use, because the write is the same one: remove every label carrying
    the prefix, then add the replacement when there is one. A second copy of
    that read-remove-add is exactly how the set path and the release path would
    come to disagree about which labels count as the hold. What this module owns
    is the VOCABULARY rather than the mechanics — a cap label carries a value the
    operator chose, the hold label carries only itself.
    """
    update_work_item_cap(
        path=path,
        item_id=item_id,
        label_prefix=MERGE_HOLD_LABEL_PREFIX,
        value=_HELD_VALUE if value else None,
    )


def merge_hold_from_labels(*, labels: Iterable[str]) -> bool:
    """Whether raw beads labels put this item under a merge hold.

    Keyed on the PREFIX rather than on the one canonical label the valve writes,
    so the reading is fail-CLOSED: any `merge-hold:` label reads as held. For a
    marker whose whole job is to stop an automated merge, an unrecognized
    variant must not read as a release.
    """
    return any(label.startswith(MERGE_HOLD_LABEL_PREFIX) for label in labels)
