"""`dispatcher.step_waivers`: the one sanctioned way a failing step proceeds.

A waiver is COMMITTED configuration -- a list of entries under the governed
repository's own `.livespec.jsonc`, each naming a `step` from the closed
vocabulary, an `owner` (a named responsible party), and a non-empty `reason`.
It is deliberately not an environment variable, a flag, or a remote toggle: a
dial that relaxes a safety refusal is committed configuration with a reviewable
diff, so a standing relaxation is visible to anyone reading the repository.

FAIL-CLOSED ON A DEFECTIVE ENTRY, which is the whole reason this parses rather
than trusts. An entry that is not a mapping, names a step outside the closed
vocabulary, or omits its owner or reason is NOT a waiver and does not relax
anything -- the refusal it would have covered still refuses. The alternative
reading is the dangerous one: treating a malformed entry as "the operator meant
to waive this" turns a typo into a silently disarmed safety gate, and a typo in
a step name is exactly the mistake this shape invites.

THE OWNER IS JOURNALED ON EVERY USE, not merely on the day the waiver lands.
An expired rationale is the owner's to retire, and the only thing that makes
that pressure real is the waived proceed appearing, with a name attached, in
the journal of every dispatch it relaxes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands._config import dispatcher_block
from livespec_orchestrator_beads_fabro.commands._dispatcher_step_ids import STEP_IDS

__all__: list[str] = [
    "STEP_WAIVERS_KEY",
    "WAIVER_ESCAPE",
    "StepWaiver",
    "resolve_step_waivers",
    "step_waivers_from_block",
    "waived_proceed_detail",
    "waived_proceed_record",
    "waiver_for",
]

# The committed key, named verbatim in every refusal that offers the escape so
# the reader knows where to write the answer.
STEP_WAIVERS_KEY = "dispatcher.step_waivers"

# The sentence every refusal appends after its own direct remedy. Single-sourced
# here rather than restated per refusal so the escape cannot drift from the key.
WAIVER_ESCAPE = (
    f"or commit an entry under `{STEP_WAIVERS_KEY}` naming this step, an owner, "
    "and a reason -- the sanctioned escape for a repository that genuinely "
    "cannot satisfy the step"
)

_WAIVERS_BLOCK = "step_waivers"
_STEP_KEY = "step"
_OWNER_KEY = "owner"
_REASON_KEY = "reason"


@dataclass(frozen=True, kw_only=True)
class StepWaiver:
    """One usable committed waiver: the step it covers, its owner, its rationale."""

    step: str
    owner: str
    reason: str


def resolve_step_waivers(*, cwd: Path) -> tuple[StepWaiver, ...]:
    """Read the dispatch target's committed waivers; an absent key waives nothing."""
    return step_waivers_from_block(block=dispatcher_block(cwd=cwd))


def step_waivers_from_block(*, block: dict[str, Any]) -> tuple[StepWaiver, ...]:
    """Every USABLE waiver in a `dispatcher` block, in declaration order.

    A key that is absent or is not a list yields no waivers at all rather than
    an error: "this repository waives nothing" is the safe reading of both, and
    it is the reading that keeps every refusal refusing.
    """
    raw = block.get(_WAIVERS_BLOCK)
    if not isinstance(raw, list):
        return ()
    entries = cast("list[Any]", raw)
    parsed = (_waiver(entry=entry) for entry in entries)
    return tuple(waiver for waiver in parsed if waiver is not None)


def waiver_for(*, waivers: tuple[StepWaiver, ...], step: str) -> StepWaiver | None:
    """The first waiver covering `step`, or None. A waiver is scoped to its step only."""
    for waiver in waivers:
        if waiver.step == step:
            return waiver
    return None


def waived_proceed_record(*, waiver: StepWaiver, waived: dict[str, object]) -> dict[str, object]:
    """The journal record of a waived proceed, carrying the waiver's OWNER.

    The refusal record the waiver relaxed rides along whole under
    `waived_outcome`, so the journal says what was waived as well as who waived
    it -- a record naming only the step would leave a reader unable to tell a
    waived red pipeline from a waived unprovable one.
    """
    return {
        "stage": "step-waived-proceed",
        "step": waiver.step,
        "terminal": False,
        "status": "waived",
        "reason": "step-waiver-proceed",
        "waiver_owner": waiver.owner,
        "waiver_reason": waiver.reason,
        "declaring_key": STEP_WAIVERS_KEY,
        "waived_outcome": waived,
    }


def waived_proceed_detail(*, waiver: StepWaiver) -> str:
    """The operator-facing line a waived proceed prints; visible, never silent."""
    return (
        f"WAIVED: step `{waiver.step}` failed but is covered by a committed "
        f"`{STEP_WAIVERS_KEY}` entry owned by {waiver.owner}; proceeding.\n"
        f"Waiver reason: {waiver.reason}\n"
    )


def _waiver(*, entry: Any) -> StepWaiver | None:
    """One entry, or None when it is not a usable waiver. Never raises."""
    if not isinstance(entry, dict):
        return None
    declared = cast("dict[str, Any]", entry)
    step = declared.get(_STEP_KEY)
    if not isinstance(step, str) or step not in STEP_IDS:
        return None
    owner = declared.get(_OWNER_KEY)
    if not isinstance(owner, str) or owner == "":
        return None
    reason = declared.get(_REASON_KEY)
    if not isinstance(reason, str) or reason == "":
        return None
    return StepWaiver(step=step, owner=owner, reason=reason)
