"""Thin Fabro CLI facade for the dispatcher dependency surface."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    CommandRunner,
)
from livespec_orchestrator_beads_fabro.effects import JsonParseFailure, parse_json

__all__: list[str] = [
    "FabroCommandResult",
    "FabroEventsResult",
    "FabroInspectResult",
    "FabroJsonResult",
    "FabroPort",
    "FabroPsResult",
    "FabroRunResult",
    "FabroRunSummary",
    "FabroTarget",
    "FabroVersionResult",
]

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
_RUN_ID_RE = re.compile(r"Run:\s*([0-9A-Za-z-]+)")


@dataclass(frozen=True, kw_only=True)
class FabroTarget:
    """Factory target for one Fabro client binary."""

    server_url: str | None = None
    dev_token: str | None = None


@dataclass(frozen=True, kw_only=True)
class FabroCommandResult:
    """Result for Fabro commands whose output is not parsed further."""

    command: CommandResult


@dataclass(frozen=True, kw_only=True)
class FabroRunResult:
    """Result for `fabro run`, including the run id printed by the CLI."""

    command: CommandResult
    run_id: str | None


@dataclass(frozen=True, kw_only=True)
class FabroJsonResult:
    """Result for a `--json` Fabro command."""

    command: CommandResult
    payload: object | None


@dataclass(frozen=True, kw_only=True)
class FabroEventsResult:
    """Parsed `fabro events --json` result."""

    command: CommandResult
    payload: object | None


@dataclass(frozen=True, kw_only=True)
class FabroInspectResult:
    """Parsed `fabro inspect --json` result with normalized status kind."""

    command: CommandResult
    payload: object | None
    status_kind: str | None


@dataclass(frozen=True, kw_only=True)
class FabroRunSummary:
    """Run row from `fabro ps -a --json` that livespec code reads."""

    run_id: str
    status_kind: str | None
    goal: str | None
    total_usd_micros: int | None


@dataclass(frozen=True, kw_only=True)
class FabroPsResult:
    """Parsed `fabro ps -a --json` result."""

    command: CommandResult
    payload: object | None
    runs: tuple[FabroRunSummary, ...]


@dataclass(frozen=True, kw_only=True)
class FabroVersionResult:
    """Raw `fabro version` result."""

    command: CommandResult
    text: str


@dataclass(frozen=True, kw_only=True)
class FabroPort:
    """Single place this repo knows Fabro is a CLI.

    The port deliberately exposes only the Fabro operations the dispatcher
    already depends on. The client binary and factory target are constructor
    data, so an upgrade-candidate binary is tested by constructing another
    port with a different `fabro_bin`.
    """

    fabro_bin: str
    target: FabroTarget
    runner: CommandRunner
    cwd: Path

    def run(
        self,
        *,
        workflow_toml: Path,
        goal_file: Path,
        inputs: tuple[str, ...],
        timeout_seconds: float,
    ) -> FabroRunResult:
        argv = [
            self.fabro_bin,
            "run",
            str(workflow_toml),
            "--goal-file",
            str(goal_file),
            *_input_args(inputs=inputs),
            "--no-upgrade-check",
            *self._server_suffix(),
        ]
        command = self._run(argv=argv, timeout_seconds=timeout_seconds, env=self._server_env())
        return FabroRunResult(command=command, run_id=_parse_run_id(output=command.stdout))

    def auth_login(self, *, timeout_seconds: float) -> FabroCommandResult | None:
        if self.target.server_url is None or self.target.dev_token is None:
            return None
        command = self._run(
            argv=[
                self.fabro_bin,
                "auth",
                "login",
                "--dev-token",
                self.target.dev_token,
                "--server",
                self.target.server_url,
            ],
            timeout_seconds=timeout_seconds,
        )
        return FabroCommandResult(command=command)

    def inspect(self, *, run_id: str, timeout_seconds: float) -> FabroInspectResult:
        command = self._run(
            argv=[self.fabro_bin, "inspect", run_id, "--json", *self._server_suffix()],
            timeout_seconds=timeout_seconds,
        )
        payload = _json_payload(command=command)
        return FabroInspectResult(
            command=command,
            payload=payload,
            status_kind=_status_kind(payload=payload),
        )

    def events(self, *, run_id: str, timeout_seconds: float) -> FabroEventsResult:
        command = self._run(
            argv=[self.fabro_bin, "events", run_id, "--json", *self._server_suffix()],
            timeout_seconds=timeout_seconds,
        )
        return FabroEventsResult(command=command, payload=_json_payload(command=command))

    def ps(self, *, timeout_seconds: float) -> FabroPsResult:
        command = self._run(
            argv=[self.fabro_bin, "ps", "-a", "--json", *self._server_suffix()],
            timeout_seconds=timeout_seconds,
        )
        payload = _json_payload(command=command)
        return FabroPsResult(command=command, payload=payload, runs=_run_summaries(payload=payload))

    def rm(self, *, run_id: str, timeout_seconds: float) -> FabroCommandResult:
        command = self._run(
            argv=[self.fabro_bin, "rm", "-f", run_id, *self._server_suffix()],
            timeout_seconds=timeout_seconds,
        )
        return FabroCommandResult(command=command)

    def validate(self, *, workflow_toml: Path, timeout_seconds: float) -> FabroJsonResult:
        command = self._run(
            argv=[self.fabro_bin, "validate", str(workflow_toml), "--json"],
            timeout_seconds=timeout_seconds,
        )
        return FabroJsonResult(command=command, payload=_json_payload(command=command))

    def version(self, *, timeout_seconds: float) -> FabroVersionResult:
        command = self._run(
            argv=[self.fabro_bin, "version"],
            timeout_seconds=timeout_seconds,
        )
        return FabroVersionResult(command=command, text=command.stdout)

    def _run(
        self,
        *,
        argv: list[str],
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        return self.runner.run(
            argv=argv,
            cwd=self.cwd,
            timeout_seconds=timeout_seconds,
            env=env,
        )

    def _server_suffix(self) -> list[str]:
        # `--server` is a per-subcommand Fabro flag. The pinned 0.254.0 CLI
        # hard-errors on `fabro --server <url> <cmd>`, so the suffix is always
        # appended after the subcommand and its arguments.
        if self.target.server_url is None:
            return []
        return ["--server", self.target.server_url]

    def _server_env(self) -> dict[str, str] | None:
        if self.target.server_url is None:
            return None
        return {"FABRO_SERVER": self.target.server_url}


def _input_args(*, inputs: tuple[str, ...]) -> list[str]:
    argv: list[str] = []
    for item in inputs:
        argv.extend(["--input", item])
    return argv


def _parse_run_id(*, output: str) -> str | None:
    plain = _ANSI_ESCAPE_RE.sub("", output)
    match = _RUN_ID_RE.search(plain)
    if match is None:
        return None
    return match.group(1)


def _json_payload(*, command: CommandResult) -> object | None:
    if command.exit_code != 0:
        return None
    parsed = parse_json(text=command.stdout)
    if isinstance(parsed, JsonParseFailure):
        return None
    return parsed


def _status_kind(*, payload: object | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    status_raw: object = cast("dict[str, Any]", payload).get("status")
    if isinstance(status_raw, str):
        return status_raw
    if isinstance(status_raw, dict):
        kind_raw: object = cast("dict[str, Any]", status_raw).get("kind")
        if isinstance(kind_raw, str):
            return kind_raw
    return None


def _run_summaries(*, payload: object | None) -> tuple[FabroRunSummary, ...]:
    summaries: list[FabroRunSummary] = []
    for run in _runs(payload=payload):
        summary = _run_summary(run=run)
        if summary is not None:
            summaries.append(summary)
    return tuple(summaries)


def _runs(*, payload: object | None) -> list[object]:
    if isinstance(payload, list):
        return cast("list[object]", payload)
    if isinstance(payload, dict):
        runs_raw: object = cast("dict[str, Any]", payload).get("runs")
        if isinstance(runs_raw, list):
            return cast("list[object]", runs_raw)
    return []


def _run_summary(*, run: object) -> FabroRunSummary | None:
    if not isinstance(run, dict):
        return None
    record = cast("dict[str, Any]", run)
    run_id_raw: object = record.get("run_id")
    if not isinstance(run_id_raw, str) or run_id_raw == "":
        return None
    return FabroRunSummary(
        run_id=run_id_raw,
        status_kind=_status_kind(payload=record),
        goal=_optional_str(value=record.get("goal")),
        total_usd_micros=_optional_int(value=record.get("total_usd_micros")),
    )


def _optional_str(*, value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(*, value: object) -> int | None:
    return value if isinstance(value, int) else None
