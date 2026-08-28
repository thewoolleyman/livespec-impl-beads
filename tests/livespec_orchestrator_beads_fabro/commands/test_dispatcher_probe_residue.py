"""Tests for the loop probe's scoped residue assertions (v076).

The three populations the contract distinguishes get one group each, and the
order is deliberate. The HARD group proves the reserved identifier set is what
fails the probe; the SOFT group proves unrelated movement is reported in BOTH
directions and asserted in neither; the UNAVAILABILITY group proves an unread
source is never reported as a clear one -- the failure that would otherwise be
indistinguishable from the green it manufactures.
"""

from __future__ import annotations

from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_residue import (
    DONE_STATUS,
    SOURCE_UNAVAILABLE_OUTCOME,
    ResidueSnapshot,
    reserved_identifiers,
    residue_report,
    unavailable_detail,
)

_ITEM = "bd-ib-probe"
_RUN = "probe:bd-ib-probe:2026-08-28T00:00:00Z"
_RESERVED = (_RUN, _ITEM)
_ATTENTION = "attention"
_LEDGER = "ledger"


def _snapshot(*, source: str = _ATTENTION, identifiers: tuple[str, ...] = ()) -> ResidueSnapshot:
    return ResidueSnapshot(source=source, available=True, identifiers=identifiers)


def test_the_reserved_set_is_the_run_identifier_plus_the_designated_item() -> None:
    assert reserved_identifiers(work_item_id=_ITEM, probe_run_id=_RUN) == (_RUN, _ITEM)


# --- HARD: the reserved identifier set only ---------------------------------


def test_a_clean_cycle_reports_no_hard_failure() -> None:
    report = residue_report(
        before=[_snapshot(identifiers=(f"impl:{_ITEM}",))],
        after=[_snapshot()],
        reserved=_RESERVED,
        item_status=DONE_STATUS,
    )

    assert report.hard_failures == ()
    assert report.unavailable == ()
    assert report.unrelated_delta == ()


def test_an_item_short_of_done_is_a_hard_failure() -> None:
    report = residue_report(
        before=[_snapshot()],
        after=[_snapshot()],
        reserved=_RESERVED,
        item_status="acceptance",
    )

    assert len(report.hard_failures) == 1
    assert "acceptance" in report.hard_failures[0]


def test_an_attention_row_referencing_a_reserved_identifier_is_a_hard_failure() -> None:
    report = residue_report(
        before=[_snapshot()],
        after=[_snapshot(identifiers=(f"impl:{_ITEM}", f"valve:{_RUN}:x"))],
        reserved=_RESERVED,
        item_status=DONE_STATUS,
    )

    assert len(report.hard_failures) == 2
    assert report.unrelated_delta == ()


# --- SOFT: the unrelated delta is reported, never asserted -------------------


def test_unrelated_movement_is_reported_in_both_directions_and_never_asserted() -> None:
    report = residue_report(
        before=[_snapshot(identifiers=("valve:other:a",))],
        after=[_snapshot(identifiers=("valve:other:b",))],
        reserved=_RESERVED,
        item_status=DONE_STATUS,
    )

    assert report.hard_failures == ()
    assert report.unrelated_delta == (
        "appeared attention:valve:other:b",
        "resolved attention:valve:other:a",
    )


def test_a_source_absent_from_the_before_snapshot_reports_its_rows_as_appeared() -> None:
    report = residue_report(
        before=[_snapshot()],
        after=[_snapshot(), _snapshot(source=_LEDGER, identifiers=("bd-ib-other",))],
        reserved=_RESERVED,
        item_status=DONE_STATUS,
    )

    assert report.unrelated_delta == ("appeared ledger:bd-ib-other",)


# --- UNAVAILABILITY: never read as emptiness --------------------------------


def test_an_unreadable_source_at_either_snapshot_is_reported_unavailable() -> None:
    unreadable = ResidueSnapshot(source=_LEDGER, available=False, detail="connection refused")

    report = residue_report(
        before=[_snapshot(), unreadable],
        after=[_snapshot()],
        reserved=_RESERVED,
        item_status=DONE_STATUS,
    )

    assert report.unavailable == ("ledger: connection refused",)


def test_the_unavailable_detail_refuses_to_read_the_unread_surface_as_clear() -> None:
    detail = unavailable_detail(unavailable=("ledger: connection refused",))

    assert SOURCE_UNAVAILABLE_OUTCOME in detail
    assert "connection refused" in detail
    assert "empty, resolved, or clear" in detail
