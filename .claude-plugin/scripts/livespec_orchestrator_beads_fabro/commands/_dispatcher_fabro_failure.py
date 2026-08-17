"""Fabro failure-detail parsing for dispatcher failed-run outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from livespec_orchestrator_beads_fabro.effects import JsonParseFailure, parse_json

__all__: list[str] = [
    "FabroFailureDetail",
    "fabro_failure_outcome_detail",
    "parse_fabro_failure_detail",
]


@dataclass(frozen=True, kw_only=True)
class FabroFailureDetail:
    """Structured failure block surfaced by `fabro inspect --json`."""

    cause: str | None
    category: str | None
    signature: str | None


def parse_fabro_failure_detail(*, stdout: str) -> FabroFailureDetail | None:
    """Extract the first useful Fabro `failure` block from inspect JSON."""
    parsed = parse_json(text=stdout)
    if isinstance(parsed, JsonParseFailure) or not isinstance(parsed, dict):
        return None
    payload = cast("dict[object, object]", parsed)
    for block in _failure_blocks(value=payload):
        detail = _failure_detail(block=block)
        if detail is not None:
            return detail
    return None


def fabro_failure_outcome_detail(
    *,
    failure: FabroFailureDetail | None,
    fallback: str,
) -> str:
    """Human-readable failed-run detail, preferring Fabro's structured cause."""
    if failure is None:
        return fallback
    parts: list[str] = []
    if failure.cause is not None:
        parts.append(failure.cause)
    if failure.category is not None:
        parts.append(f"category={failure.category}")
    if failure.signature is not None:
        parts.append(f"signature={failure.signature}")
    return "; ".join(parts) if parts else fallback


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
