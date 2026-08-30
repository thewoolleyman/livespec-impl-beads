"""One reconciliation pass on the dispatch path, and the record it leaves.

`reconcile-runs` was operator-invoked only, which made the invariant it
enforces depend on somebody remembering to enforce it. This module is the
seam that runs it automatically, from ONE call site — `dispatch_preamble`.

ONE call site, deliberately. The preamble is the head of every `dispatcher.py
dispatch` AND of every `loop` iteration (`_dispatcher_loop_command._start_loop`
calls it before `candidates(...)` selects anything), so a single call there is
exactly "once per loop iteration, before selection" and "once before
admission" at the same time. Adding a second call in the loop command would
reconcile the same inventory twice per tick — two `fabro ps` round-trips per
factory for one answer — so the wiring is a property of where the preamble
sits, not of how many places call this.

Reconciliation is NOT a precondition of dispatching. A factory that cannot be
surveyed, a ledger that cannot be read, a config that will not parse — none of
them says anything about whether the item in hand may be dispatched, and
refusing on them would convert an unrelated outage into a queue stall. So the
pass is fail-open: every recoverable failure becomes a `failure_detail` on the
journal record and the dispatch proceeds.

Fail-open is how a blind spot hides, so the pass ALWAYS journals, including
when it found nothing. A silent pass and a pass that found nothing are
otherwise the same absence, and only one of them means the wiring works.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from returns.unsafe import unsafe_perform_io

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import invoker_from_args
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import (
    JournalFile,
    ShellCommandRunner,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import load_items
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import journal_path, store_config
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs import (
    ReconcileRunsSummary,
    reconcile_runs,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_attribution import (
    read_journaled_runs,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_factories import (
    reconcile_factory_targets,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_grace import (
    DEFAULT_BLOCKED_RUN_GRACE_SECONDS,
    resolve_blocked_run_grace_seconds,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_inputs import (
    ReconcileInputs,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_run_stamp import repo_run_attribution
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt
from livespec_orchestrator_beads_fabro.errors import (
    BeadsCommandError,
    BeadsConnectionError,
    BeadsCredentialMissingError,
    BeadsMappingError,
    BeadsTenantMissingError,
    ConnectionPrefixMissingError,
    LivespecConfigUnreadableError,
)

__all__: list[str] = [
    "JOURNAL_STAGE_RECONCILE_RUNS",
    "ReconcilePassSummary",
    "reconcile_runs_pass",
]

JOURNAL_STAGE_RECONCILE_RUNS = "reconcile-runs-pass"

# What the pass absorbs rather than propagates. Every entry is an EXPECTED
# failure of a surface the pass merely reads — an unreachable tenant, an
# unparsable `.livespec.jsonc`, an unwritable path. A bug still raises and
# still reaches the supervisor, because swallowing one here would make the
# dispatch path quietly stop reconciling with nothing to read afterwards.
_RECOVERABLE: tuple[type[Exception], ...] = (
    OSError,
    BeadsCommandError,
    BeadsConnectionError,
    BeadsCredentialMissingError,
    BeadsMappingError,
    BeadsTenantMissingError,
    ConnectionPrefixMissingError,
    LivespecConfigUnreadableError,
)

# The summary a repo with no declared factory produces. Shared rather than
# constructed per call because it is immutable and carries no per-pass state.
_NOTHING_SURVEYED = ReconcileRunsSummary(reconciled=(), errors=(), dry_run=False)


@dataclass(frozen=True, kw_only=True)
class ReconcilePassSummary:
    """What one wired reconciliation pass surveyed, found, and could not do.

    `orphans_found` counts every orphan the join produced, whether or not it
    was successfully reconciled; `orphans_reconciled` counts only the ones
    whose termination actually landed. Reporting one number for both would
    make a factory that refuses every cancel read as a clean pass.
    """

    factories_surveyed: int
    orphans_found: int
    orphans_reconciled: int
    errors: int
    failure_detail: str | None


def reconcile_runs_pass(*, args: argparse.Namespace, repo: Path) -> ReconcilePassSummary:
    """Reconcile every declared factory once, journal the pass, and never raise."""
    journal = JournalFile(
        path=journal_path(args=args, repo=repo),
        identity=invoker_from_args(args=args),
    )
    outcome = attempt(
        action=lambda: _survey(args=args, repo=repo, journal=journal),
        exceptions=_RECOVERABLE,
    )
    summary = _failed_pass(outcome=outcome) if isinstance(outcome, AttemptFailure) else outcome
    journal.append(
        record={
            "stage": JOURNAL_STAGE_RECONCILE_RUNS,
            "factories_surveyed": summary.factories_surveyed,
            "orphans_found": summary.orphans_found,
            "orphans_reconciled": summary.orphans_reconciled,
            "errors": summary.errors,
            "failure_detail": summary.failure_detail,
        }
    )
    return summary


def _survey(
    *,
    args: argparse.Namespace,
    repo: Path,
    journal: JournalFile,
) -> ReconcilePassSummary:
    factories = reconcile_factory_targets(repo=repo)
    if not factories:
        # No declared factory means no inventory to survey, so the ledger read
        # and the beads client below would be pure cost. Short-circuiting here
        # keeps an unconfigured repo's dispatch path free of a tenant round-trip
        # it can do nothing with.
        return _pass_summary(factories_surveyed=0, summary=_NOTHING_SURVEYED)
    store = store_config(repo=repo)
    summary = reconcile_runs(
        inputs=ReconcileInputs(
            repo=repo,
            fabro_bin=args.fabro_bin,
            id_prefix=store.prefix,
            items=load_items(repo=repo),
            journaled=read_journaled_runs(path=journal.path),
            runner=ShellCommandRunner(),
            journal=journal,
            ledger=make_beads_client(config=store),
            attribution=repo_run_attribution(repo=repo),
            blocked_run_grace_seconds=unsafe_perform_io(
                resolve_blocked_run_grace_seconds(cwd=repo).value_or(
                    DEFAULT_BLOCKED_RUN_GRACE_SECONDS
                )
            ),
        ),
        factories=factories,
        dry_run=False,
    )
    return _pass_summary(factories_surveyed=len(factories), summary=summary)


def _pass_summary(
    *,
    factories_surveyed: int,
    summary: ReconcileRunsSummary,
) -> ReconcilePassSummary:
    # An error naming a run IS an orphan the join found and the pass could not
    # dispose of; an error naming no run is a factory-level failure and no
    # orphan at all. Counting them alike would inflate the orphan census with
    # unreachable factories.
    unreconciled = sum(1 for error in summary.errors if error.run_id is not None)
    return ReconcilePassSummary(
        factories_surveyed=factories_surveyed,
        orphans_found=len(summary.reconciled) + unreconciled,
        orphans_reconciled=sum(1 for run in summary.reconciled if run.termination_succeeded),
        errors=len(summary.errors),
        failure_detail=None,
    )


def _failed_pass(*, outcome: AttemptFailure) -> ReconcilePassSummary:
    return ReconcilePassSummary(
        factories_surveyed=0,
        orphans_found=0,
        orphans_reconciled=0,
        errors=1,
        failure_detail=f"{type(outcome.error).__name__}: {outcome.error}",
    )
