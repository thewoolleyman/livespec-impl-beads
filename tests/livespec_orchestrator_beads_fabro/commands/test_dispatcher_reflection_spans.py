"""Tests for the extracted dispatcher reflection span/summary emitters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_reflection_spans import (
    emit_spans,
    emit_summary,
    join_ids,
    stage_summary,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_stall_telemetry import (
    STALL_CAUSE_ZERO_OUTPUT,
    STALL_STATUS,
    StallSignal,
)


@dataclass(frozen=True, kw_only=True)
class Outcome:
    stage: str


@dataclass(frozen=True, kw_only=True)
class Finding:
    category: str
    severity: str
    count: int
    subject: str


@dataclass(frozen=True, kw_only=True)
class Report:
    mode: str
    item_count: int
    green_count: int
    failed_count: int
    blocked_count: int
    green_streak: int
    findings: tuple[Finding, ...]
    stalls: tuple[StallSignal, ...] = ()


def test_summary_helpers_render_stable_strings() -> None:
    assert stage_summary(outcomes=(Outcome(stage="pr-view"), Outcome(stage="fabro-run"))) == (
        "fabro-run, pr-view"
    )
    assert join_ids(ids=("bd-a", "bd-b")) == "bd-a, bd-b"


def test_emit_summary_writes_no_findings_line(capsys: pytest.CaptureFixture[str]) -> None:
    emit_summary(
        report=Report(
            mode="observe",
            item_count=1,
            green_count=1,
            failed_count=0,
            blocked_count=0,
            green_streak=1,
            findings=(),
        )
    )

    assert "reflection: no findings" in capsys.readouterr().err


def test_emit_spans_writes_pass_and_finding_children(tmp_path: Path) -> None:
    spans_path = tmp_path / "otel" / "spans.jsonl"
    emit_spans(
        report=Report(
            mode="observe",
            item_count=1,
            green_count=0,
            failed_count=1,
            blocked_count=0,
            green_streak=0,
            findings=(
                Finding(
                    category="stage-timeout",
                    severity="warn",
                    count=1,
                    subject="stage timeouts (exit 124) for: bd-a",
                ),
            ),
        ),
        spans_path=spans_path,
    )

    spans_doc = json.loads(spans_path.read_text(encoding="utf-8").strip())
    resource = spans_doc["resourceSpans"][0]
    spans = resource["scopeSpans"][0]["spans"]
    assert [span["name"] for span in spans] == ["reflection.pass", "reflection.finding"]
    assert spans[1]["parentSpanId"] == spans[0]["spanId"]


def test_emit_spans_writes_a_stall_child_naming_the_cancelled_run(tmp_path: Path) -> None:
    """A watchdog cancellation ships its own span carrying run id + cause."""
    spans_path = tmp_path / "otel" / "spans.jsonl"
    emit_spans(
        report=Report(
            mode="observe",
            item_count=1,
            green_count=0,
            failed_count=0,
            blocked_count=0,
            green_streak=0,
            findings=(),
            stalls=(
                StallSignal(
                    work_item_id="bd-a",
                    run_id="01M1RUN",
                    stage="fabro-run",
                    cause=STALL_CAUSE_ZERO_OUTPUT,
                ),
            ),
        ),
        spans_path=spans_path,
    )

    spans_doc = json.loads(spans_path.read_text(encoding="utf-8").strip())
    spans = spans_doc["resourceSpans"][0]["scopeSpans"][0]["spans"]
    assert [span["name"] for span in spans] == ["reflection.pass", "reflection.stall"]
    assert spans[1]["parentSpanId"] == spans[0]["spanId"]
    stall_attrs = {a["key"]: a["value"] for a in spans[1]["attributes"]}
    assert stall_attrs["fabro.run_id"] == {"stringValue": "01M1RUN"}
    assert stall_attrs["livespec.stall.cause"] == {"stringValue": STALL_CAUSE_ZERO_OUTPUT}
    assert stall_attrs["livespec.outcome"] == {"stringValue": STALL_STATUS}
    pass_attrs = {a["key"]: a["value"] for a in spans[0]["attributes"]}
    assert pass_attrs["livespec.reflection.stall_count"] == {"intValue": "1"}
