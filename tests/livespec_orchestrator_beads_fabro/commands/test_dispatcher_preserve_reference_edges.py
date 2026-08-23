"""Edge coverage for Fabro preserve-by-reference comments."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro.commands import _dispatcher_preserve_reference as preserve
from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.errors import WorkItemNotFoundError
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem


@dataclass(kw_only=True)
class _RecordingJournal:
    records: list[dict[str, object]] = field(default_factory=list)

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


@dataclass(kw_only=True)
class _FailingDumpRunner:
    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = argv
        _ = cwd
        _ = timeout_seconds
        _ = env
        _ = stdin
        return CommandResult(exit_code=2, stdout="", stderr="run storage not found")


class _BrokenClient:
    def add_comment(self, *, issue_id: str, body: str) -> None:
        _ = body
        raise WorkItemNotFoundError(item_id=issue_id)


def _broken_client(*, config: StoreConfig) -> _BrokenClient:
    _ = config
    return _BrokenClient()


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="livespec-impl-beads",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _item() -> WorkItem:
    return WorkItem(
        id="bd-ib-preserve-edge",
        type="task",
        status="active",
        title="Preserve failed work",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-23T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )


def _outcome(*, run_id: str | None = "01M0RUN") -> DispatchOutcome:
    return DispatchOutcome(
        work_item_id="bd-ib-preserve-edge",
        status="failed",
        stage="fabro-run",
        pr_number=None,
        merge_sha=None,
        detail="terminal",
        fabro_run_id=run_id,
    )


def _args(*, server: str | None = "https://factory.example.test") -> argparse.Namespace:
    return argparse.Namespace(
        fabro_bin="fabro",
        fabro_factory_target=FactoryTarget(name="hp", server=server, dev_token=None),
    )


def test_missing_run_id_writes_explicit_unavailable_pointer(tmp_path: Path) -> None:
    append_work_item(path=_config(), item=_item())

    preserve.preserve_checkpointed_work_reference(
        args=_args(),
        repo=tmp_path,
        item=_item(),
        outcome=_outcome(run_id=None),
        journal=_RecordingJournal(),
    )

    body = str(make_beads_client(config=_config()).list_comments(issue_id=_item().id)[-1]["text"])
    assert "run id: (unavailable)" in body
    assert "required pointer data was missing" in body
    assert "byte size: (not recorded; pointer incomplete)" in body
    assert "sha256: (not recorded; pointer incomplete)" in body


def test_dump_failure_writes_resolve_failure_comment(tmp_path: Path) -> None:
    append_work_item(path=_config(), item=_item())

    preserve.preserve_checkpointed_work_reference(
        args=_args(),
        repo=tmp_path,
        item=_item(),
        outcome=_outcome(),
        journal=_RecordingJournal(),
        runner=_FailingDumpRunner(),
    )

    body = str(make_beads_client(config=_config()).list_comments(issue_id=_item().id)[-1]["text"])
    assert "artifact: fabro dump failed with exit code 2" in body
    assert "stderr: run storage not found" in body
    assert "byte size: (not recorded; dump failed)" in body
    assert "sha256: (not recorded; dump failed)" in body
    assert "treat the reference as dangling" in body


def test_comment_write_failure_is_journaled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal = _RecordingJournal()
    monkeypatch.setattr(preserve, "make_beads_client", _broken_client)

    preserve.preserve_checkpointed_work_reference(
        args=_args(),
        repo=tmp_path,
        item=_item(),
        outcome=_outcome(run_id=None),
        journal=journal,
    )

    assert journal.records == [
        {
            "stage": "preserve-by-reference-error",
            "work_item_id": _item().id,
            "reason": "WorkItemNotFoundError",
        }
    ]


def test_configured_repo_store_config_is_used(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib"}}}',
        encoding="utf-8",
    )
    monkeypatch.setenv("LIVESPEC_BEADS_FAKE", "1")
    append_work_item(path=_config(), item=_item())

    preserve.preserve_checkpointed_work_reference(
        args=_args(),
        repo=repo,
        item=_item(),
        outcome=_outcome(run_id=None),
        journal=_RecordingJournal(),
    )

    body = str(make_beads_client(config=_config()).list_comments(issue_id=_item().id)[-1]["text"])
    assert "factory server url: https://factory.example.test" in body
