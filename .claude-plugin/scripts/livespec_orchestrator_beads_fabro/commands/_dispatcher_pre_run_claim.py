"""Pre-run dispatch claim release helpers."""

from __future__ import annotations

from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import store_config
from livespec_orchestrator_beads_fabro.store import update_work_item_status
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = ["release_pre_run_claim_if_needed"]

_PRE_RUN_FAILURE_STAGES = frozenset(
    (
        "github-app-auth",
        "goal-minijinja-preflight",
        "ledger-comments",
        "ledger-labels",
        "run-config-overlay",
    )
)


def release_pre_run_claim_if_needed(
    *,
    repo: Path,
    item: WorkItem,
    outcome: DispatchOutcome,
    journal: JournalFile,
) -> None:
    if not _should_release_pre_run_claim(item=item, outcome=outcome):
        return
    update_work_item_status(
        path=store_config(repo=repo),
        item_id=item.id,
        status="ready",
        clear_assignee=True,
    )
    journal.append(
        record={
            "stage": "ledger-admit-release",
            "work_item_id": item.id,
            "status": "ready",
            "reason": "pre-run-failure-without-fabro-run-id",
            "outcome_stage": outcome.stage,
        }
    )


def _should_release_pre_run_claim(*, item: WorkItem, outcome: DispatchOutcome) -> bool:
    return (
        item.status == "active"
        and outcome.status == "failed"
        and outcome.fabro_run_id is None
        and outcome.stage in _PRE_RUN_FAILURE_STAGES
    )
