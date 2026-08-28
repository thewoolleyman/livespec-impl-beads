"""Operator valve for reconciling already-merged active or parked items.

The merged-PR RESOLUTION half lives in `_dispatcher_reconcile_merged_pr` and is
re-exported here, so this module stays the command supervisor — preflight,
journal, janitor, acceptance, outcome — and its published surface is unchanged.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._config import resolve_fabro_bin
from livespec_orchestrator_beads_fabro.commands._dispatcher_command_common import (
    EXIT_FAILURE,
    EXIT_PRECONDITION_ERROR,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_completion import (
    complete_and_accept,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_lock import (
    live_dispatch_lock,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandRunner,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_janitor import post_merge
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import (
    invoker_from_args,
    require_invoker_refusal,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import (
    JournalFile,
    ShellCommandRunner,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import (
    emit_outcomes,
    load_items,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_selection import (
    janitor_core_ref,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_otel_wiring import parse_janitor
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import journal_path
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    DispatchPlan,
    build_plan,
    janitor_reconcile_checkout_path,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_merged_pr import (
    merged_pr_list_argv,
    parse_merged_pr_list,
    resolve_merged_pr,
)
from livespec_orchestrator_beads_fabro.io import write_stderr
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "merged_pr_list_argv",
    "parse_merged_pr_list",
    "reconcile_plan",
    "run_reconcile_merged_command",
]

_RECONCILE_MERGED_ALLOWED_STATUSES = frozenset({"active", "backlog", "ready", "blocked"})
# The refusal for a rework-pending item, which NAMES the route that replaces
# this valve. It is deliberately unconditional on `--force`: forcing past it
# would re-run a post-run disposition that already ran and chose rework.
_REWORK_PENDING_REFUSAL = (
    "ERROR: reconcile-merged refused: work-item {item_id} carries rework:pending, so its "
    "dispatch already COMPLETED its post-run disposition and that disposition's outcome "
    "was rework. Drive the fix-forward rework re-dispatch instead — the next dispatcher "
    "drain pass, or `dispatcher.py dispatch --repo {repo} --item {item_id}`. --force does "
    "not bypass this refusal.\n"
)


def run_reconcile_merged_command(
    *, args: argparse.Namespace, runner: CommandRunner | None = None
) -> int:
    """Run the post-merge janitor + acceptance valve for a stranded merged item."""
    repo = Path(args.repo)
    # FIRST, ahead of the tenant read and of every write: an unattributed
    # invocation under `dispatcher.require_invoker` is refused here so the
    # refusal itself performs no half of the reconcile.
    invoker_refusal = require_invoker_refusal(args=args, repo=repo)
    if invoker_refusal is not None:
        _ = write_stderr(text=invoker_refusal)
        return EXIT_PRECONDITION_ERROR
    preflight = _reconcile_preflight(args=args, repo=repo)
    if isinstance(preflight, int):
        return preflight
    item = preflight.item
    janitor = preflight.janitor
    command_runner = ShellCommandRunner() if runner is None else runner
    journal = JournalFile(
        path=journal_path(args=args, repo=repo),
        identity=invoker_from_args(args=args),
    )
    plan = reconcile_plan(repo=repo, item=item, janitor=janitor)
    merged = resolve_merged_pr(plan=plan, item=item, runner=command_runner, journal=journal)
    if isinstance(merged, str):
        _ = write_stderr(text=merged)
        return EXIT_PRECONDITION_ERROR
    if merged is None:
        _ = write_stderr(text=f"ERROR: no merged PR found for active work-item {item.id}\n")
        return EXIT_PRECONDITION_ERROR
    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=plan,
        runner=command_runner,
        journal=journal,
        merged=merged,
    )
    if outcome.status == "green" and outcome.stage == "done":
        complete_and_accept(repo=repo, item=item, outcome=outcome, journal=journal)
    journal.append(record={"stage": "outcome", "outcome": _outcome_payload(outcome=outcome)})
    emit_outcomes(outcomes=[outcome], as_json=args.as_json)
    return 0 if outcome.status == "green" and outcome.stage == "done" else EXIT_FAILURE


@dataclass(frozen=True, kw_only=True)
class _ReconcilePreflight:
    item: WorkItem
    janitor: tuple[str, ...] | None


def _reconcile_preflight(*, args: argparse.Namespace, repo: Path) -> _ReconcilePreflight | int:
    if not repo.exists():
        _ = write_stderr(text="ERROR: --repo does not exist\n")
        return EXIT_PRECONDITION_ERROR
    items = {item.id: item for item in load_items(repo=repo)}
    item = items.get(args.item)
    if item is None:
        _ = write_stderr(text=f"ERROR: work-item {args.item} not found\n")
        return EXIT_PRECONDITION_ERROR
    item_refusal = _item_precondition_refusal(item=item, repo=repo)
    if item_refusal is not None:
        _ = write_stderr(text=item_refusal)
        return EXIT_PRECONDITION_ERROR
    janitor, janitor_ok = parse_janitor(raw=args.janitor)
    if not janitor_ok:
        return 2
    if not args.force:
        live_detail = _live_dispatch_refusal(args=args, repo=repo, item=item)
        if live_detail is not None:
            _ = write_stderr(text=live_detail)
            return EXIT_PRECONDITION_ERROR
    return _ReconcilePreflight(item=item, janitor=janitor)


def _item_precondition_refusal(*, item: WorkItem, repo: Path) -> str | None:
    """The two refusals decided by the item's own ledger state, in order.

    Rework-pending is checked FIRST because it binds WHATEVER the item's
    status is, so a marked `acceptance` item is refused here rather than
    reaching the status gate; and it sits ahead of the `--force`-gated live
    lock check in the caller so `--force` cannot reach past it.
    """
    if item.rework_pending:
        return _REWORK_PENDING_REFUSAL.format(item_id=item.id, repo=repo)
    if item.status not in _RECONCILE_MERGED_ALLOWED_STATUSES:
        return (
            f"ERROR: reconcile-merged expected active or parked item {item.id}; "
            f"found {item.status}\n"
        )
    return None


def _live_dispatch_refusal(*, args: argparse.Namespace, repo: Path, item: WorkItem) -> str | None:
    _ = args
    lock = live_dispatch_lock(repo=repo, work_item_id=item.id)
    if lock is None:
        return None
    age_seconds = max(0.0, time.time() - lock.started_at_epoch)
    return (
        f"ERROR: reconcile-merged refused: dispatch lock is held by live pid "
        f"{lock.pid} for work-item {item.id} (age {age_seconds:.1f}s). "
        f"Confirm with `fabro ps`, wait for the janitor window to close, or rerun "
        f"with --force only after confirming the original dispatcher process is dead.\n"
    )


def reconcile_plan(*, repo: Path, item: WorkItem, janitor: tuple[str, ...] | None) -> DispatchPlan:
    """Build the subset of a dispatch plan needed by the reconcile valve."""
    return build_plan(
        repo=repo,
        work_item_id=item.id,
        workflow_toml=repo / "tmp" / f"reconcile-{item.id}-workflow.toml",
        goal_file=repo / "tmp" / f"reconcile-{item.id}-goal.md",
        fabro_bin=resolve_fabro_bin(cwd=repo),
        janitor=janitor,
        janitor_checkout=janitor_reconcile_checkout_path(repo=repo, work_item_id=item.id),
        janitor_core_ref=janitor_core_ref(repo=repo),
    )


def _outcome_payload(*, outcome: DispatchOutcome) -> dict[str, object]:
    return {
        "work_item_id": outcome.work_item_id,
        "status": outcome.status,
        "stage": outcome.stage,
        "pr_number": outcome.pr_number,
        "merge_sha": outcome.merge_sha,
        "detail": outcome.detail,
        "fabro_run_id": outcome.fabro_run_id,
    }
