"""The `reconcile-runs` dispatcher subcommand (aliased `stale-run-sweep`).

`stale-run-sweep` is kept as an alias rather than as a second
implementation. It surveyed one factory, considered only `runnable` and
`running` runs, and skipped any run whose item it could not find — three
filters that together let a run parked at the human gate hold a scheduler
slot indefinitely. Everything it did correctly, this command does; nothing
would be gained by keeping a narrower sweep reachable under its old name.

`--dry-run --json` is the read-only projection: it emits the orphan set and
performs no export, no termination, and no journal write, so a caller can
render "orphaned factory runs" without the survey itself being an act.

The projection carries a second lane beside the orphans: the parked runs the
grace arm is still HOLDING, each with the seconds it has left. A hold that
nothing renders is indistinguishable from a run nobody is watching, which is
the failure the grace arm exists to bound, so the held lane is emitted on
every run — dry or not.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from returns.unsafe import unsafe_perform_io

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro.commands._config import resolve_fabro_bin
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
from livespec_orchestrator_beads_fabro.commands._dispatcher_run_stamp import (
    repo_run_attribution,
)
from livespec_orchestrator_beads_fabro.io import write_stdout

__all__: list[str] = ["run_reconcile_runs_command"]


def run_reconcile_runs_command(*, args: argparse.Namespace) -> int:
    """Reconcile every configured factory, or report why one could not be."""
    repo = Path(args.repo) if args.repo is not None else Path.cwd()
    store = store_config(repo=repo)
    journal = journal_path(args=args, repo=repo)
    summary = reconcile_runs(
        inputs=ReconcileInputs(
            repo=repo,
            fabro_bin=(
                args.fabro_bin if args.fabro_bin is not None else resolve_fabro_bin(cwd=repo)
            ),
            id_prefix=store.prefix,
            items=load_items(repo=repo),
            journaled=read_journaled_runs(path=journal),
            runner=ShellCommandRunner(),
            journal=JournalFile(path=journal, identity=invoker_from_args(args=args)),
            ledger=make_beads_client(config=store),
            attribution=repo_run_attribution(repo=repo),
            blocked_run_grace_seconds=unsafe_perform_io(
                resolve_blocked_run_grace_seconds(cwd=repo).value_or(
                    DEFAULT_BLOCKED_RUN_GRACE_SECONDS
                )
            ),
        ),
        factories=reconcile_factory_targets(repo=repo, factory=args.factory),
        dry_run=args.dry_run,
    )
    _emit(summary=summary, as_json=args.as_json)
    return 1 if _has_failure(summary=summary) else 0


def _has_failure(*, summary: ReconcileRunsSummary) -> bool:
    if summary.errors:
        return True
    return any(not run.termination_succeeded for run in summary.reconciled)


def _emit(*, summary: ReconcileRunsSummary, as_json: bool) -> None:
    if as_json:
        payload = {
            "dry_run": summary.dry_run,
            "errors": [asdict(error) for error in summary.errors],
            "held": [asdict(run) for run in summary.held],
            "reconciled": [asdict(run) for run in summary.reconciled],
        }
        _ = write_stdout(text=json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return
    for error in summary.errors:
        _ = write_stdout(text=f"ERROR   {error.factory_name}  {error.reason}: {error.detail}\n")
    for run in summary.reconciled:
        _ = write_stdout(
            text=(
                f"ORPHAN  {run.work_item_id}  {run.run_id}  factory={run.factory_name} "
                f"run={run.status_kind} item={run.work_item_status} "
                f"reason={run.orphan_reason} route={run.termination_route}\n"
            )
        )
    for run in summary.held:
        _ = write_stdout(
            text=(
                f"HELD    {run.work_item_id}  {run.run_id}  factory={run.factory_name} "
                f"run={run.status_kind} item={run.work_item_status} "
                f"reason={run.hold_reason} remaining={run.seconds_remaining}\n"
            )
        )
    if not summary.errors and not summary.reconciled and not summary.held:
        _ = write_stdout(text="(no orphaned fabro runs found)\n")
