"""Admission valve orchestration for the Dispatcher.

This module owns the Dispatcher's admission / candidate-selection valve:
host-only candidates are refused through the completion disposition helper,
manual or unresolvable-assignee candidates are held and surfaced, and
admitted candidates are transitioned `ready -> active` with their resolved
assignee before Fabro launch.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path

from returns.unsafe import unsafe_perform_io

from livespec_orchestrator_beads_fabro.commands import _dispatcher_self_update as selfup
from livespec_orchestrator_beads_fabro.commands._dispatcher_claim_reclaim import (
    claimed_active_accounting,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_completion import host_only_refusal
from livespec_orchestrator_beads_fabro.commands._dispatcher_credentials import read_dispatch_labels
from livespec_orchestrator_beads_fabro.commands._dispatcher_decision_journal import (
    auto_disposition_journal_record,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_lock import (
    write_dispatch_lock,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile, utc_now_iso
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_outcomes import (
    failed_dispatch_outcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import store_config
from livespec_orchestrator_beads_fabro.commands._dispatcher_provider_exhaustion import (
    provider_exhaustion_refusal,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_valves import (
    DEFAULT_WIP_CAP,
    admission_held_detail,
    plan_admissions,
    resolve_assignee,
    resolve_wip_cap,
)
from livespec_orchestrator_beads_fabro.io import write_stderr
from livespec_orchestrator_beads_fabro.store import update_work_item_status
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "Admission",
    "admission_held_outcome",
    "admit_and_select",
]


@dataclass(frozen=True, kw_only=True)
class Admission:
    """The outcome of the admission valve over a candidate set.

    `admitted` carries the items transitioned `ready -> active` (assignee
    set) that the Dispatcher then launches; `deferred` carries
    capacity-deferred items that remain `ready`; `refused` carries the
    non-launched terminal outcomes — host-only routing refusals plus
    admission holds (manual / unresolvable assignee) — that ride in the
    wave's outcome list so the verdict and the post-verdict alarm see them.
    """

    admitted: list[WorkItem]
    deferred: list[DispatchOutcome]
    refused: list[DispatchOutcome]


@dataclass(frozen=True, kw_only=True)
class _CapacitySnapshot:
    active_count: int
    wip_cap: int
    free_slots: int
    live_lock_active_ids: tuple[str, ...]
    journal_unreadable_active_ids: tuple[str, ...]
    green_terminal_active_ids: tuple[str, ...]


def admit_and_select(
    *,
    repo: Path,
    items: list[WorkItem],
    candidates: list[WorkItem],
    journal: JournalFile,
    enforce_cap: bool,
) -> Admission:
    """Run the admission valve over the rank-sorted candidate set.

    The sole enforcer of the approval/admission valve + per-repo WIP cap. For
    each candidate, in order: a host-only self-machinery item is routed away
    (refused, never admitted — the uvd hang-guard); then `plan_admissions`
    holds a manual pending item, auto-approves an auto pending item into
    `ready`, holds an unresolvable-assignee item, and admits the highest-`rank`
    ready items into the free WIP slots, writing each `ready -> active` with
    its resolved assignee. `enforce_cap` reads the per-repo `wip_cap` from
    `.livespec.jsonc` and discounts the already-`active` items.
    A targeted `dispatch --item` is an operator override that passes
    `enforce_cap=False` (every host-cleared candidate gets a slot).
    `dispatcher.py dispatch --item` reaches that override.
    `drive --action impl:` does not, because it routes selected items through
    the cap-enforcing `loop` path used by unattended draining. The admit writes
    + the held surfaces are journaled here; the launched items flow on to
    `_dispatch_one`.

    """
    admittable, refused = _filter_host_only_candidates(
        repo=repo,
        candidates=candidates,
        journal=journal,
    )
    accounting = claimed_active_accounting(repo=repo, items=items, journal=journal)
    if enforce_cap:
        # An unreadable `.livespec.jsonc` falls back to the documented cap,
        # visibly and here rather than inside the reader. `unsafe_perform_io`
        # is required: `IOResult.value_or` returns `IO[value]`, not the value.
        wip_cap = unsafe_perform_io(resolve_wip_cap(cwd=repo).value_or(DEFAULT_WIP_CAP))
        free_slots = max(0, wip_cap - accounting.active_count)
    else:
        wip_cap = None
        free_slots = len(admittable)
    plan = plan_admissions(
        ready_items=admittable,
        free_slots=free_slots,
        cwd=repo,
        resolve_assignee=resolve_assignee,
    )
    admitted: list[WorkItem] = []
    deferred: list[DispatchOutcome] = []
    config = store_config(repo=repo)
    approved_ids = {item.id for item in plan.approved}
    for item in plan.approved:
        update_work_item_status(path=config, item_id=item.id, status="ready")
        journal.append(record={"stage": "ledger-approve", "work_item_id": item.id})
        journal.append(
            record=auto_disposition_journal_record(
                work_item_id=item.id,
                disposition="auto-approve",
                governing_settings=_auto_approve_governing_settings(item=item),
            )
        )
    for item, assignee in plan.admitted:
        journal_item = replace(item, status="ready") if item.id in approved_ids else item
        update_work_item_status(
            path=config, item_id=journal_item.id, status="active", assignee=assignee
        )
        dispatch_id = selfup.run_id()
        _ = write_dispatch_lock(repo=repo, work_item_id=item.id, dispatch_id=dispatch_id)
        journal.append(
            record={"stage": "ledger-admit", "work_item_id": item.id, "assignee": assignee}
        )
        admitted.append(replace(journal_item, status="active", assignee=assignee))
    for item, reason in plan.held:
        held = admission_held_outcome(item=item, reason=reason)
        journal.append(record={"stage": "outcome", "outcome": asdict(held)})
        _ = write_stderr(text=f"SURFACE: {admission_held_detail(item_id=item.id, reason=reason)}\n")
        refused.append(held)
    if wip_cap is not None:
        deferred = _capacity_deferred_outcomes(
            admittable=admittable,
            admitted=admitted,
            held=plan.held,
            capacity=_CapacitySnapshot(
                active_count=accounting.active_count,
                wip_cap=wip_cap,
                free_slots=free_slots,
                live_lock_active_ids=accounting.live_lock_active_ids,
                journal_unreadable_active_ids=accounting.journal_unreadable_active_ids,
                green_terminal_active_ids=accounting.green_terminal_active_ids,
            ),
            journal=journal,
        )
    return Admission(admitted=admitted, deferred=deferred, refused=refused)


def _filter_host_only_candidates(
    *,
    repo: Path,
    candidates: list[WorkItem],
    journal: JournalFile,
) -> tuple[list[WorkItem], list[DispatchOutcome]]:
    admittable: list[WorkItem] = []
    refused: list[DispatchOutcome] = []
    for item in candidates:
        exhaustion_refusal = provider_exhaustion_refusal(
            work_item_id=item.id,
            journal=journal,
            journal_path=getattr(journal, "path", None),
            now_iso=utc_now_iso(),
        )
        if exhaustion_refusal is not None:
            refused.append(exhaustion_refusal)
            continue
        raw_labels = read_dispatch_labels(repo=repo, item=item)
        if isinstance(raw_labels, str):
            refused.append(
                failed_dispatch_outcome(
                    journal=journal,
                    work_item_id=item.id,
                    stage="ledger-labels",
                    detail=raw_labels,
                )
            )
            continue
        host_refusal = host_only_refusal(
            repo=repo,
            item=item,
            journal=journal,
            raw_labels=raw_labels,
        )
        if host_refusal is not None:
            refused.append(host_refusal)
        else:
            admittable.append(item)
    return admittable, refused


def _auto_approve_governing_settings(*, item: WorkItem) -> tuple[str, ...]:
    if item.admission_policy == "auto":
        return ("admission:auto",)
    return ("auto_approve_ready",)


def admission_held_outcome(*, item: WorkItem, reason: str) -> DispatchOutcome:
    """Build the `admission-held` terminal for an item held at the admission valve.

    A `failed` outcome (so the dispatch exit code flips to 1 and the
    maintainer's eyes are required) at the `admission-held` stage; nothing is
    launched and nothing is closed — a manual item stays at `pending-approval`
    for the maintainer to approve, while an unresolvable item stays put until
    assignment is fixed.
    """
    return DispatchOutcome(
        work_item_id=item.id,
        status="failed",
        stage="admission-held",
        pr_number=None,
        merge_sha=None,
        detail=admission_held_detail(item_id=item.id, reason=reason),
    )


def _capacity_deferred_outcomes(
    *,
    admittable: list[WorkItem],
    admitted: list[WorkItem],
    held: tuple[tuple[WorkItem, str], ...],
    capacity: _CapacitySnapshot,
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
    capacity: _CapacitySnapshot,
) -> DispatchOutcome:
    return DispatchOutcome(
        work_item_id=item.id,
        status="capacity-deferred",
        stage="capacity-deferred",
        pr_number=None,
        merge_sha=None,
        detail=_capacity_deferred_detail(item=item, capacity=capacity),
    )


def _capacity_deferred_detail(*, item: WorkItem, capacity: _CapacitySnapshot) -> str:
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
