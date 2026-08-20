"""Shared tier 0 config type and payload helpers (importable support module)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pytest
from livespec_orchestrator_beads_fabro.commands._fabro_port import (
    FabroCommand,
    FabroPort,
)

__all__: list[str] = []

_DEFAULT_SERVER_URL = "http://127.0.0.1:32276"
TIMEOUT_SECONDS = 30.0
TERMINAL_STATUS_KINDS = frozenset(
    (
        "blocked",
        "canceled",
        "cancelled",
        "completed",
        "done",
        "error",
        "errored",
        "failed",
        "green",
        "merged",
        "succeeded",
        "success",
    )
)


@dataclass(frozen=True, kw_only=True)
class _FabroTier0Config:
    fabro_bin: str
    server_url: str
    expected_client_version: str
    expected_client_commit: str
    expected_client_date: str
    expected_server_version: str
    expected_server_commit: str
    expected_server_date: str
    completed_run_id: str | None


def _assert_success(*, command: FabroCommand) -> None:
    assert command.exit_code == 0, command.stderr or command.stdout


def _completed_run_id(*, port: FabroPort) -> str:
    ps = port.ps(timeout_seconds=TIMEOUT_SECONDS)
    _assert_success(command=ps.command)
    for record in _run_records(payload=ps.payload):
        status_kind = _status_kind(record=record)
        if status_kind in TERMINAL_STATUS_KINDS:
            return cast("str", record["run_id"])
    pytest.fail("fabro ps returned no completed run; set FABRO_EUT_COMPLETED_RUN_ID")


def _run_records(*, payload: object | None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [_mapping(value=record) for record in payload if isinstance(record, dict)]
    if isinstance(payload, dict):
        raw_runs: object = payload.get("runs")
        if isinstance(raw_runs, list):
            return [_mapping(value=record) for record in raw_runs if isinstance(record, dict)]
    return []


def _inspect_record(*, value: object | None) -> dict[str, Any]:
    if isinstance(value, list):
        for entry in cast("list[object]", value):
            if isinstance(entry, dict):
                return cast("dict[str, Any]", entry)
        pytest.fail("fabro inspect --json returned a list with no run record")
    return _mapping(value=value)


def _mapping(*, value: object | None) -> dict[str, Any]:
    assert isinstance(value, dict)
    return cast("dict[str, Any]", value)


def _status_kind(*, record: dict[str, Any]) -> str | None:
    status = record.get("status")
    if isinstance(status, str):
        return status
    if isinstance(status, dict):
        kind = status.get("kind")
        if isinstance(kind, str):
            return kind
    return None
