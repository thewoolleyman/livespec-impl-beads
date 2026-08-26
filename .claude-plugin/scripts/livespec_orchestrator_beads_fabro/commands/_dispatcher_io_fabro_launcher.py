"""Fabro launcher side-effect seam for the Dispatcher."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    CommandRunner,
    FabroRunResult,
    JournalWriter,
    dispatch_fabro_run_inputs,
    run_fabro_factory_auth_login,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_heartbeat_probe import (
    HeartbeatLivenessProbe,
    LayeredLivenessProbe,
    heartbeat_lookup_keys,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import store_config
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    DispatchPlan,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_watchdog import (
    LivenessSample,
    StallVerdict,
    decide_stall,
    parse_last_event_epoch,
    resolve_stall_seconds,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port import (
    FabroPort,
    FabroRunSummary,
    fabro_port_for_plan,
)
from livespec_orchestrator_beads_fabro.commands._otel_receive import HeartbeatSink
from livespec_orchestrator_beads_fabro.errors import BeadsCommandError, BeadsConnectionError
from livespec_orchestrator_beads_fabro.store import read_work_items

__all__: list[str] = ["WatchedFabroLauncher"]

# The `fabro run` subprocess ceiling rides on `plan.fabro_timeout_seconds`,
# derived per dispatch from the resolved node timeouts and stall timeout
# (`_node_timeouts.derive_fabro_timeout_seconds`) — the watched and
# synchronous launchers deliberately read the SAME number, so a repository
# that lengthens a node cannot have one path outlive the other.
_FABRO_PROBE_TIMEOUT_SECONDS = 60.0
_FABRO_RM_TIMEOUT_SECONDS = 120.0
_WATCHDOG_POLL_INTERVAL_SECONDS = 30.0


@dataclass(frozen=True, kw_only=True)
class _WatchResult:
    stalled_run_id: str | None = None
    abandoned_run_id: str | None = None
    abandoned_item_status: str | None = None


@dataclass(frozen=True, kw_only=True)
class _WallClockEventProbe:
    """The coarse wall-clock backstop expressed as a liveness probe."""

    plan: DispatchPlan
    port: FabroPort
    run_id: str | None

    def sample(self, *, observed_at: float) -> LivenessSample:
        if self.run_id is None:
            return LivenessSample(last_event_epoch=None, observed_at=observed_at)
        events = self.port.events(
            run_id=self.run_id,
            timeout_seconds=_FABRO_PROBE_TIMEOUT_SECONDS,
        )
        inspect = self.port.inspect(
            run_id=self.run_id,
            timeout_seconds=_FABRO_PROBE_TIMEOUT_SECONDS,
        )
        events_json = events.command.stdout if events.command.exit_code == 0 else ""
        inspect_json = inspect.command.stdout if inspect.command.exit_code == 0 else ""
        epoch = parse_last_event_epoch(events_json=events_json, inspect_json=inspect_json)
        return LivenessSample(last_event_epoch=epoch, observed_at=observed_at)


@dataclass(frozen=True, kw_only=True)
class WatchedFabroLauncher:
    """Production FabroLauncher: `fabro run` + the coarse wall-clock watchdog."""

    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    heartbeat_path: Path | None = None

    def launch(
        self,
        *,
        plan: DispatchPlan,
        runner: CommandRunner,
        journal: JournalWriter,
    ) -> FabroRunResult:
        run_fabro_factory_auth_login(plan=plan, runner=runner)
        port = fabro_port_for_plan(plan=plan, runner=runner)
        holder: dict[str, CommandResult] = {}
        run_id_holder: dict[str, str | None] = {}

        def _run_fabro() -> None:
            result = port.run(
                workflow_toml=plan.workflow_toml,
                goal_file=plan.goal_file,
                inputs=dispatch_fabro_run_inputs(plan=plan),
                timeout_seconds=plan.fabro_timeout_seconds,
            )
            holder["result"] = cast("CommandResult", result.command)
            run_id_holder["run_id"] = result.run_id

        thread = threading.Thread(target=_run_fabro, name=f"fabro-run-{plan.work_item_id}")
        thread.daemon = True
        thread.start()
        watched = self._watch(plan=plan, runner=runner, journal=journal, thread=thread, port=port)
        if watched.abandoned_run_id is not None:
            thread.join(timeout=_FABRO_RM_TIMEOUT_SECONDS)
            return FabroRunResult(
                command=holder.get(
                    "result",
                    CommandResult(exit_code=1, stdout="", stderr="cancelled by stale item reaper"),
                ),
                abandoned_run_id=watched.abandoned_run_id,
                abandoned_item_status=watched.abandoned_item_status,
            )
        if watched.stalled_run_id is not None:
            thread.join(timeout=_FABRO_RM_TIMEOUT_SECONDS)
            return FabroRunResult(
                command=holder.get(
                    "result",
                    CommandResult(exit_code=124, stdout="", stderr="cancelled by stall watchdog"),
                ),
                stalled_run_id=watched.stalled_run_id,
            )
        thread.join()
        return FabroRunResult(command=holder["result"], run_id=run_id_holder.get("run_id"))

    def _watch(
        self,
        *,
        plan: DispatchPlan,
        runner: CommandRunner,
        journal: JournalWriter,
        thread: threading.Thread,
        port: FabroPort,
    ) -> _WatchResult:
        stall_seconds = resolve_stall_seconds()
        samples: list[LivenessSample] = []
        known_run_id: str | None = None
        while thread.is_alive():
            self.sleep(_WATCHDOG_POLL_INTERVAL_SECONDS)
            if not thread.is_alive():
                return _WatchResult()
            run = self._discover_run(plan=plan, port=port)
            run_id = run.run_id if run is not None and run.status_kind == "running" else None
            known_run_id = run_id if run_id is not None else known_run_id
            if run is not None:
                item_status = _work_item_status(repo=plan.repo, work_item_id=plan.work_item_id)
                if item_status is not None and item_status != "active":
                    self._reap_stale_run(
                        plan=plan,
                        runner=runner,
                        journal=journal,
                        run_id=run.run_id,
                        item_status=item_status,
                    )
                    return _WatchResult(
                        abandoned_run_id=run.run_id,
                        abandoned_item_status=item_status,
                    )
            samples.append(self._sample(plan=plan, port=port, run_id=run_id))
            if known_run_id is None or run is None or run.status_kind != "running":
                continue
            if decide_stall(samples=tuple(samples), stall_seconds=stall_seconds) == (
                StallVerdict.STALLED
            ):
                self._cancel(plan=plan, port=port, journal=journal, run_id=known_run_id)
                return _WatchResult(stalled_run_id=known_run_id)
        return _WatchResult()

    def _discover_run(self, *, plan: DispatchPlan, port: FabroPort) -> FabroRunSummary | None:
        ps = port.ps(timeout_seconds=_FABRO_PROBE_TIMEOUT_SECONDS)
        if ps.command.exit_code != 0:
            return None
        for run in ps.runs:
            if run.work_item_id == plan.work_item_id and run.status_kind in {
                "runnable",
                "running",
            }:
                return run
        return None

    def _sample(
        self,
        *,
        plan: DispatchPlan,
        port: FabroPort,
        run_id: str | None,
    ) -> LivenessSample:
        observed_at = self.clock()
        wall_clock = _WallClockEventProbe(plan=plan, port=port, run_id=run_id)
        if self.heartbeat_path is None:
            return wall_clock.sample(observed_at=observed_at)
        heartbeat = HeartbeatLivenessProbe(
            sink=HeartbeatSink(path=self.heartbeat_path),
            keys=heartbeat_lookup_keys(work_item_id=plan.work_item_id, run_id=run_id),
        )
        layered = LayeredLivenessProbe(primary=heartbeat, fallback=wall_clock)
        return layered.sample(observed_at=observed_at)

    def _cancel(
        self,
        *,
        plan: DispatchPlan,
        port: FabroPort,
        journal: JournalWriter,
        run_id: str,
    ) -> None:
        rm = port.rm(
            run_id=run_id,
            timeout_seconds=_FABRO_RM_TIMEOUT_SECONDS,
        )
        journal.append(
            record={
                "work_item_id": plan.work_item_id,
                "stage": "watchdog-stall-cancel",
                "run_id": run_id,
                "rm_exit_code": rm.command.exit_code,
            }
        )

    def _reap_stale_run(
        self,
        *,
        plan: DispatchPlan,
        runner: CommandRunner,
        journal: JournalWriter,
        run_id: str,
        item_status: str,
    ) -> None:
        rm = fabro_port_for_plan(plan=plan, runner=runner).rm(
            run_id=run_id,
            timeout_seconds=_FABRO_RM_TIMEOUT_SECONDS,
        )
        journal.append(
            record={
                "work_item_id": plan.work_item_id,
                "stage": "stale-run-reap",
                "run_id": run_id,
                "item_status": item_status,
                "rm_exit_code": rm.command.exit_code,
            }
        )


def _work_item_status(*, repo: Path, work_item_id: str) -> str | None:
    config = store_config(repo=repo) if (repo / ".livespec.jsonc").is_file() else None
    if config is None:
        return None
    try:
        items = read_work_items(path=config)
    except (BeadsCommandError, BeadsConnectionError):
        return None
    for item in items:
        if item.id == work_item_id:
            return item.status
    return None
