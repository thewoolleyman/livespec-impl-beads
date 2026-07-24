"""Tests for dispatcher process-start liveness helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands import _dispatcher_pid_liveness as liveness


def _proc_stat(*, started_ticks: str = "1234") -> str:
    fields = ["S", *("0" for _ in range(18)), started_ticks]
    return f"123 (dispatcher process) {' '.join(fields)}"


def test_process_started_at_epoch_combines_boot_time_and_ticks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    proc = tmp_path / "proc"
    pid_dir = proc / "42"
    pid_dir.mkdir(parents=True)
    (pid_dir / "stat").write_text(_proc_stat(started_ticks="250"), encoding="utf-8")
    (proc / "stat").write_text("cpu 0 0 0 0\nbtime 1000\n", encoding="utf-8")

    def fake_sysconf(*args: object) -> int:
        assert args == ("SC_CLK_TCK",)
        return 100

    def map_proc_path(*args: object) -> Path:
        assert len(args) == 1
        raw = args[0]
        assert isinstance(raw, str)
        return proc / raw.removeprefix("/proc/")

    monkeypatch.setattr(liveness, "Path", map_proc_path)
    monkeypatch.setattr(liveness.os, "sysconf", fake_sysconf)

    assert liveness.process_started_at_epoch(pid=42) == 1002.5


def test_process_started_at_epoch_returns_none_when_proc_pid_stat_is_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def map_proc_path(*args: object) -> Path:
        assert len(args) == 1
        raw = args[0]
        assert isinstance(raw, str)
        return tmp_path / raw.removeprefix("/proc/")

    monkeypatch.setattr(liveness, "Path", map_proc_path)

    assert liveness.process_started_at_epoch(pid=42) is None


@pytest.mark.parametrize(
    "stat_text",
    [
        "missing process name terminator",
        "123 (cmd) S 0",
        _proc_stat(started_ticks="not-digits"),
    ],
)
def test_linux_proc_started_ticks_rejects_malformed_stat(stat_text: str) -> None:
    assert liveness.linux_proc_started_ticks(stat_text=stat_text) is None


def test_linux_proc_started_ticks_extracts_field_twenty_two() -> None:
    assert liveness.linux_proc_started_ticks(stat_text=_proc_stat(started_ticks="5678")) == 5678


def test_linux_booted_at_epoch_returns_none_when_proc_stat_is_unreadable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def map_proc_stat(*args: object) -> Path:
        assert len(args) == 1
        return tmp_path / "missing-stat"

    monkeypatch.setattr(liveness, "Path", map_proc_stat)

    assert liveness.linux_booted_at_epoch() is None


def test_linux_booted_at_epoch_returns_none_without_btime(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    proc_stat = tmp_path / "stat"
    proc_stat.write_text("cpu 0 0 0 0\n", encoding="utf-8")

    def map_proc_stat(*args: object) -> Path:
        assert len(args) == 1
        return proc_stat

    monkeypatch.setattr(liveness, "Path", map_proc_stat)

    assert liveness.linux_booted_at_epoch() is None


def test_clock_ticks_per_second_returns_none_when_sysconf_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_sysconf(*args: object) -> int:
        assert args == ("SC_CLK_TCK",)
        raise ValueError("unknown")

    monkeypatch.setattr(liveness.os, "sysconf", failing_sysconf)

    assert liveness.clock_ticks_per_second() is None


def test_clock_ticks_per_second_rejects_non_positive_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def zero_sysconf(*args: object) -> int:
        assert args == ("SC_CLK_TCK",)
        return 0

    monkeypatch.setattr(liveness.os, "sysconf", zero_sysconf)

    assert liveness.clock_ticks_per_second() is None


def test_process_started_at_epoch_returns_none_without_clock_ticks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    proc = tmp_path / "proc"
    pid_dir = proc / "42"
    pid_dir.mkdir(parents=True)
    (pid_dir / "stat").write_text(_proc_stat(), encoding="utf-8")
    (proc / "stat").write_text("btime 1000\n", encoding="utf-8")

    def map_proc_path(*args: object) -> Path:
        assert len(args) == 1
        raw = args[0]
        assert isinstance(raw, str)
        return proc / raw.removeprefix("/proc/")

    monkeypatch.setattr(liveness, "Path", map_proc_path)

    def zero_sysconf(*args: object) -> int:
        assert args == ("SC_CLK_TCK",)
        return 0

    monkeypatch.setattr(liveness.os, "sysconf", zero_sysconf)

    assert liveness.process_started_at_epoch(pid=42) is None
