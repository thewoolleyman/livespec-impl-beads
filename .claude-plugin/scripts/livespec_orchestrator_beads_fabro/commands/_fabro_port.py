"""Thin Fabro CLI facade for the dispatcher dependency surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from livespec_orchestrator_beads_fabro.commands._fabro_port_records import (
    FabroFailureDetail,
    FabroRunSummary,
    fabro_failure_detail_from_payload,
    fabro_run_id_from_output,
    fabro_run_summaries_from_payload,
    fabro_run_summaries_from_stdout,
    fabro_status_kind_from_payload,
)
from livespec_orchestrator_beads_fabro.effects import JsonParseFailure, parse_json

__all__: list[str] = [
    "FabroCommand",
    "FabroCommandResult",
    "FabroEventsResult",
    "FabroFailureDetail",
    "FabroInspectResult",
    "FabroJsonResult",
    "FabroPort",
    "FabroPsResult",
    "FabroRunResult",
    "FabroRunSummary",
    "FabroTarget",
    "FabroVersionResult",
    "fabro_port_for_plan",
    "fabro_run_summaries_from_stdout",
]


class FabroCommand(Protocol):
    """Result fields consumed from the dispatcher's command runner."""

    @property
    def exit_code(self) -> int: ...

    @property
    def stdout(self) -> str: ...

    @property
    def stderr(self) -> str: ...


class _FabroRunner(Protocol):
    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> FabroCommand: ...


@dataclass(frozen=True, kw_only=True)
class FabroTarget:
    """Factory target for one Fabro client binary."""

    server_url: str | None = None
    dev_token: str | None = None


@dataclass(frozen=True, kw_only=True)
class FabroCommandResult:
    """Result for Fabro commands whose output is not parsed further."""

    command: FabroCommand


@dataclass(frozen=True, kw_only=True)
class FabroRunResult:
    """Result for `fabro run`, including the run id printed by the CLI."""

    command: FabroCommand
    run_id: str | None


@dataclass(frozen=True, kw_only=True)
class FabroJsonResult:
    """Result for a `--json` Fabro command."""

    command: FabroCommand
    payload: object | None


@dataclass(frozen=True, kw_only=True)
class FabroEventsResult:
    """Parsed `fabro events --json` result."""

    command: FabroCommand
    payload: object | None


@dataclass(frozen=True, kw_only=True)
class FabroInspectResult:
    """Parsed `fabro inspect --json` result with normalized status kind."""

    command: FabroCommand
    payload: object | None
    status_kind: str | None
    failure: FabroFailureDetail | None


@dataclass(frozen=True, kw_only=True)
class FabroPsResult:
    """Parsed `fabro ps -a --json` result."""

    command: FabroCommand
    payload: object | None
    runs: tuple[FabroRunSummary, ...]


@dataclass(frozen=True, kw_only=True)
class FabroVersionResult:
    """Raw `fabro version` result."""

    command: FabroCommand
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
    runner: _FabroRunner
    cwd: Path

    def run(
        self,
        *,
        workflow_toml: Path,
        goal_file: Path,
        inputs: tuple[str, ...],
        timeout_seconds: float,
    ) -> FabroRunResult:
        command = self._run(
            argv=[
                self.fabro_bin,
                "run",
                str(workflow_toml),
                "--goal-file",
                str(goal_file),
                *_input_args(inputs=inputs),
                "--no-upgrade-check",
                *self._server_suffix(),
            ],
            timeout_seconds=timeout_seconds,
            env=self._server_env(),
        )
        return FabroRunResult(
            command=command,
            run_id=fabro_run_id_from_output(output=f"{command.stdout}\n{command.stderr}"),
        )

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
            status_kind=fabro_status_kind_from_payload(payload=payload),
            failure=fabro_failure_detail_from_payload(payload=payload),
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
        return FabroPsResult(
            command=command,
            payload=payload,
            runs=fabro_run_summaries_from_payload(payload=payload),
        )

    def rm(self, *, run_id: str, timeout_seconds: float) -> FabroCommandResult:
        command = self._run(
            argv=[self.fabro_bin, "rm", "-f", run_id, *self._server_suffix()],
            timeout_seconds=timeout_seconds,
        )
        return FabroCommandResult(command=command)

    def top_level_server_parse_probe(
        self,
        *,
        subcommand: tuple[str, ...],
        timeout_seconds: float,
    ) -> FabroCommandResult:
        server_url = self.target.server_url or ""
        command = self._run(
            argv=[self.fabro_bin, "--server", server_url, *subcommand],
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
    ) -> FabroCommand:
        if env is None:
            return self.runner.run(argv=argv, cwd=self.cwd, timeout_seconds=timeout_seconds)
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


def fabro_port_for_plan(*, plan: Any, runner: _FabroRunner) -> FabroPort:
    """Construct the Fabro CLI port from a dispatch plan."""
    return FabroPort(
        fabro_bin=plan.fabro_bin,
        target=FabroTarget(
            server_url=plan.fabro_factory_server,
            dev_token=plan.fabro_factory_dev_token,
        ),
        runner=runner,
        cwd=plan.repo,
    )


def _input_args(*, inputs: tuple[str, ...]) -> list[str]:
    argv: list[str] = []
    for item in inputs:
        argv.extend(["--input", item])
    return argv


def _json_payload(*, command: FabroCommand) -> object | None:
    if command.exit_code != 0:
        return None
    parsed = parse_json(text=command.stdout)
    if isinstance(parsed, JsonParseFailure):
        return None
    return parsed
