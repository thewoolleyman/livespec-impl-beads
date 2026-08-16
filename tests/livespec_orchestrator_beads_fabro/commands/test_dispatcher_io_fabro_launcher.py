"""Tests for the Fabro launcher IO extraction."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands import (
    _dispatcher_io,
    _dispatcher_io_fabro_launcher,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_io_fabro_launcher import (
    WatchedFabroLauncher,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import build_plan
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem


@dataclass(kw_only=True)
class _QueuedRunner:
    calls: list[str]
    rm_calls: list[str]
    reaped: bool = False

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env)
        command = argv[1]
        self.calls.append(command)
        if command == "ps":
            return CommandResult(
                exit_code=0,
                stdout=(
                    '[{"run_id": "01QUEUED", '
                    '"status": {"kind": "runnable"}, '
                    '"goal": "Work-item: bd-ib-queued\\nRepo: /tmp/repo"}]'
                ),
                stderr="",
            )
        if command == "rm":
            self.rm_calls.append(argv[3])
            self.reaped = True
            return CommandResult(exit_code=0, stdout="", stderr="")
        return CommandResult(exit_code=0, stdout="Run: 01QUEUED\n", stderr="")


@dataclass(kw_only=True)
class _QueuedThread:
    target: Callable[[], None]
    name: str
    runner: _QueuedRunner
    daemon: bool = False
    alive_checks: int = 0

    def start(self) -> None:
        pass

    def is_alive(self) -> bool:
        self.alive_checks += 1
        return not self.runner.reaped and self.alive_checks < 3

    def join(self, timeout: float | None = None) -> None:
        _ = timeout
        if "run" not in self.runner.calls:
            self.target()


@dataclass(kw_only=True)
class _Journal:
    records: list[dict[str, object]]

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


def test_watched_launcher_remains_the_dispatcher_io_public_entry_point() -> None:
    assert _dispatcher_io.WatchedFabroLauncher is WatchedFabroLauncher


def test_watched_launcher_covers_finished_thread_watch_path(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    @dataclass(kw_only=True)
    class _SynchronousThread:
        target: Callable[[], None]
        name: str
        daemon: bool = False

        def start(self) -> None:
            self.target()

        def is_alive(self) -> bool:
            return False

        def join(self, timeout: float | None = None) -> None:
            _ = timeout

    @dataclass(kw_only=True)
    class _Runner:
        def run(
            self,
            *,
            argv: list[str],
            cwd: Path,
            timeout_seconds: float,
        ) -> CommandResult:
            _ = (argv, cwd, timeout_seconds)
            return CommandResult(exit_code=0, stdout="done", stderr="")

    def _thread(*, target: Callable[[], None], name: str) -> _SynchronousThread:
        return _SynchronousThread(target=target, name=name)

    monkeypatch.setattr(_dispatcher_io_fabro_launcher.threading, "Thread", _thread)
    plan = build_plan(
        repo=tmp_path,
        work_item_id="bd-ib-fcipkv",
        workflow_toml=tmp_path / "workflow.toml",
        goal_file=tmp_path / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=tmp_path / "janitor",
    )

    result = WatchedFabroLauncher(sleep=lambda _seconds: None, clock=lambda: 0.0).launch(
        plan=plan,
        runner=_Runner(),
        journal=object(),  # type: ignore[arg-type]
    )

    assert result.command.exit_code == 0
    assert result.command.stdout == "done"
    assert result.stalled_run_id is None


def test_queued_thread_join_skips_target_after_run_returns() -> None:
    calls: list[str] = []
    runner = _QueuedRunner(calls=["run"], rm_calls=[])
    thread = _QueuedThread(
        target=lambda: calls.append("target"),
        name="fabro-run-bd-ib-queued",
        runner=runner,
    )

    thread.join()

    assert calls == []


def test_watched_launcher_reaps_queued_run_after_item_closes(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def _thread(*, target: Callable[[], None], name: str) -> _QueuedThread:
        return _QueuedThread(target=target, name=name, runner=runner)

    def _done_items(*, path: StoreConfig) -> list[WorkItem]:
        _ = path
        return [
            WorkItem(
                id="bd-ib-queued",
                type="task",
                status="done",
                title="done",
                description="done",
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
        ]

    runner = _QueuedRunner(calls=[], rm_calls=[])
    journal = _Journal(records=[])
    monkeypatch.setattr(_dispatcher_io_fabro_launcher.threading, "Thread", _thread)
    monkeypatch.setattr(
        _dispatcher_io_fabro_launcher, "read_work_items", _done_items, raising=False
    )
    plan = build_plan(
        repo=tmp_path,
        work_item_id="bd-ib-queued",
        workflow_toml=tmp_path / "workflow.toml",
        goal_file=tmp_path / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=tmp_path / "janitor",
    )

    result = WatchedFabroLauncher(sleep=lambda _seconds: None, clock=lambda: 0.0).launch(
        plan=plan,
        runner=runner,
        journal=journal,
    )

    assert runner.rm_calls == ["01QUEUED"]
    assert result.abandoned_run_id == "01QUEUED"
    assert result.abandoned_item_status == "done"
    assert journal.records == [
        {
            "work_item_id": "bd-ib-queued",
            "stage": "stale-run-reap",
            "run_id": "01QUEUED",
            "item_status": "done",
            "rm_exit_code": 0,
        }
    ]
