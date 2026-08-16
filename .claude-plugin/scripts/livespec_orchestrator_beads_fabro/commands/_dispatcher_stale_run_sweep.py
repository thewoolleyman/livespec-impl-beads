"""Standalone stale Fabro run sweep for orphaned dispatcher launches."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from livespec_orchestrator_beads_fabro.commands._config import (
    resolve_fabro_bin,
    resolve_fabro_factory,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_argv import (
    fabro_ps_argv,
    fabro_rm_argv,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import load_items
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import build_plan
from livespec_orchestrator_beads_fabro.effects import JsonParseFailure, parse_json
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
_WORK_ITEM_RE = re.compile(r"^Work-item:\s*(\S+)", re.MULTILINE)


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
    ) -> CommandResult: ...


@dataclass(frozen=True, kw_only=True)
class _WatchableFabroRun:
    work_item_id: str
    run_id: str
    status_kind: str


def reap_stale_fabro_runs(
    *,
    repo: Path,
    runner: _StaleRunSweepRunner,
    items: list[WorkItem],
    fabro_bin: str,
    fabro_factory_server: str | None,
) -> StaleFabroRunSweepSummary:
    """Reap runnable/running Fabro runs whose ledger item is no longer active."""
    plan = build_plan(
        repo=repo,
        work_item_id="stale-run-sweep",
        workflow_toml=repo / ".fabro/workflows/implement-work-item/workflow.toml",
        goal_file=repo / ".fabro/stale-run-sweep-goal.md",
        fabro_bin=fabro_bin,
        fabro_factory_server=fabro_factory_server,
        janitor=None,
        janitor_checkout=repo / ".stale-run-sweep-janitor-unused",
    )
    ps = runner.run(
        argv=fabro_ps_argv(plan=plan),
        cwd=repo,
        timeout_seconds=_FABRO_PROBE_TIMEOUT_SECONDS,
    )
    if ps.exit_code != 0:
        return StaleFabroRunSweepSummary(reaped=(), probe_exit_code=ps.exit_code)
    item_statuses = {item.id: item.status for item in items}
    reaped: list[ReapedStaleFabroRun] = []
    for run in _watchable_fabro_runs(ps_json=ps.stdout):
        item_status = item_statuses.get(run.work_item_id)
        if item_status is None or item_status == "active":
            continue
        rm = runner.run(
            argv=fabro_rm_argv(plan=plan, run_id=run.run_id),
            cwd=repo,
            timeout_seconds=_FABRO_RM_TIMEOUT_SECONDS,
        )
        reaped.append(
            ReapedStaleFabroRun(
                work_item_id=run.work_item_id,
                run_id=run.run_id,
                run_status=run.status_kind,
                item_status=item_status,
                rm_exit_code=rm.exit_code,
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
    )
    _emit_summary(summary=summary, as_json=args.as_json)
    return 1 if summary.probe_exit_code != 0 or _has_failed_rm(summary=summary) else 0


def _watchable_fabro_runs(*, ps_json: str) -> tuple[_WatchableFabroRun, ...]:
    parsed_raw = parse_json(text=ps_json)
    if isinstance(parsed_raw, JsonParseFailure):
        return ()
    runs = _runs_list(parsed_raw=parsed_raw)
    return tuple(run for raw in runs for run in [_watchable_fabro_run(raw=raw)] if run is not None)


def _runs_list(*, parsed_raw: object) -> list[object]:
    if isinstance(parsed_raw, list):
        return cast("list[object]", parsed_raw)
    if isinstance(parsed_raw, dict):
        runs_raw: object = cast("dict[str, Any]", parsed_raw).get("runs")
        if isinstance(runs_raw, list):
            return cast("list[object]", runs_raw)
    return []


def _watchable_fabro_run(*, raw: object) -> _WatchableFabroRun | None:
    if not isinstance(raw, dict):
        return None
    run = cast("dict[str, Any]", raw)
    work_item_id = _work_item_id(goal=run.get("goal"))
    status_kind = _status_kind(status=run.get("status"))
    run_id_raw: object = run.get("run_id")
    if (
        work_item_id is None
        or status_kind not in {"runnable", "running"}
        or not isinstance(run_id_raw, str)
        or run_id_raw == ""
    ):
        return None
    return _WatchableFabroRun(
        work_item_id=work_item_id,
        run_id=run_id_raw,
        status_kind=status_kind,
    )


def _work_item_id(*, goal: object) -> str | None:
    if not isinstance(goal, str):
        return None
    match = _WORK_ITEM_RE.search(goal)
    return None if match is None else match.group(1)


def _status_kind(*, status: object) -> str | None:
    if isinstance(status, str):
        return status
    if isinstance(status, dict):
        kind_raw: object = cast("dict[str, Any]", status).get("kind")
        if isinstance(kind_raw, str):
            return kind_raw
    return None


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
