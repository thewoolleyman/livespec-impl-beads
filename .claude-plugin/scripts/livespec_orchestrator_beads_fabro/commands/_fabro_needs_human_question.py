"""Why a TERMINATED factory run routed its work-item to a human, read off `inspect`.

Contract v093 in `SPECIFICATION/contracts.md` — the clause ruling that a
factory run never awaits a human — settles the shape this module is written
against, and it is the opposite of the obvious one. A factory run NEVER
parks on a question: a
needs-human outcome terminates the run non-green, preserves its tree by
reference, and rests the work-item at `blocked` with lane reason
`needs-human`. The ledger is the only place a human decision waits, and the
human's answer is a ledger valve — `resolve-blocked:<item-id>:ready` — never
an answer sent to a live run.

So the question this module reads is a fact about a DEAD run. There is
nothing to resume and nothing to answer on the factory side; what the
`needs_human` terminal node left behind is the only account of WHY the loop
gave up and WHERE the work survived, and today that account is visible
nowhere — the ledger item carries its title and nothing else.

Do NOT gate any read here on a run STATUS. A terminated run is `failed`, and
a park-shaped status filter would match nothing while reporting cleanly, which
is the wrong-instrument failure this repository catalogues. The discriminator
is the terminal node's own evidence, in two independent forms:

- the `LIVESPEC_NEEDS_HUMAN` sentinel the node writes to stderr before
  exiting 1, and
- a checkpoint whose `next_node_id` names the `needs_human` terminal.

Either alone is sufficient. Reading BOTH is what makes the discriminator
robust to the one thing that is genuinely unknown here: WHICH field of an
`inspect` record carries a script node's stderr. No captured payload for a
needs-human run exists in this repository and the implementation sandbox
reaches no factory, so rather than guess a key name, the sentinel is searched
for across every string in the record. That is sound precisely because the
token is OURS — the workflow's own `needs_human` script emits it (keep the
literal in lockstep via `_dispatcher_plan.NEEDS_HUMAN_MARKER`) — so it cannot
collide with fabro's vocabulary, and a schema change that moves stderr to a
different key cannot break the read. The checkpoint leg reuses
`_fabro_escalation`, whose `next_node_id` structure was MEASURED on run
01M10CYZ8S9TNPZ2MW096NJW7V.

WHY THE PAYLOAD CARRIES NO OFFERED OPTIONS, which is a deliberate absence and
not an oversight. Under v093 a terminated run cannot offer any: the former
`[R] Retry / [I] Re-implement / [A] Abandon` answers became ledger valves when
the `escalate` hexagon was replaced by this dead-end node. Scraping a run
record for options would be hunting for a shape the ratified contract forbids
from existing. The offered options are the valves, and naming them belongs to
the lane that renders the item, not to a reader of the run.

`tree_preserved` is carried separately from `preserved_ref` because the two
answer different questions and the expensive mistake is conflating them. The
node pushes best-effort; when the push FAILS it says so and no ref exists. A
human choosing to rework from the preserved tree needs to know that the tree
is not there before choosing, so a failed push is reported as a fact rather
than as a missing ref.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import NEEDS_HUMAN_MARKER
from livespec_orchestrator_beads_fabro.commands._fabro_escalation import (
    ESCALATION_NODE_ID,
    fabro_escalation_from_payload,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port_records import fabro_inspect_record

__all__: list[str] = [
    "NEEDS_HUMAN_NODE_ID",
    "NeedsHumanQuestion",
    "needs_human_question_from_payload",
]

# The workflow's terminal node id, shared with the escalation reader so one
# rename cannot leave two modules disagreeing about which node this is.
NEEDS_HUMAN_NODE_ID = ESCALATION_NODE_ID

# The three sentinels the `needs_human` script writes to stderr, all derived
# from the ONE shared marker so a workflow edit cannot desynchronise them.
# `_PRESERVED` and `_PUSH_FAILED` both CONTAIN the bare marker, so every match
# below keys on the colon-terminated form that distinguishes them.
_PROMPT_SENTINEL = f"{NEEDS_HUMAN_MARKER}: "
_PRESERVED_SENTINEL = f"{NEEDS_HUMAN_MARKER}_PRESERVED: "
_PUSH_FAILED_SENTINEL = f"{NEEDS_HUMAN_MARKER}_PUSH_FAILED"


@dataclass(frozen=True, kw_only=True)
class NeedsHumanQuestion:
    """The terminated run's own account of why it routed the item to a human.

    Every field is independently optional because each comes from a different
    sentinel or structure, and a record carrying only one of them is still
    worth surfacing: the alternative is the status quo, where the ledger item
    says nothing but its title.
    """

    prompt: str | None
    reason: str | None
    preserved_ref: str | None
    tree_preserved: bool


def needs_human_question_from_payload(*, payload: object | None) -> NeedsHumanQuestion | None:
    """The needs-human account this run left, or `None` if it left none.

    `None` says the record shows no needs-human ending — neither the sentinel
    nor a checkpoint routing to the terminal node. It never means "ended that
    way but said nothing": a run whose sentinel is present but whose text is
    unreadable still yields a question, because the ROUTING is itself the fact
    a human needs.
    """
    record = fabro_inspect_record(payload=payload)
    if record is None:
        return None
    lines = _sentinel_lines(value=record)
    routed = _routed_to_terminal(record=record)
    if not lines and not routed:
        return None
    return NeedsHumanQuestion(
        prompt=_after(lines=lines, sentinel=_PROMPT_SENTINEL),
        reason=_engine_reason(record=record),
        preserved_ref=_after(lines=lines, sentinel=_PRESERVED_SENTINEL),
        tree_preserved=not any(_PUSH_FAILED_SENTINEL in line for line in lines),
    )


def _routed_to_terminal(*, record: dict[str, Any]) -> bool:
    """Whether any checkpoint routes to the needs-human terminal node."""
    for checkpoint in _checkpoint_mappings(record=record):
        candidate: object = checkpoint.get("next_node_id")
        if isinstance(candidate, str) and candidate.strip() == NEEDS_HUMAN_NODE_ID:
            return True
    return False


def _checkpoint_mappings(*, record: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """Every checkpoint mapping on the record, wrappers and nested state alike.

    Deliberately looser than `_fabro_escalation`'s own walk: that reader needs
    the NEWEST checkpoint because it is discriminating between two endings,
    while this one only asks whether the terminal was ever routed to.
    """
    found: list[dict[str, Any]] = []
    entries: object = record.get("checkpoints")
    if isinstance(entries, list):
        for entry in cast("list[object]", entries):
            if not isinstance(entry, dict):
                continue
            typed = cast("dict[str, Any]", entry)
            found.append(typed)
            nested: object = typed.get("checkpoint")
            if isinstance(nested, dict):
                found.append(cast("dict[str, Any]", nested))
    top_level: object = record.get("checkpoint")
    if isinstance(top_level, dict):
        found.append(cast("dict[str, Any]", top_level))
    return tuple(found)


def _engine_reason(*, record: dict[str, Any]) -> str | None:
    """Why the loop routed here, when the ENGINE routed it rather than an agent.

    `None` is the agent-reported ending — a node that SUCCEEDED and rode a
    conditional edge — which records no loop failure signature. That absence is
    itself informative, so the lane renders the two differently rather than
    treating a missing reason as a missing read.
    """
    escalation = fabro_escalation_from_payload(payload=record)
    if escalation is None:
        return None
    return ", ".join(escalation.loop_failure_signatures)


def _after(*, lines: tuple[str, ...], sentinel: str) -> str | None:
    """The text following the first occurrence of one sentinel."""
    for line in lines:
        index = line.find(sentinel)
        if index >= 0:
            trailing = line[index + len(sentinel) :].strip()
            if trailing != "":
                return trailing
    return None


def _sentinel_lines(*, value: object) -> tuple[str, ...]:
    """Every line carrying a needs-human sentinel, from anywhere in the record.

    Searched across all strings rather than at a known key: which field holds a
    script node's stderr is the one thing genuinely unknown here, while the
    token itself is this workflow's own and cannot appear by accident.

    Lines are kept VERBATIM rather than stripped. The sentinels this feeds are
    colon-and-space terminated, so trimming a line would silently unmatch a
    sentinel whose message is empty — and that is precisely the case `_after`
    exists to reject rather than report as content.
    """
    found: list[str] = []
    for text in _strings(value=value):
        found.extend(line for line in text.splitlines() if NEEDS_HUMAN_MARKER in line)
    return tuple(found)


def _strings(*, value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        nested = cast("dict[str, Any]", value).values()
        return tuple(text for item in nested for text in _strings(value=item))
    if isinstance(value, list):
        entries = cast("list[object]", value)
        return tuple(text for item in entries for text in _strings(value=item))
    return ()
