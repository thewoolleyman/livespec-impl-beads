"""Merge and post-merge janitor flow for the Dispatcher engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_janitor import post_merge
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_journal import journal_stage
from livespec_orchestrator_beads_fabro.commands._dispatcher_merge_pr_association import (
    pr_view_for_merge_sha,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    DispatchPlan,
    PrView,
    parse_pr_view,
    pr_arm_argv,
    pr_update_branch_argv,
    pr_view_argv,
)

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
        CommandRunner,
        DispatchOutcome,
        JournalWriter,
        PollPolicy,
        SleepFn,
    )

__all__: list[str] = ["await_merge", "confirm_pr", "outcome_after_await"]

_GH_TIMEOUT_SECONDS = 300.0


def confirm_pr(
    *,
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
) -> PrView | None:
    view = _view_pr(plan=plan, runner=runner, journal=journal)
    if view is None:
        return None
    if view.auto_merge_armed or view.state == "MERGED":
        return view
    argv = pr_arm_argv(plan=plan, number=view.number)
    # An EMPTY argv is the merge hold saying there is no forge write to make.
    # This is the fallback-arming path, which exists precisely for a pr stage
    # that could not arm -- so running it for a held item would take the one
    # branch that silently undoes a pr stage which correctly armed nothing.
    if not argv:
        return view
    arm = runner.run(
        argv=argv,
        cwd=plan.repo,
        timeout_seconds=_GH_TIMEOUT_SECONDS,
    )
    journal_stage(journal=journal, plan=plan, stage="pr-arm-fallback", result=arm)
    return _view_pr(plan=plan, runner=runner, journal=journal)


def await_merge(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
    sleep: SleepFn,
    poll: PollPolicy,
) -> PrView | DispatchOutcome | None:
    for attempt in range(poll.attempts):
        view = _view_pr(plan=plan, runner=runner, journal=journal)
        if view is not None and view.state == "MERGED":
            return view
        if view is not None and view.merge_state_status == "BEHIND":
            update = runner.run(
                argv=pr_update_branch_argv(plan=plan, number=view.number),
                cwd=plan.repo,
                timeout_seconds=_GH_TIMEOUT_SECONDS,
            )
            journal_stage(journal=journal, plan=plan, stage="pr-update-branch", result=update)
        elif view is not None and view.terminal_required_check_failures:
            checks = ", ".join(view.terminal_required_check_failures)
            return outcome_type(
                work_item_id=plan.work_item_id,
                status="failed",
                stage="merge-poll",
                pr_number=view.number,
                merge_sha=view.merge_sha,
                detail=f"required check failed terminally: {checks}",
            )
        if attempt + 1 < poll.attempts:
            sleep(poll.interval_seconds)
    return None


def outcome_after_await(  # noqa: PLR0913 — kw-only disposition; each field is an independent caller input.
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
    merged: PrView | DispatchOutcome | None,
    pr_number: int,
    run_id: str | None,
) -> DispatchOutcome:
    """One terminal outcome from `await_merge`'s three-way answer.

    The poll reports a MERGED view, a terminal failure it already decided (a
    required check that failed for good), or an exhausted budget, and each is a
    different outcome. It lives beside the poll rather than inside `run_dispatch`
    so that function stays one readable list of stages rather than a stage list
    with a disposition tree hanging off its end.
    """
    # Discriminated on `PrView` rather than on `outcome_type`, which is a
    # runtime PARAMETER and so narrows nothing for the reader or the checker.
    if isinstance(merged, PrView):
        return post_merge(
            outcome_type=outcome_type,
            plan=plan,
            runner=runner,
            journal=journal,
            merged=pr_view_for_merge_sha(
                repo=plan.repo,
                work_item_id=plan.work_item_id,
                merged=merged,
                runner=runner,
                journal=journal,
            ),
        )
    if merged is None:
        return outcome_type(
            work_item_id=plan.work_item_id,
            status="failed",
            stage="merge-poll",
            pr_number=pr_number,
            merge_sha=None,
            detail="PR did not reach MERGED within the poll budget",
            fabro_run_id=run_id,
        )
    return merged


def _view_pr(
    *,
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
) -> PrView | None:
    result = runner.run(
        argv=pr_view_argv(plan=plan),
        cwd=plan.repo,
        timeout_seconds=_GH_TIMEOUT_SECONDS,
    )
    journal_stage(journal=journal, plan=plan, stage="pr-view", result=result)
    if result.exit_code != 0:
        return None
    return parse_pr_view(stdout=result.stdout)
