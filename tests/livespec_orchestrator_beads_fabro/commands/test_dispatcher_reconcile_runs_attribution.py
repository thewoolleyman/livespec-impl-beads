"""Tests for the dispatch-journal index and the run-to-work-item attribution."""

from __future__ import annotations

import json
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_attribution import (
    NON_TERMINAL_STATUS_KINDS,
    ORPHAN_REASON_ITEM_MISSING,
    ORPHAN_REASON_ITEM_NOT_ACTIVE,
    ORPHAN_REASON_SUPERSEDED_RUN,
    FactoryRunInventory,
    attributed_runs,
    journaled_runs,
    read_journaled_runs,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port_records import FabroRunSummary


def test_the_journal_index_survives_every_malformed_line_shape() -> None:
    journal = "\n".join(
        [
            "not-json",
            json.dumps(["not-a-mapping"]),
            json.dumps({"stage": "dispatch-id", "work_item_id": "bd-ib-super"}),
            json.dumps({"stage": "fabro-run", "run_id": "01ORPHANED"}),
            json.dumps({"work_item_id": "bd-ib-super", "run_id": ""}),
            json.dumps({"work_item_id": "bd-ib-super", "fabro_run_id": "01OLD"}),
            json.dumps({"work_item_id": "bd-ib-super", "fabro_run_id": "01NEW"}),
        ]
    )

    indexed = journaled_runs(text=journal)

    # Last write wins, so a re-dispatch supersedes the run its predecessor recorded.
    assert indexed.newest_run_id_by_item == {"bd-ib-super": "01NEW"}
    assert indexed.item_id_by_run == {"01OLD": "bd-ib-super", "01NEW": "bd-ib-super"}


def test_read_journaled_runs_reads_a_file_and_tolerates_an_absent_one(tmp_path: Path) -> None:
    present = tmp_path / "journal.jsonl"
    _ = present.write_text(
        json.dumps({"work_item_id": "bd-ib-one", "run_id": "01ONE"}) + "\n",
        encoding="utf-8",
    )

    read = read_journaled_runs(path=present)
    absent = read_journaled_runs(path=tmp_path / "missing.jsonl")

    assert read.newest_run_id_by_item == {"bd-ib-one": "01ONE"}
    assert read.item_id_by_run == {"01ONE": "bd-ib-one"}
    assert absent.newest_run_id_by_item == {}


def test_every_non_terminal_status_kind_is_in_scope() -> None:
    assert set(NON_TERMINAL_STATUS_KINDS) == {
        "blocked",
        "paused",
        "runnable",
        "running",
        "starting",
    }


def test_terminal_and_foreign_and_goalless_runs_are_out_of_scope() -> None:
    rows = attributed_runs(
        inventory=_inventory(
            runs=[
                _run(run_id="01DONE", work_item_id="bd-ib-super", status_kind="succeeded"),
                _run(run_id="01FOREIGN", work_item_id="overseer-abc", status_kind="blocked"),
                _run(run_id="01NOGOAL", work_item_id=None, status_kind="blocked"),
                _run(run_id="01GONE", work_item_id="bd-ib-gone", status_kind="starting"),
            ],
            item_statuses={},
        )
    )

    assert [(row.run.run_id, row.base_reason) for row in rows] == [
        ("01GONE", ORPHAN_REASON_ITEM_MISSING)
    ]
    assert rows[0].work_item_status is None


def test_the_journal_attribution_wins_over_the_goal_regex() -> None:
    journal = json.dumps({"work_item_id": "bd-ib-real", "run_id": "01RUN"})

    rows = attributed_runs(
        inventory=_inventory(
            runs=[_run(run_id="01RUN", work_item_id="bd-ib-wrong", status_kind="running")],
            item_statuses={"bd-ib-real": "closed", "bd-ib-wrong": "active"},
            journal=journal,
        )
    )

    assert [(row.work_item_id, row.base_reason) for row in rows] == [
        ("bd-ib-real", ORPHAN_REASON_ITEM_NOT_ACTIVE)
    ]


def test_a_live_claim_has_no_moot_reason_and_a_superseded_one_does() -> None:
    journal = "\n".join(
        [
            json.dumps({"work_item_id": "bd-ib-super", "fabro_run_id": "01OLD"}),
            json.dumps({"work_item_id": "bd-ib-super", "fabro_run_id": "01NEW"}),
        ]
    )

    rows = attributed_runs(
        inventory=_inventory(
            runs=[
                _run(run_id="01OLD", work_item_id="bd-ib-super", status_kind="paused"),
                _run(run_id="01NEW", work_item_id="bd-ib-super", status_kind="running"),
            ],
            item_statuses={"bd-ib-super": "active"},
            journal=journal,
        )
    )

    assert [(row.run.run_id, row.base_reason) for row in rows] == [
        ("01OLD", ORPHAN_REASON_SUPERSEDED_RUN),
        ("01NEW", None),
    ]


def _inventory(
    *,
    runs: list[FabroRunSummary],
    item_statuses: dict[str, str],
    journal: str = "",
) -> FactoryRunInventory:
    return FactoryRunInventory(
        runs=runs,
        item_statuses=item_statuses,
        journaled=journaled_runs(text=journal),
        id_prefix="bd-ib",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
    )


def _run(*, run_id: str, work_item_id: str | None, status_kind: str) -> FabroRunSummary:
    return FabroRunSummary(
        run_id=run_id,
        status_kind=status_kind,
        goal=None if work_item_id is None else f"Work-item: {work_item_id}",
        total_usd_micros=None,
        work_item_id=work_item_id,
    )
