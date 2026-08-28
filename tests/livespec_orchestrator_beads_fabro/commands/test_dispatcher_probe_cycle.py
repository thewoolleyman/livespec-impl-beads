"""Tests for the seam the loop probe drives and its production composition (v076).

The `DispatchProbeCycle` group injects both published entry points, so nothing
here reaches the live Dispatcher: the recorder proves the ORDERING the
confinement contract depends on -- `publish` before `merge` -- while staying
entirely inside the hermetic tier.

The journal-reader group leads with its unreadable cases. A reader that
answered "no step outcomes and no verdict" from a journal it could not read
would hand the probe a clean-looking observation built from nothing, so the
absent, undecodable, and non-object shapes are tested before the happy one.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_cycle import (
    ACCEPTANCE_STAGE,
    DispatchProbeCycle,
    ProbePublish,
    changed_paths_argv,
    journal_records,
    merged_paths_argv,
    observed_acceptance,
    observed_step_outcomes,
    parse_paths,
    probe_publish_branch,
)

_ITEM = "bd-ib-probe"


class _ScriptedRunner:
    """A `CommandRunner` returning a queued result and recording every argv."""

    def __init__(self, *, results: list[CommandResult]) -> None:
        self.results: list[CommandResult] = results
        self.argvs: list[list[str]] = []

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env, stdin)
        self.argvs.append(argv)
        return self.results.pop(0)


def _cycle(
    *,
    runner: _ScriptedRunner,
    journal: Path,
    calls: list[str],
    drive_exit: int = 0,
    complete_exit: int = 0,
) -> DispatchProbeCycle:
    def drive(*, args: argparse.Namespace) -> int:
        _ = args
        calls.append("drive")
        return drive_exit

    def complete(*, args: argparse.Namespace) -> int:
        _ = args
        calls.append("complete")
        return complete_exit

    def status_lookup(*, work_item_id: str) -> str:
        calls.append(f"status:{work_item_id}")
        return "done"

    return DispatchProbeCycle(
        args=argparse.Namespace(),
        repo=journal.parent,
        runner=runner,
        journal_path=journal,
        default_branch="master",
        drive=drive,
        complete=complete,
        item_status_lookup=status_lookup,
    )


# --- the pure argv / parsing helpers ----------------------------------------


def test_the_publish_branch_follows_the_repo_convention() -> None:
    assert probe_publish_branch(work_item_id=_ITEM) == f"feat/{_ITEM}"


def test_the_changed_paths_argv_diffs_the_branch_against_the_default() -> None:
    assert changed_paths_argv(default_branch="master", branch="feat/x") == [
        "git",
        "diff",
        "--name-only",
        "origin/master...origin/feat/x",
    ]


def test_the_merged_paths_argv_reads_one_commit() -> None:
    assert merged_paths_argv(merge_commit="abc123") == [
        "git",
        "show",
        "--name-only",
        "--pretty=format:",
        "abc123",
    ]


def test_path_parsing_drops_blank_lines_and_trims() -> None:
    assert parse_paths(stdout="  a.md \n\n b.md\n") == ("a.md", "b.md")


# --- the journal reader: unreadable shapes first ----------------------------


def test_an_absent_journal_yields_no_records(tmp_path: Path) -> None:
    assert journal_records(journal_path=tmp_path / "missing.jsonl") == ()


def test_an_undecodable_journal_yields_no_records(tmp_path: Path) -> None:
    journal = tmp_path / "journal.jsonl"
    _ = journal.write_bytes(b"\xff\xfe not utf-8\n")

    assert journal_records(journal_path=journal) == ()


def test_unparseable_and_non_object_lines_are_skipped(tmp_path: Path) -> None:
    journal = tmp_path / "journal.jsonl"
    _ = journal.write_text('not json\n[1, 2]\n{"stage": "outcome"}\n', encoding="utf-8")

    assert journal_records(journal_path=journal) == ({"stage": "outcome"},)


def test_step_outcomes_are_keyed_on_the_closed_step_vocabulary() -> None:
    records = [
        {"step": "master-ci", "status": "passed"},
        {"step": "not-a-ratified-step", "status": "passed"},
        {"stage": "probe-start"},
    ]

    assert observed_step_outcomes(records=records) == ({"step": "master-ci", "status": "passed"},)


def test_an_unjournaled_acceptance_reads_as_unobserved_rather_than_as_a_pass() -> None:
    verdict, absent = observed_acceptance(records=[{"stage": "probe-start"}])

    assert verdict != "PASS"
    assert absent != ()


def test_the_newest_acceptance_record_wins_and_carries_its_absent_evidence() -> None:
    records = [
        {"stage": ACCEPTANCE_STAGE, "verdict": "FAIL", "absent_evidence": []},
        {"stage": ACCEPTANCE_STAGE, "verdict": "PASS", "absent_evidence": ["telemetry"]},
    ]

    assert observed_acceptance(records=records) == ("PASS", ("telemetry",))


def test_a_malformed_absent_evidence_field_reads_as_no_listed_evidence() -> None:
    records = [{"stage": ACCEPTANCE_STAGE, "verdict": "PASS", "absent_evidence": "telemetry"}]

    assert observed_acceptance(records=records) == ("PASS", ())


# --- the production cycle: ordering, never the live Dispatcher ---------------


def test_publish_drives_the_dispatch_then_reads_the_branch_paths(tmp_path: Path) -> None:
    runner = _ScriptedRunner(
        results=[CommandResult(exit_code=0, stdout=".livespec-probe/latest.md\n", stderr="")]
    )
    calls: list[str] = []
    cycle = _cycle(runner=runner, journal=tmp_path / "j.jsonl", calls=calls)

    published = cycle.publish(work_item_id=_ITEM)

    assert calls == ["drive"]
    assert published.branch == f"feat/{_ITEM}"
    assert published.paths == (".livespec-probe/latest.md",)
    assert published.readable
    assert runner.argvs == [changed_paths_argv(default_branch="master", branch=f"feat/{_ITEM}")]


def test_an_unreadable_diff_publishes_as_unreadable_not_as_an_empty_change(
    tmp_path: Path,
) -> None:
    runner = _ScriptedRunner(
        results=[CommandResult(exit_code=128, stdout="", stderr="bad revision")]
    )
    cycle = _cycle(runner=runner, journal=tmp_path / "j.jsonl", calls=[])

    published = cycle.publish(work_item_id=_ITEM)

    assert not published.readable
    assert published.paths == ()
    assert "bad revision" in published.detail


def test_merge_completes_the_disposition_and_carries_the_verified_paths(
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    cycle = _cycle(runner=_ScriptedRunner(results=[]), journal=tmp_path / "j.jsonl", calls=calls)
    published = ProbePublish(
        branch=f"feat/{_ITEM}", paths=(".livespec-probe/latest.md",), merge_commit="abc123"
    )

    merged = cycle.merge(published=published)

    assert calls == ["complete"]
    assert merged.merged
    assert merged.merge_commit == "abc123"
    assert merged.merged_paths == (".livespec-probe/latest.md",)


def test_a_failing_disposition_reports_unmerged_with_its_exit_code(tmp_path: Path) -> None:
    cycle = _cycle(
        runner=_ScriptedRunner(results=[]),
        journal=tmp_path / "j.jsonl",
        calls=[],
        complete_exit=3,
    )

    merged = cycle.merge(published=ProbePublish(branch="feat/x", paths=()))

    assert not merged.merged
    assert "3" in merged.detail


def test_observe_reads_the_journal_and_the_item_status(tmp_path: Path) -> None:
    journal = tmp_path / "j.jsonl"
    _ = journal.write_text(
        '{"step": "master-ci", "status": "passed"}\n'
        '{"stage": "acceptance-ai-pass", "verdict": "PASS", "absent_evidence": []}\n',
        encoding="utf-8",
    )
    calls: list[str] = []
    cycle = _cycle(runner=_ScriptedRunner(results=[]), journal=journal, calls=calls)

    observation = cycle.observe(work_item_id=_ITEM)

    assert observation.step_outcomes == ({"step": "master-ci", "status": "passed"},)
    assert observation.verdict == "PASS"
    assert observation.absent_evidence == ()
    assert observation.item_status == "done"
    assert calls == [f"status:{_ITEM}"]


def test_item_status_reads_the_lookup_seam_directly(tmp_path: Path) -> None:
    calls: list[str] = []
    cycle = _cycle(runner=_ScriptedRunner(results=[]), journal=tmp_path / "j.jsonl", calls=calls)

    assert cycle.item_status(work_item_id=_ITEM) == "done"
    assert calls == [f"status:{_ITEM}"]
