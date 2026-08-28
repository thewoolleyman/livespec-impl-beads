"""The CLOSED step-id vocabulary of the dispatch preflight / post-merge discipline.

Three steps, each carrying a stable identifier that every one of its outcome
records names: the two pre-dispatch preflights (`source-checkout`, `master-ci`)
and the post-merge janitor's bootstrap of the governed repository's
commit-refuse hooks (`janitor-bootstrap`). The set is extensible only by
ratification, so it lives in one module rather than as a literal at each of its
half-dozen use sites: a fourth identifier invented at a call site would be
indistinguishable, in the journal, from a ratified one.

WHY THE IDENTIFIER IS LOAD-BEARING RATHER THAN DECORATIVE. A degraded
post-merge outcome has to persist into a refusal of the NEXT dispatch, and that
refusal has to name a pre-dispatch RE-VERIFICATION for the very integration
point the degradation named. Both halves are addressed BY THE IDENTIFIER: free
prose describing what failed cannot be matched against a waiver entry, and
cannot be matched against the verification that clears it. Give the step a name
and the persistence becomes mechanical; leave it as prose and it cannot be
written at all.

Gauge and observability postures ratified elsewhere -- the fail-closed cost
gate's hand-picked warn posture, any storage-headroom gauge posture -- are NOT
steps of this vocabulary and must never be added to it.
"""

from __future__ import annotations

__all__: list[str] = [
    "JANITOR_BOOTSTRAP",
    "MASTER_CI",
    "SOURCE_CHECKOUT",
    "STEP_IDS",
]

SOURCE_CHECKOUT = "source-checkout"
MASTER_CI = "master-ci"
JANITOR_BOOTSTRAP = "janitor-bootstrap"

# A tuple rather than a set so the closed vocabulary has a stable ORDER when it
# is rendered into operator-facing text; membership tests read the same either
# way, and a three-element scan is not the cost worth optimising here.
STEP_IDS: tuple[str, ...] = (SOURCE_CHECKOUT, MASTER_CI, JANITOR_BOOTSTRAP)
