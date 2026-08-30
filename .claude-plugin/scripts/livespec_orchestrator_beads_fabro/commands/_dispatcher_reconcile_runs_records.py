"""The reconciler's result records and the journal entries it writes.

One `orphan-run-reconciled` record per reconciled run, carrying the whole
join that justified the act — run id, factory, status kind, work-item and
its ledger status, orphan reason — beside what was done about it: the
termination route and the export comment the ruling requires. Reading that
record alone answers "why was this run terminated, and where did its work
go", which is the question a slot that disappeared always raises.

The `fabro rm --force` fallback gets its OWN stage name in addition to the
reconciled record. It is the destructive route, and a fallback that is
counted the same as a clean cancel cannot be noticed becoming routine.
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import JournalWriter
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_join import OrphanRun
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_terminate import (
    TERMINATION_ROUTE_RM,
    TerminationOutcome,
)

__all__: list[str] = [
    "JOURNAL_STAGE_ERROR",
    "JOURNAL_STAGE_EXPORT",
    "JOURNAL_STAGE_RECONCILED",
    "JOURNAL_STAGE_RM_FALLBACK",
    "TERMINATION_ROUTE_NONE",
    "ReconcileError",
    "ReconcileRunsSummary",
    "ReconciledRun",
    "journal_error",
    "journal_export",
    "journal_reconciled",
    "reconciled_from",
]

JOURNAL_STAGE_RECONCILED = "orphan-run-reconciled"
JOURNAL_STAGE_ERROR = "orphan-run-reconcile-error"
JOURNAL_STAGE_EXPORT = "orphan-run-reconcile-export"
JOURNAL_STAGE_RM_FALLBACK = "orphan-run-reconcile-rm-fallback"

# What a `--dry-run` projection reports instead of a route: nothing was
# terminated, and naming a route it did not take would read as a record of
# an act that never happened.
TERMINATION_ROUTE_NONE = "none"


@dataclass(frozen=True, kw_only=True)
class ReconciledRun:
    """One orphan and the disposition the reconciler gave it."""

    run_id: str
    factory_name: str
    factory_server_url: str
    status_kind: str
    work_item_id: str
    work_item_status: str | None
    orphan_reason: str
    termination_route: str
    termination_succeeded: bool
    termination_detail: str
    export_comment_id: str | None


@dataclass(frozen=True, kw_only=True)
class ReconcileError:
    """One reconciliation that could not be completed, and why."""

    factory_name: str
    factory_server_url: str | None
    run_id: str | None
    work_item_id: str | None
    reason: str
    detail: str


@dataclass(frozen=True, kw_only=True)
class ReconcileRunsSummary:
    """One pass over every surveyed factory."""

    reconciled: tuple[ReconciledRun, ...]
    errors: tuple[ReconcileError, ...]
    dry_run: bool


def reconciled_from(
    *,
    orphan: OrphanRun,
    termination: TerminationOutcome | None,
    export_comment_id: str | None,
) -> ReconciledRun:
    """Fold one orphan and its termination into the reported record."""
    return ReconciledRun(
        run_id=orphan.run_id,
        factory_name=orphan.factory_name,
        factory_server_url=orphan.factory_server_url,
        status_kind=orphan.status_kind,
        work_item_id=orphan.work_item_id,
        work_item_status=orphan.work_item_status,
        orphan_reason=orphan.orphan_reason,
        termination_route=(TERMINATION_ROUTE_NONE if termination is None else termination.route),
        termination_succeeded=termination is not None and termination.succeeded,
        termination_detail=(
            "dry run: nothing was exported or terminated"
            if termination is None
            else termination.detail
        ),
        export_comment_id=export_comment_id,
    )


def journal_reconciled(*, journal: JournalWriter, run: ReconciledRun) -> None:
    """Record one reconciliation, plus a distinct record for the rm fallback."""
    record: dict[str, object] = {
        "stage": JOURNAL_STAGE_RECONCILED,
        "run_id": run.run_id,
        "factory_name": run.factory_name,
        "factory_server_url": run.factory_server_url,
        "status_kind": run.status_kind,
        "work_item_id": run.work_item_id,
        "work_item_status": run.work_item_status,
        "orphan_reason": run.orphan_reason,
        "termination_route": run.termination_route,
        "termination_succeeded": run.termination_succeeded,
        "termination_detail": run.termination_detail,
        "export_comment_id": run.export_comment_id,
    }
    journal.append(record=record)
    if run.termination_route == TERMINATION_ROUTE_RM:
        journal.append(
            record={
                "stage": JOURNAL_STAGE_RM_FALLBACK,
                "run_id": run.run_id,
                "factory_server_url": run.factory_server_url,
                "work_item_id": run.work_item_id,
                "termination_succeeded": run.termination_succeeded,
                "termination_detail": run.termination_detail,
            }
        )


def journal_export(*, journal: JournalWriter, orphan: OrphanRun, body: str) -> None:
    """Record a pointer body that had no ledger item to live on."""
    journal.append(
        record={
            "stage": JOURNAL_STAGE_EXPORT,
            "run_id": orphan.run_id,
            "factory_server_url": orphan.factory_server_url,
            "work_item_id": orphan.work_item_id,
            "orphan_reason": orphan.orphan_reason,
            "pointer_body": body,
        }
    )


def journal_error(*, journal: JournalWriter, error: ReconcileError) -> None:
    """Record one reconciliation that could not be completed."""
    journal.append(
        record={
            "stage": JOURNAL_STAGE_ERROR,
            "factory_name": error.factory_name,
            "factory_server_url": error.factory_server_url,
            "run_id": error.run_id,
            "work_item_id": error.work_item_id,
            "reason": error.reason,
            "detail": error.detail,
        }
    )
