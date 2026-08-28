"""Tests for the loop probe's production composition (v076).

Every read seam is injected here, so the suite exercises the composition without
reaching the live Dispatcher. The two residue-source groups each lead with the
FAILING read, because "unavailable, loudly" is the behaviour that distinguishes
this wiring from one that would hand the probe a manufactured clean snapshot.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_wiring import (
    ATTENTION_SOURCE,
    DEFAULT_BRANCH_FALLBACK,
    LEDGER_SOURCE,
    AttentionResidueSource,
    LedgerResidueSource,
    item_status_of,
    production_cycle,
    production_sources,
    resolve_default_branch,
)
from livespec_orchestrator_beads_fabro.errors import BeadsConnectionError
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem
from livespec_runtime.attention_item import AttentionItem, Handoff, SourceRef

_ITEM = "bd-ib-probe"


class _ScriptedRunner:
    """A `CommandRunner` returning one queued result per call."""

    def __init__(self, *, results: list[CommandResult]) -> None:
        self.results: list[CommandResult] = results

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (argv, cwd, timeout_seconds, env, stdin)
        return self.results.pop(0)


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


def _item(*, status: str = "ready") -> WorkItem:
    return WorkItem(
        id=_ITEM,
        type="task",
        status=status,
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
    )


def _repo(*, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib",'
        ' "fake": true}}}',
        encoding="utf-8",
    )
    return repo


def _attention(*, name: str) -> AttentionItem:
    return AttentionItem(
        id=name,
        kind="impl",
        urgency="medium",
        summary="something",
        source_ref=SourceRef(repo="repo"),
        handoff=Handoff(kind="drive", command="drive"),
    )


# --- the attention source ---------------------------------------------------


def test_an_unreadable_attention_surface_snapshots_as_unavailable(tmp_path: Path) -> None:
    def boom(*, project_root: Path, repo_name: str) -> Sequence[AttentionItem]:
        _ = (project_root, repo_name)
        raise BeadsConnectionError(detail="tenant unreachable")

    snapshot = AttentionResidueSource(repo=tmp_path, read=boom).snapshot()

    assert not snapshot.available
    assert snapshot.source == ATTENTION_SOURCE
    assert "tenant unreachable" in snapshot.detail


def test_a_readable_attention_surface_snapshots_its_identifiers(tmp_path: Path) -> None:
    def read(*, project_root: Path, repo_name: str) -> Sequence[AttentionItem]:
        _ = (project_root, repo_name)
        return [_attention(name="impl:bd-ib-one"), _attention(name="impl:bd-ib-two")]

    snapshot = AttentionResidueSource(repo=tmp_path, read=read).snapshot()

    assert snapshot.available
    assert snapshot.identifiers == ("impl:bd-ib-one", "impl:bd-ib-two")


# --- the ledger source ------------------------------------------------------


def test_an_unreadable_ledger_snapshots_as_unavailable(tmp_path: Path) -> None:
    def boom(*, repo: Path) -> Sequence[WorkItem]:
        _ = repo
        raise BeadsConnectionError(detail="tenant unreachable")

    snapshot = LedgerResidueSource(repo=tmp_path, read=boom).snapshot()

    assert not snapshot.available
    assert snapshot.source == LEDGER_SOURCE


def test_the_ledger_snapshot_carries_live_rows_and_drops_settled_ones(tmp_path: Path) -> None:
    def read(*, repo: Path) -> Sequence[WorkItem]:
        _ = repo
        return [_item(status="ready"), _item(status="done")]

    snapshot = LedgerResidueSource(repo=tmp_path, read=read).snapshot()

    assert snapshot.available
    assert snapshot.identifiers == (_ITEM,)


def test_the_production_sources_are_the_attention_surface_and_the_ledger(
    tmp_path: Path,
) -> None:
    sources = production_sources(repo=tmp_path)

    assert [type(one).__name__ for one in sources] == [
        "AttentionResidueSource",
        "LedgerResidueSource",
    ]


# --- the item-status read and the default-branch read -----------------------


def test_item_status_of_reads_the_designated_item_from_the_tenant(tmp_path: Path) -> None:
    repo = _repo(tmp_path=tmp_path)
    append_work_item(path=_config(repo_root=repo), item=_item(status="acceptance"))

    assert item_status_of(repo=repo, work_item_id=_ITEM) == "acceptance"


def test_an_item_absent_from_the_tenant_reports_an_explicit_absence(tmp_path: Path) -> None:
    repo = _repo(tmp_path=tmp_path)

    assert "absent" in item_status_of(repo=repo, work_item_id="bd-ib-nothing")


def test_the_default_branch_is_read_from_the_remote_head(tmp_path: Path) -> None:
    runner = _ScriptedRunner(
        results=[CommandResult(exit_code=0, stdout="origin/main\n", stderr="")]
    )

    assert resolve_default_branch(repo=tmp_path, runner=runner) == "main"


def test_an_unset_remote_head_falls_back_to_the_family_default(tmp_path: Path) -> None:
    runner = _ScriptedRunner(results=[CommandResult(exit_code=128, stdout="", stderr="no HEAD")])

    assert resolve_default_branch(repo=tmp_path, runner=runner) == DEFAULT_BRANCH_FALLBACK


def test_an_empty_remote_head_falls_back_to_the_family_default(tmp_path: Path) -> None:
    runner = _ScriptedRunner(results=[CommandResult(exit_code=0, stdout="\n", stderr="")])

    assert resolve_default_branch(repo=tmp_path, runner=runner) == DEFAULT_BRANCH_FALLBACK


# --- the production cycle ---------------------------------------------------


def test_the_production_cycle_wires_the_published_surfaces_and_the_status_read(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path=tmp_path)
    append_work_item(path=_config(repo_root=repo), item=_item(status="active"))
    args = argparse.Namespace(journal=str(tmp_path / "j.jsonl"))

    cycle = production_cycle(args=args, repo=repo)

    assert cycle.default_branch == DEFAULT_BRANCH_FALLBACK
    assert cycle.item_status(work_item_id=_ITEM) == "active"
