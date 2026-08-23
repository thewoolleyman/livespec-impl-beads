"""Tests for failed/blocked Fabro run preserve-by-reference comments."""

from __future__ import annotations

import argparse
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem


@dataclass(kw_only=True)
class _RecordingJournal:
    records: list[dict[str, object]] = field(default_factory=list)

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


@dataclass(kw_only=True)
class _DumpRunner:
    export_diff: bool
    calls: list[list[str]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = cwd
        _ = timeout_seconds
        _ = env
        _ = stdin
        self.calls.append(argv)
        output_dir = Path(argv[argv.index("-o") + 1])
        if self.export_diff:
            diff = output_dir / "stages" / "002-implement@1" / "diff.patch"
            diff.parent.mkdir(parents=True)
            _ = diff.write_text("diff --git a/app.py b/app.py\n+print('kept')\n", encoding="utf-8")
        return CommandResult(exit_code=0, stdout="", stderr="")


def _module() -> ModuleType:
    module_path = (
        Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
        / "_dispatcher_preserve_reference.py"
    )
    assert module_path.is_file()
    return importlib.import_module(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_preserve_reference"
    )


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
        id="bd-ib-preserve",
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


def _outcome(*, status: str) -> DispatchOutcome:
    return DispatchOutcome(
        work_item_id="bd-ib-preserve",
        status=status,
        stage="fabro-run",
        pr_number=None,
        merge_sha=None,
        detail="terminal",
        fabro_run_id="01M0RUN",
    )


def _args() -> argparse.Namespace:
    return argparse.Namespace(
        fabro_bin="fabro",
        fabro_factory_target=FactoryTarget(
            name="hp",
            server="https://hp-xubuntu.perch-rudd.ts.net:32276",
            dev_token=None,
        ),
    )


def test_failed_run_comment_records_resolvable_diff_pointer(tmp_path: Path) -> None:
    module = _module()
    append_work_item(path=_config(), item=_item())
    journal = _RecordingJournal()
    runner = _DumpRunner(export_diff=True)

    module.preserve_checkpointed_work_reference(
        args=_args(),
        repo=tmp_path,
        item=_item(),
        outcome=_outcome(status="failed"),
        journal=journal,
        runner=runner,
    )

    comments = make_beads_client(config=_config()).list_comments(issue_id="bd-ib-preserve")
    body = str(comments[-1]["text"])
    assert "livespec-preserve-by-reference" in body
    assert "run id: 01M0RUN" in body
    assert "factory server url: https://hp-xubuntu.perch-rudd.ts.net:32276" in body
    assert "stage artifact path: stages/002-implement@1/diff.patch" in body
    assert "byte size: 44" in body
    assert "sha256:" in body
    assert "recorded sha256 is the integrity check" in body
    assert "normalized diff payload byte size" not in body
    assert "fabro dump 01M0RUN --server https://hp-xubuntu.perch-rudd.ts.net:32276 -o" in body
    assert runner.calls[0][:5] == [
        "fabro",
        "dump",
        "01M0RUN",
        "--server",
        "https://hp-xubuntu.perch-rudd.ts.net:32276",
    ]
    assert journal.records[-1]["stage"] == "preserve-by-reference"


def test_blocked_run_comment_is_honest_when_no_diff_was_produced(tmp_path: Path) -> None:
    module = _module()
    append_work_item(path=_config(), item=_item())
    journal = _RecordingJournal()

    module.preserve_checkpointed_work_reference(
        args=_args(),
        repo=tmp_path,
        item=_item(),
        outcome=_outcome(status="blocked"),
        journal=journal,
        runner=_DumpRunner(export_diff=False),
    )

    comments = make_beads_client(config=_config()).list_comments(issue_id="bd-ib-preserve")
    body = str(comments[-1]["text"])
    assert "livespec-preserve-by-reference" in body
    assert "run produced no checkpointed diff artifact" in body
    assert "stage artifact path: stages/002-implement@1/diff.patch (missing)" in body
    assert "byte size: (not recorded; artifact missing)" in body
    assert "sha256: (not recorded; artifact missing)" in body
    assert journal.records[-1]["artifact_present"] is False


def test_green_run_adds_no_preserve_comment(tmp_path: Path) -> None:
    module = _module()
    append_work_item(path=_config(), item=_item())
    runner = _DumpRunner(export_diff=True)

    module.preserve_checkpointed_work_reference(
        args=_args(),
        repo=tmp_path,
        item=_item(),
        outcome=_outcome(status="green"),
        journal=_RecordingJournal(),
        runner=runner,
    )

    assert runner.calls == []
    assert make_beads_client(config=_config()).list_comments(issue_id="bd-ib-preserve") == []
