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

from livespec_orchestrator_beads_fabro.effects import IsoDatetimeParseFailure, parse_iso_datetime
from livespec_orchestrator_beads_fabro.store import read_work_item_comments

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from livespec_orchestrator_beads_fabro.store import WorkItemComment
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
_EXPECTED_HEADER_SHAPE = "`plan-handoff-entry|plan-scope-event`, `author: `, `timestamp: `"
_AUTHOR_LINE_INDEX = 1
_TIMESTAMP_LINE_INDEX = 2
_MIN_HEADER_LINES = 2
_FULL_HEADER_LINES = 3


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
    for index, comment in enumerate(
        read_work_item_comments(path=config, work_item_id=epic_id), start=1
    ):
        if not comment.text.startswith((PLAN_HANDOFF_PREFIX, PLAN_SCOPE_PREFIX)):
            continue
        entries.append(
            _parse_entry(
                comment=comment,
                comment_ref=_comment_ref(epic_id=epic_id, comment=comment, index=index),
            )
        )
    return tuple(entries)


def _parse_entry(*, comment: WorkItemComment, comment_ref: str) -> PlanTimelineEntry:
    header, _, body = comment.text.partition("\n\n")
    lines = header.splitlines()
    if len(lines) < _MIN_HEADER_LINES:
        raise _format_error(comment_ref=comment_ref, detail="missing author line")
    created_at = _created_at(lines=lines, comment=comment)
    return PlanTimelineEntry(
        kind=HANDOFF_KIND if lines[0] == PLAN_HANDOFF_PREFIX else SCOPE_KIND,
        body=body,
        author=lines[_AUTHOR_LINE_INDEX].removeprefix("author: "),
        created_at=created_at,
    )


def _created_at(*, lines: list[str], comment: WorkItemComment) -> str:
    if len(lines) >= _FULL_HEADER_LINES and lines[_TIMESTAMP_LINE_INDEX].startswith("timestamp: "):
        header_created_at = lines[_TIMESTAMP_LINE_INDEX].removeprefix("timestamp: ")
        if _is_parseable_timestamp(value=header_created_at):
            return header_created_at
    return comment.created_at or ""


def _is_parseable_timestamp(*, value: str) -> bool:
    parsed = parse_iso_datetime(text=value.replace("Z", "+00:00"))
    return not isinstance(parsed, IsoDatetimeParseFailure)


def _comment_ref(*, epic_id: str, comment: WorkItemComment, index: int) -> str:
    if comment.comment_id is not None:
        return comment.comment_id
    return f"{epic_id} comment #{index}"


def _format_error(*, comment_ref: str, detail: str) -> ValueError:
    problem = f"Malformed plan timeline comment {comment_ref}: {detail}"
    expected = f"expected plan timeline header {_EXPECTED_HEADER_SHAPE}, then a blank line and body"
    message = f"{problem}; {expected}"
    return ValueError(message)
