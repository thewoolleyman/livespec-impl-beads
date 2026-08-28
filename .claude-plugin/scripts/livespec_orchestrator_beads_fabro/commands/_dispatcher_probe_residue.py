"""Scoped residue assertions for the loop probe's before/after snapshots.

The loop-probe clause of `SPECIFICATION/contracts.md` splits what the probe
observes into two populations that are graded DIFFERENTLY, and the split is the
whole design. HARD assertions key on the probe's RESERVED IDENTIFIER SET -- its
run identifier and its designated item -- because those are the only pieces of
state the probe itself caused. Everything else is REPORTED and never asserted:
a probe cycle spans admission to acceptance, unrelated attention items
legitimately appear and resolve through concurrent operator activity in that
window, and failing on their movement would be the mirror image of the
global-emptiness assertion the contract forbids. So this module asserts nothing
about unrelated state in EITHER direction -- it does not require it absent and
it does not require it preserved.

The third outcome is the one that matters most and is easiest to lose. A source
that CANNOT BE READ at either snapshot fails the probe with a
source-unavailable outcome. Unavailability is not emptiness, not resolution and
not success: a residue read that answered "nothing referencing the reserved set
remains" because it could not read the surface at all would be a manufactured
green, and it would look exactly like the real one.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

__all__: list[str] = [
    "DONE_STATUS",
    "SOURCE_UNAVAILABLE_OUTCOME",
    "ResidueReport",
    "ResidueSnapshot",
    "ResidueSource",
    "reserved_identifiers",
    "residue_report",
    "unavailable_detail",
]

# The probe's failure outcome when an attention or ledger source cannot be read.
SOURCE_UNAVAILABLE_OUTCOME = "source-unavailable"
DONE_STATUS = "done"


@dataclass(frozen=True, kw_only=True)
class ResidueSnapshot:
    """One read of a residue source: what it held, or why it could not be read.

    `available` is carried explicitly rather than inferred from an empty
    `identifiers` tuple, because the two are the exact pair this contract
    refuses to conflate.
    """

    source: str
    available: bool
    identifiers: tuple[str, ...] = ()
    detail: str = ""


class ResidueSource(Protocol):
    """An attention or ledger surface the probe snapshots before and after."""

    def snapshot(self) -> ResidueSnapshot: ...


@dataclass(frozen=True, kw_only=True)
class ResidueReport:
    """The scoped residue verdict: hard failures, unavailability, and the delta."""

    hard_failures: tuple[str, ...]
    unavailable: tuple[str, ...]
    unrelated_delta: tuple[str, ...]


def reserved_identifiers(*, work_item_id: str, probe_run_id: str) -> tuple[str, ...]:
    """The probe's reserved identifier set: its run identifier plus its item."""
    return (probe_run_id, work_item_id)


def residue_report(
    *,
    before: Sequence[ResidueSnapshot],
    after: Sequence[ResidueSnapshot],
    reserved: Sequence[str],
    item_status: str,
) -> ResidueReport:
    """Grade the before/after snapshots: hard on the reserved set, soft elsewhere."""
    unavailable = tuple(
        f"{snapshot.source}: {snapshot.detail}"
        for snapshot in (*before, *after)
        if not snapshot.available
    )
    return ResidueReport(
        hard_failures=_hard_failures(after=after, reserved=reserved, item_status=item_status),
        unavailable=unavailable,
        unrelated_delta=_unrelated_delta(before=before, after=after, reserved=reserved),
    )


def unavailable_detail(*, unavailable: Sequence[str]) -> str:
    """The operator-facing text for a source that could not be read."""
    return (
        "a residue source could not be read; the probe reports"
        f" {SOURCE_UNAVAILABLE_OUTCOME} rather than treating the unread surface as"
        f" empty, resolved, or clear. Unreadable: {'; '.join(unavailable)}"
    )


def _hard_failures(
    *,
    after: Sequence[ResidueSnapshot],
    reserved: Sequence[str],
    item_status: str,
) -> tuple[str, ...]:
    failures: list[str] = []
    if item_status != DONE_STATUS:
        failures.append(f"the designated item did not reach {DONE_STATUS}; it is {item_status}")
    for snapshot in after:
        failures.extend(
            _reserved_residue(source=snapshot.source, identifier=identifier)
            for identifier in _reserved_hits(snapshot=snapshot, reserved=reserved)
        )
    return tuple(failures)


def _reserved_residue(*, source: str, identifier: str) -> str:
    return (
        f"{source} still carries {identifier}, which references the probe's"
        " reserved identifier set"
    )


def _unrelated_delta(
    *,
    before: Sequence[ResidueSnapshot],
    after: Sequence[ResidueSnapshot],
    reserved: Sequence[str],
) -> tuple[str, ...]:
    prior = {
        snapshot.source: _unreserved(snapshot=snapshot, reserved=reserved) for snapshot in before
    }
    delta: list[str] = []
    for snapshot in after:
        held = _unreserved(snapshot=snapshot, reserved=reserved)
        was = prior.get(snapshot.source, frozenset())
        delta.extend(f"appeared {snapshot.source}:{name}" for name in sorted(held - was))
        delta.extend(f"resolved {snapshot.source}:{name}" for name in sorted(was - held))
    return tuple(delta)


def _reserved_hits(*, snapshot: ResidueSnapshot, reserved: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        identifier
        for identifier in snapshot.identifiers
        if _references(identifier=identifier, reserved=reserved)
    )


def _unreserved(*, snapshot: ResidueSnapshot, reserved: Sequence[str]) -> frozenset[str]:
    return frozenset(
        identifier
        for identifier in snapshot.identifiers
        if not _references(identifier=identifier, reserved=reserved)
    )


def _references(*, identifier: str, reserved: Sequence[str]) -> bool:
    """Whether one surface identifier references anything in the reserved set.

    Containment rather than equality: an attention surface keys its rows by
    composite names such as `impl:<work-item-id>`, so the reserved item id
    appears INSIDE the identifier rather than as the whole of it.
    """
    return any(name in identifier for name in reserved)
