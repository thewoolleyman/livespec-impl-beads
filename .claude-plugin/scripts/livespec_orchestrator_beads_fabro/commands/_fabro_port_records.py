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
_REMOTE_COMPACTION_CATEGORY = "deterministic"
_TRANSIENT_SIGNATURE_SEGMENT = "|transient_infra|"


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


def _inspect_record(*, payload: object | None) -> dict[str, Any] | None:
    """Normalize an `inspect` payload to the single run record it describes.

    `fabro inspect <run> --json` returns a single-element LIST on the pinned
    build (0.254.0), not a bare mapping. Measured against six real payloads on
    2026-08-20. Mapping payloads are still accepted so a future shape change
    back to a bare object does not regress.
    """
    if isinstance(payload, dict):
        return cast("dict[str, Any]", payload)
    if isinstance(payload, list):
        for entry in cast("list[object]", payload):
            if isinstance(entry, dict):
                return cast("dict[str, Any]", entry)
    return None


def fabro_status_kind_from_payload(*, payload: object | None) -> str | None:
    record = _inspect_record(payload=payload)
    if record is None:
        return None
    status_raw: object = record.get("status")
    if isinstance(status_raw, str):
        return status_raw
    if isinstance(status_raw, dict):
        kind_raw: object = cast("dict[str, Any]", status_raw).get("kind")
        if isinstance(kind_raw, str):
            return kind_raw
    return None


def fabro_failure_detail_from_payload(*, payload: object | None) -> FabroFailureDetail | None:
    record = _inspect_record(payload=payload)
    if record is None:
        return None
    typed_payload = cast("dict[object, object]", record)
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
    causes = _cause_values(value=block.get("causes"))
    remote_compaction_cause = _remote_compaction_cause(causes=causes)
    cause = remote_compaction_cause or _first_cause(causes=causes)
    reclassified = remote_compaction_cause is not None
    category = _failure_category(
        category=_str_value(value=block.get("category")),
        reclassified=reclassified,
    )
    signature = _failure_signature(
        signature=_str_value(value=block.get("signature")),
        reclassified=reclassified,
    )
    if cause is None and category is None and signature is None:
        return None
    return FabroFailureDetail(cause=cause, category=category, signature=signature)


def _cause_values(*, value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    values = cast("list[object]", value)
    return tuple(text for item in values if (text := _str_value(value=item)) is not None)


def _first_cause(*, causes: tuple[str, ...]) -> str | None:
    return next(iter(causes), None)


def _remote_compaction_cause(*, causes: tuple[str, ...]) -> str | None:
    for text in causes:
        if _is_remote_compaction_404(text=text):
            return text
    return None


def _is_remote_compaction_404(*, text: str) -> bool:
    lowered = text.lower()
    return (
        "error running remote compact task" in lowered
        and "404 not found" in lowered
        and "responses/compact" in lowered
    )


def _failure_category(*, category: str | None, reclassified: bool) -> str | None:
    if reclassified:
        return _REMOTE_COMPACTION_CATEGORY
    return category


def _failure_signature(*, signature: str | None, reclassified: bool) -> str | None:
    if not reclassified or signature is None:
        return signature
    return signature.replace(_TRANSIENT_SIGNATURE_SEGMENT, f"|{_REMOTE_COMPACTION_CATEGORY}|")


def _str_value(*, value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
