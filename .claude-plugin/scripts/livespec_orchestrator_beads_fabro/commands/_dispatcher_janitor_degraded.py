"""How a post-merge janitor degradation READS: its operator prose and its step id.

Split out of `_dispatcher_engine_janitor` along the cohesion seam between
DRIVING the post-merge flow -- the lock, the checkout provisioning, the janitor
run, which stay there -- and SHAPING the one outcome that flow can report when a
provisioning step fails, which is all this module does.

THE SPLIT IS WHAT KEEPS THE CLOSED VOCABULARY CLOSED. Only ONE provisioning
stage is a step of the ratified set, and only it carries the structured identity
that makes its degradation persist into the next dispatch's refusal. Deciding
that here, in one place with the reason written down, is what stops the other
provisioning stages from drifting into a set that is extensible only by
ratification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_journal import tail
from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_bootstrap_recipe import (
    integration_point,
    remedy,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_step_ids import JANITOR_BOOTSTRAP

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
        CommandResult,
        DispatchOutcome,
    )
    from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_bootstrap_recipe import (
        JanitorBootstrapRecipe,
    )
    from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan, PrView

__all__: list[str] = [
    "DegradedStep",
    "degraded_step",
    "merged_degraded_for_plan",
    "merged_degraded_outcome",
]


@dataclass(frozen=True, kw_only=True)
class DegradedStep:
    """The provisioning step that failed: its prose, its cause, and its identity.

    `step_id` is None for every provisioning stage that is NOT a member of the
    closed step vocabulary -- a host-environment failure with no integration
    point an adopter could provide, and therefore nothing a later dispatch could
    re-verify or an adopter could clear.

    `missing_point` and `remedy_text` are how a degradation OUTSIDE that closed
    vocabulary still says what is missing and how to clear it. The janitor VENUE
    is the case that needs them: the ratified venue clause requires a degraded
    outcome carrying the missing point and the remedy, and states in the same
    breath that the venue is not a new step of the closed set. Both halves hold
    only if the two facts can travel without a step id -- carried here, they do,
    and the persistence gate still ignores the outcome because its `step` is
    None.
    """

    description: str
    reason: str
    step_id: str | None = None
    missing_point: str | None = None
    remedy_text: str | None = None


def degraded_step(
    *, description: str, result: CommandResult, step_id: str | None = None
) -> DegradedStep:
    """One failed provisioning stage, named and reasoned, ready to be shaped."""
    return DegradedStep(
        description=description, reason=tail(text=result.stderr, limit=500), step_id=step_id
    )


def merged_degraded_for_plan(
    *,
    outcome_type: type[DispatchOutcome],
    plan: DispatchPlan,
    merged: PrView,
    step: DegradedStep,
    recipe: JanitorBootstrapRecipe,
) -> DispatchOutcome:
    """The same outcome for a degradation the DISPATCH PLAN can speak for.

    Every post-merge degradation past the lock claim knows its plan, and the
    plan supplies the two things the outcome cannot invent: whose work-item
    this is, and the janitor argv the operator would run by hand. Reading both
    off the plan HERE, beside the shaping they feed, is what stops a caller
    from remediating with a janitor command this dispatch never planned.
    """
    return merged_degraded_outcome(
        outcome_type=outcome_type,
        work_item_id=plan.work_item_id,
        merged=merged,
        step=step,
        recipe=recipe,
        janitor_argv=plan.janitor,
    )


def merged_degraded_outcome(
    *,
    outcome_type: type[DispatchOutcome],
    work_item_id: str,
    merged: PrView,
    step: DegradedStep,
    recipe: JanitorBootstrapRecipe,
    janitor_argv: tuple[str, ...] | None = None,
) -> DispatchOutcome:
    """A merged-but-janitor-did-not-run outcome; STRUCTURED when it names a step.

    The merge is confirmed on the remote either way, so this is a `green`
    outcome at a distinct stage rather than a work-item failure: the work
    landed, and what did not run is the host-side gate.

    `recipe` is the RESOLVED hook-install recipe of this dispatch, required on
    every arm rather than only the janitor-bootstrap one so the integration
    point a degradation names can never be a different recipe from the one the
    janitor actually tried to run.
    """
    remediation = (
        (
            f" Remediate the host, then run `{' '.join(janitor_argv)}` in a clean "
            "checkout of merged master to close the gate by hand."
        )
        if janitor_argv is not None
        else ""
    )
    bootstrap_step = step.step_id == JANITOR_BOOTSTRAP
    return outcome_type(
        work_item_id=work_item_id,
        status="green",
        stage="janitor-env-degraded",
        pr_number=merged.number,
        merge_sha=merged.merge_sha,
        detail=(
            f"merged, but the post-merge janitor DID NOT RUN: {step.description} failed "
            f"({step.reason}). This is a host-environment problem, not a work-item "
            f"failure — the merge is confirmed on the remote.{remediation}"
        ),
        step=step.step_id,
        missing_integration_point=(
            integration_point(recipe=recipe) if bootstrap_step else step.missing_point
        ),
        remedy=remedy(recipe=recipe) if bootstrap_step else step.remedy_text,
    )
