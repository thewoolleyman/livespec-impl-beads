"""Run-to-work-item attribution, preferring recorded facts over the goal regex.

A `fabro ps -a --json` row carries no work-item field, so every consumer used to
re-derive the owning item from the run's GOAL TEXT with the
`^Work-item:\\s*(\\S+)` regex in `_fabro_port_records`. That derivation is the
weakest evidence available. It reads a rendered prose brief rather than a field,
so a goal-template edit silently breaks it; and because it keys on the ITEM it
cannot tell two runs for the SAME item apart, so a superseded run and the
re-dispatch that replaced it attribute identically. Both failures return a
plausible answer with no error.

Two stronger sources are recorded at dispatch time. The work-item's
`dispatch_fabro_run_id` metadata key names the newest run the Dispatcher
launched for it, and the dispatch journal keeps every run id it has ever
recorded against that item. This module is the ONE place the three are ordered,
so no consumer can drift back onto the regex leg by forgetting the other two
exist:

1. item metadata — the run id the LEDGER itself names for this run.
2. the dispatch journal's newest record naming this run id.
3. the goal-text regex — the bootstrap, and the only leg available in the
   window between `fabro run` creating a run and the Dispatcher stamping it.

`RunAttribution()` with no sources is REGEX-ONLY, and that is a legitimate
value rather than a degraded one: a call site with no ledger or journal to hand
still routes its decision through this precedence, so the day it gains a source
the stronger leg wins with no edit at the call site.

A journal record counts as a run record when it carries BOTH a `work_item_id`
and a `run_id`. Naming the stages instead (`fabro-run`, `dispatch-id`,
`watchdog-discovery-poll`, ...) would be narrower but would fail in the
expensive direction: a stage added later would carry the run id and be silently
ignored, and the miss would look exactly like an item that had never been
dispatched.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroRunSummary

__all__: list[str] = [
    "GOAL_TEXT_ONLY",
    "RunAttribution",
    "journal_run_ids",
    "newest_journaled_run_id",
    "run_attribution",
]

JournalRecords = Iterable[Mapping[str, object]]


@dataclass(frozen=True, kw_only=True)
class RunAttribution:
    """The ordered evidence one consumer has for mapping runs onto items.

    Both maps are keyed by RUN id, which is the direction that stays
    single-valued: an item accumulates many runs over its life, a run belongs to
    exactly one item.
    """

    metadata_run_ids: Mapping[str, str] = field(default_factory=dict)
    journal_run_ids: Mapping[str, str] = field(default_factory=dict)

    def work_item_id_for(self, *, run: FabroRunSummary) -> str | None:
        """Return the work-item this run belongs to, by strongest evidence first."""
        recorded = self.metadata_run_ids.get(run.run_id)
        if recorded is not None:
            return recorded
        journaled = self.journal_run_ids.get(run.run_id)
        if journaled is not None:
            return journaled
        return run.work_item_id

    def owns(self, *, run: FabroRunSummary, work_item_id: str) -> bool:
        """Whether this run belongs to the named work-item."""
        return self.work_item_id_for(run=run) == work_item_id


# The attribution a call site with no ledger and no journal to hand still routes
# through. Shared rather than constructed per call because a `RunAttribution()`
# default argument would be a call in a default (ruff B008); it is safe to share
# because the dataclass is frozen and neither map is ever mutated in place.
GOAL_TEXT_ONLY = RunAttribution()


def run_attribution(
    *,
    metadata_run_ids: Mapping[str, str] | None = None,
    journal_records: JournalRecords = (),
) -> RunAttribution:
    """Build an attribution from a ledger run-id index and journal records."""
    return RunAttribution(
        metadata_run_ids=dict(metadata_run_ids or {}),
        journal_run_ids=journal_run_ids(records=journal_records),
    )


def journal_run_ids(*, records: JournalRecords) -> dict[str, str]:
    """Map every journaled run id to the work-item the journal names for it."""
    mapped: dict[str, str] = {}
    for record in records:
        run_id = _text(value=record.get("run_id"))
        work_item_id = _text(value=record.get("work_item_id"))
        if run_id is not None and work_item_id is not None:
            mapped[run_id] = work_item_id
    return mapped


def newest_journaled_run_id(*, records: JournalRecords, work_item_id: str) -> str | None:
    """Return the newest Fabro run id the dispatch journal names for one item.

    "Newest" is LAST-WINS over the record order, which is sound because the
    journal is append-only: a later record for the same item cannot describe an
    earlier run. This is the seam the reconciler needs to call a run SUPERSEDED
    — an item whose newest journaled run is not the run under judgment has
    moved on, whatever that run's own status still claims.
    """
    newest: str | None = None
    for record in records:
        if _text(value=record.get("work_item_id")) != work_item_id:
            continue
        run_id = _text(value=record.get("run_id"))
        if run_id is not None:
            newest = run_id
    return newest


def _text(*, value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
