"""Integration-tier acceptance for the loop probe's cycle and consent boundary.

Binds two `SPECIFICATION/scenarios.md` headings through the real
`dispatcher.main(argv=["probe", ...])` CLI and the real store/client seam
against the in-memory `FakeBeadsClient`:

- "Scenario 74 — The probe demonstrates the loop on a taken item and leaves only
  explained state".
- "Scenario 75 — The probe takes; it never files, and absence of evidence never
  passes it".

Only the `ProbeCycle` and the residue sources are stood in — the same seam the
sibling dispatch journeys stand in for `run_dispatch`. Everything the scenarios
actually assert about is production code: the argument parser, the ordering of
the three bracketing refusals, the ledger read, the journal writes, the
confinement verification, the residue grading, and the rendered verdict.

The refusal cases assert the tenant is UNCHANGED as well as what the command
said. "The probe takes; it never files" is a claim about a write that did not
happen, and an exit code cannot carry it — only reading the tenant back can.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._beads_client import (
    FakeBeadsClient,
    make_beads_client,
    reset_fake_singleton,
)
from livespec_orchestrator_beads_fabro.commands import _dispatcher_probe
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import FALLBACK_SOURCE
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
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_residue import (
    ResidueSnapshot,
    ResidueSource,
)
from livespec_orchestrator_beads_fabro.commands.dispatcher import main
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

_ITEM = "bd-ib-probe"
_ARTIFACT = f"{PROBE_DIRECTORY}/latest.md"
_ESCAPING_PATH = "justfile"
_MERGE_COMMIT = "abc1234"
_INVOKER = "operator:probe-integration"
_CRITERIA = "The probe drives the designated item to a terminal done.\n"
_EXIT_PRECONDITION_ERROR = 3
_EXIT_FAILURE = 1


@pytest.fixture(autouse=True)
def _hermetic_fake_backend(monkeypatch: pytest.MonkeyPatch) -> object:
    monkeypatch.setenv("LIVESPEC_BEADS_FAKE", "1")
    monkeypatch.delenv("LIVESPEC_INVOKER", raising=False)
    reset_fake_singleton()
    yield
    reset_fake_singleton()


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
        acceptance_criteria=_CRITERIA,
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
        status: str = "done",
    ) -> None:
        self.calls: list[str] = []
        self.status: str = status
        self.published: ProbePublish = published or ProbePublish(
            branch=f"feat/{_ITEM}", paths=(_ARTIFACT,)
        )
        self.merged: ProbeMerge = merged or ProbeMerge(
            merged=True, merge_commit=_MERGE_COMMIT, merged_paths=(_ARTIFACT,)
        )
        self.observation: ProbeObservation = ProbeObservation(
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
    return (
        _StaticSource(
            snapshots=[
                ResidueSnapshot(source="attention", available=True, identifiers=("impl:bd-other",)),
                ResidueSnapshot(source="attention", available=True),
            ]
        ),
    )


def _unavailable_sources() -> tuple[ResidueSource, ...]:
    return (
        _StaticSource(
            snapshots=[
                ResidueSnapshot(
                    source="attention",
                    available=False,
                    detail="the attention source could not be read",
                )
            ]
        ),
    )


def _install(
    *,
    monkeypatch: pytest.MonkeyPatch,
    cycle: _RecordingCycle,
    sources: tuple[ResidueSource, ...],
) -> None:
    """Stand in the live cycle + residue sources at the production seam."""
    monkeypatch.setattr(
        _dispatcher_probe, "production_cycle", lambda **_kwargs: cycle, raising=True
    )
    monkeypatch.setattr(
        _dispatcher_probe, "production_sources", lambda **_kwargs: sources, raising=True
    )


def _probe_argv(*, repo: Path, journal: Path, item: str | None = _ITEM) -> list[str]:
    argv = ["probe", "--repo", str(repo), "--invoker", _INVOKER, "--journal", str(journal)]
    return argv if item is None else [*argv, "--item", item]


def _journal_records(*, journal: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line]


def test_a_full_probe_cycle_passes_every_stage_and_journals_an_attributed_run(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path=tmp_path)
    journal = tmp_path / "journal.jsonl"
    append_work_item(path=_config(repo_root=repo), item=_item())
    cycle = _RecordingCycle()
    _install(monkeypatch=monkeypatch, cycle=cycle, sources=_clean_sources())

    exit_code = main(argv=_probe_argv(repo=repo, journal=journal))

    assert exit_code == 0
    assert cycle.calls == [f"publish:{_ITEM}", "merge", "observe"]
    start, result = _journal_records(journal=journal)
    probe_run_id = start["probe_run_id"]
    assert isinstance(probe_run_id, str) and _ITEM in probe_run_id
    # Attribution is asserted, not derived: a probe whose records carried the
    # fallback identity would have been refused before this record was written.
    assert start["invoker_source"] != FALLBACK_SOURCE
    assert start["invoker"] == _INVOKER
    assert (result["outcome"], result["probe_run_id"]) == ("pass", probe_run_id)
    # The unrelated before/after delta rides the passing verdict as REPORTED
    # data. An unrelated attention row moving is not the probe's business, and
    # asserting on it would make an unrelated repository make this probe red.
    assert "unrelated" in capsys.readouterr().out


def test_an_escaping_change_fails_the_probe_before_the_merge(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path=tmp_path)
    journal = tmp_path / "journal.jsonl"
    append_work_item(path=_config(repo_root=repo), item=_item())
    cycle = _RecordingCycle(
        published=ProbePublish(branch=f"feat/{_ITEM}", paths=(_ARTIFACT, _ESCAPING_PATH)),
        status="active",
    )
    _install(monkeypatch=monkeypatch, cycle=cycle, sources=_clean_sources())

    exit_code = main(argv=_probe_argv(repo=repo, journal=journal))

    assert exit_code == _EXIT_FAILURE
    # "Fails WITHOUT merging" is the whole clause: the merge stage was never
    # asked for, which the recorded call list is the only witness to.
    assert "merge" not in cycle.calls
    out = capsys.readouterr().out
    assert _ESCAPING_PATH in out
    assert "Remedy: stop; nothing merged." in out
    [_, result] = _journal_records(journal=journal)
    assert result["outcome"] == "confinement-escape"


def test_a_merged_escape_fails_naming_the_commit_and_the_revert_obligation(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path=tmp_path)
    journal = tmp_path / "journal.jsonl"
    append_work_item(path=_config(repo_root=repo), item=_item())
    # The confined publish clears the pre-merge verification, and the escape is
    # only visible in what the disposition actually merged — which is what the
    # post-merge backstop exists for.
    cycle = _RecordingCycle(
        merged=ProbeMerge(
            merged=True, merge_commit=_MERGE_COMMIT, merged_paths=(_ARTIFACT, _ESCAPING_PATH)
        ),
        status="active",
    )
    _install(monkeypatch=monkeypatch, cycle=cycle, sources=_clean_sources())

    exit_code = main(argv=_probe_argv(repo=repo, journal=journal))

    assert exit_code == _EXIT_FAILURE
    assert "merge" in cycle.calls
    out = capsys.readouterr().out
    assert _MERGE_COMMIT in out
    assert "revert" in out
    [_, result] = _journal_records(journal=journal)
    assert result["outcome"] == "merged-escape"


def test_the_probe_refuses_without_a_designated_item_and_files_nothing(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path=tmp_path)
    journal = tmp_path / "journal.jsonl"

    exit_code = main(argv=_probe_argv(repo=repo, journal=journal, item=None))

    assert exit_code == _EXIT_PRECONDITION_ERROR
    assert "--item" in capsys.readouterr().err
    # It took nothing and created nothing: the consent boundary holds, and no
    # journal exists to attribute a probe that never legitimately started.
    assert _fake().list_issues() == []
    assert not journal.exists()


def test_the_probe_refuses_an_item_it_cannot_drive_to_done(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path=tmp_path)
    journal = tmp_path / "journal.jsonl"
    append_work_item(path=_config(repo_root=repo), item=_item(acceptance_policy="human-only"))

    exit_code = main(argv=_probe_argv(repo=repo, journal=journal))

    assert exit_code == _EXIT_PRECONDITION_ERROR
    stderr = capsys.readouterr().err
    assert "human-only" in stderr
    # The refusal names the label to set AT FILING, so the operator's next step
    # is a filing decision rather than a mutation of this item by the probe.
    assert PROBE_ACCEPTANCE_LABEL in stderr
    assert not journal.exists()


def test_an_unavailable_residue_source_fails_the_probe_and_clears_nothing(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path=tmp_path)
    journal = tmp_path / "journal.jsonl"
    append_work_item(path=_config(repo_root=repo), item=_item())
    cycle = _RecordingCycle()
    _install(monkeypatch=monkeypatch, cycle=cycle, sources=_unavailable_sources())

    exit_code = main(argv=_probe_argv(repo=repo, journal=journal))

    assert exit_code == _EXIT_FAILURE
    # Unreadable is not empty: the cycle is not driven at all, so nothing can be
    # reported cleared or resolved off state the probe never read.
    assert cycle.calls == []
    [_, result] = _journal_records(journal=journal)
    assert result["outcome"] == "source-unavailable"
    assert "attention" in capsys.readouterr().out
