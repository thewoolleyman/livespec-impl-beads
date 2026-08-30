"""Tests for the watchdog's per-poll run-discovery and its journal record."""

from __future__ import annotations

from dataclasses import dataclass

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_watchdog_discovery import (
    DISCOVERY_JOURNAL_STAGE,
    DISCOVERY_REASON_MATCHED,
    DISCOVERY_REASON_NO_PS_ROWS,
    DISCOVERY_REASON_PS_EXIT_NONZERO,
    DISCOVERY_REASON_STATUS_KIND_NOT_RUNNING,
    DISCOVERY_REASON_WORK_ITEM_ID_MISMATCH,
    classify_discovery,
    journaled_discovery,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port import (
    FabroPsResult,
    FabroRunSummary,
)
from livespec_orchestrator_beads_fabro.commands._run_attribution import RunAttribution


@dataclass(kw_only=True)
class _Journal:
    records: list[dict[str, object]]

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


def _row(
    *,
    run_id: str = "01RUN",
    status_kind: str | None = "running",
    work_item_id: str | None = "bd-ib-mine",
) -> FabroRunSummary:
    return FabroRunSummary(
        run_id=run_id,
        status_kind=status_kind,
        goal=None,
        work_item_id=work_item_id,
        total_usd_micros=None,
    )


def _ps(*, exit_code: int = 0, runs: tuple[FabroRunSummary, ...] = ()) -> FabroPsResult:
    return FabroPsResult(
        command=CommandResult(exit_code=exit_code, stdout="", stderr=""),
        payload=None,
        runs=runs,
    )


def test_classify_matches_a_running_row_for_this_work_item() -> None:
    row = _row()

    outcome = classify_discovery(work_item_id="bd-ib-mine", ps_exit_code=0, runs=(row,))

    assert outcome.run is row
    assert outcome.reason == DISCOVERY_REASON_MATCHED
    assert outcome.work_item_row_count == 1
    assert outcome.status_kinds == ("running",)


def test_classify_matches_a_runnable_row_so_the_stale_item_reaper_still_sees_it() -> None:
    row = _row(status_kind="runnable")

    outcome = classify_discovery(work_item_id="bd-ib-mine", ps_exit_code=0, runs=(row,))

    assert outcome.run is row
    assert outcome.reason == DISCOVERY_REASON_MATCHED


def test_classify_reports_a_failed_ps_probe_rather_than_a_missing_row() -> None:
    # A failed probe observed NOTHING, so it must not be reported as an
    # observation about the run — the two demand different remedies.
    outcome = classify_discovery(work_item_id="bd-ib-mine", ps_exit_code=1, runs=())

    assert outcome.run is None
    assert outcome.reason == DISCOVERY_REASON_PS_EXIT_NONZERO
    assert outcome.ps_exit_code == 1


def test_classify_reports_an_empty_ps_listing_distinctly() -> None:
    outcome = classify_discovery(work_item_id="bd-ib-mine", ps_exit_code=0, runs=())

    assert outcome.run is None
    assert outcome.reason == DISCOVERY_REASON_NO_PS_ROWS
    assert outcome.ps_row_count == 0


def test_classify_reports_a_work_item_id_mismatch_when_only_other_runs_are_listed() -> None:
    outcome = classify_discovery(
        work_item_id="bd-ib-mine",
        ps_exit_code=0,
        runs=(_row(work_item_id="bd-ib-other"),),
    )

    assert outcome.run is None
    assert outcome.reason == DISCOVERY_REASON_WORK_ITEM_ID_MISMATCH
    assert outcome.ps_row_count == 1
    assert outcome.work_item_row_count == 0


def test_classify_counts_rows_whose_goal_text_yielded_no_work_item_id() -> None:
    # The discriminator between "remote ps omitted the in-flight run" and
    # "the row IS the run but its goal text did not attribute": both land on
    # work-item-id-mismatch, and only this counter tells them apart.
    outcome = classify_discovery(
        work_item_id="bd-ib-mine",
        ps_exit_code=0,
        runs=(_row(work_item_id=None), _row(work_item_id="bd-ib-other")),
    )

    assert outcome.reason == DISCOVERY_REASON_WORK_ITEM_ID_MISMATCH
    assert outcome.unattributed_row_count == 1


def test_classify_reports_a_non_running_status_kind_for_a_row_that_is_ours() -> None:
    outcome = classify_discovery(
        work_item_id="bd-ib-mine",
        ps_exit_code=0,
        runs=(_row(status_kind="failed"), _row(status_kind=None)),
    )

    assert outcome.run is None
    assert outcome.reason == DISCOVERY_REASON_STATUS_KIND_NOT_RUNNING
    assert outcome.status_kinds == ("failed", None)


def test_journaled_discovery_records_a_match_with_the_run_identity() -> None:
    journal = _Journal(records=[])

    run = journaled_discovery(
        work_item_id="bd-ib-mine",
        ps=_ps(runs=(_row(run_id="01MINE"),)),
        journal=journal,
    )

    assert run is not None
    assert run.run_id == "01MINE"
    assert journal.records == [
        {
            "work_item_id": "bd-ib-mine",
            "stage": DISCOVERY_JOURNAL_STAGE,
            "matched": True,
            "reason": DISCOVERY_REASON_MATCHED,
            "ps_exit_code": 0,
            "ps_row_count": 1,
            "work_item_row_count": 1,
            "unattributed_row_count": 0,
            "status_kinds": ["running"],
            "run_id": "01MINE",
            "status_kind": "running",
        }
    ]


def test_journaled_discovery_records_a_miss_instead_of_returning_none_silently() -> None:
    journal = _Journal(records=[])

    run = journaled_discovery(
        work_item_id="bd-ib-mine",
        ps=_ps(exit_code=2),
        journal=journal,
    )

    assert run is None
    assert journal.records == [
        {
            "work_item_id": "bd-ib-mine",
            "stage": DISCOVERY_JOURNAL_STAGE,
            "matched": False,
            "reason": DISCOVERY_REASON_PS_EXIT_NONZERO,
            "ps_exit_code": 2,
            "ps_row_count": 0,
            "work_item_row_count": 0,
            "unattributed_row_count": 0,
            "status_kinds": [],
            "run_id": None,
            "status_kind": None,
        }
    ]


def test_every_discovery_failure_mode_has_its_own_reason_name() -> None:
    reasons = {
        DISCOVERY_REASON_MATCHED,
        DISCOVERY_REASON_PS_EXIT_NONZERO,
        DISCOVERY_REASON_NO_PS_ROWS,
        DISCOVERY_REASON_WORK_ITEM_ID_MISMATCH,
        DISCOVERY_REASON_STATUS_KIND_NOT_RUNNING,
    }

    assert len(reasons) == len(
        (
            "matched",
            "ps-exit-nonzero",
            "no-ps-rows",
            "work-item-id-mismatch",
            "status-kind-not-running",
        )
    )


def test_discovery_matches_a_run_the_goal_regex_attributes_to_another_item() -> None:
    """The stamp answers the row the goal text mis-names — the outage's own shape.

    `work-item-id-mismatch` is indistinguishable from "no run of mine exists" in
    the ps listing alone, which is why a goal the regex mis-parses could blind
    the watchdog for eleven days without a single record saying so.
    """
    row = _row(run_id="01MINE", work_item_id="bd-ib-someone-else")
    attribution = RunAttribution(metadata_run_ids={"01MINE": "bd-ib-mine"})

    unattributed = classify_discovery(work_item_id="bd-ib-mine", ps_exit_code=0, runs=(row,))
    attributed = classify_discovery(
        work_item_id="bd-ib-mine",
        ps_exit_code=0,
        runs=(row,),
        attribution=attribution,
    )

    assert unattributed.reason == DISCOVERY_REASON_WORK_ITEM_ID_MISMATCH
    assert unattributed.run is None
    assert attributed.reason == DISCOVERY_REASON_MATCHED
    assert attributed.run is row


def test_a_row_the_stamp_claims_is_no_longer_counted_as_unattributed() -> None:
    row = _row(run_id="01MINE", work_item_id=None)
    attribution = RunAttribution(metadata_run_ids={"01MINE": "bd-ib-mine"})

    outcome = classify_discovery(
        work_item_id="bd-ib-mine",
        ps_exit_code=0,
        runs=(row,),
        attribution=attribution,
    )

    assert outcome.unattributed_row_count == 0
    assert outcome.reason == DISCOVERY_REASON_MATCHED
