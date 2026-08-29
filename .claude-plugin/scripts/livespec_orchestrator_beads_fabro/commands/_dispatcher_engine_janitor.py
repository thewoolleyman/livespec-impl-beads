"""Post-merge janitor flow for the Dispatcher engine."""

from __future__ import annotations

from contextlib import ExitStack
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_journal import (
    run_stage,
    tail,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_bootstrap_recipe import (
    JanitorBootstrapRecipe,
    resolve_janitor_bootstrap_recipe,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_degraded import (
    DegradedStep,
    merged_degraded_outcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_lock import (
    claim_janitor_lock,
    janitor_lock_path,
    release_janitor_lock,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    CORE_PLUGIN_ROOT_ENV_VAR,
    DispatchPlan,
    PrView,
    janitor_bootstrap_argv,
    janitor_core_clone_argv,
    janitor_trust_argv,
    janitor_worktree_add_argv,
    janitor_worktree_remove_argv,
    pull_primary_argv,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_step_ids import JANITOR_BOOTSTRAP

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
        CommandResult,
        CommandRunner,
        DispatchOutcome,
        JournalWriter,
    )

__all__: list[str] = ["post_merge"]

_GIT_TIMEOUT_SECONDS = 600.0
_JANITOR_TIMEOUT_SECONDS = 3600.0


def post_merge(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
    merged: PrView,
) -> DispatchOutcome:
    # Resolved ONCE for the whole post-merge flow: the recipe the janitor
    # invokes and the recipe a degradation names have to be the same recipe,
    # and a second resolution is how they come to disagree.
    recipe = resolve_janitor_bootstrap_recipe(cwd=plan.repo)
    lock_path = janitor_lock_path(plan=plan)
    lock_detail = claim_janitor_lock(path=lock_path, owner=plan.work_item_id)
    if lock_detail is not None:
        return merged_degraded_outcome(
            outcome_type=outcome_type,
            work_item_id=plan.work_item_id,
            merged=merged,
            step=DegradedStep(description="claiming the janitor checkout lock", reason=lock_detail),
            recipe=recipe,
        )
    with ExitStack() as stack:
        _ = stack.callback(release_janitor_lock, path=lock_path)
        return _post_merge_locked(
            outcome_type=outcome_type,
            plan=plan,
            runner=runner,
            journal=journal,
            merged=merged,
            recipe=recipe,
        )


def _post_merge_locked(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
    merged: PrView,
    recipe: JanitorBootstrapRecipe,
) -> DispatchOutcome:
    pull = run_stage(
        runner=runner,
        journal=journal,
        plan=plan,
        stage="pull-primary",
        command=(pull_primary_argv(plan=plan), plan.repo, _GIT_TIMEOUT_SECONDS, None),
    )
    if pull.exit_code != 0:
        return _merged_degraded(
            outcome_type=outcome_type,
            plan=plan,
            merged=merged,
            step=_degraded_step(
                description=f"refreshing the primary checkout {plan.repo} via pull-primary",
                result=pull,
            ),
            recipe=recipe,
        )
    degraded = _provision_janitor_checkout(
        outcome_type=outcome_type,
        plan=plan,
        runner=runner,
        journal=journal,
        merged=merged,
        recipe=recipe,
    )
    if degraded is not None:
        return degraded
    janitor = run_stage(
        runner=runner,
        journal=journal,
        plan=plan,
        stage="janitor-post-merge",
        command=(
            list(plan.janitor),
            plan.janitor_checkout,
            _JANITOR_TIMEOUT_SECONDS,
            {CORE_PLUGIN_ROOT_ENV_VAR: str(plan.janitor_core_checkout / ".claude-plugin")},
        ),
    )
    if janitor.exit_code != 0:
        return outcome_type(
            work_item_id=plan.work_item_id,
            status="failed",
            stage="janitor-post-merge",
            pr_number=merged.number,
            merge_sha=merged.merge_sha,
            detail=(
                f"post-merge janitor red in fresh checkout {plan.janitor_checkout} "
                f"(kept for diagnosis): {tail(text=janitor.stderr)}"
            ),
        )
    cleanup = run_stage(
        runner=runner,
        journal=journal,
        plan=plan,
        stage="janitor-checkout-remove",
        command=(janitor_worktree_remove_argv(plan=plan), plan.repo, _GIT_TIMEOUT_SECONDS, None),
    )
    if cleanup.exit_code != 0:
        return outcome_type(
            work_item_id=plan.work_item_id,
            status="failed",
            stage="janitor-checkout-remove",
            pr_number=merged.number,
            merge_sha=merged.merge_sha,
            detail=tail(text=cleanup.stderr),
        )
    return outcome_type(
        work_item_id=plan.work_item_id,
        status="green",
        stage="done",
        pr_number=merged.number,
        merge_sha=merged.merge_sha,
        detail="merged, post-merge janitor green",
    )


def _provision_janitor_checkout(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
    merged: PrView,
    recipe: JanitorBootstrapRecipe,
) -> DispatchOutcome | None:
    _ = run_stage(
        runner=runner,
        journal=journal,
        plan=plan,
        stage="janitor-checkout-preclean",
        command=(janitor_worktree_remove_argv(plan=plan), plan.repo, _GIT_TIMEOUT_SECONDS, None),
    )
    ref = merged.merge_sha if merged.merge_sha is not None else "origin/master"
    core_step = (
        f"provisioning livespec core at {plan.janitor_core_checkout} (ref {plan.janitor_core_ref})"
    )
    steps = (
        (
            "janitor-checkout-add",
            janitor_worktree_add_argv(plan=plan, ref=ref),
            plan.repo,
            f"provisioning the fresh janitor checkout at {plan.janitor_checkout} (ref {ref})",
            None,
        ),
        (
            "janitor-checkout-trust",
            janitor_trust_argv(),
            plan.janitor_checkout,
            f"`mise trust` inside the janitor checkout {plan.janitor_checkout}",
            None,
        ),
        (
            "janitor-checkout-bootstrap",
            janitor_bootstrap_argv(recipe=recipe),
            plan.repo,
            f"installing commit-refuse hooks via `{recipe.text}` in {plan.repo}",
            JANITOR_BOOTSTRAP,
        ),
        (
            "janitor-core-provision",
            janitor_core_clone_argv(plan=plan),
            plan.janitor_checkout,
            core_step,
            None,
        ),
    )
    for stage, argv, cwd, step, step_id in steps:
        result = run_stage(
            runner=runner,
            journal=journal,
            plan=plan,
            stage=stage,
            command=(argv, cwd, _GIT_TIMEOUT_SECONDS, None),
        )
        if result.exit_code != 0:
            return _merged_degraded(
                outcome_type=outcome_type,
                plan=plan,
                merged=merged,
                step=_degraded_step(description=step, result=result, step_id=step_id),
                recipe=recipe,
            )
    return None


def _degraded_step(
    *, description: str, result: CommandResult, step_id: str | None = None
) -> DegradedStep:
    """One failed provisioning stage, named and reasoned, ready to be shaped."""
    return DegradedStep(
        description=description, reason=tail(text=result.stderr, limit=500), step_id=step_id
    )


def _merged_degraded(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    merged: PrView,
    step: DegradedStep,
    recipe: JanitorBootstrapRecipe,
) -> DispatchOutcome:
    return merged_degraded_outcome(
        outcome_type=outcome_type,
        work_item_id=plan.work_item_id,
        merged=merged,
        step=step,
        recipe=recipe,
        janitor_argv=plan.janitor,
    )
