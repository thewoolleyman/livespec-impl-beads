"""First-class telemetry signal for a stall-watchdog cancellation.

The coarse wall-clock watchdog (`_dispatcher_watchdog`) `fabro rm -f`-es a
run whose event stream has flatlined for the full stall window, and the
engine reports the distinct `stalled-no-progress` outcome
(`_dispatcher_engine_journal.stalled_outcome`). Until this module that
incident was observable only by RECONSTRUCTION: the outcome reached the
notifier and the append-only dispatch journal, but nothing carried it onto
the OTLP export path, so "how often does the factory hang emitting zero
output, and on which runs" had to be answered by reading per-dispatch
journal files rather than by querying telemetry.

The gap was worse than a missing span. The reflection scan's verdict
partition (`_dispatcher_reflection.scan_outcomes`) buckets `green` /
`failed` / `blocked` and NOTHING ELSE, so a `stalled-no-progress` outcome
landed in none of the three: it moved `item_count` and left every other
counter unchanged, which reads exactly like a wave that dispatched an item
and then reported nothing at all about it. This module supplies the
missing cluster.

The signal is derived PURELY from the terminal `DispatchOutcome`s the wave
has already produced — no new probe, no new subprocess — so a defect here
can never change a dispatch verdict, which is the load-bearing
loop-reflection-gate invariant `_dispatcher_reflection` carries.

ATTRIBUTE VOCABULARY (`stall_attributes`) reuses an already-allowlisted
correlation key wherever one exists — `work.item.id`, `fabro.run_id`,
`livespec.stage`, `livespec.outcome` — so the incident joins the existing
correlation triple in the enrich stage rather than opening a private
namespace only this emitter understands. Only the cause key
`livespec.stall.cause` is new, and it is added to
`_otel_scrub.ATTRIBUTE_ALLOWLIST` in the same change: an attribute absent
from that allowlist is DROPPED by the enrich stage before egress, so an
emitter that invents a key without allowlisting it ships a span whose
payload silently disappears between the local file and Honeycomb.

ZERO-OUTPUT SOURCE DATUM — DEFERRED, deliberately (plan
`acp-implement-zero-output-hang` deferral D3, work-item 29f.6). The
fabro-side PER-TURN output measurement (an ACP turn reporting `stderr[0b]`
`stdout[0b]` with `active_time_ms=0`) is not available to the
orchestrator, so `cause` carries the orchestrator-derived default
`zero-output-no-progress` unless the outcome already names a more specific
observed cause. When the fabro-side datum lands it REFINES `cause`; it
does not replace this module, exactly as the metrics-heartbeat primary
refines rather than replaces the coarse watchdog it feeds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

__all__: list[str] = [
    "STALL_CAUSE_ZERO_OUTPUT",
    "STALL_STATUS",
    "UNKNOWN_RUN_ID",
    "StallSignal",
    "stall_attributes",
    "stall_signals",
]

# The engine's terminal status for a watchdog-confirmed stall. Written from
# exactly one place (`_dispatcher_engine_journal.stalled_outcome`) and only
# after the run was `fabro rm -f`-ed, so matching on it IS matching on a
# watchdog cancellation — no journal correlation is needed to identify one.
STALL_STATUS = "stalled-no-progress"

# The orchestrator-derived cause. The host can see that the run stopped
# producing events for the full window; it CANNOT see the per-turn
# zero-output datum that would distinguish an ACP turn that never spoke
# from a deadlock further down (deferral D3, above).
STALL_CAUSE_ZERO_OUTPUT = "zero-output-no-progress"

# Placeholder run id. A stall outcome names its run today; the placeholder
# exists so an outcome that somehow cannot name one still EMITS the
# incident with a legible marker instead of being dropped — an unqueryable
# stall is the exact failure this module exists to end.
UNKNOWN_RUN_ID = "unknown"


class StallOutcomeLike(Protocol):
    """The `DispatchOutcome` fields one stall signal is derived from."""

    @property
    def work_item_id(self) -> str:
        """Work-item the stalled dispatch was carrying."""
        ...

    @property
    def status(self) -> str:
        """Terminal status; `STALL_STATUS` marks a watchdog cancellation."""
        ...

    @property
    def stage(self) -> str:
        """Dispatch stage the run was cancelled in."""
        ...

    @property
    def fabro_run_id(self) -> str | None:
        """Cancelled Fabro run id, when the outcome carries one."""
        ...

    @property
    def fabro_failure_cause(self) -> str | None:
        """Observed failure cause, when a more specific one was read."""
        ...


@dataclass(frozen=True, kw_only=True)
class StallSignal:
    """One watchdog-cancelled dispatch, in the shape the emitter ships."""

    work_item_id: str
    run_id: str
    stage: str
    cause: str


def stall_signals(*, outcomes: tuple[StallOutcomeLike, ...]) -> tuple[StallSignal, ...]:
    """Derive one signal per watchdog-cancelled outcome, in wave order.

    A pure filter over the wave's terminal outcomes: `STALL_STATUS` is
    written from one place and only after the cancellation, so the status
    alone identifies the incident and no journal correlation is needed.
    """
    return tuple(
        StallSignal(
            work_item_id=outcome.work_item_id,
            run_id=_run_id(outcome=outcome),
            stage=outcome.stage,
            cause=_cause(outcome=outcome),
        )
        for outcome in outcomes
        if outcome.status == STALL_STATUS
    )


def stall_attributes(*, signal: StallSignal) -> dict[str, object]:
    """Build the OTLP attribute set for one stall signal.

    Every key is allowlisted in `_otel_scrub.ATTRIBUTE_ALLOWLIST`; four of
    the five are the correlation/host-truth keys the rest of the pipeline
    already joins on, so a stall span groups with its dispatch rather than
    standing alone.
    """
    return {
        "work.item.id": signal.work_item_id,
        "fabro.run_id": signal.run_id,
        "livespec.stage": signal.stage,
        "livespec.outcome": STALL_STATUS,
        "livespec.stall.cause": signal.cause,
    }


def _run_id(*, outcome: StallOutcomeLike) -> str:
    """The cancelled run's id, or `UNKNOWN_RUN_ID` when the outcome names none."""
    run_id = outcome.fabro_run_id
    if run_id is None or run_id.strip() == "":
        return UNKNOWN_RUN_ID
    return run_id.strip()


def _cause(*, outcome: StallOutcomeLike) -> str:
    """The observed failure cause when the outcome carries one, else the default.

    A specific observed cause always wins: the emitter must not overwrite
    a measured reason with the generic orchestrator-derived one.
    """
    cause = outcome.fabro_failure_cause
    if cause is None or cause.strip() == "":
        return STALL_CAUSE_ZERO_OUTPUT
    return cause.strip()
