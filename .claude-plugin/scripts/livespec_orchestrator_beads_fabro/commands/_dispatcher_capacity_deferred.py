"""The admission valve's capacity-deferred reporting surface.

Split out of `_dispatcher_admission` so the valve stays under the file LLOC
ceiling while the rework leg joins it. This is its own cohesive concern: the
valve DECIDES who is admitted, while everything here only DESCRIBES the items
a full cap left behind — the counted classes, the operator responses, and the
single-item override plus the cost of taking it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "CapacitySnapshot",
    "capacity_deferred_outcomes",
]


@dataclass(frozen=True, kw_only=True)
class CapacitySnapshot:
    active_count: int
    wip_cap: int
    free_slots: int
    live_lock_active_ids: tuple[str, ...]
    journal_unreadable_active_ids: tuple[str, ...]
    green_terminal_active_ids: tuple[str, ...]


def capacity_deferred_outcomes(
    *,
    admittable: list[WorkItem],
    admitted: list[WorkItem],
    held: tuple[tuple[WorkItem, str], ...],
    capacity: CapacitySnapshot,
    journal: JournalFile,
) -> list[DispatchOutcome]:
    admitted_ids = {item.id for item in admitted}
    held_ids = {item.id for item, _ in held}
    outcomes = [
        _capacity_deferred_outcome(
            item=item,
            capacity=capacity,
        )
        for item in admittable
        if item.id not in admitted_ids and item.id not in held_ids
    ]
    for outcome in outcomes:
        journal.append(record={"stage": "outcome", "outcome": asdict(outcome)})
    return outcomes


def _capacity_deferred_outcome(
    *,
    item: WorkItem,
    capacity: CapacitySnapshot,
) -> DispatchOutcome:
    return DispatchOutcome(
        work_item_id=item.id,
        status="capacity-deferred",
        stage="capacity-deferred",
        pr_number=None,
        merge_sha=None,
        detail=_capacity_deferred_detail(item=item, capacity=capacity),
    )


def _capacity_deferred_detail(*, item: WorkItem, capacity: CapacitySnapshot) -> str:
    parts = [
        "capacity deferred:",
        f"active_count={capacity.active_count}",
        f"wip_cap={capacity.wip_cap}",
        f"free_slots={capacity.free_slots}",
    ]
    if capacity.live_lock_active_ids:
        parts.append(f"live_lock_active_ids={','.join(capacity.live_lock_active_ids)}")
    if capacity.journal_unreadable_active_ids:
        parts.append(
            f"journal_unreadable_active_ids={','.join(capacity.journal_unreadable_active_ids)}"
        )
        live_lock_response = ((), ("wait_for_live_locks",))[
            min(len(capacity.live_lock_active_ids), 1)
        ]
        operator_responses = (*live_lock_response, "inspect_unreadable_journals")
        parts.append(f"operator_response={','.join(operator_responses)}")
    if capacity.green_terminal_active_ids:
        parts.append(f"green_terminal_active_ids={','.join(capacity.green_terminal_active_ids)}")
        parts.append("green_terminal_active_status=already_reclaimed_no_slot")
    parts.append(f"single_item_override=dispatcher.py dispatch --item {item.id}")
    parts.append("single_item_override_enforces_cap=false")
    parts.append(
        "single_item_override_cost="
        + "_".join(
            [
                "deliberately_exceeds_wip_cap_bound_for_same_repo",
                "merge_rebase_contention_during_unattended_draining",
            ]
        )
    )
    return " ".join(parts)
