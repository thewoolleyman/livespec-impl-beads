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
    dispatch_ids = _dispatch_ids_by_item(records=read_journal_records(journal_path=journal_path))
    for outcome in outcomes:
        if outcome.status != "green":
            continue
        dispatch_id = dispatch_ids.get(outcome.work_item_id, "")
        journal.append(
            record=run_turn_check_record(
                sink=sink,
                work_item_id=outcome.work_item_id,
                dispatch_id=dispatch_id,
            )
        )


def _dispatch_ids_by_item(*, records: tuple[dict[str, object], ...]) -> dict[str, str]:
    dispatch_ids: dict[str, str] = {}
    for record in records:
        if record.get("stage") != "dispatch-id":
            continue
        work_item_id = record.get("work_item_id")
        dispatch_id = record.get("dispatch_id")
        if isinstance(work_item_id, str) and isinstance(dispatch_id, str):
            dispatch_ids[work_item_id] = dispatch_id
    return dispatch_ids
