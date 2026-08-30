"""Provisioning the post-merge janitor's venue: the checkout, and what it needs.

Split out of `_dispatcher_engine_janitor` along the cohesion seam between
DRIVING the post-merge flow -- the lock, the primary pull, the janitor run and
its cleanup, which stay there -- and PROVISIONING the venue that flow runs in,
which is all this module does: the pre-clean, the fresh detached worktree, its
mise trust, the governed repository's commit-refuse-hook bootstrap, and the
livespec-core clone.

WHY THE RESOLUTIONS ARE READ BEFORE ANYTHING IS PROVISIONED. Two of the five
stages run a command that is only resolvable from a DECLARATION the governed
repository makes -- the hook-install recipe under `dispatcher.janitor_bootstrap`,
and the livespec-core ref and repository under `compat.pinned` / `compat.core_repo`
-- and an unresolved declaration is never completed from a default that would
run something the repository never named (`SPECIFICATION/contracts.md`, the
janitor-bootstrap recipe and janitor-core provisioning resolution clauses). The
merge has already landed by the time this runs, so each unresolved declaration
becomes the named degraded outcome the design has for it, before a venue is
provisioned for work that cannot run in it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_journal import run_stage
from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_degraded import (
    DegradedStep,
    merged_degraded_for_plan,
    step_from_result,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    UNRESOLVED_JANITOR_CORE_REF_DEFECT,
    UNUSABLE_JANITOR_CORE_REPO_DEFECT,
    janitor_bootstrap_argv,
    janitor_core_clone_argv,
    janitor_trust_argv,
    janitor_worktree_add_argv,
    janitor_worktree_remove_argv,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_step_ids import JANITOR_BOOTSTRAP

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
        CommandRunner,
        DispatchOutcome,
        JournalWriter,
    )
    from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_bootstrap_recipe import (
        JanitorBootstrapRecipe,
    )
    from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan, PrView

__all__: list[str] = ["provision_janitor_checkout"]

_GIT_TIMEOUT_SECONDS = 600.0


def provision_janitor_checkout(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
    merged: PrView,
    recipe: JanitorBootstrapRecipe,
) -> DispatchOutcome | None:
    """Provision the janitor's venue; a degraded outcome when a stage cannot run."""
    if recipe.defect is not None:
        # A present-but-unusable declaration resolves NO command, so the
        # bootstrap stage would hand the runner an empty argv -- a crash, after
        # the merge has already landed, where the design has a named degraded
        # outcome. The pre-dispatch re-verification refuses on the same defect,
        # but only once a degradation stands: on a FIRST dispatch this is the
        # one place the defect is caught, so it is caught before anything is
        # provisioned for a bootstrap that cannot run.
        return merged_degraded_for_plan(
            outcome_type=outcome_type,
            plan=plan,
            merged=merged,
            step=DegradedStep(
                description=(
                    f"resolving the commit-refuse-hook install recipe to bootstrap in {plan.repo}"
                ),
                reason=recipe.defect,
                step_id=JANITOR_BOOTSTRAP,
            ),
            recipe=recipe,
        )
    core_step = (
        f"provisioning livespec core at {plan.janitor_core_checkout} (ref {plan.janitor_core_ref})"
    )
    core_ref = plan.janitor_core_ref
    core_repo_url = plan.janitor_core_repo_url
    if core_ref is None or core_repo_url is None:
        # The same reasoning one declaration over. A missing `compat.pinned`
        # would otherwise clone a moving master/main tip that can move under an
        # in-flight dispatch, and an unusable `compat.core_repo` would clone the
        # fleet repository an adopter has already said is not its core -- both
        # silently, where the design has a named degraded outcome.
        return merged_degraded_for_plan(
            outcome_type=outcome_type,
            plan=plan,
            merged=merged,
            step=DegradedStep(
                description=core_step,
                reason=(
                    UNRESOLVED_JANITOR_CORE_REF_DEFECT
                    if core_ref is None
                    else UNUSABLE_JANITOR_CORE_REPO_DEFECT
                ),
            ),
            recipe=recipe,
        )
    _ = run_stage(
        runner=runner,
        journal=journal,
        plan=plan,
        stage="janitor-checkout-preclean",
        command=(janitor_worktree_remove_argv(plan=plan), plan.repo, _GIT_TIMEOUT_SECONDS, None),
    )
    ref = merged.merge_sha if merged.merge_sha is not None else "origin/master"
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
            janitor_core_clone_argv(plan=plan, ref=core_ref, repo_url=core_repo_url),
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
            return merged_degraded_for_plan(
                outcome_type=outcome_type,
                plan=plan,
                merged=merged,
                step=step_from_result(description=step, result=result, step_id=step_id),
                recipe=recipe,
            )
    return None
