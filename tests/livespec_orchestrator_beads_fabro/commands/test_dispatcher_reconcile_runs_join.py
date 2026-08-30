"""Tests for the reconciler's pure run-inventory-to-ledger join."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._fabro_port_records import FabroRunSummary

_MODULE_PATH = (
    Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
    / "_dispatcher_reconcile_runs_join.py"
)
_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_join"
_ATTRIBUTION_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._run_attribution"


def test_blocked_run_whose_item_closed_is_an_orphan() -> None:
    assert _MODULE_PATH.is_file()
    module = importlib.import_module(_MODULE_NAME)

    orphans = module.classify_orphans(
        runs=[_run(run_id="01BLOCKED", work_item_id="bd-ib-closed", status_kind="blocked")],
        item_statuses={"bd-ib-closed": "closed"},
        journaled=module.journaled_runs(text=""),
        id_prefix="bd-ib",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
    )

    assert [(run.run_id, run.orphan_reason, run.status_kind) for run in orphans] == [
        ("01BLOCKED", module.ORPHAN_REASON_ITEM_NOT_ACTIVE, "blocked")
    ]


def test_live_remote_run_is_not_an_orphan_with_nobody_watching() -> None:
    module = importlib.import_module(_MODULE_NAME)
    journal = json.dumps({"stage": "fabro-run", "work_item_id": "bd-ib-live", "run_id": "01LIVE"})

    orphans = module.classify_orphans(
        runs=[_run(run_id="01LIVE", work_item_id="bd-ib-live", status_kind="running")],
        item_statuses={"bd-ib-live": "active"},
        journaled=module.journaled_runs(text=journal),
        id_prefix="bd-ib",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
    )

    assert orphans == ()


def test_active_item_with_no_journaled_run_is_left_alone() -> None:
    module = importlib.import_module(_MODULE_NAME)

    orphans = module.classify_orphans(
        runs=[_run(run_id="01LIVE", work_item_id="bd-ib-live", status_kind="running")],
        item_statuses={"bd-ib-live": "active"},
        journaled=module.journaled_runs(text=""),
        id_prefix="bd-ib",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
    )

    assert orphans == ()


def test_superseded_and_missing_and_terminal_and_foreign_runs() -> None:
    module = importlib.import_module(_MODULE_NAME)
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

    orphans = module.classify_orphans(
        runs=[
            _run(run_id="01OLD", work_item_id="bd-ib-super", status_kind="paused"),
            _run(run_id="01NEW", work_item_id="bd-ib-super", status_kind="running"),
            _run(run_id="01GONE", work_item_id="bd-ib-gone", status_kind="starting"),
            _run(run_id="01DONE", work_item_id="bd-ib-super", status_kind="succeeded"),
            _run(run_id="01FOREIGN", work_item_id="overseer-abc", status_kind="blocked"),
            _run(run_id="01NOGOAL", work_item_id=None, status_kind="blocked"),
        ],
        item_statuses={"bd-ib-super": "active"},
        journaled=module.journaled_runs(text=journal),
        id_prefix="bd-ib",
        factory_name="vps",
        factory_server_url="https://vps.example:32276",
    )

    assert [(run.run_id, run.orphan_reason) for run in orphans] == [
        ("01OLD", module.ORPHAN_REASON_SUPERSEDED_RUN),
        ("01GONE", module.ORPHAN_REASON_ITEM_MISSING),
    ]
    assert orphans[1].work_item_status is None
    assert orphans[0].factory_name == "vps"


def test_journal_attribution_wins_over_the_goal_regex() -> None:
    module = importlib.import_module(_MODULE_NAME)
    journal = json.dumps({"work_item_id": "bd-ib-real", "run_id": "01RUN"})

    orphans = module.classify_orphans(
        runs=[_run(run_id="01RUN", work_item_id="bd-ib-wrong", status_kind="running")],
        item_statuses={"bd-ib-real": "closed", "bd-ib-wrong": "active"},
        journaled=module.journaled_runs(text=journal),
        id_prefix="bd-ib",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
    )

    assert [(run.work_item_id, run.orphan_reason) for run in orphans] == [
        ("bd-ib-real", module.ORPHAN_REASON_ITEM_NOT_ACTIVE)
    ]


def test_a_ledger_stamped_run_is_spared_though_its_goal_text_names_a_closed_item() -> None:
    """The stamp is the whole point: the goal regex alone gets this run wrong.

    The control below runs the IDENTICAL join with no attribution and shows it
    classified as an orphan, so this pair discriminates the ledger leg from the
    regex leg rather than merely exercising it.
    """
    module = importlib.import_module(_MODULE_NAME)
    attribution = importlib.import_module(_ATTRIBUTION_MODULE_NAME)

    orphans = module.classify_orphans(
        runs=[_run(run_id="01RUN", work_item_id="bd-ib-closed", status_kind="running")],
        item_statuses={"bd-ib-closed": "closed", "bd-ib-active": "active"},
        journaled=module.journaled_runs(text=""),
        id_prefix="bd-ib",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
        attribution=attribution.RunAttribution(metadata_run_ids={"01RUN": "bd-ib-active"}),
    )

    assert orphans == ()


def test_the_same_run_without_the_stamp_reads_as_an_orphan() -> None:
    module = importlib.import_module(_MODULE_NAME)

    orphans = module.classify_orphans(
        runs=[_run(run_id="01RUN", work_item_id="bd-ib-closed", status_kind="running")],
        item_statuses={"bd-ib-closed": "closed", "bd-ib-active": "active"},
        journaled=module.journaled_runs(text=""),
        id_prefix="bd-ib",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
    )

    assert [(run.work_item_id, run.orphan_reason) for run in orphans] == [
        ("bd-ib-closed", module.ORPHAN_REASON_ITEM_NOT_ACTIVE)
    ]


def test_ledger_metadata_outranks_the_journal_which_outranks_the_goal_text() -> None:
    module = importlib.import_module(_MODULE_NAME)
    attribution = importlib.import_module(_ATTRIBUTION_MODULE_NAME)
    journal = json.dumps({"work_item_id": "bd-ib-journaled", "run_id": "01RUN"})

    orphans = module.classify_orphans(
        runs=[_run(run_id="01RUN", work_item_id="bd-ib-goal", status_kind="running")],
        item_statuses={
            "bd-ib-goal": "active",
            "bd-ib-journaled": "acceptance",
            "bd-ib-stamped": "closed",
        },
        journaled=module.journaled_runs(text=journal),
        id_prefix="bd-ib",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
        attribution=attribution.RunAttribution(metadata_run_ids={"01RUN": "bd-ib-stamped"}),
    )

    assert [(run.work_item_id, run.orphan_reason) for run in orphans] == [
        ("bd-ib-stamped", module.ORPHAN_REASON_ITEM_NOT_ACTIVE)
    ]


def test_a_foreign_tenants_stamped_run_stays_out_of_scope() -> None:
    module = importlib.import_module(_MODULE_NAME)
    attribution = importlib.import_module(_ATTRIBUTION_MODULE_NAME)

    orphans = module.classify_orphans(
        runs=[_run(run_id="01RUN", work_item_id="bd-ib-goal", status_kind="running")],
        item_statuses={"bd-ib-goal": "closed"},
        journaled=module.journaled_runs(text=""),
        id_prefix="bd-ib",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
        attribution=attribution.RunAttribution(metadata_run_ids={"01RUN": "overseer-abc"}),
    )

    assert orphans == ()


def test_read_journaled_runs_reads_a_file_and_tolerates_an_absent_one(tmp_path: Path) -> None:
    module = importlib.import_module(_MODULE_NAME)
    present = tmp_path / "journal.jsonl"
    _ = present.write_text(
        json.dumps({"work_item_id": "bd-ib-one", "run_id": "01ONE"}) + "\n",
        encoding="utf-8",
    )

    read = module.read_journaled_runs(path=present)
    absent = module.read_journaled_runs(path=tmp_path / "missing.jsonl")

    assert read.newest_run_id_by_item == {"bd-ib-one": "01ONE"}
    assert read.item_id_by_run == {"01ONE": "bd-ib-one"}
    assert absent.newest_run_id_by_item == {}


def test_every_non_terminal_status_kind_is_in_scope() -> None:
    module = importlib.import_module(_MODULE_NAME)

    assert set(module.NON_TERMINAL_STATUS_KINDS) == {
        "blocked",
        "paused",
        "runnable",
        "running",
        "starting",
    }


def _run(*, run_id: str, work_item_id: str | None, status_kind: str) -> FabroRunSummary:
    return FabroRunSummary(
        run_id=run_id,
        status_kind=status_kind,
        goal=None if work_item_id is None else f"Work-item: {work_item_id}",
        total_usd_micros=None,
        work_item_id=work_item_id,
    )
