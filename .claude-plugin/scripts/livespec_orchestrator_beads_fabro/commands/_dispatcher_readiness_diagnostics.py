"""Operator-facing readiness diagnostics for dispatcher refusals."""

from __future__ import annotations

from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._sibling_status_lookup import (
    make_sibling_status_lookup,
    sibling_dependency_diagnostics,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = ["not_ready_requested_items_error"]


def not_ready_requested_items_error(
    *,
    requested_ids: set[str],
    items: list[WorkItem],
    repo: Path,
) -> str:
    missing = ", ".join(sorted(requested_ids))
    claimed = _claimed_diagnostics(requested_ids=requested_ids, items=items)
    if claimed:
        return (
            f"ERROR: requested work-item(s) already claimed by a dispatch: {missing}; {claimed}\n"
        )
    diagnostics = _sibling_diagnostics(requested_ids=requested_ids, items=items, repo=repo)
    if diagnostics:
        detail = "; ".join(diagnostics)
        return f"ERROR: requested work-item(s) blocked by sibling dependency: {missing}: {detail}\n"
    return f"ERROR: requested work-item(s) not in the ready set: {missing}\n"


def _claimed_diagnostics(*, requested_ids: set[str], items: list[WorkItem]) -> str | None:
    item_by_id = {item.id: item for item in items}
    claimed = [item_by_id[item_id] for item_id in sorted(requested_ids) if item_id in item_by_id]
    if not claimed or any(item.status != "active" for item in claimed):
        return None
    details = [
        f"status={item.status} assignee={item.assignee or '<unassigned>'}" for item in claimed
    ]
    details.append(
        " ".join(
            (
                "Inspect the dispatch journal and reconcile-runs for a stranded claim",
                "before checking dependencies.",
            )
        )
    )
    return "; ".join(details)


def _sibling_diagnostics(
    *, requested_ids: set[str], items: list[WorkItem], repo: Path
) -> tuple[str, ...]:
    item_by_id = {item.id: item for item in items}
    lookup = make_sibling_status_lookup(project_root=repo)
    diagnostics: list[str] = []
    for item_id in sorted(requested_ids):
        item = item_by_id.get(item_id)
        if item is None:
            continue
        diagnostics.extend(sibling_dependency_diagnostics(item=item, sibling_status_lookup=lookup))
    return tuple(diagnostics)
