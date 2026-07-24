"""Process liveness helpers for dispatcher host lock payloads."""

from __future__ import annotations

import os
from pathlib import Path

from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt

__all__: list[str] = [
    "clock_ticks_per_second",
    "linux_booted_at_epoch",
    "linux_proc_started_ticks",
    "process_started_at_epoch",
]

_PROC_STAT_SPLIT_PARTS = 2
_PROC_STAT_FIELDS_AFTER_NAME = 20
_PROC_STAT_START_TICKS_INDEX = 19
_PROC_STAT_KEY_VALUE_FIELDS = 2


def process_started_at_epoch(*, pid: int) -> float | None:
    stat_raw = attempt(
        action=lambda: Path(f"/proc/{pid}/stat").read_text(encoding="utf-8"),
        exceptions=(OSError,),
    )
    if isinstance(stat_raw, AttemptFailure):
        return None
    started_ticks = linux_proc_started_ticks(stat_text=stat_raw)
    booted_at_epoch = linux_booted_at_epoch()
    ticks_per_second = clock_ticks_per_second()
    if started_ticks is None or booted_at_epoch is None or ticks_per_second is None:
        return None
    return booted_at_epoch + (started_ticks / ticks_per_second)


def linux_proc_started_ticks(*, stat_text: str) -> int | None:
    after_name = stat_text.rsplit(")", maxsplit=1)
    if len(after_name) != _PROC_STAT_SPLIT_PARTS:
        return None
    fields = after_name[1].split()
    if len(fields) < _PROC_STAT_FIELDS_AFTER_NAME:
        return None
    started_raw = fields[_PROC_STAT_START_TICKS_INDEX]
    return int(started_raw) if started_raw.isdecimal() else None


def linux_booted_at_epoch() -> float | None:
    stat_raw = attempt(
        action=lambda: Path("/proc/stat").read_text(encoding="utf-8"),
        exceptions=(OSError,),
    )
    if isinstance(stat_raw, AttemptFailure):
        return None
    for line in stat_raw.splitlines():
        parts = line.split()
        if (
            len(parts) == _PROC_STAT_KEY_VALUE_FIELDS
            and parts[0] == "btime"
            and parts[1].isdecimal()
        ):
            return float(parts[1])
    return None


def clock_ticks_per_second() -> float | None:
    ticks = attempt(action=lambda: os.sysconf("SC_CLK_TCK"), exceptions=(OSError, ValueError))
    if isinstance(ticks, AttemptFailure) or ticks <= 0:
        return None
    return float(ticks)
