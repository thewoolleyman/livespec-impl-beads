"""The plan-epic timeline, and the resume directive derived from it.

The plan operation asks which action to take on every resume. That question is
right for an operator sitting at the terminal and wrong for the overseer
daemon's context-threshold restart, which re-enters the same thread with its own
recorded next action already on the timeline and nobody present to answer. This
module supplies the deterministic half of the rule: whether the session carries
the unattended marker, which next actions the newest handoff records, and
whether the resume may proceed without asking.

Refusing to ask is the narrow case. It requires the marker AND exactly one
recorded next action on the NEWEST handoff entry; zero, several, or an
attended session all fall back to the picker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.store import read_work_item_comments

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "HANDOFF_KIND",
    "PLAN_HANDOFF_PREFIX",
    "PLAN_SCOPE_PREFIX",
    "SCOPE_KIND",
    "UNATTENDED_ENV_VAR",
    "PlanTimelineEntry",
    "ResumeDirective",
    "is_unattended_session",
    "read_timeline",
    "recorded_next_actions",
    "resume_directive",
]

UNATTENDED_ENV_VAR = "LIVESPEC_PLAN_UNATTENDED"
HANDOFF_KIND = "handoff"
SCOPE_KIND = "scope"
PLAN_HANDOFF_PREFIX = "plan-handoff-entry"
PLAN_SCOPE_PREFIX = "plan-scope-event"

_TRUTHY = frozenset({"1", "on", "true", "yes"})
_NEXT_ACTION_MARKER = "next action"
_MARKER_ORNAMENTS = "-*# "


@dataclass(frozen=True, kw_only=True)
class PlanTimelineEntry:
    """One parsed plan-epic timeline entry."""

    kind: str
    body: str
    author: str
    created_at: str


@dataclass(frozen=True, kw_only=True)
class ResumeDirective:
    """Whether a resume asks which action to take, and what it takes instead."""

    ask: bool
    next_action: str | None
    reason: str


def is_unattended_session(*, env: Mapping[str, str]) -> bool:
    """Report whether this session carries the unattended-resume marker."""
    return env.get(UNATTENDED_ENV_VAR, "").strip().lower() in _TRUTHY


def recorded_next_actions(*, body: str) -> tuple[str, ...]:
    """Return every next action a handoff body names, in written order.

    A marker line that names nothing after its colon records no action: it is
    counted as absent rather than as an empty instruction to execute.
    """
    actions: list[str] = []
    for line in body.splitlines():
        marker_line = line.strip().lstrip(_MARKER_ORNAMENTS).strip()
        if not marker_line.lower().startswith(_NEXT_ACTION_MARKER):
            continue
        _, separator, action = marker_line.partition(":")
        if not separator or not action.strip():
            continue
        actions.append(action.strip())
    return tuple(actions)


def resume_directive(*, entries: Sequence[PlanTimelineEntry], unattended: bool) -> ResumeDirective:
    """Decide whether this resume asks which action to take, or just takes it."""
    if not unattended:
        return ResumeDirective(ask=True, next_action=None, reason="interactive resume")
    handoffs = [entry for entry in entries if entry.kind == HANDOFF_KIND]
    if not handoffs:
        return ResumeDirective(
            ask=True,
            next_action=None,
            reason="no handoff entry on the plan timeline",
        )
    actions = recorded_next_actions(body=handoffs[-1].body)
    if len(actions) != 1:
        return ResumeDirective(
            ask=True,
            next_action=None,
            reason=f"newest handoff records {len(actions)} next actions, not exactly one",
        )
    return ResumeDirective(
        ask=False,
        next_action=actions[0],
        reason="unattended resume takes the single recorded next action",
    )


def read_timeline(*, config: StoreConfig, epic_id: str) -> tuple[PlanTimelineEntry, ...]:
    """Read plan-epic handoff and scope comments oldest-first, each kind-labelled."""
    entries: list[PlanTimelineEntry] = []
    for comment in read_work_item_comments(path=config, work_item_id=epic_id):
        if not comment.text.startswith((PLAN_HANDOFF_PREFIX, PLAN_SCOPE_PREFIX)):
            continue
        entries.append(_parse_entry(text=comment.text))
    return tuple(entries)


def _parse_entry(*, text: str) -> PlanTimelineEntry:
    header, body = text.split("\n\n", maxsplit=1)
    lines = header.splitlines()
    return PlanTimelineEntry(
        kind=HANDOFF_KIND if lines[0] == PLAN_HANDOFF_PREFIX else SCOPE_KIND,
        body=body,
        author=lines[1].removeprefix("author: "),
        created_at=lines[2].removeprefix("timestamp: "),
    )
