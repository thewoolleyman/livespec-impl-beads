"""Scenario 42 integration coverage for list-plans."""

import importlib
import json
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_COMMAND_MODULE = (
    _REPO_ROOT
    / ".claude-plugin"
    / "scripts"
    / "livespec_orchestrator_beads_fabro"
    / "commands"
    / "list_plans.py"
)


def _load_command_module() -> ModuleType:
    assert _COMMAND_MODULE.is_file()
    module = importlib.import_module("livespec_orchestrator_beads_fabro.commands.list_plans")
    assert hasattr(module, "list_plans")
    return module


def test_scenario42_list_plans_enumerates_unarchived_plans(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_command_module()
    plan = tmp_path / "plan"
    _ = (plan / "beta-topic").mkdir(parents=True)
    _ = (plan / "alpha-topic").mkdir()
    _ = (plan / "archive" / "old-topic").mkdir(parents=True)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    rc = module.main(argv=["--json", "--project-root", str(tmp_path)])

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    captured = capsys.readouterr()
    assert rc == 0
    assert json.loads(captured.out) == {"plans": ["alpha-topic", "beta-topic"]}
    assert "old-topic" not in captured.out
    assert "plan/archive" not in captured.out
    assert after == before


def test_scenario42_missing_plan_directory_exits_zero(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_command_module()

    rc = module.main(argv=["--json", "--project-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert rc == 0
    assert json.loads(captured.out) == {"plans": []}
