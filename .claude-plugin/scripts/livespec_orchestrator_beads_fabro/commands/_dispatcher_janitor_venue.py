"""WHERE the post-merge and reconcile janitor provisions its fresh checkout.

Split out of `_dispatcher_engine_janitor` along the seam between DRIVING the
post-merge flow -- the lock, the primary refresh, the janitor run, the cleanup,
all of which stay there -- and PROVISIONING the venue that flow runs in: which
ref the fresh checkout is made at, and the stages that create it.

THE VENUE IS THE MERGED DEFAULT-BRANCH TIP, NEVER THE ITEM'S HISTORICAL MERGE
SHA. Pinning the venue to the merge sha makes a janitor-environment fix that
lands AFTER an item's merge unable to EVER clear that item: every reconcile
re-provisions a checkout from before the fix existed and fails identically, a
deterministic deadlock whose only in-band exit is a one-off `--janitor`
override. Measured on the `homelab` adopter 2026-08-29: `hl-cid234` merged as
`16fe3ac`, the recipe that would have let its janitor pass landed one commit
later as `918c6cf`, and two reconcile attempts -- the second AFTER pull-primary
had already fast-forwarded the primary checkout past the fix -- both
provisioned at `16fe3ac` and failed on a recipe that cannot exist at that sha.

PROVISIONING AT THE TIP KEEPS THE GUARANTEE THE SHA PIN WAS BOUGHT WITH, BUT
ONLY ONCE IT IS CONFIRMED. The tip proves the item's merge is present because
the tip CONTAINS it -- which is a property to be CHECKED, not assumed. A
resolved tip that does not contain the item's merge is a DEGRADED post-merge
outcome carrying the missing point and the remedy, never a silent proceed
against a venue that cannot prove the work landed.

The branch itself is resolved through the ratified default-branch-resolution
helper that `SPECIFICATION/contracts.md` requires of every dispatch-path stage
naming the target's primary branch, so an adopter whose primary branch is `main`
gets its own tip rather than the `master` literal this fleet happens to use. A
branch nobody could name is not a venue either: when both resolution routes are
silent the venue degrades rather than guessing at a ref.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_journal import run_stage
from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_degraded import (
    DegradedStep,
    degraded_step,
    merged_degraded_for_plan,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_master_ci_lookups import (
    resolve_default_branch,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    janitor_bootstrap_argv,
    janitor_core_clone_argv,
    janitor_trust_argv,
    janitor_venue_contains_merge_argv,
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

__all__: list[str] = [
    "UNRESOLVED_VENUE",
    "JanitorVenue",
    "provision_janitor_checkout",
    "resolve_janitor_venue",
]

_GIT_TIMEOUT_SECONDS = 600.0
_VENUE_TIMEOUT_SECONDS = 30.0

# What a venue that could not be resolved renders as. A sentinel rather than a
# branch literal, for the reason the whole module exists: the wrong answer here
# is a ref we guessed at, and prose naming `origin/master` would tell an adopter
# on `main` that we looked for a branch they do not have.
UNRESOLVED_VENUE = "<unresolved>"

_UNRESOLVED_BRANCH_REMEDY = (
    "give the target repository a resolvable default branch on this host -- "
    "`git remote set-head origin --auto` in the primary checkout sets "
    "`refs/remotes/origin/HEAD`, or a working `gh` credential lets "
    "`gh repo view --json defaultBranchRef` answer -- so the janitor venue can be "
    "provisioned at a named default-branch tip"
)


@dataclass(frozen=True, kw_only=True)
class JanitorVenue:
    """The ref the janitor provisions at, or the degradation that stands in for it.

    `ref` is `UNRESOLVED_VENUE` on every arm carrying a `defect`, so a caller
    that ignores the defect provisions at a sentinel that cannot resolve rather
    than at a plausible-looking ref -- except on the tip-lacks-the-merge arm,
    which carries the resolved tip precisely because naming it is what makes the
    degradation actionable.
    """

    ref: str
    defect: DegradedStep | None = None


def resolve_janitor_venue(
    *, plan: DispatchPlan, runner: CommandRunner, merge_sha: str | None
) -> JanitorVenue:
    """The default-branch tip containing `merge_sha`, or the degradation replacing it.

    A `merge_sha` of None is not a degradation: the caller has no merge to
    confirm, so the tip is the venue with nothing left to prove about it.
    """
    branch = resolve_default_branch(repo=plan.repo, runner=runner)
    if branch is None:
        return JanitorVenue(ref=UNRESOLVED_VENUE, defect=_unresolved_branch_step(plan=plan))
    tip = f"origin/{branch}"
    if merge_sha is None:
        return JanitorVenue(ref=tip)
    contains = runner.run(
        argv=janitor_venue_contains_merge_argv(plan=plan, tip=tip, merge_sha=merge_sha),
        cwd=plan.repo,
        timeout_seconds=_VENUE_TIMEOUT_SECONDS,
    )
    if contains.exit_code != 0:
        return JanitorVenue(ref=tip, defect=_tip_without_merge_step(tip=tip, merge_sha=merge_sha))
    return JanitorVenue(ref=tip)


def provision_janitor_checkout(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    runner: CommandRunner,
    journal: JournalWriter,
    merged: PrView,
    recipe: JanitorBootstrapRecipe,
) -> DispatchOutcome | None:
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
    # Resolved BEFORE the preclean, on the same principle as the recipe defect
    # above: a venue that cannot be named, or that cannot be shown to carry the
    # item's merge, degrades with nothing provisioned for it.
    venue = resolve_janitor_venue(plan=plan, runner=runner, merge_sha=merged.merge_sha)
    if venue.defect is not None:
        return merged_degraded_for_plan(
            outcome_type=outcome_type,
            plan=plan,
            merged=merged,
            step=venue.defect,
            recipe=recipe,
        )
    _ = run_stage(
        runner=runner,
        journal=journal,
        plan=plan,
        stage="janitor-checkout-preclean",
        command=(janitor_worktree_remove_argv(plan=plan), plan.repo, _GIT_TIMEOUT_SECONDS, None),
    )
    core_step = (
        f"provisioning livespec core at {plan.janitor_core_checkout} (ref {plan.janitor_core_ref})"
    )
    steps = (
        (
            "janitor-checkout-add",
            janitor_worktree_add_argv(plan=plan, tip=venue.ref),
            plan.repo,
            (
                f"provisioning the fresh janitor checkout at {plan.janitor_checkout} "
                f"(merged default-branch tip {venue.ref})"
            ),
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
            return merged_degraded_for_plan(
                outcome_type=outcome_type,
                plan=plan,
                merged=merged,
                step=degraded_step(description=step, result=result, step_id=step_id),
                recipe=recipe,
            )
    return None


def _unresolved_branch_step(*, plan: DispatchPlan) -> DegradedStep:
    """No default branch could be named, so there is no tip to provision at."""
    return DegradedStep(
        description=(
            f"resolving the default-branch tip to provision the janitor venue in {plan.repo}"
        ),
        reason=(
            "neither `git symbolic-ref refs/remotes/origin/HEAD` nor `gh repo view --json "
            "defaultBranchRef` named a default branch, so the venue has no tip to be provisioned "
            "at and the merge-presence of any tip cannot be confirmed"
        ),
        missing_point="a resolvable default branch for the target repository",
        remedy_text=_UNRESOLVED_BRANCH_REMEDY,
    )


def _tip_without_merge_step(*, tip: str, merge_sha: str) -> DegradedStep:
    """The tip resolved, but it does not carry the item's merge -- so it is not the venue."""
    return DegradedStep(
        description=(
            f"confirming the resolved default-branch tip {tip} contains the item's merge "
            f"{merge_sha}"
        ),
        reason=(
            f"`git merge-base --is-ancestor {merge_sha} {tip}` reports the tip does NOT contain "
            "the merge, so a janitor run there would prove nothing about this item's work"
        ),
        missing_point=f"a {tip} tip containing the item's merge {merge_sha}",
        remedy_text=(
            f"refresh the target repository so its {tip} carries {merge_sha} and re-run the "
            "reconcile; if the merge is genuinely absent from the default branch then it did not "
            "land where this dispatch believes it did, and the item's disposition is what needs "
            "correcting"
        ),
    )
