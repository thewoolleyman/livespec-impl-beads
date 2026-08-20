"""A visibility guard on runaway plan-record authoring.

A blocked session writes records instead of making progress: one wrote 15
handoff entries and about 12 research notes in a single day while it was
stuck. Nothing noticed, because each individual write is legitimate and the
plan store has no notion of how fast it is being written to.

This module counts what a plan thread recorded per day and reports the days
that ran past a threshold. It only WARNS. Nothing here refuses a write, and
the threshold is a smell, not a rule: a genuinely busy day is allowed to
exceed it, and the point is that somebody sees it did.

Handoff and scope entries are counted per author-day, since the ledger dates
and attributes each one. Research notes carry neither, so they are counted per
day from the working tree's modification times — which is what this session
wrote, and is deliberately not treated as an authorship record.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from livespec_orchestrator_beads_fabro.commands._plan_timeline import PlanTimelineEntry

__all__: list[str] = [
    "DEFAULT_DAILY_RECORD_THRESHOLD",
    "HANDOFF_ENTRIES_KIND",
    "RESEARCH_NOTES_KIND",
    "PlanRecordRateWarning",
    "plan_record_rate_warnings",
]

DEFAULT_DAILY_RECORD_THRESHOLD = 6
HANDOFF_ENTRIES_KIND = "handoff-entries"
RESEARCH_NOTES_KIND = "research-notes"


@dataclass(frozen=True, kw_only=True)
class PlanRecordRateWarning:
    """One day on which plan-record authoring ran past the threshold."""

    kind: str
    day: str
    author: str | None
    count: int
    threshold: int
    message: str


def plan_record_rate_warnings(
    *,
    entries: Sequence[PlanTimelineEntry],
    research_paths: Sequence[Path] = (),
    threshold: int = DEFAULT_DAILY_RECORD_THRESHOLD,
) -> tuple[PlanRecordRateWarning, ...]:
    """Report every author-day and day whose plan-record count exceeds the threshold."""
    warnings: list[PlanRecordRateWarning] = []
    entry_days: Counter[tuple[str, str]] = Counter()
    for entry in entries:
        day = _day_of(timestamp=entry.created_at)
        if day is not None:
            entry_days[(entry.author, day)] += 1
    for (author, day), count in sorted(entry_days.items()):
        if count > threshold:
            warnings.append(
                _warning(
                    kind=HANDOFF_ENTRIES_KIND,
                    day=day,
                    author=author,
                    count=count,
                    threshold=threshold,
                )
            )
    research_days: Counter[str] = Counter(_day_of_path(path=path) for path in research_paths)
    for day, count in sorted(research_days.items()):
        if count > threshold:
            warnings.append(
                _warning(
                    kind=RESEARCH_NOTES_KIND,
                    day=day,
                    author=None,
                    count=count,
                    threshold=threshold,
                )
            )
    return tuple(warnings)


def _warning(
    *, kind: str, day: str, author: str | None, count: int, threshold: int
) -> PlanRecordRateWarning:
    who = f" by {author}" if author is not None else ""
    return PlanRecordRateWarning(
        kind=kind,
        day=day,
        author=author,
        count=count,
        threshold=threshold,
        message=(
            f"plan-record rate: {count} {kind}{who} on {day} exceeds the "
            f"threshold of {threshold}; a session writing records this fast is "
            "usually blocked rather than productive"
        ),
    )


def _day_of(*, timestamp: str) -> str | None:
    head, _, _ = timestamp.partition("T")
    if len(head) != len("YYYY-MM-DD"):
        return None
    return head


def _day_of_path(*, path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()
