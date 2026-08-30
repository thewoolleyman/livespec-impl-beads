"""Reconcile every configured factory's non-terminal run inventory.

The invariant: at any moment, on every configured factory, the set of
non-terminal Fabro runs equals the set of ledger items that are `active`
under a claim whose journaled run id is that run. Any other non-terminal run
is an ORPHAN, and reconciling it is a machine act — export its record,
terminate it, journal what happened — with no human in the loop.

Reconciling a run NEVER touches the work-item. Not its status, not its
`blocked_reason`, not its labels. A needs-human decision lives in the ledger
and a human clears it there; what this module removes is a factory-side
scheduler slot held for a question that is already moot, which is a
different object entirely. The ledger seam handed in cannot express those
writes, so the guarantee is structural rather than a convention.

Failure is per-factory and per-run. One unreachable factory journals an
error and the survey continues on the rest, because the alternative — one
outage suppressing reconciliation everywhere — is exactly the silent-hold
failure this command exists to end.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandRunner,
    JournalWriter,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_export import (
    LedgerComments,
    export_orphan_reference,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_join import (
    JournaledRuns,
    OrphanRun,
    classify_orphans,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_records import (
    JOURNAL_STAGE_ERROR,
    ReconciledRun,
    ReconcileError,
    ReconcileRunsSummary,
    journal_error,
    journal_export,
    journal_reconciled,
    journal_unauthenticated,
    reconciled_from,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_terminate import (
    terminate_orphan_run,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroPort, FabroTarget
from livespec_orchestrator_beads_fabro.commands._fabro_port_http import (
    FabroHttpTransport,
    UrllibFabroHttpTransport,
)
from livespec_orchestrator_beads_fabro.commands._run_attribution import (
    GOAL_TEXT_ONLY,
    RunAttribution,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "JOURNAL_STAGE_ERROR",
    "ReconcileError",
    "ReconcileInputs",
    "ReconcileRunsSummary",
    "ReconciledRun",
    "reconcile_runs",
]

_PS_TIMEOUT_SECONDS = 60.0
_ERROR_NO_SERVER_URL = "factory-server-url-missing"
_ERROR_PS_FAILED = "factory-ps-failed"
_ERROR_EXPORT_FAILED = "export-not-verified"


@dataclass(frozen=True, kw_only=True)
class ReconcileInputs:
    """Everything one reconciliation pass reads or writes through."""

    repo: Path
    fabro_bin: str
    id_prefix: str
    items: Sequence[WorkItem]
    journaled: JournaledRuns
    runner: CommandRunner
    journal: JournalWriter
    ledger: LedgerComments
    # The run-to-item evidence this repo has recorded. Defaulted to the
    # regex-only value so a caller that cannot reach the ledger still reconciles
    # rather than refusing; the join composes it with the journal index.
    attribution: RunAttribution = GOAL_TEXT_ONLY
    http: FabroHttpTransport = field(default_factory=UrllibFabroHttpTransport)
    # Narrows the pass to runs attributed to ONE work-item. The default (None)
    # is the whole-inventory sweep; a lifecycle-write hook sets it so closing
    # item A can never reap item B's run as a side effect of A's disposition.
    # It narrows what is ACTED ON, never what is classified: the join still
    # sees every item's status, so a targeted pass and a sweep agree about
    # every run they both look at.
    only_work_item_id: str | None = None


def reconcile_runs(
    *,
    inputs: ReconcileInputs,
    factories: Sequence[FactoryTarget],
    dry_run: bool = False,
) -> ReconcileRunsSummary:
    """Survey every factory, reconciling the orphans the ledger disowns."""
    item_statuses = {item.id: item.status for item in inputs.items}
    reconciled: list[ReconciledRun] = []
    errors: list[ReconcileError] = []
    for factory in factories:
        if factory.server is None:
            errors.append(
                ReconcileError(
                    factory_name=factory.name,
                    factory_server_url=None,
                    run_id=None,
                    work_item_id=None,
                    reason=_ERROR_NO_SERVER_URL,
                    detail=(
                        f"factory {factory.name} declares no server url; a bare Fabro "
                        f"target would survey whichever server the client defaults to"
                    ),
                )
            )
            continue
        _reconcile_one_factory(
            inputs=inputs,
            factory=factory,
            item_statuses=item_statuses,
            dry_run=dry_run,
            reconciled=reconciled,
            errors=errors,
        )
    if not dry_run:
        for error in errors:
            journal_error(journal=inputs.journal, error=error)
    return ReconcileRunsSummary(
        reconciled=tuple(reconciled),
        errors=tuple(errors),
        dry_run=dry_run,
    )


def _reconcile_one_factory(
    *,
    inputs: ReconcileInputs,
    factory: FactoryTarget,
    item_statuses: dict[str, str],
    dry_run: bool,
    reconciled: list[ReconciledRun],
    errors: list[ReconcileError],
) -> None:
    port = _port_for(inputs=inputs, factory=factory)
    ps = port.ps(timeout_seconds=_PS_TIMEOUT_SECONDS)
    if ps.command.exit_code != 0:
        errors.append(
            ReconcileError(
                factory_name=factory.name,
                factory_server_url=factory.server,
                run_id=None,
                work_item_id=None,
                reason=_ERROR_PS_FAILED,
                detail=f"fabro ps exited {ps.command.exit_code}",
            )
        )
        return
    orphans = classify_orphans(
        runs=ps.runs,
        item_statuses=item_statuses,
        journaled=inputs.journaled,
        id_prefix=inputs.id_prefix,
        factory_name=factory.name,
        factory_server_url=str(factory.server),
        attribution=inputs.attribution,
    )
    for orphan in orphans:
        if inputs.only_work_item_id is not None and orphan.work_item_id != inputs.only_work_item_id:
            continue
        outcome = _reconcile_one_run(inputs=inputs, port=port, orphan=orphan, dry_run=dry_run)
        if isinstance(outcome, ReconcileError):
            errors.append(outcome)
            continue
        reconciled.append(outcome)


def _reconcile_one_run(
    *,
    inputs: ReconcileInputs,
    port: FabroPort,
    orphan: OrphanRun,
    dry_run: bool,
) -> ReconciledRun | ReconcileError:
    if dry_run:
        return reconciled_from(orphan=orphan, termination=None, export_comment_id=None)
    export = export_orphan_reference(
        orphan=orphan,
        repo=inputs.repo,
        fabro_bin=inputs.fabro_bin,
        runner=inputs.runner,
        ledger=inputs.ledger,
    )
    if not export.exported:
        return ReconcileError(
            factory_name=orphan.factory_name,
            factory_server_url=orphan.factory_server_url,
            run_id=orphan.run_id,
            work_item_id=orphan.work_item_id,
            reason=_ERROR_EXPORT_FAILED,
            detail=export.detail,
        )
    if export.journal_body is not None:
        journal_export(journal=inputs.journal, orphan=orphan, body=export.journal_body)
    if port.server_api().bearer_token() is None:
        journal_unauthenticated(journal=inputs.journal, orphan=orphan)
    termination = terminate_orphan_run(
        port=port,
        run_id=orphan.run_id,
        status_kind=orphan.status_kind,
    )
    run = reconciled_from(
        orphan=orphan,
        termination=termination,
        export_comment_id=export.comment_id,
    )
    journal_reconciled(journal=inputs.journal, run=run)
    return run


def _port_for(*, inputs: ReconcileInputs, factory: FactoryTarget) -> FabroPort:
    return FabroPort(
        fabro_bin=inputs.fabro_bin,
        target=FabroTarget(server_url=factory.server, dev_token=factory.dev_token),
        runner=inputs.runner,
        cwd=inputs.repo,
        http=inputs.http,
    )
