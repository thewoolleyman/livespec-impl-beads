"""Tier 0 Enemy Unit Tests for the real Fabro dependency.

This suite is intentionally outside `tests/` so the hermetic `just check`
aggregate never needs a live Fabro server or credentials. Invoke it explicitly:

    just fabro-enemy-tier0
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner
from livespec_orchestrator_beads_fabro.commands._fabro_port import (
    FabroCommand,
    FabroPort,
    FabroTarget,
)

__all__: list[str] = []

_DEFAULT_SERVER_URL = "http://127.0.0.1:32276"
_WORKFLOW_PATH = Path(".claude-plugin/.fabro/workflows/implement-work-item/workflow.fabro")
_TIMEOUT_SECONDS = 30.0
_EXPECTED_PS_FIELDS = frozenset(("run_id", "status", "goal", "total_usd_micros"))
_EXPECTED_INSPECT_FIELDS = frozenset(("status", "updated_at"))
_EVENT_TIMESTAMP_FIELDS = frozenset(("timestamp", "ts", "at"))
_TERMINAL_STATUS_KINDS = frozenset(
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


@pytest.fixture(scope="module")
def config() -> _FabroTier0Config:
    return _FabroTier0Config(
        fabro_bin=os.environ.get("FABRO_EUT_BIN", "fabro"),
        server_url=os.environ.get("FABRO_EUT_SERVER", _DEFAULT_SERVER_URL),
        expected_client_version=os.environ.get("FABRO_EUT_EXPECTED_CLIENT_VERSION", "0.254.0"),
        expected_client_commit=os.environ.get("FABRO_EUT_EXPECTED_CLIENT_COMMIT", "8de6611"),
        expected_client_date=os.environ.get("FABRO_EUT_EXPECTED_CLIENT_DATE", "2026-07-30"),
        expected_server_version=os.environ.get("FABRO_EUT_EXPECTED_SERVER_VERSION", "0.254.0"),
        expected_server_commit=os.environ.get("FABRO_EUT_EXPECTED_SERVER_COMMIT", "8de6611"),
        expected_server_date=os.environ.get("FABRO_EUT_EXPECTED_SERVER_DATE", "2026-08-02"),
        completed_run_id=os.environ.get("FABRO_EUT_COMPLETED_RUN_ID"),
    )


@pytest.fixture(scope="module")
def port(*, config: _FabroTier0Config) -> FabroPort:
    return FabroPort(
        fabro_bin=config.fabro_bin,
        target=FabroTarget(server_url=config.server_url),
        runner=ShellCommandRunner(),
        cwd=Path.cwd(),
    )


def test_version_reports_client_and_server_independently(
    *,
    config: _FabroTier0Config,
    port: FabroPort,
) -> None:
    result = port.version(timeout_seconds=_TIMEOUT_SECONDS)

    _assert_success(command=result.command)
    text = result.text.lower()
    assert "client" in text
    assert "server" in text
    assert config.expected_client_version in result.text
    assert config.expected_client_commit in result.text
    assert config.expected_client_date in result.text
    assert config.expected_server_version in result.text
    assert config.expected_server_commit in result.text
    assert config.expected_server_date in result.text
    assert config.server_url in result.text


def test_validate_accepts_livespec_workflow_templated_acp_command(
    *,
    port: FabroPort,
) -> None:
    workflow_text = _WORKFLOW_PATH.read_text()

    assert 'acp.command="{{ inputs.acp_adapter }}"' in workflow_text
    result = port.validate(workflow_toml=_WORKFLOW_PATH, timeout_seconds=_TIMEOUT_SECONDS)

    _assert_success(command=result.command)
    assert result.payload is not None


def test_ps_records_carry_reader_field_set(*, port: FabroPort) -> None:
    result = port.ps(timeout_seconds=_TIMEOUT_SECONDS)

    _assert_success(command=result.command)
    records = _run_records(payload=result.payload)
    assert records
    assert result.runs
    for record in records:
        assert set(record) >= _EXPECTED_PS_FIELDS
        assert isinstance(record["run_id"], str)
        assert record["run_id"]
        assert _status_kind(record=record) is not None


def test_server_flag_is_per_subcommand(*, port: FabroPort) -> None:
    suffixed = port.ps(timeout_seconds=_TIMEOUT_SECONDS)
    top_level = port.top_level_server_parse_probe(
        subcommand=("ps", "-a", "--json"),
        timeout_seconds=_TIMEOUT_SECONDS,
    )

    _assert_success(command=suffixed.command)
    assert top_level.command.exit_code != 0
    parse_error_text = f"{top_level.command.stdout}\n{top_level.command.stderr}".lower()
    assert "--server" in parse_error_text


def test_inspect_and_events_completed_run_field_sets(
    *,
    config: _FabroTier0Config,
    port: FabroPort,
) -> None:
    run_id = config.completed_run_id or _completed_run_id(port=port)
    inspect = port.inspect(run_id=run_id, timeout_seconds=_TIMEOUT_SECONDS)
    events = port.events(run_id=run_id, timeout_seconds=_TIMEOUT_SECONDS)

    _assert_success(command=inspect.command)
    _assert_success(command=events.command)
    inspect_record = _mapping(value=inspect.payload)
    assert set(inspect_record) >= _EXPECTED_INSPECT_FIELDS
    assert inspect.status_kind is not None
    event_records = _event_records(stdout=events.command.stdout, payload=events.payload)
    assert event_records
    assert any(_has_event_timestamp(event=event) for event in event_records)


def _assert_success(*, command: FabroCommand) -> None:
    assert command.exit_code == 0, command.stderr or command.stdout


def _completed_run_id(*, port: FabroPort) -> str:
    ps = port.ps(timeout_seconds=_TIMEOUT_SECONDS)
    _assert_success(command=ps.command)
    for record in _run_records(payload=ps.payload):
        status_kind = _status_kind(record=record)
        if status_kind in _TERMINAL_STATUS_KINDS:
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


def _event_records(*, stdout: str, payload: object | None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [_mapping(value=item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        events = payload.get("events")
        if isinstance(events, list):
            return [_mapping(value=item) for item in events if isinstance(item, dict)]
        return [cast("dict[str, Any]", payload)]
    records: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if line.strip() == "":
            continue
        decoded = json.loads(line)
        if isinstance(decoded, dict):
            records.append(cast("dict[str, Any]", decoded))
    return records


def _has_event_timestamp(*, event: dict[str, Any]) -> bool:
    for key in _EVENT_TIMESTAMP_FIELDS:
        value = event.get(key)
        if isinstance(value, str):
            return bool(value)
        if isinstance(value, int | float) and not isinstance(value, bool):
            return True
    return False
