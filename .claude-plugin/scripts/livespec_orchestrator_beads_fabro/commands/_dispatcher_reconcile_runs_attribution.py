"""What the dispatch journal knows, and which work-item each run belongs to.

This is the reconciler's first layer: it turns one factory's raw run
inventory into rows that name a work-item, a ledger status, and the
moot-question reason — if any — that the ledger has for releasing the run.
Deciding what to DO about a row belongs to the classifier above it.

Three properties of the attribution are deliberate rather than incidental.

A run whose work-item is `active` and whose newest journaled run id IS this
run is never an orphan, even when no dispatcher process is watching it. A
remote run outlives the process that launched it, so "no local process is
watching" is a statement about this host, never about the work.

Attribution prefers the JOURNAL to the goal text. The goal regex parses
prose the run itself carries; the journal is what this repo recorded when
it launched the run, and it is the only surface that can tell a superseded
run from the run a live claim actually belongs to.

Runs whose attributed work-item id does not carry this tenant's id prefix
are OUT OF SCOPE entirely. The family factories are shared — a dozen
tenants submit to the same server — so without the prefix scope every other
tenant's healthy run would read as `item-missing` against this ledger and be
terminated. That failure would be silent and would look exactly like correct
operation, because a foreign run is genuinely absent from this ledger.

Every status kind Fabro can hold that is not terminal is considered. The
predecessor sweep looked only at `runnable` / `running`, which is precisely
why a run parked at the in-loop human gate was never looked at again.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands._fabro_port_records import FabroRunSummary
from livespec_orchestrator_beads_fabro.effects import (
    AttemptFailure,
    JsonParseFailure,
    attempt,
    parse_json,
)

__all__: list[str] = [
    "NON_TERMINAL_STATUS_KINDS",
    "ORPHAN_REASON_ITEM_MISSING",
    "ORPHAN_REASON_ITEM_NOT_ACTIVE",
    "ORPHAN_REASON_SUPERSEDED_RUN",
    "AttributedRun",
    "FactoryRunInventory",
    "JournaledRuns",
    "attributed_runs",
    "journaled_runs",
    "read_journaled_runs",
]

NON_TERMINAL_STATUS_KINDS: tuple[str, ...] = (
    "blocked",
    "paused",
    "runnable",
    "running",
    "starting",
)

ORPHAN_REASON_ITEM_MISSING = "item-missing"
ORPHAN_REASON_ITEM_NOT_ACTIVE = "item-not-active"
ORPHAN_REASON_SUPERSEDED_RUN = "superseded-run"

_ACTIVE_STATUS = "active"
# The two spellings a dispatch journal record uses for the Fabro run it
# names. `fabro-run` outcome records carry `fabro_run_id`; the
# preserve-by-reference records carry `run_id`.
_RUN_ID_KEYS = ("fabro_run_id", "run_id")


@dataclass(frozen=True, kw_only=True)
class JournaledRuns:
    """What the dispatch journal knows about run-to-item association.

    `newest_run_id_by_item` is last-write-wins over the journal's own append
    order, so a re-dispatch supersedes the run its predecessor recorded.
    """

    newest_run_id_by_item: Mapping[str, str]
    item_id_by_run: Mapping[str, str]


@dataclass(frozen=True, kw_only=True)
class FactoryRunInventory:
    """One factory's run inventory and everything the join reads it against."""

    runs: Sequence[FabroRunSummary]
    item_statuses: Mapping[str, str]
    journaled: JournaledRuns
    id_prefix: str
    factory_name: str
    factory_server_url: str


@dataclass(frozen=True, kw_only=True)
class AttributedRun:
    """One non-terminal run joined to its work-item and its moot-question reason.

    `base_reason` is `None` when the LEDGER is still waiting on this run. That
    is not the same as "leave it alone": the grace arm above this layer takes
    a parked run with no moot reason and bounds how long it may hold a slot.
    """

    run: FabroRunSummary
    work_item_id: str
    work_item_status: str | None
    base_reason: str | None


def journaled_runs(*, text: str) -> JournaledRuns:
    """Index a dispatch journal's raw text by work-item and by run id."""
    newest: dict[str, str] = {}
    item_by_run: dict[str, str] = {}
    for line in text.splitlines():
        record = _record(line=line)
        if record is None:
            continue
        work_item_id = _str_value(value=record.get("work_item_id"))
        run_id = _run_id(record=record)
        if work_item_id is None or run_id is None:
            continue
        newest[work_item_id] = run_id
        item_by_run[run_id] = work_item_id
    return JournaledRuns(newest_run_id_by_item=newest, item_id_by_run=item_by_run)


def read_journaled_runs(*, path: Path) -> JournaledRuns:
    """Read the dispatch journal, treating an unreadable file as no knowledge.

    An absent journal is the ordinary state of a fresh clone, and it must not
    make the join louder: with no journaled run ids the `superseded-run` arm
    simply never fires, and every other arm still holds.
    """
    read = attempt(action=lambda: path.read_text(encoding="utf-8"), exceptions=(OSError,))
    if isinstance(read, AttemptFailure):
        return JournaledRuns(newest_run_id_by_item={}, item_id_by_run={})
    return journaled_runs(text=read)


def attributed_runs(*, inventory: FactoryRunInventory) -> tuple[AttributedRun, ...]:
    """Every in-scope non-terminal run, joined to its item and its moot reason."""
    rows: list[AttributedRun] = []
    for run in inventory.runs:
        work_item_id = _attributed_item_id(run=run, inventory=inventory)
        if run.status_kind not in NON_TERMINAL_STATUS_KINDS or work_item_id is None:
            continue
        work_item_status = inventory.item_statuses.get(work_item_id)
        rows.append(
            AttributedRun(
                run=run,
                work_item_id=work_item_id,
                work_item_status=work_item_status,
                base_reason=_orphan_reason(
                    work_item_id=work_item_id,
                    work_item_status=work_item_status,
                    run_id=run.run_id,
                    journaled=inventory.journaled,
                ),
            )
        )
    return tuple(rows)


def _attributed_item_id(*, run: FabroRunSummary, inventory: FactoryRunInventory) -> str | None:
    attributed = inventory.journaled.item_id_by_run.get(run.run_id, run.work_item_id)
    if attributed is None or not attributed.startswith(f"{inventory.id_prefix}-"):
        return None
    return attributed


def _orphan_reason(
    *,
    work_item_id: str,
    work_item_status: str | None,
    run_id: str,
    journaled: JournaledRuns,
) -> str | None:
    if work_item_status is None:
        return ORPHAN_REASON_ITEM_MISSING
    if work_item_status != _ACTIVE_STATUS:
        return ORPHAN_REASON_ITEM_NOT_ACTIVE
    newest = journaled.newest_run_id_by_item.get(work_item_id)
    if newest is not None and newest != run_id:
        return ORPHAN_REASON_SUPERSEDED_RUN
    return None


def _record(*, line: str) -> Mapping[str, object] | None:
    parsed = parse_json(text=line)
    if isinstance(parsed, JsonParseFailure) or not isinstance(parsed, dict):
        return None
    return cast("Mapping[str, object]", cast("dict[str, Any]", parsed))


def _run_id(*, record: Mapping[str, object]) -> str | None:
    for key in _RUN_ID_KEYS:
        value = _str_value(value=record.get(key))
        if value is not None:
            return value
    return None


def _str_value(*, value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value or None
