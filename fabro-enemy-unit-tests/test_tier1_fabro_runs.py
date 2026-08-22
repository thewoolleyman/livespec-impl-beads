"""Tier 1 Enemy Unit Tests for live Fabro run semantics.

This suite launches real workflows and can spend real runtime. It is
deliberately excluded from `just fabro-enemy-tier0` and `just check`; invoke it
explicitly:

    just fabro-enemy-tier1
"""

from __future__ import annotations

from pathlib import Path

from _tier0_support import (
    TIMEOUT_SECONDS,
    _assert_success,
    _FabroTier0Config,
    _inspect_record,
)
from _tier1_support import (
    _await_ps_summary,
    _event_name,
    _event_records,
    _failure_block,
    _has_event_timestamp,
    _terminal_outcome,
    _write_goal,
    _write_workflow,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroPort

__all__: list[str] = []

_RUN_TIMEOUT_SECONDS = 300.0
_PASSING_WORKFLOW = """
digraph FabroEnemyPassing {
    start [shape=Mdiamond, label="Start"]
    done [shape=parallelogram, label="Done", script="echo fabro-enemy-tier1-pass"]
    exit [shape=Msquare, label="Exit"]
    start -> done
    done -> exit
}
"""
_FAILING_WORKFLOW = """
digraph FabroEnemyFailing {
    start [shape=Mdiamond, label="Start"]
    fail [shape=parallelogram, label="Fail", script="echo fabro-enemy-tier1-fail >&2; exit 42"]
    exit [shape=Msquare, label="Exit"]
    start -> fail
    fail -> exit
}
"""
_SLEEPING_WORKFLOW = """
digraph FabroEnemySleeping {
    start [shape=Mdiamond, label="Start"]
    sleep [shape=parallelogram, label="Sleep", timeout="600s", script="sleep 600"]
    exit [shape=Msquare, label="Exit"]
    start -> sleep
    sleep -> exit
}
"""
_FORCED_REMOVAL_STATUS_KINDS = frozenset(("canceled", "cancelled", "failed", "removed"))


def test_preflight_accepts_the_tier1_minimal_run_configuration(
    *,
    tmp_path: Path,
    port: FabroPort,
) -> None:
    workflow = _write_workflow(tmp_path=tmp_path, name="passing", body=_PASSING_WORKFLOW)
    goal = _write_goal(tmp_path=tmp_path, title="preflight")

    result = port.preflight(
        workflow_toml=workflow,
        goal_file=goal,
        inputs=(),
        timeout_seconds=TIMEOUT_SECONDS,
    )

    _assert_success(command=result.command)
    assert result.payload is not None


def test_completed_run_maps_to_green_terminal_path_and_emits_liveness_events(
    *,
    tmp_path: Path,
    config: _FabroTier0Config,
    port: FabroPort,
) -> None:
    workflow = _write_workflow(tmp_path=tmp_path, name="passing", body=_PASSING_WORKFLOW)
    goal = _write_goal(tmp_path=tmp_path, title="completed")

    run = port.run(
        workflow_toml=workflow,
        goal_file=goal,
        inputs=(),
        timeout_seconds=_RUN_TIMEOUT_SECONDS,
    )

    _assert_success(command=run.command)
    assert run.run_id is not None
    inspect = port.inspect(run_id=run.run_id, timeout_seconds=TIMEOUT_SECONDS)
    _assert_success(command=inspect.command)
    assert (
        _terminal_outcome(
            config=config,
            inspect=inspect,
            run_id=run.run_id,
            exit_code=run.command.exit_code,
            stderr=run.command.stderr,
        )
        is None
    )
    events = port.events(run_id=run.run_id, timeout_seconds=TIMEOUT_SECONDS)
    _assert_success(command=events.command)
    event_records = _event_records(stdout=events.command.stdout, payload=events.payload)
    assert any(_has_event_timestamp(event=event) for event in event_records)
    assert any(_event_name(event=event) is not None for event in event_records)


def test_failed_run_maps_to_failed_terminal_path_and_structured_failure_block(
    *,
    tmp_path: Path,
    config: _FabroTier0Config,
    port: FabroPort,
) -> None:
    workflow = _write_workflow(tmp_path=tmp_path, name="failing", body=_FAILING_WORKFLOW)
    goal = _write_goal(tmp_path=tmp_path, title="failed")

    run = port.run(
        workflow_toml=workflow,
        goal_file=goal,
        inputs=(),
        timeout_seconds=_RUN_TIMEOUT_SECONDS,
    )

    assert run.command.exit_code != 0
    assert run.run_id is not None
    inspect = port.inspect(run_id=run.run_id, timeout_seconds=TIMEOUT_SECONDS)
    _assert_success(command=inspect.command)
    outcome = _terminal_outcome(
        config=config,
        inspect=inspect,
        run_id=run.run_id,
        exit_code=run.command.exit_code,
        stderr=run.command.stderr,
    )
    assert outcome is not None
    assert outcome.status == "failed"
    record = _inspect_record(value=inspect.payload)
    failure = _failure_block(value=record)
    assert failure is not None
    assert any(key in failure for key in ("category", "signature", "causes"))


def test_force_remove_in_flight_run_terminates_and_updates_ps_status(
    *,
    tmp_path: Path,
    port: FabroPort,
) -> None:
    workflow = _write_workflow(tmp_path=tmp_path, name="sleeping", body=_SLEEPING_WORKFLOW)
    goal = _write_goal(tmp_path=tmp_path, title="force-remove")

    run = port.run(
        workflow_toml=workflow,
        goal_file=goal,
        inputs=(),
        timeout_seconds=10.0,
    )
    assert run.run_id is not None
    rm = port.rm(run_id=run.run_id, timeout_seconds=TIMEOUT_SECONDS)
    _assert_success(command=rm.command)

    summary = _await_ps_summary(port=port, run_id=run.run_id)

    assert summary is not None
    assert summary.status_kind in _FORCED_REMOVAL_STATUS_KINDS
