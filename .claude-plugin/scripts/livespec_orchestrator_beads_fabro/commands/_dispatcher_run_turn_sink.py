"""Persisted guard signal for Fabro `run_turn` Honeycomb egress.

The live OTLP receiver exports sandbox spans synchronously through the
Honeycomb exporter seam. This sink records only the cheap, non-secret fact
that a span named `run_turn` from the `fabro` dataset was accepted by that
exporter, keyed by the dispatch correlation ids the Dispatcher already
projects into `OTEL_RESOURCE_ATTRIBUTES`.
"""

from __future__ import annotations

import json
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
        if dataset != _FABRO_DATASET or span.get("name") != _RUN_TURN_SPAN:
            return False
        ids = _correlation_ids(span=span, resource_attrs=resource_attrs)
        if not ids:
            return False
        with self._lock:
            exported = self._read()
            for key in ids:
                exported[key] = at
            self._write(exported=exported)
        return True

    def has_export(self, *, keys: tuple[str, ...]) -> bool:
        """True when any candidate key has recorded a `run_turn` export."""
        with self._lock:
            exported = self._read()
        return any(key in exported for key in keys if key != "")

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

    def _write(self, *, exported: dict[str, float]) -> None:
        text = json.dumps(exported, separators=(",", ":"), sort_keys=True)
        tmp = self.path.with_name(f"{self.path.name}.tmp")
        written = attempt(
            action=lambda: _write_atomic(path=self.path, tmp=tmp, text=text),
            exceptions=(OSError,),
        )
        if isinstance(written, AttemptFailure):
            return


def run_turn_check_record(
    *,
    sink: RunTurnSink,
    work_item_id: str,
    dispatch_id: str,
) -> dict[str, object]:
    """Build the post-dispatch telemetry assertion journal record."""
    keys = (work_item_id, dispatch_id)
    return {
        "stage": "run-turn-telemetry-check",
        "work_item_id": work_item_id,
        "dispatch_id": dispatch_id,
        "run_turn_exported": sink.has_export(keys=keys),
    }


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
