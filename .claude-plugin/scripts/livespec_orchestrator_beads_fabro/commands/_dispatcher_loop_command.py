"""Dispatcher loop command handler."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_admission import (
    admit_and_select,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_command_common import (
    EXIT_FAILURE,
    EXIT_PRECONDITION_ERROR,
    EXIT_UNGRADEABLE_CRITERIA,
    alarm_on_terminal_failure,
    dispatch_exit_code,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_cost_gate import (
    cost_gate_after_verdict,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_effective_criteria import (
    pre_dispatch_criteria_refusal,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_factory_ledger import (
    args_with_dispatch_factory_target,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import (
    JournalFile,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import (
    emit_outcomes,
    ledger_blocked_after_normalization,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop import dispatch_one
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_selection import (
    candidates,
    prepare,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_otel_wiring import arm_otel_egress
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import (
    journal_path,
    run_turn_sink_path,
    spans_path,
    store_config,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_post_verdict import (
    reflector_oob_after_verdict,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reflection import reflect
from livespec_orchestrator_beads_fabro.commands._dispatcher_run_checks import (
    dispatch_preamble,
    requested_items_preflight_error,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_run_turn_guard import (
    append_run_turn_checks,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_run_turn_sink import RunTurnSink
from livespec_orchestrator_beads_fabro.commands._dispatcher_self_update import (
    post_verdict_runner,
    self_update_after_verdict,
)
from livespec_orchestrator_beads_fabro.io import write_stderr
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "run_loop_command",
]


@dataclass(frozen=True, kw_only=True)
class _LoopStart:
    janitor: tuple[str, ...] | None
    items: list[WorkItem]
    journal: JournalFile


def run_loop_command(*, args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    started = _start_loop(args=args, repo=repo)
    if isinstance(started, int):
        return started
    janitor = started.janitor
    items = started.items
    journal = started.journal
    selected_candidates = candidates(args=args, items=items, repo=repo)[: args.budget]
    if args.dry_run:
        picked = _dry_run_outcomes(selected_candidates=selected_candidates)
        # The journal record and the reported outcome list are projected from
        # the SAME `picked` value, so the audit record and the "what would this
        # drain do?" surface can never disagree.
        journal.append(
            record={
                "stage": "loop-pick",
                "dry_run": True,
                "budget": args.budget,
                "picked": [outcome.work_item_id for outcome in picked],
            }
        )
        emit_outcomes(outcomes=picked, as_json=args.as_json)
        return 0
    # The pre-dispatch wall guards the DRAIN too, and it sits after the dry-run
    # return deliberately: `--dry-run` creates no run, so it stays a reporting
    # surface that shows the operator exactly which candidate needs criteria.
    ungradeable = pre_dispatch_criteria_refusal(items=selected_candidates, cwd=repo)
    if ungradeable is not None:
        _ = write_stderr(text=ungradeable)
        return EXIT_UNGRADEABLE_CRITERIA
    outcomes = _dispatch_loop_wave(
        args=args,
        repo=repo,
        items=items,
        selected_candidates=selected_candidates,
        journal=journal,
        janitor=janitor,
    )
    if not outcomes:
        emit_outcomes(outcomes=[], as_json=args.as_json)
        return 0
    emit_outcomes(outcomes=outcomes, as_json=args.as_json)
    # Verdict is computed BEFORE the mechanical reflection stage and is
    # immutable by it (loop-reflection-gate best-practices §6: reflection
    # never changes a dispatch verdict). reflect() is fail-open and never
    # raises — it cannot alter `exit_code`.
    exit_code = dispatch_exit_code(outcomes=outcomes)
    alarm_on_terminal_failure(
        outcomes=outcomes,
        include_loop_summary=True,
        journal=journal,
    )
    cost_gate_after_verdict(
        args=args,
        repo=repo,
        outcomes=outcomes,
        journal=journal,
        runner=post_verdict_runner(runner=None),
    )
    self_update_after_verdict(
        repo=repo,
        outcomes=outcomes,
        journal=journal,
        runner=post_verdict_runner(runner=None),
    )
    dispatch_journal_path = journal_path(args=args, repo=repo)
    append_run_turn_checks(
        outcomes=tuple(outcomes),
        journal=journal,
        journal_path=dispatch_journal_path,
        sink=RunTurnSink(path=run_turn_sink_path(args=args, repo=repo)),
    )
    reflect(
        outcomes=outcomes,
        journal=journal,
        journal_path=dispatch_journal_path,
        spans_path=spans_path(args=args, repo=repo),
    )
    reflector_oob_after_verdict(args=args, repo=repo, journal=journal)
    return exit_code


def _dry_run_outcomes(*, selected_candidates: list[WorkItem]) -> list[DispatchOutcome]:
    """Project the planned selection onto the reported outcome surface.

    SPECIFICATION/contracts.md requires --dry-run to "compute and report
    exactly the selection the same invocation would dispatch", and permits
    journaling that selection only as an ADDITION — not as the discharge of
    the reporting obligation. Nothing here launches a run, mutates the ledger,
    or writes the work-item store: the candidates are re-labelled, never
    dispatched.
    """
    return [
        DispatchOutcome(
            work_item_id=item.id,
            status="dry-run",
            stage="loop-pick",
            pr_number=None,
            merge_sha=None,
            detail="planned selection; not dispatched",
        )
        for item in selected_candidates
    ]


def _dispatch_loop_wave(
    *,
    args: argparse.Namespace,
    repo: Path,
    items: list[WorkItem],
    selected_candidates: list[WorkItem],
    journal: JournalFile,
    janitor: tuple[str, ...] | None,
) -> list[DispatchOutcome]:
    return _admit_and_dispatch_loop_wave(
        args=args,
        repo=repo,
        items=items,
        selected_candidates=selected_candidates,
        journal=journal,
        janitor=janitor,
    )


def _admit_and_dispatch_loop_wave(
    *,
    args: argparse.Namespace,
    repo: Path,
    items: list[WorkItem],
    selected_candidates: list[WorkItem],
    journal: JournalFile,
    janitor: tuple[str, ...] | None,
) -> list[DispatchOutcome]:
    # The admission valve drains the candidate set up to the per-repo WIP cap:
    # host-only items are routed away, manual / unresolvable items are held +
    # surfaced, and the highest-rank admission-eligible items fill the free
    # slots (ready -> active, assignee set). Capacity-deferred items simply
    # wait for the next pass.
    admission = admit_and_select(
        repo=repo,
        items=items,
        candidates=selected_candidates,
        journal=journal,
        enforce_cap=True,
    )
    journal.append(
        record={
            "stage": "loop-pick",
            "dry_run": False,
            "budget": args.budget,
            "picked": [item.id for item in admission.admitted],
        }
    )
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        futures = [
            pool.submit(
                dispatch_one,
                args=args_with_dispatch_factory_target(args=args, repo=repo, work_item_id=item.id),
                repo=repo,
                item=item,
                journal=journal,
                janitor=janitor,
            )
            for item in admission.admitted
        ]
        dispatched = [future.result() for future in futures]
    # Held / host-only-refused items ride in the outcomes so the verdict and
    # post-verdict alarm see them; capacity-deferred items ride along too, but
    # verdict/alarm classification treats them as non-defects.
    return admission.refused + admission.deferred + dispatched


def _start_loop(*, args: argparse.Namespace, repo: Path) -> _LoopStart | int:
    janitor, preamble_exit = dispatch_preamble(args=args, repo=repo)
    if preamble_exit is not None:
        return preamble_exit
    arm_otel_egress(args=args, repo=repo)
    prepared = prepare(args=args, repo=repo)
    if prepared is None:
        return EXIT_PRECONDITION_ERROR
    items, journal = prepared
    if not args.skip_ledger_check and ledger_blocked_after_normalization(
        items=items,
        config=store_config(repo=repo),
        journal=journal,
    ):
        return EXIT_FAILURE
    requested_ids = set(args.items or [])
    if requested_ids:
        preflight_error = requested_items_preflight_error(
            requested_ids=requested_ids, items=items, repo=repo
        )
        if preflight_error is not None:
            _ = write_stderr(text=preflight_error)
            return EXIT_PRECONDITION_ERROR
    return _LoopStart(janitor=janitor, items=items, journal=journal)
