"""OTLP span rendering for Dispatcher review-gate telemetry."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_review_gate_parse import (
    ReviewGateTelemetry,
)
from livespec_orchestrator_beads_fabro.commands._otel_scrub import attr as _attr

__all__: list[str] = [
    "ReviewGateSpanIdentity",
    "emit_review_gate_span",
    "review_gate_request_line",
]

_OTLP_SERVICE_NAME = "livespec-dispatcher"
_OTLP_SERVICE_NAMESPACE = "livespec-family"
_OTLP_SCOPE_NAME = "livespec.dispatcher.review-gate"
_OTLP_SCOPE_VERSION = "0.1.0"
_SPAN_KIND_INTERNAL = 1


@dataclass(frozen=True, kw_only=True)
class ReviewGateSpanIdentity:
    """Dispatch identity fields stamped onto a review-gate span."""

    work_item_id: str
    dispatch_id: str
    run_id: str
    dispatch_factory: str | None = None


def emit_review_gate_span(
    *,
    telemetry: ReviewGateTelemetry,
    spans_path: Path,
    identity: ReviewGateSpanIdentity,
    now_ns: int,
) -> None:
    """Append one OTLP/HTTP JSON span carrying review-gate telemetry."""
    line = review_gate_request_line(
        telemetry=telemetry,
        work_item_id=identity.work_item_id,
        dispatch_id=identity.dispatch_id,
        run_id=identity.run_id,
        dispatch_factory=identity.dispatch_factory,
        now_ns=now_ns,
    )
    spans_path.parent.mkdir(parents=True, exist_ok=True)
    with spans_path.open("a", encoding="utf-8") as handle:
        _ = handle.write(line + "\n")


def review_gate_request_line(
    *,
    telemetry: ReviewGateTelemetry,
    work_item_id: str,
    dispatch_id: str,
    run_id: str,
    now_ns: int,
    dispatch_factory: str | None = None,
) -> str:
    """Build one OTLP `ExportTraceServiceRequest` JSON line."""
    attrs: dict[str, object] = {
        "work.item.id": work_item_id,
        "livespec.dispatch.id": dispatch_id,
        "fabro.run_id": run_id,
        "review.verdict": telemetry.verdict,
        "review.fix_rounds": telemetry.fix_rounds,
        "review.hit_cap": telemetry.hit_cap,
        "pr.shipped_on_cap": telemetry.shipped_on_cap,
    }
    if dispatch_factory is not None:
        attrs["livespec.dispatch.factory"] = dispatch_factory
    span = {
        "traceId": _hex_id(key=f"review-gate-trace:{dispatch_id}:{run_id}", nbytes=16),
        "spanId": _hex_id(key=f"review-gate-span:{run_id}", nbytes=8),
        "name": "review.gate",
        "kind": _SPAN_KIND_INTERNAL,
        "startTimeUnixNano": str(now_ns),
        "endTimeUnixNano": str(now_ns),
        "attributes": [_attr(key=key, value=value) for key, value in attrs.items()],
    }
    request: dict[str, object] = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": _OTLP_SERVICE_NAME}},
                        {
                            "key": "service.namespace",
                            "value": {"stringValue": _OTLP_SERVICE_NAMESPACE},
                        },
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": _OTLP_SCOPE_NAME, "version": _OTLP_SCOPE_VERSION},
                        "spans": [span],
                    }
                ],
            }
        ]
    }
    return json.dumps(request, separators=(",", ":"), sort_keys=True)


def _hex_id(*, key: str, nbytes: int) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[: nbytes * 2]
