"""Tests for the shared run-to-work-item attribution helper."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroRunSummary

_MODULE_PATH = (
    Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
    / "_run_attribution.py"
)
_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._run_attribution"


def _module() -> Any:
    assert _MODULE_PATH.is_file()
    return importlib.import_module(_MODULE_NAME)


def _row(*, run_id: str, work_item_id: str | None) -> FabroRunSummary:
    return FabroRunSummary(
        run_id=run_id,
        status_kind="running",
        goal=None if work_item_id is None else f"Work-item: {work_item_id}\nRepo: /tmp/repo",
        work_item_id=work_item_id,
        total_usd_micros=None,
    )


def test_empty_attribution_falls_back_to_the_goal_text_regex() -> None:
    module = _module()

    attribution = module.RunAttribution()

    assert attribution.work_item_id_for(run=_row(run_id="01A", work_item_id="bd-ib-a")) == "bd-ib-a"


def test_item_metadata_outranks_both_the_journal_and_the_goal_regex() -> None:
    module = _module()

    attribution = module.run_attribution(
        metadata_run_ids={"01A": "bd-ib-truth"},
        journal_records=({"work_item_id": "bd-ib-journal", "run_id": "01A"},),
    )

    assert attribution.work_item_id_for(run=_row(run_id="01A", work_item_id="bd-ib-goal")) == (
        "bd-ib-truth"
    )


def test_the_journal_outranks_the_goal_regex_when_metadata_is_silent() -> None:
    module = _module()

    attribution = module.run_attribution(
        journal_records=({"work_item_id": "bd-ib-journal", "run_id": "01A"},),
    )

    assert attribution.work_item_id_for(run=_row(run_id="01A", work_item_id="bd-ib-goal")) == (
        "bd-ib-journal"
    )


def test_attribution_is_correct_where_the_goal_regex_names_the_wrong_item() -> None:
    """The mis-attribution the regex cannot detect: a goal quoting another item.

    A rendered goal that quotes a SIBLING work-item on its own leading
    `Work-item:` line — a re-dispatch brief carrying a superseded id, a plan
    excerpt pasted above the assignment — attributes the run to that sibling.
    The regex reports it with no error, and the sibling is a real item, so the
    wrong answer survives every sanity check a consumer could apply to it.
    """
    module = _module()
    run = _row(run_id="01RUN", work_item_id="bd-ib-sibling")

    assert run.work_item_id == "bd-ib-sibling"
    assert module.RunAttribution().work_item_id_for(run=run) == "bd-ib-sibling"

    attribution = module.run_attribution(metadata_run_ids={"01RUN": "bd-ib-owner"})

    assert attribution.work_item_id_for(run=run) == "bd-ib-owner"
    assert attribution.owns(run=run, work_item_id="bd-ib-owner")
    assert not attribution.owns(run=run, work_item_id="bd-ib-sibling")


def test_a_run_with_no_evidence_at_all_attributes_to_nothing() -> None:
    module = _module()

    attribution = module.run_attribution(metadata_run_ids={"01OTHER": "bd-ib-other"})

    assert attribution.work_item_id_for(run=_row(run_id="01A", work_item_id=None)) is None


def test_journal_run_ids_skips_records_that_name_no_run_or_no_item() -> None:
    module = _module()

    mapped = module.journal_run_ids(
        records=(
            {"work_item_id": "bd-ib-a", "run_id": "01A"},
            {"work_item_id": "bd-ib-b", "run_id": None},
            {"work_item_id": "  ", "run_id": "01BLANK"},
            {"run_id": "01ORPHAN"},
        )
    )

    assert mapped == {"01A": "bd-ib-a"}


def test_newest_journaled_run_id_returns_the_last_run_recorded_for_the_item() -> None:
    module = _module()
    records = (
        {"work_item_id": "bd-ib-a", "run_id": "01FIRST"},
        {"work_item_id": "bd-ib-other", "run_id": "01ELSEWHERE"},
        {"work_item_id": "bd-ib-a", "stage": "ledger-admit"},
        {"work_item_id": "bd-ib-a", "run_id": "01SECOND"},
    )

    assert module.newest_journaled_run_id(records=records, work_item_id="bd-ib-a") == "01SECOND"


def test_newest_journaled_run_id_is_none_for_an_item_the_journal_never_ran() -> None:
    module = _module()

    assert (
        module.newest_journaled_run_id(
            records=({"work_item_id": "bd-ib-other", "run_id": "01X"},),
            work_item_id="bd-ib-a",
        )
        is None
    )
