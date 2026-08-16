"""Tests for the standalone stale Fabro run sweep."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.types import WorkItem


@dataclass(kw_only=True)
class _RecordingRunner:
    ps_json: str
    calls: list[list[str]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env)
        self.calls.append(argv)
        if argv[1] == "ps":
            return CommandResult(exit_code=0, stdout=self.ps_json, stderr="")
        if argv[1] == "rm":
            return CommandResult(exit_code=0, stdout="", stderr="")
        return CommandResult(exit_code=1, stdout="", stderr=f"unexpected argv: {argv!r}")


def test_standalone_sweep_reaps_orphaned_closed_item_runs(tmp_path: Path) -> None:
    module_path = (
        Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
        / "_dispatcher_stale_run_sweep.py"
    )
    assert module_path.is_file()
    module = importlib.import_module(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_stale_run_sweep"
    )
    runner = _RecordingRunner(
        ps_json=json.dumps(
            [
                {
                    "run_id": "01CLOSEDQUEUED",
                    "goal": "Work-item: bd-ib-closed\nRepo: /tmp/repo",
                    "status": {"kind": "runnable"},
                },
                {
                    "run_id": "01CLOSEDRUNNING",
                    "goal": "Work-item: bd-ib-running\nRepo: /tmp/repo",
                    "status": "running",
                },
                {
                    "run_id": "01ACTIVE",
                    "goal": "Work-item: bd-ib-active\nRepo: /tmp/repo",
                    "status": "running",
                },
            ]
        )
    )
    items = [
        _item(id="bd-ib-closed", status="done"),
        _item(id="bd-ib-running", status="closed"),
        _item(id="bd-ib-active", status="active"),
    ]

    summary = module.reap_stale_fabro_runs(
        repo=tmp_path,
        runner=runner,
        items=items,
        fabro_bin="fabro",
        fabro_factory_server=None,
    )

    rm_calls = [call for call in runner.calls if call[1] == "rm"]
    assert rm_calls == [
        ["fabro", "rm", "-f", "01CLOSEDQUEUED"],
        ["fabro", "rm", "-f", "01CLOSEDRUNNING"],
    ]
    assert [(run.work_item_id, run.run_id, run.item_status) for run in summary.reaped] == [
        ("bd-ib-closed", "01CLOSEDQUEUED", "done"),
        ("bd-ib-running", "01CLOSEDRUNNING", "closed"),
    ]


def _item(*, id: str, status: str) -> WorkItem:
    return WorkItem(
        id=id,
        type="task",
        status=status,
        title=id,
        description=id,
        origin="freeform",
        gap_id=None,
        rank="a0",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-16T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )
