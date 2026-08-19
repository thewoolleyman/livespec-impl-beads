"""Persisted guard signal for Fabro `run_turn` Honeycomb egress.

The live OTLP receiver exports sandbox spans synchronously through the
Honeycomb exporter seam. This sink records only the cheap, non-secret fact
that a span named `run_turn` from the `fabro` dataset was accepted by that
exporter. Fabro-side `run_turn` spans do not carry per-dispatch
correlation ids, so the sink records a global last-seen signal for the
post-dispatch guard and also indexes any correlation ids present on future
compatible span shapes.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from livespec_orchestrator_beads_fabro.commands._otel_scrub import scrub
from livespec_orchestrator_beads_fabro.effects import (
    AttemptFailure,
    JsonParseFailure,
    attempt,
    parse_json,
)

__all__: list[str] = [
    "RunTurnSink",
    "run_turn_check_record",
]

_FABRO_DATASET = "fabro"
_RUN_TURN_SPAN = "run_turn"
_CORRELATION_KEYS = ("work.item.id", "livespec.dispatch.id")
_GLOBAL_EXPORT_KEY = "fabro.run_turn"
_REASON_ACCEPTED = "accepted"
_REASON_DATASET = "dataset"
_REASON_SPAN_NAME = "span-name"
_DIAGNOSTIC_SUFFIX = "-diagnostics.json"

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class RunTurnSink:
    """Persisted `{work-item/dispatch id -> last-export timestamp}` map."""

    path: Path
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def record_export(
        self,
        *,
        span: dict[str, object],
        resource_attrs: dict[str, str],
        dataset: str,
        at: float,
    ) -> bool:
        """Record one successful Honeycomb export of a Fabro `run_turn` span."""
        span_name = _span_name(span=span)
        if dataset != _FABRO_DATASET:
            self._record_diagnostic(
                reason=_REASON_DATASET,
                dataset=dataset,
                span_name=span_name,
                at=at,
            )
            return False
        if span_name != _RUN_TURN_SPAN:
            self._record_diagnostic(
                reason=_REASON_SPAN_NAME,
                dataset=dataset,
                span_name=span_name,
                at=at,
            )
            return False
        ids = (_GLOBAL_EXPORT_KEY, *_correlation_ids(span=span, resource_attrs=resource_attrs))
        with self._lock:
            exported = self._read()
            for key in ids:
                exported[key] = at
            written = self._write(exported=exported)
        self._record_diagnostic(
            reason=_REASON_ACCEPTED,
            dataset=dataset,
            span_name=span_name,
            at=at,
            write_failed=not written,
        )
        return True

    def has_export(
        self, *, keys: tuple[str, ...], exported_at_or_after: float | None = None
    ) -> bool:
        """True when any candidate key has recorded a `run_turn` export."""
        with self._lock:
            exported = self._read()
        candidates = (_GLOBAL_EXPORT_KEY, *keys)
        return any(
            _is_fresh_export(at=exported.get(key), exported_at_or_after=exported_at_or_after)
            for key in candidates
            if key != ""
        )

    def _read(self) -> dict[str, float]:
        if not self.path.is_file():
            return {}
        stored = attempt(
            action=lambda: self.path.read_text(encoding="utf-8"), exceptions=(OSError,)
        )
        if isinstance(stored, AttemptFailure):
            return {}
        raw = parse_json(text=stored)
        if isinstance(raw, JsonParseFailure) or not isinstance(raw, dict):
            return {}
        exported: dict[str, float] = {}
        for key, value in cast("dict[str, object]", raw).items():
            if isinstance(value, bool):
                continue
            if isinstance(value, int | float):
                exported[scrub(value=key)] = float(value)
        return exported

    def _write(self, *, exported: dict[str, float]) -> bool:
        text = json.dumps(exported, separators=(",", ":"), sort_keys=True)
        tmp = self.path.with_name(f"{self.path.name}.tmp")
        written = attempt(
            action=lambda: _write_atomic(path=self.path, tmp=tmp, text=text),
            exceptions=(OSError,),
        )
        if isinstance(written, AttemptFailure):
            _LOGGER.warning("run_turn export marker write failed: path=%s", self.path)
            return False
        return True

    def _record_diagnostic(
        self,
        *,
        reason: str,
        dataset: str,
        span_name: str,
        at: float,
        write_failed: bool = False,
    ) -> None:
        with self._lock:
            diagnostic = _read_diagnostic(path=_diagnostic_path(path=self.path))
            if reason == _REASON_ACCEPTED:
                diagnostic["accepted"] = _int_value(raw=diagnostic.get("accepted")) + 1
            else:
                rejected = _rejected_counts(raw=diagnostic.get("rejected"))
                rejected[reason] = rejected.get(reason, 0) + 1
                diagnostic["rejected"] = rejected
            if write_failed:
                diagnostic["write_failures"] = _int_value(raw=diagnostic.get("write_failures")) + 1
            else:
                _ = diagnostic.setdefault("write_failures", 0)
            diagnostic["last"] = {
                "at": at,
                "dataset": scrub(value=dataset),
                "reason": reason,
                "span_name": scrub(value=span_name),
            }
            _write_diagnostic(path=_diagnostic_path(path=self.path), diagnostic=diagnostic)


def run_turn_check_record(
    *,
    sink: RunTurnSink,
    work_item_id: str,
    dispatch_id: str,
    started_at_epoch: float | None = None,
) -> dict[str, object]:
    """Build the post-dispatch telemetry assertion journal record."""
    keys = (work_item_id, dispatch_id)
    return {
        "stage": "run-turn-telemetry-check",
        "work_item_id": work_item_id,
        "dispatch_id": dispatch_id,
        "run_turn_exported": sink.has_export(keys=keys, exported_at_or_after=started_at_epoch),
    }


def _span_name(*, span: dict[str, object]) -> str:
    raw = span.get("name")
    if isinstance(raw, str):
        return raw
    return ""


def _diagnostic_path(*, path: Path) -> Path:
    return path.with_name(f"{path.stem}{_DIAGNOSTIC_SUFFIX}")


def _read_diagnostic(*, path: Path) -> dict[str, object]:
    diagnostic: dict[str, object] = {
        "accepted": 0,
        "rejected": {},
        "write_failures": 0,
    }
    if not path.is_file():
        return diagnostic
    stored = attempt(action=lambda: path.read_text(encoding="utf-8"), exceptions=(OSError,))
    if isinstance(stored, AttemptFailure):
        return diagnostic
    raw = parse_json(text=stored)
    if isinstance(raw, JsonParseFailure) or not isinstance(raw, dict):
        return diagnostic
    parsed = cast("dict[str, object]", raw)
    diagnostic["accepted"] = _int_value(raw=parsed.get("accepted"))
    diagnostic["rejected"] = _rejected_counts(raw=parsed.get("rejected"))
    diagnostic["write_failures"] = _int_value(raw=parsed.get("write_failures"))
    return diagnostic


def _write_diagnostic(*, path: Path, diagnostic: dict[str, object]) -> None:
    text = json.dumps(diagnostic, separators=(",", ":"), sort_keys=True)
    tmp = path.with_name(f"{path.name}.tmp")
    written = attempt(
        action=lambda: _write_atomic(path=path, tmp=tmp, text=text),
        exceptions=(OSError,),
    )
    if isinstance(written, AttemptFailure):
        _LOGGER.warning("run_turn export diagnostic write failed: path=%s", path)


def _int_value(*, raw: object) -> int:
    if isinstance(raw, bool):
        return 0
    if isinstance(raw, int):
        return raw
    return 0


def _rejected_counts(*, raw: object) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    counts: dict[str, int] = {}
    for key, value in cast("dict[str, object]", raw).items():
        counts[key] = _int_value(raw=value)
    return counts


def _is_fresh_export(*, at: float | None, exported_at_or_after: float | None) -> bool:
    if at is None:
        return False
    if exported_at_or_after is None:
        return True
    return at >= exported_at_or_after


def _correlation_ids(*, span: dict[str, object], resource_attrs: dict[str, str]) -> tuple[str, ...]:
    attrs = dict(resource_attrs)
    attrs.update(_span_string_attrs(span=span))
    ids: list[str] = []
    for key in _CORRELATION_KEYS:
        value = attrs.get(key)
        if value is not None and value != "" and value not in ids:
            ids.append(scrub(value=value))
    return tuple(ids)


def _span_string_attrs(*, span: dict[str, object]) -> dict[str, str]:
    raw_attrs = span.get("attributes")
    if not isinstance(raw_attrs, list):
        return {}
    attrs: dict[str, str] = {}
    for raw in cast("list[object]", raw_attrs):
        if not isinstance(raw, dict):
            continue
        entry = cast("dict[str, object]", raw)
        key = entry.get("key")
        value = entry.get("value")
        if not isinstance(key, str) or key not in _CORRELATION_KEYS:
            continue
        if not isinstance(value, dict):
            continue
        string_value = cast("dict[str, object]", value).get("stringValue")
        if isinstance(string_value, str):
            attrs[key] = string_value
    return attrs


def _write_atomic(*, path: Path, tmp: Path, text: str) -> None:
    _ = path.parent.mkdir(parents=True, exist_ok=True)
    _ = tmp.write_text(text, encoding="utf-8")
    _ = tmp.replace(path)
