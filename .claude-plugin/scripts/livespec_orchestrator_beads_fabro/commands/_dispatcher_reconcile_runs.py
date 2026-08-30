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

A run parked at a human gate whose item is still live has no moot question to
release it, so it is governed instead by `dispatcher.blocked_run_grace_seconds`
(`_dispatcher_reconcile_runs_grace.py`). Past the grace it becomes an orphan
like any other and takes the same export-then-terminate path; inside it — or
with a park nobody can measure — it is REPORTED as held and left running. The
held set is carried separately from the reconciled set precisely so that
"reported" can never become "terminated" by a later edit.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandRunner,
    JournalWriter,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_attribution import (
    FactoryRunInventory,
    JournaledRuns,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_export import (
    LedgerComments,
    export_orphan_reference,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_grace import (
    DEFAULT_BLOCKED_RUN_GRACE_SECONDS,
    BlockedRunGrace,
    HeldRun,
    parked_seconds_from_record,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_join import (
    OrphanRun,
    blocked_grace_candidate_ids,
    classify_blocked_holds,
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
from livespec_orchestrator_beads_fabro.commands._fabro_port_records import fabro_inspect_record
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
_INSPECT_TIMEOUT_SECONDS = 60.0
_ERROR_NO_SERVER_URL = "factory-server-url-missing"
_ERROR_PS_FAILED = "factory-ps-failed"
_ERROR_EXPORT_FAILED = "export-not-verified"


@dataclass(frozen=True, kw_only=True)
class ReconcileInputs:
    """Everything one reconciliation pass reads or writes through.

    `now_epoch` is a seam rather than a call site: the grace arm compares a
    measured park against a configured bound, and a test that cannot say what
    time it is can only assert the boundary by sleeping.
    """

    repo: Path
    fabro_bin: str
    id_prefix: str
    items: Sequence[WorkItem]
    journaled: JournaledRuns
    runner: CommandRunner
    journal: JournalWriter
    ledger: LedgerComments
    http: FabroHttpTransport = field(default_factory=UrllibFabroHttpTransport)
    blocked_run_grace_seconds: int = DEFAULT_BLOCKED_RUN_GRACE_SECONDS
    now_epoch: float | None = None


@dataclass(kw_only=True)
class _PassResults:
    """What one pass has accumulated across every factory surveyed so far.

    `held` rides beside `reconciled` rather than inside it: a held run is a
    REPORT and a reconciled one is an ACT, and keeping them in one list is how
    a later edit would come to terminate the first by iterating the second.
    """

    reconciled: list[ReconciledRun] = field(default_factory=list)
    errors: list[ReconcileError] = field(default_factory=list)
    held: list[HeldRun] = field(default_factory=list)


def reconcile_runs(
    *,
    inputs: ReconcileInputs,
    factories: Sequence[FactoryTarget],
    dry_run: bool = False,
) -> ReconcileRunsSummary:
    """Survey every factory, reconciling the orphans the ledger disowns."""
    item_statuses = {item.id: item.status for item in inputs.items}
    results = _PassResults()
    for factory in factories:
        if factory.server is None:
            results.errors.append(
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
            results=results,
        )
    if not dry_run:
        for error in results.errors:
            journal_error(journal=inputs.journal, error=error)
    return ReconcileRunsSummary(
        reconciled=tuple(results.reconciled),
        errors=tuple(results.errors),
        dry_run=dry_run,
        held=tuple(results.held),
    )


def _reconcile_one_factory(
    *,
    inputs: ReconcileInputs,
    factory: FactoryTarget,
    item_statuses: dict[str, str],
    dry_run: bool,
    results: _PassResults,
) -> None:
    port = _port_for(inputs=inputs, factory=factory)
    ps = port.ps(timeout_seconds=_PS_TIMEOUT_SECONDS)
    if ps.command.exit_code != 0:
        results.errors.append(
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
    inventory = FactoryRunInventory(
        runs=ps.runs,
        item_statuses=item_statuses,
        journaled=inputs.journaled,
        id_prefix=inputs.id_prefix,
        factory_name=factory.name,
        factory_server_url=str(factory.server),
    )
    grace = _measured_grace(inputs=inputs, port=port, inventory=inventory)
    orphans = classify_orphans(inventory=inventory, grace=grace)
    results.held.extend(classify_blocked_holds(inventory=inventory, grace=grace))
    for orphan in orphans:
        outcome = _reconcile_one_run(inputs=inputs, port=port, orphan=orphan, dry_run=dry_run)
        if isinstance(outcome, ReconcileError):
            results.errors.append(outcome)
            continue
        results.reconciled.append(outcome)


def _measured_grace(
    *,
    inputs: ReconcileInputs,
    port: FabroPort,
    inventory: FactoryRunInventory,
) -> BlockedRunGrace | None:
    """Measure the park of every run the grace arm governs, or None when off.

    A `blocked_run_grace_seconds` of `0` disables the arm outright: no run is
    inspected, none is held, and classification falls back to the
    moot-question join alone.
    """
    if inputs.blocked_run_grace_seconds <= 0:
        return None
    candidates = blocked_grace_candidate_ids(inventory=inventory)
    now_epoch = time.time() if inputs.now_epoch is None else inputs.now_epoch
    return BlockedRunGrace(
        grace_seconds=inputs.blocked_run_grace_seconds,
        parked_seconds_by_run={
            run_id: _parked_seconds(port=port, run_id=run_id, now_epoch=now_epoch)
            for run_id in candidates
        },
    )


def _parked_seconds(*, port: FabroPort, run_id: str, now_epoch: float) -> float | None:
    inspected = port.inspect(run_id=run_id, timeout_seconds=_INSPECT_TIMEOUT_SECONDS)
    return parked_seconds_from_record(
        record=fabro_inspect_record(payload=inspected.payload),
        now_epoch=now_epoch,
    )


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
