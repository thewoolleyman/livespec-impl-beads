"""WIP-cap accounting for active dispatch claims.

This module deliberately chooses WIP-slot reclamation for readable
green-terminal active rows. Bounding by age would still delay recovery behind
an arbitrary clock threshold, and deferral-only surfacing was already shipped
by bd-ib-snyquw.1 but fires after capacity has been refused. Reclaiming here
addresses accumulated stale occupancy; bd-ib-vfsg addresses the upstream
green-outcome race that creates new rows in this state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_lock import (
    live_dispatch_lock,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt, parse_json
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "ActiveClaimAccounting",
    "ActiveClaimHold",
    "claimed_active_accounting",
    "claimed_active_count",
    "claimed_active_projection",
]


@dataclass(frozen=True, kw_only=True)
class ActiveClaimHold:
    work_item_id: str
    reason: str
    backed_by_live_watchable_run: bool


@dataclass(frozen=True, kw_only=True)
class ActiveClaimAccounting:
    active_count: int
    live_lock_active_ids: tuple[str, ...]
    green_terminal_active_ids: tuple[str, ...]
    journal_unreadable_active_ids: tuple[str, ...]
    actionable_holds: tuple[ActiveClaimHold, ...] = field(default=(), compare=False)


@dataclass(frozen=True, kw_only=True)
class _TerminalHistory:
    last_admit_index: int | None = None
    last_outcome_index: int | None = None
    last_outcome_status: str | None = None


def claimed_active_count(*, repo: Path, items: list[WorkItem], journal: JournalFile) -> int:
    return claimed_active_accounting(repo=repo, items=items, journal=journal).active_count


def claimed_active_projection(
    *, repo: Path, items: list[WorkItem], journal: JournalFile
) -> ActiveClaimAccounting:
    return _claimed_active_accounting(
        repo=repo,
        items=items,
        journal=journal,
        record_abandonment=False,
    )


def claimed_active_accounting(
    *, repo: Path, items: list[WorkItem], journal: JournalFile
) -> ActiveClaimAccounting:
    return _claimed_active_accounting(
        repo=repo,
        items=items,
        journal=journal,
        record_abandonment=True,
    )


def _claimed_active_accounting(
    *,
    repo: Path,
    items: list[WorkItem],
    journal: JournalFile,
    record_abandonment: bool,
) -> ActiveClaimAccounting:
    histories: dict[str, _TerminalHistory] | None = None
    live_lock_active_ids: list[str] = []
    green_terminal_active_ids: list[str] = []
    journal_unreadable_active_ids: list[str] = []
    actionable_holds: list[ActiveClaimHold] = []
    for item in items:
        if item.status != "active":
            continue
        if live_dispatch_lock(repo=repo, work_item_id=item.id) is not None:
            live_lock_active_ids.append(item.id)
            continue
        if histories is None:
            histories = _terminal_histories(journal=journal)
        if histories is None:
            journal_unreadable_active_ids.append(item.id)
            actionable_holds.append(
                ActiveClaimHold(
                    work_item_id=item.id,
                    reason="journal-unreadable",
                    backed_by_live_watchable_run=False,
                )
            )
            continue
        history = histories.get(item.id)
        if _green_terminal_after_latest_admit(history=history):
            green_terminal_active_ids.append(item.id)
        elif not record_abandonment and history is None:
            actionable_holds.append(
                ActiveClaimHold(
                    work_item_id=item.id,
                    reason="no-outcome-since-ledger-admit",
                    backed_by_live_watchable_run=False,
                )
            )
        if record_abandonment:
            journal.append(record=_abandoned_record(item=item, history=history))
    return ActiveClaimAccounting(
        active_count=(len(live_lock_active_ids) + len(journal_unreadable_active_ids)),
        live_lock_active_ids=tuple(live_lock_active_ids),
        green_terminal_active_ids=tuple(green_terminal_active_ids),
        journal_unreadable_active_ids=tuple(journal_unreadable_active_ids),
        actionable_holds=tuple(actionable_holds),
    )


def _green_terminal_after_latest_admit(*, history: _TerminalHistory | None) -> bool:
    if history is None or history.last_outcome_index is None:
        return False
    if (
        history.last_admit_index is not None
        and history.last_outcome_index < history.last_admit_index
    ):
        return False
    return history.last_outcome_status == "green"


def _terminal_histories(*, journal: JournalFile) -> dict[str, _TerminalHistory] | None:
    lines = _journal_lines(path=journal.path)
    if lines is None:
        return None
    histories: dict[str, _TerminalHistory] = {}
    for index, line in enumerate(lines):
        record = _journal_record(line=line)
        if record is None:
            continue
        _record_history(histories=histories, index=index, record=record)
    return histories


def _journal_lines(*, path: Path) -> tuple[str, ...] | None:
    read = attempt(action=lambda: path.read_text(encoding="utf-8"), exceptions=(OSError,))
    if isinstance(read, AttemptFailure):
        return None
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
    elif history.last_outcome_status == "green":
        reason = "green-terminal-active-reclaimed"
    else:
        reason = "terminal-outcome-non-green"
    return {
        "stage": "dispatch-claim-abandoned",
        "work_item_id": item.id,
        "status": item.status,
        "reason": reason,
    }
