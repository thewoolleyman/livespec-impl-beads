"""Tests for the `probe --item` entry point (v076).

EVERY case runs against `FakeBeadsClient` through the `hermetic_fake_backend`
fixture and an injected cycle; nothing here reaches the live Dispatcher, which
is exactly what the last case pins down -- the production fall-back is
monkeypatched rather than exercised, so the default composition is covered
without a dispatch ever being launched.

The refusal cases assert what the command did NOT do as well as what it said:
an empty tenant after a refusal is the observable form of "the probe takes; it
never files".
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._beads_client import FakeBeadsClient, make_beads_client
from livespec_orchestrator_beads_fabro.commands import _dispatcher_probe
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import FALLBACK_SOURCE
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe import run_probe_command
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_confinement import (
    PROBE_DIRECTORY,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_cycle import (
    ProbeMerge,
    ProbeObservation,
    ProbePublish,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_refusals import (
    PROBE_ACCEPTANCE_LABEL,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_report import (
    CONFINEMENT_ESCAPE_OUTCOME,
    PASSED_OUTCOME,
    PROBE_START_STAGE,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_residue import (
    ResidueSnapshot,
    ResidueSource,
)
from livespec_orchestrator_beads_fabro.commands.dispatcher import main
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

_ITEM = "bd-ib-probe"
_ARTIFACT = f"{PROBE_DIRECTORY}/latest.md"
_TWO_ASSERTIONS = "The probe refuses without an item.\nThe probe never files one.\n"
_EXIT_PRECONDITION_ERROR = 3
_EXIT_FAILURE = 1
_INVOKER = "operator:probe-test"


def _config(*, repo_root: Path | None = None) -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd-ib",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
        repo_root=repo_root,
    )


def _item(**overrides: object) -> WorkItem:
    base = WorkItem(
        id=_ITEM,
        type="task",
        status="ready",
        title="A probe fixture",
        description="Drive the loop.",
        origin="freeform",
        gap_id=None,
        rank="a2",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-28T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy="ai-only",
        acceptance_criteria=_TWO_ASSERTIONS,
    )
    return replace(base, **overrides)


def _repo(*, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib",'
        ' "fake": true}}}',
        encoding="utf-8",
    )
    return repo


def _fake() -> FakeBeadsClient:
    client = make_beads_client(config=_config())
    assert isinstance(client, FakeBeadsClient)
    return client


class _StaticSource:
    """A residue source answering with one fixed snapshot per call."""

    def __init__(self, *, snapshots: list[ResidueSnapshot]) -> None:
        self.snapshots: list[ResidueSnapshot] = snapshots

    def snapshot(self) -> ResidueSnapshot:
        return self.snapshots.pop(0) if len(self.snapshots) > 1 else self.snapshots[0]


class _RecordingCycle:
    """A `ProbeCycle` recording which stages the probe actually asked it for."""

    def __init__(
        self,
        *,
        published: ProbePublish | None = None,
        merged: ProbeMerge | None = None,
        observation: ProbeObservation | None = None,
        status: str = "done",
    ) -> None:
        self.calls: list[str] = []
        self.status: str = status
        self.published: ProbePublish = published or ProbePublish(
            branch=f"feat/{_ITEM}", paths=(_ARTIFACT,)
        )
        self.merged: ProbeMerge = merged or ProbeMerge(
            merged=True, merge_commit="abc1234", merged_paths=(_ARTIFACT,)
        )
        self.observation: ProbeObservation = observation or ProbeObservation(
            step_outcomes=({"step": "master-ci", "status": "passed"},),
            verdict="PASS",
            absent_evidence=(),
            item_status=status,
        )

    def publish(self, *, work_item_id: str) -> ProbePublish:
        self.calls.append(f"publish:{work_item_id}")
        return self.published

    def merge(self, *, published: ProbePublish) -> ProbeMerge:
        _ = published
        self.calls.append("merge")
        return self.merged

    def observe(self, *, work_item_id: str) -> ProbeObservation:
        _ = work_item_id
        self.calls.append("observe")
        return self.observation

    def item_status(self, *, work_item_id: str) -> str:
        _ = work_item_id
        return self.status


def _clean_sources() -> tuple[ResidueSource, ...]:
    return (_StaticSource(snapshots=[ResidueSnapshot(source="attention", available=True)]),)


# --- the CLI surface --------------------------------------------------------


def _args(*, repo: Path, tmp_path: Path, item: str | None = _ITEM) -> argparse.Namespace:
    return argparse.Namespace(
        repo=str(repo),
        item=item,
        invoker=_INVOKER,
        journal=str(tmp_path / "journal.jsonl"),
        as_json=False,
    )


def test_the_subcommand_refuses_without_an_item_and_files_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path=tmp_path)

    exit_code = run_probe_command(args=_args(repo=repo, tmp_path=tmp_path, item=None))

    assert exit_code == _EXIT_PRECONDITION_ERROR
    assert "--item" in capsys.readouterr().err
    assert _fake().list_issues() == []


def test_the_subcommand_refuses_an_unattributed_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path=tmp_path)
    monkeypatch.delenv("LIVESPEC_INVOKER", raising=False)
    args = _args(repo=repo, tmp_path=tmp_path)
    args.invoker = None

    exit_code = run_probe_command(args=args)

    assert exit_code == _EXIT_PRECONDITION_ERROR
    assert "unattributed" in capsys.readouterr().err


def test_the_subcommand_refuses_an_item_absent_from_the_tenant(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path=tmp_path)

    exit_code = run_probe_command(args=_args(repo=repo, tmp_path=tmp_path))

    assert exit_code == _EXIT_PRECONDITION_ERROR
    assert "not in the tenant" in capsys.readouterr().err


def test_the_subcommand_refuses_a_non_ai_only_designated_item(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path=tmp_path)
    append_work_item(path=_config(repo_root=repo), item=_item(acceptance_policy="human-only"))

    exit_code = run_probe_command(args=_args(repo=repo, tmp_path=tmp_path))

    assert exit_code == _EXIT_PRECONDITION_ERROR
    assert PROBE_ACCEPTANCE_LABEL in capsys.readouterr().err


def test_a_passing_probe_journals_its_run_identifier_with_a_non_fallback_invoker(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path=tmp_path)
    append_work_item(path=_config(repo_root=repo), item=_item())
    args = _args(repo=repo, tmp_path=tmp_path)

    exit_code = run_probe_command(args=args, cycle=_RecordingCycle(), sources=_clean_sources())

    assert exit_code == 0
    records = [
        json.loads(line) for line in Path(args.journal).read_text(encoding="utf-8").splitlines()
    ]
    start = records[0]
    assert start["stage"] == PROBE_START_STAGE
    assert start["probe_run_id"].startswith(f"probe:{_ITEM}:")
    assert start["invoker"] == _INVOKER
    assert start["invoker_source"] != FALLBACK_SOURCE
    assert records[-1]["outcome"] == PASSED_OUTCOME
    assert PASSED_OUTCOME in capsys.readouterr().out


def test_a_failing_probe_reports_the_stage_the_state_and_the_remedy_as_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path=tmp_path)
    append_work_item(path=_config(repo_root=repo), item=_item())
    args = _args(repo=repo, tmp_path=tmp_path)
    args.as_json = True
    cycle = _RecordingCycle(
        published=ProbePublish(branch=f"feat/{_ITEM}", paths=("justfile",)), status="active"
    )

    exit_code = run_probe_command(args=args, cycle=cycle, sources=_clean_sources())

    assert exit_code == _EXIT_FAILURE
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == CONFINEMENT_ESCAPE_OUTCOME
    assert payload["item_status"] == "active"
    assert "nothing merged" in payload["remedy"]


def test_the_human_rendering_reports_the_remedy_and_the_unrelated_delta(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path=tmp_path)
    append_work_item(path=_config(repo_root=repo), item=_item())
    source = _StaticSource(
        snapshots=[
            ResidueSnapshot(source="attention", available=True),
            ResidueSnapshot(source="attention", available=True, identifiers=("valve:other:b",)),
        ]
    )

    exit_code = run_probe_command(
        args=_args(repo=repo, tmp_path=tmp_path), cycle=_RecordingCycle(), sources=(source,)
    )

    assert exit_code == 0
    assert "unrelated (reported, not asserted): appeared" in capsys.readouterr().out


def test_the_human_rendering_of_a_failure_names_the_remedy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path=tmp_path)
    append_work_item(path=_config(repo_root=repo), item=_item())
    cycle = _RecordingCycle(
        published=ProbePublish(branch=f"feat/{_ITEM}", paths=("justfile",)), status="active"
    )

    exit_code = run_probe_command(
        args=_args(repo=repo, tmp_path=tmp_path), cycle=cycle, sources=_clean_sources()
    )

    assert exit_code == _EXIT_FAILURE
    out = capsys.readouterr().out
    assert "item_status=active" in out
    assert "Remedy: stop; nothing merged." in out


def test_the_subcommand_falls_back_to_the_production_cycle_and_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path=tmp_path)
    append_work_item(path=_config(repo_root=repo), item=_item())
    cycle = _RecordingCycle()

    def fake_cycle(*, args: argparse.Namespace, repo: Path) -> _RecordingCycle:
        _ = (args, repo)
        return cycle

    def fake_sources(*, repo: Path) -> tuple[ResidueSource, ...]:
        _ = repo
        return _clean_sources()

    monkeypatch.setattr(_dispatcher_probe, "production_cycle", fake_cycle)
    monkeypatch.setattr(_dispatcher_probe, "production_sources", fake_sources)

    assert run_probe_command(args=_args(repo=repo, tmp_path=tmp_path)) == 0
    assert cycle.calls == [f"publish:{_ITEM}", "merge", "observe"]


def test_the_parser_registers_probe_as_a_dispatcher_subcommand(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path=tmp_path)

    exit_code = main(argv=["probe", "--repo", str(repo), "--invoker", _INVOKER])

    assert exit_code == _EXIT_PRECONDITION_ERROR
    assert "--item" in capsys.readouterr().err
