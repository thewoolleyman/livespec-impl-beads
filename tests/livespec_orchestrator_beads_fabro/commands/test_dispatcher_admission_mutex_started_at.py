"""Additional started-at coverage for the dispatch admission mutex."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands import _dispatcher_admission_mutex as mutex
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult


@dataclass(kw_only=True)
class _EmptyPsRunner:
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
        return CommandResult(exit_code=0, stdout=json.dumps({"runs": []}), stderr="")


def test_live_slot_without_started_at_epoch_stays_held(tmp_path: Path) -> None:
    slot = mutex.admission_mutex_slot_path(repo=tmp_path, slot=0)
    slot.parent.mkdir(parents=True, exist_ok=True)
    _ = slot.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")

    result = mutex.claim_dispatch_admission_mutex(
        repo=tmp_path, fabro_bin="/abs/fabro", runner=_EmptyPsRunner(), cap=1
    )

    assert isinstance(result, mutex.AdmissionMutexRefusal)
    assert f"slot 0: pid {os.getpid()}" in result.detail
