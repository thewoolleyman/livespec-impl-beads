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

from livespec_orchestrator_beads_fabro.commands._dispatcher_step_ids import JANITOR_BOOTSTRAP
from livespec_orchestrator_beads_fabro.commands._dispatcher_step_janitor_bootstrap import (
    INTEGRATION_POINT,
    REMEDY,
)

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
    from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import PrView

__all__: list[str] = ["DegradedStep", "merged_degraded_outcome"]


@dataclass(frozen=True, kw_only=True)
class DegradedStep:
    """The provisioning step that failed: its prose, its cause, and its identity.

    `step_id` is None for every provisioning stage that is NOT a member of the
    closed step vocabulary -- a host-environment failure with no integration
    point an adopter could provide, and therefore nothing a later dispatch could
    re-verify or an adopter could clear.
    """

    description: str
    reason: str
    step_id: str | None = None


def merged_degraded_outcome(
    *,
    outcome_type: type[DispatchOutcome],
    work_item_id: str,
    merged: PrView,
    step: DegradedStep,
    janitor_argv: tuple[str, ...] | None = None,
) -> DispatchOutcome:
    """A merged-but-janitor-did-not-run outcome; STRUCTURED when it names a step.

    The merge is confirmed on the remote either way, so this is a `green`
    outcome at a distinct stage rather than a work-item failure: the work
    landed, and what did not run is the host-side gate.
    """
    remediation = (
        (
            f" Remediate the host, then run `{' '.join(janitor_argv)}` in a clean "
            "checkout of merged master to close the gate by hand."
        )
        if janitor_argv is not None
        else ""
    )
    degraded_step = step.step_id == JANITOR_BOOTSTRAP
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
        missing_integration_point=INTEGRATION_POINT if degraded_step else None,
        remedy=REMEDY if degraded_step else None,
    )
