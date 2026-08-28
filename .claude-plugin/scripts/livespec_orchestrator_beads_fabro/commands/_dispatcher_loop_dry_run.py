"""The `loop --dry-run` planning surface.

Split out of `_dispatcher_loop_command` so the loop handler stays under the
file LLOC ceiling once the rework leg joins its selection. The concern is its
own: everything here is READ-ONLY with respect to the work-item store — it
answers "what would this drain do?" and dispatches nothing — while the loop
handler owns the pass that actually launches runs.
"""

from __future__ import annotations

from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.commands._dispatcher_rework_admission import (
    ReworkPass,
    projected_rework_candidates,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "dry_run_outcomes",
]


def dry_run_outcomes(
    *,
    repo: Path,
    items: list[WorkItem],
    journal: JournalFile,
    selected_candidates: list[WorkItem],
    rework: ReworkPass,
) -> list[DispatchOutcome]:
    """Project the planned selection onto the reported outcome surface.

    SPECIFICATION/contracts.md requires --dry-run to "compute and report
    exactly the selection the same invocation would dispatch", and permits
    journaling that selection only as an ADDITION — not as the discharge of
    the reporting obligation. Nothing here launches a run, mutates the ledger,
    or writes the work-item store: the candidates are re-labelled, never
    dispatched. The marked rework rows lead the list because that is the order
    the same invocation would launch them in; they are read through the
    accounting's side-effect-free projection so the read-only guarantee holds.
    """
    planned = [
        *projected_rework_candidates(repo=repo, items=items, journal=journal, rework=rework),
        *selected_candidates,
    ]
    return [
        DispatchOutcome(
            work_item_id=item.id,
            status="dry-run",
            stage="loop-pick",
            pr_number=None,
            merge_sha=None,
            detail="planned selection; not dispatched",
        )
        for item in planned
    ]
