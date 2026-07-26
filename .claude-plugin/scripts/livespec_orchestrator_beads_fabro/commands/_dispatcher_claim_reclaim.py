"""WIP-cap accounting for active dispatch claims."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_lock import (
    live_dispatch_lock,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt, parse_json
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = ["claimed_active_count"]


@dataclass(frozen=True, kw_only=True)
class _TerminalHistory:
    last_admit_index: int | None = None
    last_outcome_index: int | None = None
    last_outcome_status: str | None = None


def claimed_active_count(*, repo: Path, items: list[WorkItem], journal: JournalFile) -> int:
    histories = _terminal_histories(journal=journal)
    count = 0
    for item in items:
        if item.status != "active":
            continue
        if live_dispatch_lock(repo=repo, work_item_id=item.id) is not None:
            count += 1
            continue
        if _claim_still_counts(history=histories.get(item.id)):
            count += 1
            continue
        journal.append(record=_abandoned_record(item=item, history=histories.get(item.id)))
    return count


def _claim_still_counts(*, history: _TerminalHistory | None) -> bool:
    if history is None or history.last_outcome_index is None:
        return False
    if (
        history.last_admit_index is not None
        and history.last_outcome_index < history.last_admit_index
    ):
        return False
    return history.last_outcome_status == "green"


def _terminal_histories(*, journal: JournalFile) -> dict[str, _TerminalHistory]:
    lines = _journal_lines(path=journal.path)
    histories: dict[str, _TerminalHistory] = {}
    for index, line in enumerate(lines):
        record = _journal_record(line=line)
        if record is None:
            continue
        _record_history(histories=histories, index=index, record=record)
    return histories


def _journal_lines(*, path: Path) -> tuple[str, ...]:
    read = attempt(action=lambda: path.read_text(encoding="utf-8"), exceptions=(OSError,))
    if isinstance(read, AttemptFailure):
        return ()
    return tuple(line for line in read.splitlines() if line)


def _journal_record(*, line: str) -> dict[str, object] | None:
    parsed = parse_json(text=line)
    if not isinstance(parsed, dict):
        return None
    return cast("dict[str, object]", parsed)


def _record_history(
    *, histories: dict[str, _TerminalHistory], index: int, record: dict[str, object]
) -> None:
    if record.get("stage") == "ledger-admit":
        work_item_id = record.get("work_item_id")
        if isinstance(work_item_id, str):
            histories[work_item_id] = _with_admit(history=histories.get(work_item_id), index=index)
    if record.get("stage") == "outcome":
        outcome = record.get("outcome")
        if isinstance(outcome, dict):
            _record_outcome(
                histories=histories,
                index=index,
                outcome=cast("dict[str, object]", outcome),
            )


def _record_outcome(
    *, histories: dict[str, _TerminalHistory], index: int, outcome: dict[str, object]
) -> None:
    work_item_id = outcome.get("work_item_id")
    status = outcome.get("status")
    if isinstance(work_item_id, str) and isinstance(status, str):
        histories[work_item_id] = _with_outcome(
            history=histories.get(work_item_id), index=index, status=status
        )


def _with_admit(*, history: _TerminalHistory | None, index: int) -> _TerminalHistory:
    if history is None:
        return _TerminalHistory(last_admit_index=index)
    return _TerminalHistory(
        last_admit_index=index,
        last_outcome_index=history.last_outcome_index,
        last_outcome_status=history.last_outcome_status,
    )


def _with_outcome(*, history: _TerminalHistory | None, index: int, status: str) -> _TerminalHistory:
    if history is None:
        return _TerminalHistory(last_outcome_index=index, last_outcome_status=status)
    return _TerminalHistory(
        last_admit_index=history.last_admit_index,
        last_outcome_index=index,
        last_outcome_status=status,
    )


def _abandoned_record(*, item: WorkItem, history: _TerminalHistory | None) -> dict[str, object]:
    if (
        history is None
        or history.last_outcome_index is None
        or (
            history.last_admit_index is not None
            and history.last_outcome_index < history.last_admit_index
        )
    ):
        reason = "no-outcome-since-ledger-admit"
    else:
        reason = "terminal-outcome-non-green"
    return {
        "stage": "dispatch-claim-abandoned",
        "work_item_id": item.id,
        "status": item.status,
        "reason": reason,
    }
