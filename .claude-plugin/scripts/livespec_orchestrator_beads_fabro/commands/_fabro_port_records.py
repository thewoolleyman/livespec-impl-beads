"""Fabro response records owned by the dispatcher Fabro port."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, cast

from livespec_orchestrator_beads_fabro.effects import JsonParseFailure, parse_json

__all__: list[str] = [
    "FabroFailureDetail",
    "FabroRunSummary",
    "fabro_failure_detail_from_payload",
    "fabro_run_id_from_output",
    "fabro_run_summaries_from_payload",
    "fabro_run_summaries_from_stdout",
    "fabro_status_kind_from_payload",
]

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
_RUN_ID_RE = re.compile(r"Run:\s*([0-9A-Za-z-]+)")
_WORK_ITEM_RE = re.compile(r"^Work-item:\s*(\S+)", re.MULTILINE)


@dataclass(frozen=True, kw_only=True)
class FabroFailureDetail:
    """Structured failure block surfaced by `fabro inspect --json`."""

    cause: str | None
    category: str | None
    signature: str | None


@dataclass(frozen=True, kw_only=True)
class FabroRunSummary:
    """Run row from `fabro ps -a --json` that livespec code reads."""

    run_id: str
    status_kind: str | None
    goal: str | None
    total_usd_micros: int | None
    work_item_id: str | None = field(default=None, compare=False)


def fabro_run_id_from_output(*, output: str) -> str | None:
    plain = _ANSI_ESCAPE_RE.sub("", output)
    match = _RUN_ID_RE.search(plain)
    if match is None:
        return None
    return match.group(1)


def fabro_run_summaries_from_stdout(*, stdout: str) -> tuple[FabroRunSummary, ...]:
    parsed = parse_json(text=stdout)
    if isinstance(parsed, JsonParseFailure):
        return ()
    return fabro_run_summaries_from_payload(payload=parsed)


def fabro_run_summaries_from_payload(*, payload: object | None) -> tuple[FabroRunSummary, ...]:
    summaries: list[FabroRunSummary] = []
    for run in _runs(payload=payload):
        summary = _run_summary(run=run)
        if summary is not None:
            summaries.append(summary)
    return tuple(summaries)


def fabro_status_kind_from_payload(*, payload: object | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    status_raw: object = cast("dict[str, Any]", payload).get("status")
    if isinstance(status_raw, str):
        return status_raw
    if isinstance(status_raw, dict):
        kind_raw: object = cast("dict[str, Any]", status_raw).get("kind")
        if isinstance(kind_raw, str):
            return kind_raw
    return None


def fabro_failure_detail_from_payload(*, payload: object | None) -> FabroFailureDetail | None:
    if not isinstance(payload, dict):
        return None
    typed_payload = cast("dict[object, object]", payload)
    for block in _failure_blocks(value=typed_payload):
        detail = _failure_detail(block=block)
        if detail is not None:
            return detail
    return None


def _runs(*, payload: object | None) -> list[object]:
    if isinstance(payload, list):
        return cast("list[object]", payload)
    if isinstance(payload, dict):
        runs_raw: object = cast("dict[str, Any]", payload).get("runs")
        if isinstance(runs_raw, list):
            return cast("list[object]", runs_raw)
    return []


def _run_summary(*, run: object) -> FabroRunSummary | None:
    if not isinstance(run, dict):
        return None
    record = cast("dict[str, Any]", run)
    run_id_raw: object = record.get("run_id")
    if not isinstance(run_id_raw, str) or run_id_raw == "":
        return None
    goal = _optional_str(value=record.get("goal"))
    return FabroRunSummary(
        run_id=run_id_raw,
        status_kind=fabro_status_kind_from_payload(payload=record),
        goal=goal,
        work_item_id=_work_item_id(goal=goal),
        total_usd_micros=_optional_int(value=record.get("total_usd_micros")),
    )


def _optional_str(*, value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(*, value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _work_item_id(*, goal: str | None) -> str | None:
    if goal is None:
        return None
    match = _WORK_ITEM_RE.search(goal)
    return None if match is None else match.group(1)


def _failure_blocks(*, value: object) -> tuple[dict[object, object], ...]:
    blocks: list[dict[object, object]] = []
    if isinstance(value, dict):
        mapping = cast("dict[object, object]", value)
        raw_failure = mapping.get("failure")
        if isinstance(raw_failure, dict):
            blocks.append(cast("dict[object, object]", raw_failure))
        for nested in mapping.values():
            blocks.extend(_failure_blocks(value=nested))
    elif isinstance(value, list):
        values = cast("list[object]", value)
        for nested in values:
            blocks.extend(_failure_blocks(value=nested))
    return tuple(blocks)


def _failure_detail(*, block: dict[object, object]) -> FabroFailureDetail | None:
    cause = _first_cause(value=block.get("causes"))
    category = _str_value(value=block.get("category"))
    signature = _str_value(value=block.get("signature"))
    if cause is None and category is None and signature is None:
        return None
    return FabroFailureDetail(cause=cause, category=category, signature=signature)


def _first_cause(*, value: object) -> str | None:
    if not isinstance(value, list):
        return None
    values = cast("list[object]", value)
    for item in values:
        text = _str_value(value=item)
        if text is not None:
            return text
    return None


def _str_value(*, value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
