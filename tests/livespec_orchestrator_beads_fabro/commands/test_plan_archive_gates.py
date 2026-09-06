"""Working-tree reference gate that guards the plan-archive directory move."""

from __future__ import annotations

import importlib
from pathlib import Path

_MODULE = "livespec_orchestrator_beads_fabro.commands._plan_archive_gates"


def _module_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / ".claude-plugin"
        / "scripts"
        / "livespec_orchestrator_beads_fabro"
        / "commands"
        / "_plan_archive_gates.py"
    )


def _write(*, path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(text, encoding="utf-8")


def test_archive_gates_module_owns_the_refusal_type_and_the_sweep() -> None:
    assert _module_path().is_file()
    gates = importlib.import_module(_MODULE)
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")

    assert plan.PlanArchiveRefusedError is gates.PlanArchiveRefusedError
    assert sorted(gates.__all__) == ["PlanArchiveRefusedError", "outside_plan_path_references"]


def test_sweep_names_every_outside_file_reading_the_plan_directory(tmp_path: Path) -> None:
    gates = importlib.import_module(_MODULE)
    _write(path=tmp_path / "plan" / "upgrade" / "rehearsal" / "probe.py", text="raise SystemExit\n")
    _write(path=tmp_path / "tests" / "test_literal.py", text='PACKAGE = "plan/upgrade/rehearsal"\n')
    _write(
        path=tmp_path / "tests" / "test_joined.py",
        text='PROBE = ROOT / "plan" / "upgrade" / "rehearsal" / "probe.py"\n',
    )

    assert gates.outside_plan_path_references(project_root=tmp_path, slug="upgrade") == (
        "tests/test_joined.py",
        "tests/test_literal.py",
    )


def test_sweep_excludes_the_plan_tree_git_venv_vendored_and_node_modules(tmp_path: Path) -> None:
    gates = importlib.import_module(_MODULE)
    reference = 'PATH = "plan/upgrade/notes.md"\n'
    _write(path=tmp_path / "plan" / "upgrade" / "notes.md", text=reference)
    _write(path=tmp_path / "plan" / "archive" / "older" / "handoff.md", text=reference)
    _write(path=tmp_path / ".git" / "COMMIT_EDITMSG", text=reference)
    _write(path=tmp_path / ".venv" / "lib" / "site.py", text=reference)
    _write(path=tmp_path / "node_modules" / "package" / "index.js", text=reference)
    _write(path=tmp_path / "scripts" / "_vendor" / "library.py", text=reference)
    _write(path=tmp_path / "docs" / "guide.md", text=reference)

    assert gates.outside_plan_path_references(project_root=tmp_path, slug="upgrade") == (
        "docs/guide.md",
    )


def test_sweep_ignores_label_strings_and_a_longer_slug_sharing_the_prefix(tmp_path: Path) -> None:
    gates = importlib.import_module(_MODULE)
    (tmp_path / "plan" / "upgrade").mkdir(parents=True)
    _write(path=tmp_path / "tests" / "test_labels.py", text='LABEL = "origin:upgrade"\n')
    _write(path=tmp_path / "tests" / "test_sibling.py", text='PATH = "plan/upgrade-two/x.md"\n')

    assert gates.outside_plan_path_references(project_root=tmp_path, slug="upgrade") == ()


def test_sweep_skips_a_file_whose_bytes_are_not_utf8_text(tmp_path: Path) -> None:
    gates = importlib.import_module(_MODULE)
    (tmp_path / "plan" / "upgrade").mkdir(parents=True)
    binary = tmp_path / "build" / "artifact.bin"
    binary.parent.mkdir(parents=True)
    _ = binary.write_bytes(b"\xffplan/upgrade/probe.py\xfe")

    assert gates.outside_plan_path_references(project_root=tmp_path, slug="upgrade") == ()


def test_outside_path_reference_refusal_names_every_referencing_file() -> None:
    gates = importlib.import_module(_MODULE)

    error = gates.PlanArchiveRefusedError.outside_path_references(
        slug="upgrade",
        paths=("tests/test_a.py", "tests/test_b.py"),
    )

    assert str(error) == (
        "files outside plan/ reference plan/upgrade/: tests/test_a.py, tests/test_b.py"
    )
