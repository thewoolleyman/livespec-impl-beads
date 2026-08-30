"""Standalone stale Fabro run sweep for orphaned dispatcher launches."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from livespec_orchestrator_beads_fabro.commands._config import (
    resolve_fabro_bin,
    resolve_fabro_factory,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import load_items
from livespec_orchestrator_beads_fabro.commands._dispatcher_run_stamp import repo_run_attribution
from livespec_orchestrator_beads_fabro.commands._fabro_port import (
    FabroPort,
    FabroTarget,
)
from livespec_orchestrator_beads_fabro.commands._run_attribution import (
    GOAL_TEXT_ONLY,
    RunAttribution,
)
from livespec_orchestrator_beads_fabro.io import write_stdout
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "ReapedStaleFabroRun",
    "StaleFabroRunSweepSummary",
    "reap_stale_fabro_runs",
    "run_stale_run_sweep_command",
]

_FABRO_PROBE_TIMEOUT_SECONDS = 60.0
_FABRO_RM_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True, kw_only=True)
class ReapedStaleFabroRun:
    """One orphaned Fabro run removed because its item is no longer active."""

    work_item_id: str
    run_id: str
    run_status: str
    item_status: str
    rm_exit_code: int


@dataclass(frozen=True, kw_only=True)
class StaleFabroRunSweepSummary:
    """Result of one standalone stale-run sweep."""

    reaped: tuple[ReapedStaleFabroRun, ...]
    probe_exit_code: int


class _StaleRunSweepRunner(Protocol):
    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult: ...


def reap_stale_fabro_runs(
    *,
    repo: Path,
    runner: _StaleRunSweepRunner,
    items: list[WorkItem],
    fabro_bin: str,
    fabro_factory_server: str | None,
    attribution: RunAttribution = GOAL_TEXT_ONLY,
) -> StaleFabroRunSweepSummary:
    """Reap runnable/running Fabro runs whose ledger item is no longer active.

    Attribution matters MORE here than anywhere else in this repo, because this
    is the only consumer whose action is destructive: a mis-attributed row is
    not a wrong report, it is a `fabro rm` aimed at the wrong run. Reading the
    ledger's own run-id stamp first means a run is reaped for its OWN item's
    status, never for a status the goal text happened to point at.
    """
    port = FabroPort(
        fabro_bin=fabro_bin,
        target=FabroTarget(server_url=fabro_factory_server),
        runner=runner,
        cwd=repo,
    )
    ps = port.ps(timeout_seconds=_FABRO_PROBE_TIMEOUT_SECONDS)
    if ps.command.exit_code != 0:
        return StaleFabroRunSweepSummary(reaped=(), probe_exit_code=ps.command.exit_code)
    item_statuses = {item.id: item.status for item in items}
    reaped: list[ReapedStaleFabroRun] = []
    for run in ps.runs:
        work_item_id = attribution.work_item_id_for(run=run)
        if work_item_id is None or run.status_kind not in {"runnable", "running"}:
            continue
        item_status = item_statuses.get(work_item_id)
        if item_status is None or item_status == "active":
            continue
        rm = port.rm(
            run_id=run.run_id,
            timeout_seconds=_FABRO_RM_TIMEOUT_SECONDS,
        )
        reaped.append(
            ReapedStaleFabroRun(
                work_item_id=work_item_id,
                run_id=run.run_id,
                run_status=run.status_kind,
                item_status=item_status,
                rm_exit_code=rm.command.exit_code,
            )
        )
    return StaleFabroRunSweepSummary(reaped=tuple(reaped), probe_exit_code=0)


def run_stale_run_sweep_command(*, args: argparse.Namespace) -> int:
    repo = Path(args.repo) if args.repo is not None else Path.cwd()
    factory = resolve_fabro_factory(cwd=repo, factory=args.factory)
    summary = reap_stale_fabro_runs(
        repo=repo,
        runner=ShellCommandRunner(),
        items=load_items(repo=repo),
        fabro_bin=args.fabro_bin if args.fabro_bin is not None else resolve_fabro_bin(cwd=repo),
        fabro_factory_server=factory.server,
        attribution=repo_run_attribution(repo=repo),
    )
    _emit_summary(summary=summary, as_json=args.as_json)
    return 1 if summary.probe_exit_code != 0 or _has_failed_rm(summary=summary) else 0


def _emit_summary(*, summary: StaleFabroRunSweepSummary, as_json: bool) -> None:
    if as_json:
        payload = {
            "probe_exit_code": summary.probe_exit_code,
            "reaped": [asdict(run) for run in summary.reaped],
        }
        _ = write_stdout(text=json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return
    if summary.probe_exit_code != 0:
        _ = write_stdout(text=f"fabro ps failed with exit {summary.probe_exit_code}\n")
        return
    if not summary.reaped:
        _ = write_stdout(text="(no stale fabro runs reaped)\n")
        return
    for run in summary.reaped:
        line = (
            f"REAPED  {run.work_item_id}  {run.run_id}  "
            f"run={run.run_status} item={run.item_status} rm_exit={run.rm_exit_code}\n"
        )
        _ = write_stdout(text=line)


def _has_failed_rm(*, summary: StaleFabroRunSweepSummary) -> bool:
    return any(run.rm_exit_code != 0 for run in summary.reaped)
