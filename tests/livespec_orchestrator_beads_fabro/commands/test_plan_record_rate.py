"""Runaway plan-record authoring is visible as a per-day warning."""

from __future__ import annotations

import os
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._plan_record_rate import (
    DEFAULT_DAILY_RECORD_THRESHOLD,
    HANDOFF_ENTRIES_KIND,
    RESEARCH_NOTES_KIND,
    plan_record_rate_warnings,
)
from livespec_orchestrator_beads_fabro.commands._plan_timeline import PlanTimelineEntry

_AUTHOR = "unattended-plan-operation-plan"


def _entries(
    *, count: int, day: str = "2026-08-20", author: str = _AUTHOR
) -> tuple[PlanTimelineEntry, ...]:
    return tuple(
        PlanTimelineEntry(
            kind="handoff",
            body=f"entry {index}",
            author=author,
            created_at=f"{day}T{index:02d}:00:00Z",
        )
        for index in range(count)
    )


def _research_notes(*, tmp_path: Path, count: int, day: str = "2026-08-20") -> list[Path]:
    stamp = int(__import__("datetime").datetime.fromisoformat(f"{day}T12:00:00+00:00").timestamp())
    paths: list[Path] = []
    for index in range(count):
        path = tmp_path / f"note-{index}.md"
        _ = path.write_text("note", encoding="utf-8")
        os.utime(path, (stamp, stamp))
        paths.append(path)
    return paths


def test_a_day_with_three_entries_does_not_warn() -> None:
    assert plan_record_rate_warnings(entries=_entries(count=3)) == ()


def test_a_day_exactly_at_the_threshold_does_not_warn() -> None:
    entries = _entries(count=DEFAULT_DAILY_RECORD_THRESHOLD)

    assert plan_record_rate_warnings(entries=entries) == ()


def test_a_day_past_the_threshold_warns_with_the_count_and_the_day() -> None:
    entries = _entries(count=DEFAULT_DAILY_RECORD_THRESHOLD + 1)

    [warning] = plan_record_rate_warnings(entries=entries)

    assert warning.kind == HANDOFF_ENTRIES_KIND
    assert warning.day == "2026-08-20"
    assert warning.author == _AUTHOR
    assert warning.count == DEFAULT_DAILY_RECORD_THRESHOLD + 1
    assert warning.threshold == DEFAULT_DAILY_RECORD_THRESHOLD
    assert str(DEFAULT_DAILY_RECORD_THRESHOLD + 1) in warning.message
    assert "2026-08-20" in warning.message


def test_entries_are_counted_per_author_day_not_across_the_thread() -> None:
    entries = _entries(count=5) + _entries(count=5, author="another-session")

    assert plan_record_rate_warnings(entries=entries) == ()


def test_entries_are_counted_per_day_not_across_the_thread() -> None:
    entries = _entries(count=5) + _entries(count=5, day="2026-08-21")

    assert plan_record_rate_warnings(entries=entries) == ()


def test_an_explicit_threshold_overrides_the_default() -> None:
    [warning] = plan_record_rate_warnings(entries=_entries(count=4), threshold=3)

    assert warning.count == 4
    assert warning.threshold == 3


def test_research_notes_past_the_threshold_warn_for_their_day(tmp_path: Path) -> None:
    paths = _research_notes(tmp_path=tmp_path, count=DEFAULT_DAILY_RECORD_THRESHOLD + 1)

    [warning] = plan_record_rate_warnings(entries=(), research_paths=paths)

    assert warning.kind == RESEARCH_NOTES_KIND
    assert warning.author is None
    assert warning.count == DEFAULT_DAILY_RECORD_THRESHOLD + 1
    assert warning.day == "2026-08-20"


def test_three_research_notes_do_not_warn(tmp_path: Path) -> None:
    paths = _research_notes(tmp_path=tmp_path, count=3)

    assert plan_record_rate_warnings(entries=(), research_paths=paths) == ()


def test_a_malformed_timestamp_is_not_counted_against_any_day() -> None:
    entries = (
        *_entries(count=DEFAULT_DAILY_RECORD_THRESHOLD),
        PlanTimelineEntry(kind="handoff", body="undated", author=_AUTHOR, created_at="whenever"),
    )

    assert plan_record_rate_warnings(entries=entries) == ()


def test_both_counters_warn_independently_in_one_pass(tmp_path: Path) -> None:
    warnings = plan_record_rate_warnings(
        entries=_entries(count=DEFAULT_DAILY_RECORD_THRESHOLD + 1),
        research_paths=_research_notes(tmp_path=tmp_path, count=DEFAULT_DAILY_RECORD_THRESHOLD + 1),
    )

    assert [warning.kind for warning in warnings] == [
        HANDOFF_ENTRIES_KIND,
        RESEARCH_NOTES_KIND,
    ]
