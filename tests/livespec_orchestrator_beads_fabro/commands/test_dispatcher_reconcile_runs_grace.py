"""Tests for the bounded slot hold on a parked run whose item is still live."""

from __future__ import annotations

import importlib
from pathlib import Path

from returns.io import IOFailure, IOResult
from returns.unsafe import unsafe_perform_io

_MODULE_PATH = (
    Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
    / "_dispatcher_reconcile_runs_grace.py"
)
_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_grace"

_NOW = 1_800_000.0


def test_the_grace_boundary_is_just_under_and_just_over() -> None:
    assert _MODULE_PATH.is_file()
    module = importlib.import_module(_MODULE_NAME)

    just_under = module.grace_hold_reason(parked_seconds=1799.0, grace_seconds=1800)
    exactly_at = module.grace_hold_reason(parked_seconds=1800.0, grace_seconds=1800)
    just_over = module.grace_hold_reason(parked_seconds=1801.0, grace_seconds=1800)

    assert just_under == module.BLOCKED_HOLD_WITHIN_GRACE
    assert exactly_at == module.BLOCKED_HOLD_WITHIN_GRACE
    assert just_over == module.ORPHAN_REASON_BLOCKED_PAST_GRACE


def test_an_unmeasured_park_is_its_own_answer_rather_than_a_zero() -> None:
    module = importlib.import_module(_MODULE_NAME)

    assert (
        module.grace_hold_reason(parked_seconds=None, grace_seconds=1800)
        == module.BLOCKED_HOLD_UNMEASURED
    )
    assert module.seconds_remaining(parked_seconds=None, grace_seconds=1800) is None
    assert module.seconds_remaining(parked_seconds=300.0, grace_seconds=1800) == 1500.0
    # A park that has passed the bound never reports negative time remaining.
    assert module.seconds_remaining(parked_seconds=2400.0, grace_seconds=1800) == 0.0


def test_the_park_is_measured_from_the_most_specific_timestamp_present() -> None:
    module = importlib.import_module(_MODULE_NAME)

    parked = module.parked_seconds_from_record(
        record={
            "start_time": "1970-01-01T00:00:00Z",
            "updated_at": "1970-01-01T00:10:00Z",
            "status": {"kind": "blocked", "blocked_at": "1970-01-01T00:20:00Z"},
        },
        now_epoch=1800.0,
    )

    # `blocked_at` wins over `updated_at` even though `updated_at` sits at the
    # top level and `blocked_at` is nested; `start_time` is never consulted.
    assert parked == 600.0


def test_a_record_with_no_park_timestamp_is_unmeasurable_rather_than_zero() -> None:
    module = importlib.import_module(_MODULE_NAME)

    assert module.parked_seconds_from_record(record=None, now_epoch=_NOW) is None
    assert module.parked_seconds_from_record(record={}, now_epoch=_NOW) is None
    # A run age is NOT a park: `start_time` alone leaves the park unmeasured.
    assert (
        module.parked_seconds_from_record(
            record={"start_time": "1970-01-01T00:00:00Z"},
            now_epoch=_NOW,
        )
        is None
    )
    assert "start_time" not in module.PARKED_SINCE_KEYS


def test_unusable_timestamp_encodings_leave_the_park_unmeasured() -> None:
    module = importlib.import_module(_MODULE_NAME)

    unparseable = module.parked_seconds_from_record(
        record={"blocked_at": "the day before yesterday"},
        now_epoch=_NOW,
    )
    wrong_type = module.parked_seconds_from_record(record={"blocked_at": True}, now_epoch=_NOW)
    listed = module.parked_seconds_from_record(record={"blocked_at": ["nope"]}, now_epoch=_NOW)
    not_a_mapping = module.parked_seconds_from_record(
        record={"status": "blocked", "blocked_since": None},
        now_epoch=_NOW,
    )

    assert (unparseable, wrong_type, listed, not_a_mapping) == (None, None, None, None)


def test_epoch_and_offset_and_naive_timestamps_are_all_read() -> None:
    module = importlib.import_module(_MODULE_NAME)

    epoch_number = module.parked_seconds_from_record(
        record={"blocked_at": 1200},
        now_epoch=1800.0,
    )
    explicit_offset = module.parked_seconds_from_record(
        record={"blocked_at": "1970-01-01T01:00:00+01:00"},
        now_epoch=1800.0,
    )
    naive = module.parked_seconds_from_record(
        record={"blocked_at": "1970-01-01T00:00:00"},
        now_epoch=1800.0,
    )

    assert (epoch_number, explicit_offset, naive) == (600.0, 1800.0, 1800.0)


def test_a_future_timestamp_is_unmeasurable_rather_than_a_negative_park() -> None:
    module = importlib.import_module(_MODULE_NAME)

    parked = module.parked_seconds_from_record(
        record={"blocked_at": 3600},
        now_epoch=1800.0,
    )

    assert parked is None


def test_the_grace_setting_defaults_to_thirty_minutes(tmp_path: Path) -> None:
    module = importlib.import_module(_MODULE_NAME)

    assert module.DEFAULT_BLOCKED_RUN_GRACE_SECONDS == 1800
    assert _read(outcome=module.resolve_blocked_run_grace_seconds(cwd=tmp_path)) == 1800


def test_a_zero_grace_setting_is_accepted_rather_than_rejected(tmp_path: Path) -> None:
    """Zero is the documented disable value, so it must READ as a value.

    Every other integer bound the Dispatcher reads floors at 1, where zero
    would mean "no bound at all". Here it means "never terminate a parked
    run", so a reader that rejected it would fail the setting closed onto the
    1800 default and silently keep reaping.
    """
    module = importlib.import_module(_MODULE_NAME)
    cwd = _config(tmp_path=tmp_path, name="zero", value="0")

    assert _read(outcome=module.resolve_blocked_run_grace_seconds(cwd=cwd)) == 0


def test_a_value_the_grace_setting_cannot_accept_is_unreadable_not_defaulted(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(_MODULE_NAME)
    negative = _config(tmp_path=tmp_path, name="negative", value="-1")
    text = _config(tmp_path=tmp_path, name="text", value='"1800"')

    assert isinstance(module.resolve_blocked_run_grace_seconds(cwd=negative), IOFailure)
    assert isinstance(module.resolve_blocked_run_grace_seconds(cwd=text), IOFailure)


def _read(*, outcome: IOResult[int, object]) -> int:
    return unsafe_perform_io(outcome.unwrap())


def _config(*, tmp_path: Path, name: str, value: str) -> Path:
    cwd = tmp_path / name
    cwd.mkdir()
    _ = (cwd / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"dispatcher": '
        f'{{"blocked_run_grace_seconds": {value}}}}}}}',
        encoding="utf-8",
    )
    return cwd
