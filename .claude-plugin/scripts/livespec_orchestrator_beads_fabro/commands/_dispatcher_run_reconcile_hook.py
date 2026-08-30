"""Targeted run reconciliation, and the post-write hook that fires it.

A work-item that leaves `active` disowns whatever factory run was working
it: the ledger is the only gate, so the moment the ledger stops saying
"someone is waiting on this run" the run is an orphan. The whole-inventory
sweep in `_dispatcher_reconcile_runs` finds that eventually; this fires it
AT the disposition, so the scheduler slot comes back in the same second the
decision is made rather than at the next tick.

Two properties make the hook safe to bolt onto a ledger write.

It is TARGETED. Only runs attributed to the item just written are acted on
(`ReconcileInputs.only_work_item_id`), and only the factory that item was
stamped with is surveyed — so a close of one item can never terminate
another's run, and cannot fan out across every declared factory for work it
knows nothing about. When the item carries no `dispatch_factory` stamp there
is no such narrowing available, so the fallback is every declared factory:
an unstamped item's run is still SOMEWHERE, and a survey that skipped it
would report a clean pass over a run it never looked at.

It NEVER fails the ledger write. The disposition has already happened and is
correct; a factory that will not answer is a fact about the factory. The
failure is journaled and the write stands. That makes the hook a
best-effort accelerator rather than a gate, which is the only honest place
for it: the fail-CLOSED half of this invariant is the `orphaned-factory-run`
ledger check in `_dispatcher_orphaned_run_check`, plus the sweep on the loop
tick and the systemd timer. Those also cover every route that never reaches
Python at all -- a hand `bd close`, or another repo's session moving an item
-- which this hook structurally cannot see.
"""

from __future__ import annotations

