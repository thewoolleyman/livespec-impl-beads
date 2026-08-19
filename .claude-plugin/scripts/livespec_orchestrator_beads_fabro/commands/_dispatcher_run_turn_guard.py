"""Post-dispatch `run_turn` telemetry assertion for the Dispatcher."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_reflection_journal import (
    read_journal_records,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_run_turn_sink import (
    RunTurnSink,
    run_turn_check_record,
)

__all__: list[str] = [
    "append_run_turn_checks",
]


class JournalWriter(Protocol):
    def append(self, *, record: dict[str, object]) -> None:
        """Persist one journal record."""
        ...


def append_run_turn_checks(
    *,
    outcomes: tuple[DispatchOutcome, ...],
    journal: JournalWriter,
    journal_path: Path,
    sink: RunTurnSink,
) -> None:
    """Append one non-blocking `run_turn` export assertion per green dispatch."""
    dispatches = _dispatches_by_item(records=read_journal_records(journal_path=journal_path))
    for outcome in outcomes:
        if outcome.status != "green":
            continue
        dispatch_id, started_at_epoch = dispatches.get(outcome.work_item_id, ("", None))
        journal.append(
            record=run_turn_check_record(
                sink=sink,
                work_item_id=outcome.work_item_id,
                dispatch_id=dispatch_id,
                started_at_epoch=started_at_epoch,
            )
        )


def _dispatches_by_item(
    *, records: tuple[dict[str, object], ...]
) -> dict[str, tuple[str, float | None]]:
    dispatches: dict[str, tuple[str, float | None]] = {}
    for record in records:
        if record.get("stage") != "dispatch-id":
            continue
        work_item_id = record.get("work_item_id")
        dispatch_id = record.get("dispatch_id")
        if isinstance(work_item_id, str) and isinstance(dispatch_id, str):
            dispatches[work_item_id] = (dispatch_id, _epoch(record=record))
    return dispatches


def _epoch(*, record: dict[str, object]) -> float | None:
    value = record.get("started_at_epoch")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)
