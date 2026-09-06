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

from typing import TYPE_CHECKING, cast

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro._store_cap_mutations import update_work_item_cap

if TYPE_CHECKING:
    from collections.abc import Iterable

    from livespec_orchestrator_beads_fabro._beads_client import BeadsRecord
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "MERGE_HOLD_LABEL_PREFIX",
    "merge_hold_from_labels",
    "read_merge_held_work_item_ids",
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


def read_merge_held_work_item_ids(*, path: StoreConfig) -> frozenset[str]:
    """Every tenant id the `merge-hold:` label holds, read straight from the labels.

    A narrow RAW read, mirroring `_store_intake_triage`: the hold is a label, and
    `store._record_to_work_item` decodes labels into the named fields the shared
    `WorkItem` model declares, so a marker the model does not carry is dropped on
    the floor before any consumer sees it. The surfaces the ratified hold binds —
    the attention row and the stranded-state discriminator — need the answer for
    every held item, so they read it here rather than each spelling the prefix.

    Fail-SOFT in the same shape the needs-attention readers use: a record with no
    usable id, or whose labels are not a list of strings, contributes nothing
    rather than failing the whole enumeration. That is safe in exactly one
    direction here, because `merge_hold_from_labels` is itself fail-closed over
    the labels it does see.
    """
    client = make_beads_client(config=path)
    return frozenset(
        issue_id
        for record in client.list_issues()
        if isinstance(issue_id := record.get("id"), str)
        and merge_hold_from_labels(labels=_labels_of(record=record))
    )


def _labels_of(*, record: BeadsRecord) -> tuple[str, ...]:
    raw = record.get("labels")
    if not isinstance(raw, list):
        return ()
    labels = cast("list[object]", raw)
    return tuple(label for label in labels if isinstance(label, str))
