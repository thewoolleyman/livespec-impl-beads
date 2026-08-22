"""Dispatch-loop candidate selection and per-item launch primitives."""

from __future__ import annotations

import argparse
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path
from typing import cast

from returns.unsafe import unsafe_perform_io

from livespec_orchestrator_beads_fabro.commands import (
    _dispatcher_self_update as selfup,
)
from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_completion import (
    warn_item_sizing,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_credentials import (
    materialize_overlay,
    read_dispatch_comments,
    read_dispatch_labels,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_id_journal import (
    DispatchJournalIdentity,
    append_dispatch_id_record,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_lock import (
    dispatch_lock_path,
    live_dispatch_lock,
    release_dispatch_lock,
    write_dispatch_lock,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    DispatchOutcome,
    run_dispatch,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import (
    GithubTokenEnvRunner,
    JournalFile,
    ShellCommandRunner,
    WatchedFabroLauncher,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_lessons import (
    read_ratified_lessons,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_outcomes import (
    failed_dispatch_outcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_run import (
    DispatchRunContext,
    run_dispatch_with_watchdog,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_selection import (
    janitor_core_ref,
    post_run_dispositions,
    run_id,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import (
    spans_path,
    workflow_toml,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    build_plan,
    janitor_checkout_path,
    render_goal,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_policy_settings import (
    DEFAULT_MERGE_ON_REVIEW_CAP,
    DEFAULT_REVIEW_FIX_CAP,
    effective_merge_on_review_cap,
    effective_review_fix_cap,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_review_gate import (
    ReviewGateEmission,
    emit_review_gate_from_fabro_events,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "dispatch_one",
]


def dispatch_one(
    *,
    args: argparse.Namespace,
    repo: Path,
    item: WorkItem,
    journal: JournalFile,
    janitor: tuple[str, ...] | None,
) -> DispatchOutcome:
    raw_factory_target = getattr(args, "fabro_factory_target", None)
    dispatch_factory = (
        raw_factory_target.name if isinstance(raw_factory_target, FactoryTarget) else None
    )
    if not isinstance(raw_factory_target, FactoryTarget):
        args.fabro_factory_target = FactoryTarget(name="default", server=None, dev_token=None)
    lock = live_dispatch_lock(repo=repo, work_item_id=item.id)
    if lock is None or lock.dispatch_id is None:
        dispatch_id = run_id()
        lock_path = write_dispatch_lock(repo=repo, work_item_id=item.id, dispatch_id=dispatch_id)
    else:
        dispatch_id = lock.dispatch_id
        lock_path = dispatch_lock_path(repo=repo, work_item_id=item.id)
    with ExitStack() as stack:
        _ = stack.callback(lambda: release_dispatch_lock(path=lock_path))
        return _dispatch_one_locked(
            args=args,
            repo=repo,
            item=item,
            journal=journal,
            janitor=janitor,
            identity=DispatchJournalIdentity(
                dispatch_id=dispatch_id,
                dispatch_factory=dispatch_factory,
            ),
        )


def _dispatch_one_locked(
    *,
    args: argparse.Namespace,
    repo: Path,
    item: WorkItem,
    journal: JournalFile,
    janitor: tuple[str, ...] | None,
    identity: DispatchJournalIdentity,
) -> DispatchOutcome:
    goal_file = Path(tempfile.gettempdir()) / f"fabro-goal-{item.id}.md"
    overlay_file = Path(tempfile.gettempdir()) / f"fabro-run-config-{item.id}.toml"
    janitor_checkout = janitor_checkout_path(repo=repo, work_item_id=item.id)
    raw_labels = read_dispatch_labels(repo=repo, item=item)
    if isinstance(raw_labels, str):
        return failed_dispatch_outcome(
            journal=journal, work_item_id=item.id, stage="ledger-labels", detail=raw_labels
        )
    factory_target = cast("FactoryTarget", args.fabro_factory_target)
    plan = build_plan(
        repo=repo,
        work_item_id=item.id,
        workflow_toml=overlay_file,
        goal_file=goal_file,
        fabro_bin=args.fabro_bin,
        fabro_factory_name=factory_target.name,
        fabro_factory_server=factory_target.server,
        fabro_factory_dev_token=factory_target.dev_token,
        janitor=janitor,
        janitor_checkout=janitor_checkout,
        janitor_core_ref=janitor_core_ref(repo=repo),
        # An unreadable `.livespec.jsonc` falls back to the documented
        # defaults, visibly and here rather than inside the reader.
        # `unsafe_perform_io` is required: `IOResult.value_or` returns
        # `IO[value]`, not the value.
        review_fix_cap=unsafe_perform_io(
            effective_review_fix_cap(item=item, cwd=repo, raw_labels=raw_labels).value_or(
                DEFAULT_REVIEW_FIX_CAP
            )
        ),
        merge_on_review_cap=unsafe_perform_io(
            effective_merge_on_review_cap(item=item, cwd=repo, raw_labels=raw_labels).value_or(
                DEFAULT_MERGE_ON_REVIEW_CAP
            )
        ),
    )
    warn_item_sizing(item=item, journal=journal)
    comments = read_dispatch_comments(repo=repo, item=item)
    if isinstance(comments, str):
        return failed_dispatch_outcome(
            journal=journal, work_item_id=item.id, stage="ledger-comments", detail=comments
        )
    # Resolved once and journaled: `workflow_toml` now picks the dispatch
    # target's OWN committed workflow over the plugin's bundled default, and
    # that config carries the sandbox image pin — so which file won is the
    # first thing to read when a dispatch dies on a missing toolchain.
    committed_workflow = workflow_toml(args=args)
    append_dispatch_id_record(
        journal=journal,
        work_item_id=item.id,
        identity=identity,
        started_at_epoch=time.time(),
        workflow_toml=committed_workflow,
    )
    token_supplier = selfup.github_token_supplier()
    if isinstance(token_supplier, str):
        return failed_dispatch_outcome(
            journal=journal,
            work_item_id=item.id,
            stage="github-app-auth",
            detail=token_supplier,
        )
    overlay_error = materialize_overlay(
        committed=committed_workflow,
        overlay=overlay_file,
        repo=repo,
        work_item_id=item.id,
        dispatch_id=identity.dispatch_id,
        token=token_supplier,
    )
    if overlay_error is not None:
        return failed_dispatch_outcome(
            journal=journal,
            work_item_id=item.id,
            stage="run-config-overlay",
            detail=overlay_error,
        )
    # Lessons are read host-side from `repo` (the dispatcher's operative
    # checkout, where the reflector maintains loop-reflection-gate/lessons.md),
    # exactly like `comments` above; only committed content is read, so an
    # unmerged reflector proposal never influences a brief.
    lessons = read_ratified_lessons(lessons_root=repo)
    goal_text = render_goal(
        item=item, repo=repo, branch=plan.branch, comments=comments, lessons=lessons
    )
    _ = goal_file.write_text(goal_text, encoding="utf-8")
    started_at, outcome = run_dispatch_with_watchdog(
        context=DispatchRunContext(
            args=args,
            repo=repo,
            plan=plan,
            journal=journal,
            overlay_file=overlay_file,
            token_supplier=token_supplier,
        ),
        run_dispatch_func=run_dispatch,
        fabro_launcher_type=WatchedFabroLauncher,
    )
    post_run_dispositions(
        args=args,
        repo=repo,
        item=item,
        outcome=outcome,
        journal=journal,
        wall_clock_seconds=time.monotonic() - started_at,
        dispatch_context_size=len(goal_text),
        token_supplier=token_supplier,
    )
    emit_review_gate_from_fabro_events(
        emission=ReviewGateEmission(
            plan=plan,
            runner=GithubTokenEnvRunner(inner=ShellCommandRunner(), token=token_supplier),
            journal=journal,
            spans_path=spans_path(args=args, repo=repo),
            work_item_id=item.id,
            dispatch_id=identity.dispatch_id,
            run_id=outcome.fabro_run_id,
            dispatch_factory=identity.dispatch_factory,
        )
    )
    return outcome
