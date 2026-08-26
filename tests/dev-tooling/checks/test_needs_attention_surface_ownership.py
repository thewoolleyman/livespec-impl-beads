"""Tests for the needs-attention surface ownership guard."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK_PATH = _REPO_ROOT / "dev-tooling" / "checks" / "needs_attention_surface_ownership.py"


def _load_check() -> ModuleType:
    assert _CHECK_PATH.is_file()
    spec = importlib.util.spec_from_file_location(
        "needs_attention_surface_ownership_under_test",
        _CHECK_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_needs_attention_composition_has_no_overseer_or_foreman_surface_reads() -> None:
    check = _load_check()

    assert check.ownership_findings(repo_root=_REPO_ROOT) == []


def test_guard_ignores_docstring_mentions_and_plan_timeline_prose() -> None:
    check = _load_check()

    assert (
        check.source_findings(
            source='"""The overseer and foreman are mentioned in prose only."""\nVALUE = 1\n',
            path=Path("commands/_needs_attention_docstring_probe.py"),
        )
        == []
    )
    assert all(
        finding.path.name != "_plan_timeline.py"
        for finding in check.ownership_findings(repo_root=_REPO_ROOT)
    )


def test_guard_flags_executable_surface_references() -> None:
    check = _load_check()

    findings = check.source_findings(
        source="\n".join(
            [
                "import foreman_api as plan_queue",
                "overseer_client = object()",
                "snapshot = overseer_client.items",
                "path = 'plan/foreman/handoff.md'",
                "",
            ]
        ),
        path=Path("commands/_needs_attention_surface_probe.py"),
    )

    assert [(finding.token, finding.lineno) for finding in findings] == [
        ("foreman", 1),
        ("overseer", 2),
        ("overseer", 3),
        ("foreman", 4),
    ]


def test_guard_fires_when_composition_reads_overseer_surface(tmp_path: Path) -> None:
    check = _load_check()
    scripts = tmp_path / ".claude-plugin" / "scripts"
    commands = scripts / "livespec_orchestrator_beads_fabro" / "commands"
    commands.mkdir(parents=True)
    source_commands = (
        _REPO_ROOT / ".claude-plugin" / "scripts" / "livespec_orchestrator_beads_fabro" / "commands"
    )
    shutil.copy2(source_commands / "needs_attention.py", commands / "needs_attention.py")
    _ = (commands / "_needs_attention_probe.py").write_text(
        "from livespec_overseer.commands.needs_attention import main\n",
        encoding="utf-8",
    )

    findings = check.ownership_findings(repo_root=tmp_path)

    assert [(finding.path.name, finding.token) for finding in findings] == [
        ("_needs_attention_probe.py", "overseer")
    ]


def test_main_returns_nonzero_for_forbidden_surface_read(
    tmp_path: Path,
    monkeypatch,
) -> None:
    check = _load_check()
    commands = (
        tmp_path / ".claude-plugin" / "scripts" / "livespec_orchestrator_beads_fabro" / "commands"
    )
    commands.mkdir(parents=True)
    _ = (commands / "needs_attention.py").write_text(
        "from livespec_foreman.attention import read_attention\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert check.main() == 1
