"""Fabro run terminal-state helpers for the dispatcher engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_journal import (
    journal_stage,
    tail,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_failure import (
    fabro_failure_outcome_detail,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan
from livespec_orchestrator_beads_fabro.commands._fabro_port import (
    FabroInspectResult,
    fabro_port_for_plan,
)

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
        CommandResult,
        CommandRunner,
        DispatchOutcome,
        JournalWriter,
    )

__all__: list[str] = [
    "fabro_run_terminal_outcome",
    "inspect_run",
]

_FABRO_INSPECT_TIMEOUT_SECONDS = 300.0


def inspect_run(
    *,
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
    run_id: str | None,
) -> FabroInspectResult | None:
    """Read and journal `fabro inspect --json` for a parsed run id."""
    if run_id is None:
        return None
    inspect = fabro_port_for_plan(plan=plan, runner=runner).inspect(
        run_id=run_id,
        timeout_seconds=_FABRO_INSPECT_TIMEOUT_SECONDS,
    )
    journal_stage(
        journal=journal,
        plan=plan,
        stage="fabro-inspect",
        result=cast("CommandResult", inspect.command),
    )
    return inspect


def fabro_run_terminal_outcome(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    run_id: str | None,
    inspect: FabroInspectResult | None,
    exit_code: int,
    stderr: str,
) -> DispatchOutcome | None:
    """Return blocked/failed Fabro-run outcome, or None for green routing."""
    blocked = _blocked_outcome(
        outcome_type=outcome_type,
        plan=plan,
        run_id=run_id,
        inspect=inspect,
    )
    if blocked is not None:
        return blocked
    if exit_code == 0:
        return None
    failure = None if inspect is None else inspect.failure
    return outcome_type(
        work_item_id=plan.work_item_id,
        status="failed",
        stage="fabro-run",
        pr_number=None,
        merge_sha=None,
        detail=fabro_failure_outcome_detail(failure=failure, fallback=tail(text=stderr)),
        fabro_run_id=run_id,
        fabro_failure_cause=None if failure is None else failure.cause,
        fabro_failure_category=None if failure is None else failure.category,
        fabro_failure_signature=None if failure is None else failure.signature,
    )


def _blocked_outcome(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    run_id: str | None,
    inspect: FabroInspectResult | None,
) -> DispatchOutcome | None:
    """Detect a run parked at the in-loop human gate (third terminal state).

    A foreground `fabro run` exits non-zero when it returns at a human
    gate, so the exit code alone cannot distinguish blocked from failed:
    the engine parses the run id from the CLI output and reads the
    authoritative status via `fabro inspect --json`. Anything other
    than a confirmed blocked status falls back to exit-code routing.
    """
    if run_id is None or inspect is None:
        return None
    if inspect.command.exit_code != 0:
        return None
    if inspect.status_kind not in {"blocked", "human_input_required"}:
        return None
    failure = inspect.failure
    return outcome_type(
        work_item_id=plan.work_item_id,
        status="blocked",
        stage="fabro-run",
        pr_number=None,
        merge_sha=None,
        detail=(
            f"run {run_id} parked at the in-loop human gate (needs-human); "
            f"answer with `fabro attach {run_id}` while the engine lives, "
            f"`fabro resume {run_id}` only if the engine died; "
            "not auto-resumed, item left open"
        ),
        fabro_run_id=run_id,
        fabro_failure_cause=None if failure is None else failure.cause,
        fabro_failure_category=None if failure is None else failure.category,
        fabro_failure_signature=None if failure is None else failure.signature,
    )
