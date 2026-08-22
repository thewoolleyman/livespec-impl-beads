"""Public path-helper surface extracted from the Dispatcher."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Protocol, cast

from livespec_orchestrator_beads_fabro.commands import _dispatcher_paths
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult


class _RunnerLike(Protocol):
    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult: ...


class _RunnerFactory(Protocol):
    def __call__(self) -> _RunnerLike: ...


def test_dispatcher_paths_exports_promoted_public_helpers() -> None:
    assert _dispatcher_paths.__all__ == [
        "calibration_spans_path",
        "cost_report_spans_path",
        "cost_sink_path",
        "heartbeat_path",
        "journal_path",
        "plugin_root",
        "reflector_oob_spans_path",
        "run_turn_sink_path",
        "spans_path",
        "store_config",
        "workflow_toml",
    ]


def test_nf39_fake_runner_helper_is_covered(tmp_path: Path) -> None:
    test_path = Path(__file__).with_name("test_dispatcher_nf39.py")
    spec = importlib.util.spec_from_file_location("test_dispatcher_nf39_for_coverage", test_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    runner_factory = cast("_RunnerFactory", vars(module)["_FakeRunner"])
    runner = runner_factory()

    result = runner.run(argv=["gh"], cwd=tmp_path, timeout_seconds=1)

    assert isinstance(result, CommandResult)
    assert result.stdout == "{}"
