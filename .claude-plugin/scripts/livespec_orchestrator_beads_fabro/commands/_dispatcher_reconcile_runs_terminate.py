"""Terminate an orphaned Fabro run, preferring the route that records intent.

Three routes, tried in a fixed order, and the order is the point.

A BLOCKED run is holding a pending interview, so it is answered with the
graph's own Abandon option through the server's answer route. That leaves
Fabro's record saying an operator-equivalent authority abandoned the run,
which is a different and more honest artifact than a run that simply
vanished. The option text is matched on the word "abandon" rather than on a
fixed label, because the label belongs to the workflow graph's edge
(`[A] Abandon (leave open for triage)`) and may be reworded there.

Anything else — and any blocked run whose interview could not be answered —
is cancelled through the server's cancel route.

`fabro rm --force` is the LAST resort, taken only after the HTTP routes
have failed, and the caller journals it under its own stage name. It
destroys everything reachable through `inspect` / `dump` / `attach` for that
run, which is exactly why it is not the first thing tried and why the export
is an unconditional precondition of reaching this module at all.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroPort

__all__: list[str] = [
    "TERMINATION_ROUTE_ANSWER",
    "TERMINATION_ROUTE_CANCEL",
    "TERMINATION_ROUTE_RM",
    "PendingAbandonAnswer",
    "TerminationOutcome",
    "abandon_answer",
    "terminate_orphan_run",
]

TERMINATION_ROUTE_ANSWER = "questions-answer"
TERMINATION_ROUTE_CANCEL = "cancel"
TERMINATION_ROUTE_RM = "rm-force"

_BLOCKED_STATUS_KIND = "blocked"
_ABANDON_HINT = "abandon"
_QUESTION_ID_KEYS = ("id", "question_id", "qid")
_OPTION_KEYS = ("options", "choices", "answers")
_OPTION_TEXT_KEYS = ("label", "text", "value", "id")
_HTTP_TIMEOUT_SECONDS = 60.0
_RM_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True, kw_only=True)
class PendingAbandonAnswer:
    """The question to answer and the option text that abandons the run."""

    question_id: str
    option: str


@dataclass(frozen=True, kw_only=True)
class TerminationOutcome:
    """Which route ended the run, whether it worked, and what was observed."""

    route: str
    succeeded: bool
    detail: str


def abandon_answer(*, payload: object | None) -> PendingAbandonAnswer | None:
    """Find the pending question's Abandon option in a questions payload."""
    for question in _questions(payload=payload):
        question_id = _first_str(record=question, keys=_QUESTION_ID_KEYS)
        option = _abandon_option(question=question)
        if question_id is not None and option is not None:
            return PendingAbandonAnswer(question_id=question_id, option=option)
    return None


def terminate_orphan_run(
    *,
    port: FabroPort,
    run_id: str,
    status_kind: str,
) -> TerminationOutcome:
    """Terminate one orphaned run through the first route that works."""
    answered = _answered_abandon(port=port, run_id=run_id, status_kind=status_kind)
    if answered is not None:
        return answered
    cancelled = port.server_api().cancel(run_id=run_id, timeout_seconds=_HTTP_TIMEOUT_SECONDS)
    if cancelled.succeeded:
        return TerminationOutcome(
            route=TERMINATION_ROUTE_CANCEL,
            succeeded=True,
            detail=f"cancel route returned {cancelled.status}",
        )
    unavailable = _route_detail(status=cancelled.status, error=cancelled.error)
    removed = port.rm(run_id=run_id, timeout_seconds=_RM_TIMEOUT_SECONDS)
    return TerminationOutcome(
        route=TERMINATION_ROUTE_RM,
        succeeded=removed.command.exit_code == 0,
        detail=(
            f"cancel route unavailable ({unavailable}); "
            f"fabro rm -f exited {removed.command.exit_code}"
        ),
    )


def _answered_abandon(
    *,
    port: FabroPort,
    run_id: str,
    status_kind: str,
) -> TerminationOutcome | None:
    if status_kind != _BLOCKED_STATUS_KIND:
        return None
    server_api = port.server_api()
    listed = server_api.questions(run_id=run_id, timeout_seconds=_HTTP_TIMEOUT_SECONDS)
    pending = abandon_answer(payload=listed.payload) if listed.succeeded else None
    if pending is None:
        return None
    answered = server_api.answer_question(
        run_id=run_id,
        question_id=pending.question_id,
        answer=pending.option,
        timeout_seconds=_HTTP_TIMEOUT_SECONDS,
    )
    if not answered.succeeded:
        return None
    return TerminationOutcome(
        route=TERMINATION_ROUTE_ANSWER,
        succeeded=True,
        detail=f"answered question {pending.question_id} with {pending.option!r}",
    )


def _route_detail(*, status: int, error: str | None) -> str:
    return error if error is not None else f"status {status}"


def _questions(*, payload: object | None) -> tuple[dict[str, Any], ...]:
    if not isinstance(payload, dict):
        return _question_records(value=payload)
    # A mapping payload is either an envelope carrying `questions`, or one
    # question sent bare. Both shapes are accepted because the route's
    # response envelope is not verified from this repo.
    nested: object = cast("dict[str, Any]", payload).get("questions")
    if isinstance(nested, list):
        return _question_records(value=cast("list[object]", nested))
    return (cast("dict[str, Any]", payload),)


def _question_records(*, value: object) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    entries = cast("list[object]", value)
    return tuple(cast("dict[str, Any]", entry) for entry in entries if isinstance(entry, dict))


def _abandon_option(*, question: dict[str, Any]) -> str | None:
    for key in _OPTION_KEYS:
        raw: object = question.get(key)
        if not isinstance(raw, list):
            continue
        option = _abandon_from_options(options=cast("list[object]", raw))
        if option is not None:
            return option
    return None


def _abandon_from_options(*, options: Sequence[object]) -> str | None:
    for option in options:
        text = _option_text(option=option)
        if text is not None and _ABANDON_HINT in text.lower():
            return text
    return None


def _option_text(*, option: object) -> str | None:
    if isinstance(option, str):
        return option
    if isinstance(option, dict):
        return _first_str(record=cast("dict[str, Any]", option), keys=_OPTION_TEXT_KEYS)
    return None


def _first_str(*, record: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value: object = record.get(key)
        if isinstance(value, str) and value != "":
            return value
    return None
