"""The vacuous-match outcome of a FILE-SCOPED check, and how a gate counts it.

A file-scoped check -- a janitor or otherwise scoped check that SELECTS the
diff files it inspects -- reports one of three outcomes. Two are the familiar
ones. The third is why this module exists: when the check's scope matched ZERO
files in the diff under judgment, the check OBSERVED NOTHING, so it has
produced no evidence and MUST NOT report a pass. It reports a distinct
`vacuous-match` outcome instead. Ratified in v091
(`SPECIFICATION/contracts.md`, the scoped-check vacuity clause of the dispatch
preflight and post-merge step discipline).

WHY THIS IS NOT PEDANTRY. homelab PR #1044 merged with ZERO files changed
under a title claiming its work item was delivered, and the scoped
`check-no-workflow-edits` passed over that empty diff all four review rounds.
A file-scoped check over an empty diff matches zero files BY CONSTRUCTION, and
zero matches rendered as green. Reading zero matches as a pass is a verdict
manufactured from absent evidence -- the class the acceptance evidence rule
was ratified against, arriving here one gate earlier.

WHY VACUITY IS NOT FAILURE EITHER. "Observed nothing" is not "observed
something bad". A vacuous-match outcome composes as absent evidence, so
`gate_tally` counts it toward NEITHER passing NOR failing: it is reported and
visible, and it moves no verdict on its own. That is the whole asymmetry --
inverting the old bug into a refusal would be just as wrong, because a
prohibition check that matched nothing has said nothing.

WHAT AN EXIT CODE CAN AND CANNOT CARRY. A shell gate's exit code is a
two-valued "did anything FAIL" channel; it cannot encode three outcomes. So a
vacuous-match check still exits 0 via `gate_exit_code`, and that IS the honest
reading: 0 here asserts only that nothing failed, never that anything passed.
The passing/failing tally the contract's "MUST NOT count toward passing" rule
governs is `GateTally` -- the surface a gate consults when it needs to know how
much was actually observed, which an exit code structurally cannot tell it.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

__all__: list[str] = [
    "VACUOUS_MATCH",
    "GateTally",
    "ScopedCheckOutcome",
    "gate_exit_code",
    "gate_tally",
    "scoped_check_outcome",
]

# The three outcomes a file-scoped check can report. `pass` and `fail` are
# evidence; `vacuous-match` is the absence of any.
ScopedCheckOutcome = Literal["pass", "fail", "vacuous-match"]

VACUOUS_MATCH: ScopedCheckOutcome = "vacuous-match"

_EXIT_FAILING = 1
_EXIT_NOT_FAILING = 0


@dataclass(frozen=True, kw_only=True, slots=True)
class GateTally:
    """What a gate counted across the scoped-check outcomes it read.

    `vacuous` is deliberately its OWN counter rather than being folded into
    either side: a gate that needs to know whether its greenness rests on
    anything can only ask that question if vacuity was counted separately.
    """

    passing: int
    failing: int
    vacuous: int


def scoped_check_outcome(*, matched_file_count: int, failing: bool) -> ScopedCheckOutcome:
    """The outcome of a file-scoped check that matched `matched_file_count` files.

    A zero match short-circuits BEFORE `failing` is consulted, and that
    ordering is the contract: with nothing observed there is no verdict to
    report, so whichever way the check's own judgment would have leaned is
    moot. One or more matched files yields the check's normal pass or fail.
    """
    if matched_file_count == 0:
        return VACUOUS_MATCH
    return "fail" if failing else "pass"


def gate_tally(*, outcomes: Iterable[ScopedCheckOutcome]) -> GateTally:
    """Count a gate's scoped-check outcomes; vacuity counts toward NEITHER side.

    The rule is enforced by construction rather than by a caller's discipline:
    a `vacuous-match` increments only `vacuous`, so no gate reading this tally
    can accidentally read "observed nothing" as passing (or as failing).
    """
    collected = tuple(outcomes)
    return GateTally(
        passing=sum(1 for outcome in collected if outcome == "pass"),
        failing=sum(1 for outcome in collected if outcome == "fail"),
        vacuous=sum(1 for outcome in collected if outcome == VACUOUS_MATCH),
    )


def gate_exit_code(*, tally: GateTally) -> int:
    """A gate's exit code: non-zero ONLY on observed FAILING evidence.

    `tally.vacuous` is not read here, and that omission is the executable form
    of "a gate counts a vacuous-match toward neither". A zero exit therefore
    means "nothing failed" -- see the module docstring on what an exit code
    can and cannot carry.
    """
    return _EXIT_FAILING if tally.failing else _EXIT_NOT_FAILING
