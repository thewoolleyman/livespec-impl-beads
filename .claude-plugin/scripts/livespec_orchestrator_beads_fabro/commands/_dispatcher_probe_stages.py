"""The loop probe's ordered stage assertions.

The loop-probe clause of `SPECIFICATION/contracts.md` fixes both WHAT the probe
asserts and the ORDER it asserts it in, and the order carries meaning the
individual assertions do not. Effective criteria are asserted BEFORE dispatch,
because an item whose criteria cannot be graded produces an acceptance verdict
that means nothing, and discovering that after a factory run has burned is
discovering it too late to act on.

The step-outcome assertion is the strict one, deliberately. The ordinary
dispatch path tolerates a warn-and-proceed record: a degraded step is loud but
not fatal, because refusing every degraded dispatch would stop the loop on
environmental noise. A PROBE has the opposite job -- it exists to report whether
the loop is healthy -- so anything other than a clean pass is a probe failure.
A probe that reported green through a warn-and-proceed would be certifying the
degradation it was run to find.

`verdict_stage_failure` refuses on ABSENT evidence as well as on a failing one.
An acceptance verdict reached without observing the evidence it grades is not a
weaker pass; it is a different claim entirely, and the probe's whole value is
that its green means the machinery was watched rather than assumed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.commands._dispatcher_effective_criteria import (
    effective_criteria,
)

if TYPE_CHECKING:
    from livespec_runtime.work_items.types import WorkItem

__all__: list[str] = [
    "CONFINEMENT_STAGE",
    "CRITERIA_STAGE",
    "MERGE_STAGE",
    "PASSED_STATUS",
    "PASSED_VERDICT",
    "PUBLISH_STAGE",
    "RESIDUE_STAGE",
    "STEP_OUTCOME_STAGE",
    "VERDICT_STAGE",
    "criteria_stage_failure",
    "step_outcome_stage_failure",
    "verdict_stage_failure",
]

CRITERIA_STAGE = "effective-criteria"
PUBLISH_STAGE = "publish"
CONFINEMENT_STAGE = "confinement"
MERGE_STAGE = "merge"
STEP_OUTCOME_STAGE = "step-outcomes"
VERDICT_STAGE = "acceptance-verdict"
RESIDUE_STAGE = "residue"

# The one journaled step-outcome status a probe cycle may carry. The dispatch
# path's own vocabulary spells a clean step `passed`; every other value it can
# write -- `failed`, a warn-and-proceed, a skipped step -- fails the probe.
PASSED_STATUS = "passed"
PASSED_VERDICT = "PASS"


def criteria_stage_failure(*, item: WorkItem) -> str | None:
    """Refuse a designated item whose effective criteria parse to nothing gradeable."""
    resolved = effective_criteria(item=item)
    if resolved.gradeable:
        return None
    return (
        f"the designated item {item.id} has no gradeable effective acceptance"
        f" criteria before dispatch ({resolved.parse_display()})"
    )


def step_outcome_stage_failure(*, outcomes: Sequence[Mapping[str, object]]) -> str | None:
    """Fail on any journaled step outcome in the probe cycle that is not a clean pass."""
    degraded = [
        f"{outcome.get('step', '<unnamed step>')}={outcome.get('status', '<no status>')}"
        for outcome in outcomes
        if outcome.get("status") != PASSED_STATUS
    ]
    if not degraded:
        return None
    return (
        "the probe cycle journaled a step outcome that is not a clean pass:"
        f" {', '.join(degraded)}"
    )


def verdict_stage_failure(*, verdict: str, absent_evidence: Sequence[str]) -> str | None:
    """Fail unless the acceptance verdict passed AND was grounded in observed evidence."""
    if absent_evidence:
        return (
            f"the acceptance verdict {verdict} was not grounded in observed"
            f" evidence; unobserved: {', '.join(absent_evidence)}"
        )
    if verdict != PASSED_VERDICT:
        return f"the acceptance verdict is {verdict}, not {PASSED_VERDICT}"
    return None