from pathlib import Path

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro.commands._config import (
    FactoryTarget,
    resolve_fabro_bin,
    resolve_fabro_factory,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import (
    JournalFile,
    ShellCommandRunner,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import load_items
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import store_config
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs import (
    ReconcileInputs,
    ReconcileRunsSummary,
    reconcile_runs,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_factories import (
    reconcile_factory_targets,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_join import (
    read_journaled_runs,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port_http import (
    FabroHttpTransport,
    UrllibFabroHttpTransport,
)
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt
from livespec_orchestrator_beads_fabro.errors import (
    BeadsCommandError,
    BeadsConnectionError,
    BeadsCredentialMissingError,
    BeadsMappingError,
    BeadsTenantMissingError,
    ConnectionPrefixMissingError,
    LivespecConfigUnreadableError,
    WorkItemNotFoundError,
)
from livespec_orchestrator_beads_fabro.store import dispatch_factory_for
from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "JOURNAL_STAGE_HOOK_ERROR",
    "dispatch_journal_path",
    "reconcile_after_lifecycle_write",
    "reconcile_runs_for_item",
    "targeted_factories",
]

JOURNAL_STAGE_HOOK_ERROR = "lifecycle-reconcile-hook-error"

_ACTIVE_STATUS = "active"
_JOURNAL_SUBPATH = ("tmp", "fabro-dispatch-journal.jsonl")

# The failures a factory survey can legitimately produce, enumerated rather
# than caught as a blanket `Exception`: an unreachable tenant, an unreadable
# `.livespec.jsonc`, a `fabro` binary that will not run, a payload that will
# not parse. A bug in the reconciler is NOT in this tuple and still raises —
# "never fail the ledger write" is a promise about the factory, not a licence
# to swallow our own defects.
_HOOK_ERRORS: tuple[type[Exception], ...] = (
    BeadsCommandError,
    BeadsConnectionError,
    BeadsCredentialMissingError,
    BeadsMappingError,
    BeadsTenantMissingError,
    ConnectionPrefixMissingError,
    LivespecConfigUnreadableError,
    WorkItemNotFoundError,
    OSError,
    RuntimeError,
    ValueError,
)


def dispatch_journal_path(*, repo: Path) -> Path:
    """The repo's default dispatch journal — the same path the CLI resolves.

    The CLI reaches it through `journal_path(args=..., repo=...)`, which needs
    an argparse namespace to honour `--journal`. A lifecycle write has no
    namespace and no override to honour, so it resolves the default directly.
    """
    return repo.joinpath(*_JOURNAL_SUBPATH)


def targeted_factories(*, repo: Path, item_id: str) -> tuple[FactoryTarget, ...]:
    """The factories a targeted reconciliation of `item_id` must survey.

    The declared set is read FIRST, and an empty one short-circuits before any
    store read: a repo that declares no factory has nothing to reconcile, and
    the cheapest correct answer must not cost a tenant round trip to reach.
    """
    declared = reconcile_factory_targets(repo=repo)
    if not declared:
        return ()
    stamped = dispatch_factory_for(path=store_config(repo=repo), work_item_id=item_id)
    if stamped is None:
        return declared
    return (resolve_fabro_factory(cwd=repo, factory=stamped),)


def reconcile_runs_for_item(
    *,
    repo: Path,
    item_id: str,
    runner: CommandRunner | None = None,
    http: FabroHttpTransport | None = None,
) -> ReconcileRunsSummary:
    """Reconcile only the non-terminal runs attributed to one work-item.

    Idempotent by construction rather than by a guard: the join considers only
    the status kinds in `NON_TERMINAL_STATUS_KINDS`, so a run that has already
    terminated — whether an earlier call terminated it or it ended on its own —
    is not an orphan and is not touched. Calling this twice over the same item
    therefore reconciles once and reports nothing the second time.
    """
    factories = targeted_factories(repo=repo, item_id=item_id)
    if not factories:
        return ReconcileRunsSummary(reconciled=(), errors=(), dry_run=False)
    config = store_config(repo=repo)
    journal = dispatch_journal_path(repo=repo)
    return reconcile_runs(
        inputs=ReconcileInputs(
            repo=repo,
            fabro_bin=resolve_fabro_bin(cwd=repo),
            id_prefix=config.prefix,
            items=load_items(repo=repo),
            journaled=read_journaled_runs(path=journal),
            runner=ShellCommandRunner() if runner is None else runner,
            journal=JournalFile(path=journal),
            ledger=make_beads_client(config=config),
            http=UrllibFabroHttpTransport() if http is None else http,
            only_work_item_id=item_id,
        ),
        factories=factories,
    )


def reconcile_after_lifecycle_write(*, path: StoreConfig, item_id: str, status: str) -> None:
    """Reconcile `item_id`'s runs after a ledger write landed it on `status`.

    Fires on every landing OTHER than `active`, which is the predicate the
    orphan join itself uses — so the hook and the invariant it serves cannot
    disagree about which dispositions disown a run. Reading it as "a transition
    FROM active" would be narrower than the join and would miss the closes and
    valve moves that leave an already-non-active item holding a live run.

    A `StoreConfig` with no `repo_root` carries no factory context to survey
    (there is no `.livespec.jsonc` to read a factories table out of), so the
    hook is a documented no-op there rather than a guess. Every seam that
    resolves its config through `resolve_store_config` carries one.
    """
    repo = path.repo_root
    if status == _ACTIVE_STATUS or repo is None:
        return
    outcome = attempt(
        action=lambda: reconcile_runs_for_item(repo=repo, item_id=item_id),
        exceptions=_HOOK_ERRORS,
    )
    if isinstance(outcome, AttemptFailure):
        _journal_hook_failure(repo=repo, item_id=item_id, error=outcome.error)


def _journal_hook_failure(*, repo: Path, item_id: str, error: BaseException) -> None:
    """Record a reconciliation the ledger write outlived.

    The journal write is itself attempted rather than trusted: a hook that
    could raise while reporting that it must not raise would defeat its own
    guarantee on the one path where the guarantee matters most.
    """
    _ = attempt(
        action=lambda: JournalFile(path=dispatch_journal_path(repo=repo)).append(
            record={
                "stage": JOURNAL_STAGE_HOOK_ERROR,
                "work_item_id": item_id,
                "reason": type(error).__name__,
                "detail": str(error),
            }
        ),
        exceptions=(OSError,),
    )
