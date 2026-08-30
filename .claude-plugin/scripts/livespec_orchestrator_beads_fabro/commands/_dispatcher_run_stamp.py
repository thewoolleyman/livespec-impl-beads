"""Stamping a live Fabro run onto its work-item, and reading the stamp back.

Both ends of one loop live here on purpose. `stamp_dispatch_run` WRITES the run
id and factory target onto the item the moment the Dispatcher first learns them;
`repo_run_attribution` READS those stamps (plus the dispatch journal) back into
the `RunAttribution` every consumer of `fabro ps` rows resolves through. Split
across two modules, the writer's key names and the reader's expectations could
drift apart and the only symptom would be attribution quietly falling back to
the goal-text regex — a silent degradation, not an error.

The write is FAIL-OPEN, and that is a deliberate asymmetry. A beads hiccup at
stamp time must not kill a Fabro run that is already doing the work: the run is
the expensive thing, the stamp is a convenience for whoever reconciles later.
But a fail-open write that says nothing is how a blind spot hides, so every
attempt journals a record carrying `stamped`, making "this dispatch has no
ledger stamp" a queryable state rather than an absence.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro._store_dispatch_factory import (
    dispatch_run_ids_for,
    record_dispatch_run,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import store_config
from livespec_orchestrator_beads_fabro.commands._dispatcher_reflection_journal import (
    read_journal_records,
)
from livespec_orchestrator_beads_fabro.commands._run_attribution import (
    RunAttribution,
    run_attribution,
)
from livespec_orchestrator_beads_fabro.errors import (
    BeadsCommandError,
    BeadsConnectionError,
    BeadsMappingError,
)

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import JournalWriter
    from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan
    from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroRunSummary

__all__: list[str] = [
    "STAMP_JOURNAL_STAGE",
    "repo_run_attribution",
    "stamp_dispatch_run",
    "stamped_attribution",
]

# The journal `stage` every stamp attempt writes under, whether or not the
# ledger write landed.
STAMP_JOURNAL_STAGE = "dispatch-run-stamp"

_JOURNAL_SUBPATH = ("tmp", "fabro-dispatch-journal.jsonl")


def stamp_dispatch_run(
    *,
    plan: DispatchPlan,
    journal: JournalWriter,
    run_id: str,
) -> RunAttribution:
    """Stamp this run onto its work-item and return the attribution it establishes.

    The returned attribution is exact rather than re-read: this process just
    asserted that `run_id` belongs to `plan.work_item_id`, so it can answer for
    that pair without another ledger round-trip — and it answers correctly even
    when the write itself failed open, because the mapping is a fact about the
    dispatch, not about the ledger.
    """
    stamped = _write_stamp(plan=plan, run_id=run_id)
    journal.append(
        record={
            "work_item_id": plan.work_item_id,
            "stage": STAMP_JOURNAL_STAGE,
            "run_id": run_id,
            "dispatch_factory": plan.fabro_factory_name,
            "dispatch_factory_server": plan.fabro_factory_server,
            "stamped": stamped,
        }
    )
    return RunAttribution(metadata_run_ids={run_id: plan.work_item_id})


def stamped_attribution(
    *,
    plan: DispatchPlan,
    journal: JournalWriter,
    run: FabroRunSummary | None,
    attribution: RunAttribution,
) -> RunAttribution:
    """Stamp on the FIRST sight of a run id; otherwise pass the attribution through.

    Keyed on the run id already being attributed rather than on a "have I
    stamped yet" flag, so a poll that discovers a DIFFERENT run id — the shape a
    re-dispatch inside one watch loop would take — re-stamps instead of leaving
    the ledger naming a run this dispatch has moved off.
    """
    if run is None or run.run_id in attribution.metadata_run_ids:
        return attribution
    return stamp_dispatch_run(plan=plan, journal=journal, run_id=run.run_id)


def repo_run_attribution(*, repo: Path) -> RunAttribution:
    """Build the attribution this repo's own recorded facts support.

    Degrades leg by leg rather than all at once: an unreadable ledger still
    leaves the journal leg, and an absent journal still leaves the ledger leg.
    Whatever is missing, the goal-text regex remains as the floor, so this never
    returns an attribution that answers FEWER runs than reading
    `run.work_item_id` directly would have.
    """
    return run_attribution(
        metadata_run_ids=_ledger_run_ids(repo=repo),
        journal_records=read_journal_records(journal_path=repo.joinpath(*_JOURNAL_SUBPATH)),
    )


def _write_stamp(*, plan: DispatchPlan, run_id: str) -> bool:
    if not (plan.repo / ".livespec.jsonc").is_file():
        return False
    try:
        record_dispatch_run(
            path=store_config(repo=plan.repo),
            work_item_id=plan.work_item_id,
            run_id=run_id,
            factory_name=plan.fabro_factory_name,
            factory_server=plan.fabro_factory_server,
        )
    except (BeadsCommandError, BeadsConnectionError, BeadsMappingError):
        return False
    return True


def _ledger_run_ids(*, repo: Path) -> dict[str, str]:
    if not (repo / ".livespec.jsonc").is_file():
        return {}
    try:
        return dispatch_run_ids_for(path=store_config(repo=repo))
    except (BeadsCommandError, BeadsConnectionError, BeadsMappingError):
        return {}
