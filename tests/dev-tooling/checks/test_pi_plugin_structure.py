"""Tests for the `pi_plugin_structure` structural check.

The check validates the orchestrator plugin's pi cross-runtime surface: the
repo-root `package.json` pi manifest, the shared plugin-root resolver, and the
`.claude-plugin/.pi-plugin/skills/livespec-orchestrator-beads-fabro-<op>/SKILL.md`
bindings — one per operation the plugin ships under `.claude-plugin/skills/`,
derived rather than enumerated.

The check is pure-filesystem (no beads / no store), so these tests build a
COMPLETE fixture surface under `tmp_path` and drive the helpers against that
root directly. `monkeypatch.chdir` is applied for parity with the other
dev-tooling check tests and so no helper defaulting to the current directory can
reach the real repository.
"""

from __future__ import annotations

import importlib.util
import json
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK_PATH = _REPO_ROOT / "dev-tooling" / "checks" / "pi_plugin_structure.py"
_CHECK_MODULE_NAME = "pi_plugin_structure_under_test"


def _load_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location(_CHECK_MODULE_NAME, _CHECK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_CHECK_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


_CHECK = _load_check()

_PLUGIN_NAME = "livespec-orchestrator-beads-fabro"
_WRAPPER_OPS = ("next", "detect-impl-gaps")
_PROSE_OPS = ("implement",)
_SKILLS_PATH = "./.claude-plugin/.pi-plugin/skills"


def _wrapper_body(*, operation: str) -> str:
    wrapper = f"{operation.replace('-', '_')}.py"
    return (
        f"---\nname: {_PLUGIN_NAME}-{operation}\n"
        f"description: Thin pi binding of {operation}.\nallowed-tools: bash\n---\n\n"
        f"# {_PLUGIN_NAME}-{operation} — pi binding\n\n"
        "Resolution is delegated to lib/resolve-plugin-root.sh.\n\n"
        '```bash\nPLUGIN_ROOT="$(bash "<skill-dir>/../../lib/resolve-plugin-root.sh" .)" || exit 1\n```\n\n'
        f'```bash\npython3 "$PLUGIN_ROOT/scripts/bin/{wrapper}" "$@"\n```\n'
    )


def _prose_body(*, operation: str) -> str:
    return (
        f"---\nname: {_PLUGIN_NAME}-{operation}\n"
        f"description: Thin pi binding of {operation}.\nallowed-tools: bash read\n---\n\n"
        f"# {_PLUGIN_NAME}-{operation} — pi binding\n\n"
        "Resolution is delegated to lib/resolve-plugin-root.sh.\n\n"
        '```bash\nPLUGIN_ROOT="$(bash "<skill-dir>/../../lib/resolve-plugin-root.sh" .)" || exit 1\n```\n\n'
        f"Read $PLUGIN_ROOT/prose/{operation}.md completely before acting.\n"
    )


def _manifest() -> dict[str, object]:
    return {
        "name": _PLUGIN_NAME,
        "keywords": ["pi-package"],
        "pi": {"skills": [_SKILLS_PATH]},
    }


@pytest.fixture
def surface(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A complete, violation-free pi surface rooted at `tmp_path`."""
    monkeypatch.chdir(tmp_path)
    plugin = tmp_path / ".claude-plugin"
    for operation in (*_WRAPPER_OPS, *_PROSE_OPS):
        (plugin / "skills" / operation).mkdir(parents=True)
    for operation in _WRAPPER_OPS:
        wrapper = plugin / "scripts" / "bin" / f"{operation.replace('-', '_')}.py"
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text("", encoding="utf-8")
        _write_binding(root=tmp_path, operation=operation, body=_wrapper_body(operation=operation))
    for operation in _PROSE_OPS:
        prose = plugin / "prose" / f"{operation}.md"
        prose.parent.mkdir(parents=True, exist_ok=True)
        prose.write_text("prose", encoding="utf-8")
        _write_binding(root=tmp_path, operation=operation, body=_prose_body(operation=operation))
    resolver = plugin / ".pi-plugin" / "lib" / "resolve-plugin-root.sh"
    resolver.parent.mkdir(parents=True, exist_ok=True)
    resolver.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    resolver.chmod(resolver.stat().st_mode | stat.S_IXUSR)
    (tmp_path / "package.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    return tmp_path


def _write_binding(*, root: Path, operation: str, body: str) -> Path:
    path = (
        root
        / ".claude-plugin"
        / ".pi-plugin"
        / "skills"
        / f"{_PLUGIN_NAME}-{operation}"
        / "SKILL.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _binding(*, root: Path, operation: str) -> Path:
    return (
        root
        / ".claude-plugin"
        / ".pi-plugin"
        / "skills"
        / f"{_PLUGIN_NAME}-{operation}"
        / "SKILL.md"
    )


def _write_manifest(*, root: Path, manifest: object) -> None:
    (root / "package.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_complete_surface_has_no_violations(surface: Path) -> None:
    assert _CHECK.violations(root=surface) == []


def test_operations_are_derived_from_the_claude_bindings(surface: Path) -> None:
    assert _CHECK.operations(root=surface) == sorted((*_WRAPPER_OPS, *_PROSE_OPS))


def test_operations_is_empty_without_a_claude_bindings_tree(tmp_path: Path) -> None:
    assert _CHECK.operations(root=tmp_path) == []


def test_backing_is_derived_from_the_presence_of_prose(surface: Path) -> None:
    assert _CHECK.wrapper_for(root=surface, operation="implement") is None
    assert _CHECK.wrapper_for(root=surface, operation="detect-impl-gaps") == "detect_impl_gaps.py"


def test_a_repo_with_no_operations_is_itself_a_violation(tmp_path: Path) -> None:
    found = _CHECK.violations(root=tmp_path)
    assert len(found) == 1
    assert "no operations found" in found[0]


def test_a_missing_binding_is_reported(surface: Path) -> None:
    _binding(root=surface, operation="next").unlink()
    assert any("missing pi binding" in violation for violation in _CHECK.violations(root=surface))


def test_a_frontmatter_name_that_does_not_match_the_directory_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace(f"{_PLUGIN_NAME}-next", "next", 1),
        encoding="utf-8",
    )
    assert any("frontmatter name is" in violation for violation in _CHECK.violations(root=surface))


def test_a_missing_description_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace("description: Thin pi binding of next.\n", ""),
        encoding="utf-8",
    )
    assert any(
        "carries no description" in violation for violation in _CHECK.violations(root=surface)
    )


def test_an_unquoted_frontmatter_value_with_colon_space_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "description: Thin pi binding of next.",
            "description: Thin pi binding of next. Mutating: it writes records.",
        ),
        encoding="utf-8",
    )
    assert any(
        "carries no description" in violation for violation in _CHECK.violations(root=surface)
    )


def test_a_quoted_frontmatter_value_with_colon_space_is_accepted(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "description: Thin pi binding of next.",
            'description: "Thin pi binding of next. Mutating: it writes records."',
        ),
        encoding="utf-8",
    )
    assert _CHECK.violations(root=surface) == []


def test_missing_allowed_tools_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace("allowed-tools: bash\n", ""), encoding="utf-8"
    )
    assert any(
        "declares no allowed-tools" in violation for violation in _CHECK.violations(root=surface)
    )


def test_a_name_breaking_the_agent_skills_rules_is_reported(surface: Path) -> None:
    directory = surface / ".claude-plugin" / ".pi-plugin" / "skills" / f"{_PLUGIN_NAME}-next"
    path = directory / "SKILL.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            f"name: {_PLUGIN_NAME}-next", f"name: {_PLUGIN_NAME}--Next"
        ),
        encoding="utf-8",
    )
    found = _CHECK.violations(root=surface)
    assert any("breaks the Agent Skills name rules" in violation for violation in found)


def test_a_body_without_frontmatter_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text("no frontmatter here\n", encoding="utf-8")
    found = _CHECK.violations(root=surface)
    assert any("frontmatter name is ''" in violation for violation in found)


def test_an_unterminated_frontmatter_block_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        f"---\nname: {_PLUGIN_NAME}-next\ndescription: Thin pi binding.\n", encoding="utf-8"
    )
    found = _CHECK.violations(root=surface)
    assert any("declares no allowed-tools" in violation for violation in found)


def test_a_blank_line_inside_frontmatter_does_not_hide_the_fields(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            f"name: {_PLUGIN_NAME}-next\n", f"\nname: {_PLUGIN_NAME}-next\n", 1
        ),
        encoding="utf-8",
    )
    assert _CHECK.violations(root=surface) == []


def test_a_body_not_delegating_to_the_resolver_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "lib/resolve-plugin-root.sh", "an inline algorithm"
        ),
        encoding="utf-8",
    )
    assert any(
        "does not delegate plugin-root resolution" in v for v in _CHECK.violations(root=surface)
    )


def test_a_body_without_the_plugin_root_variable_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="implement")
    path.write_text(
        path.read_text(encoding="utf-8").replace("$PLUGIN_ROOT", "SOME_OTHER_ROOT"),
        encoding="utf-8",
    )
    assert any(
        "carries no $PLUGIN_ROOT" in violation for violation in _CHECK.violations(root=surface)
    )


def test_a_live_claude_plugin_root_token_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    token = "${CLAUDE_PLUGIN" + "_ROOT}"
    path.write_text(
        path.read_text(encoding="utf-8") + f"\nSee {token} for the root.\n", encoding="utf-8"
    )
    assert any(
        "live Claude plugin-root token" in violation
        for violation in _CHECK.violations(root=surface)
    )


def test_a_reference_to_another_runtimes_bindings_tree_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8") + "\nSee .codex-plugin/skills/next instead.\n",
        encoding="utf-8",
    )
    assert any(
        "another runtime's bindings tree" in violation
        for violation in _CHECK.violations(root=surface)
    )


def test_a_prose_backed_binding_that_does_not_read_its_prose_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="implement")
    path.write_text(
        path.read_text(encoding="utf-8").replace("prose/implement.md", "its own restated steps"),
        encoding="utf-8",
    )
    assert any("does not read prose/implement.md" in v for v in _CHECK.violations(root=surface))


def test_a_wrapper_backed_binding_that_does_not_invoke_its_wrapper_is_reported(
    surface: Path,
) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace("scripts/bin/next.py", "scripts/bin/other.py"),
        encoding="utf-8",
    )
    assert any("does not invoke scripts/bin/next.py" in v for v in _CHECK.violations(root=surface))


def test_a_fenced_invocation_using_uv_run_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            'python3 "$PLUGIN_ROOT/scripts/bin/next.py" "$@"',
            'uv run python3 "$PLUGIN_ROOT/scripts/bin/next.py" "$@"',
        ),
        encoding="utf-8",
    )
    assert any("uses `uv run`" in violation for violation in _CHECK.violations(root=surface))


def test_a_fenced_invocation_hardcoding_the_plugin_directory_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            'python3 "$PLUGIN_ROOT/scripts/bin/next.py" "$@"',
            'python3 ".claude-plugin/scripts/bin/next.py" "$@"',
        ),
        encoding="utf-8",
    )
    assert any(
        "hard-codes a plugin-directory literal" in v for v in _CHECK.violations(root=surface)
    )


def test_a_fenced_invocation_without_the_plugin_root_token_is_reported(surface: Path) -> None:
    path = _binding(root=surface, operation="next")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            'python3 "$PLUGIN_ROOT/scripts/bin/next.py" "$@"',
            'python3 "$SOME_OTHER_ROOT/scripts/bin/next.py" "$@"',
        ),
        encoding="utf-8",
    )
    found = _CHECK.violations(root=surface)
    assert any("lacks the $PLUGIN_ROOT token" in violation for violation in found)


def test_an_undeclared_binding_is_reported(surface: Path) -> None:
    _write_binding(root=surface, operation="retired-op", body=_wrapper_body(operation="retired-op"))
    assert any(
        "undeclared pi binding" in violation for violation in _CHECK.violations(root=surface)
    )


def test_a_missing_bindings_tree_is_reported(surface: Path) -> None:
    found = _CHECK.undeclared_violations(root=surface / "elsewhere", expected=set())
    assert len(found) == 1
    assert "missing pi bindings tree" in found[0]


def test_a_missing_resolver_is_reported(surface: Path) -> None:
    (surface / ".claude-plugin" / ".pi-plugin" / "lib" / "resolve-plugin-root.sh").unlink()
    assert any(
        "missing the shared plugin-root resolver" in v for v in _CHECK.violations(root=surface)
    )


def test_a_non_executable_resolver_is_reported(surface: Path) -> None:
    resolver = surface / ".claude-plugin" / ".pi-plugin" / "lib" / "resolve-plugin-root.sh"
    resolver.chmod(0o644)
    assert any("is not executable" in violation for violation in _CHECK.violations(root=surface))


def test_a_missing_manifest_is_reported(surface: Path) -> None:
    (surface / "package.json").unlink()
    assert any(
        "missing pi package manifest" in violation for violation in _CHECK.violations(root=surface)
    )


def test_an_unparseable_manifest_is_reported(surface: Path) -> None:
    (surface / "package.json").write_text("{not json", encoding="utf-8")
    assert any("not valid JSON" in violation for violation in _CHECK.violations(root=surface))


def test_a_manifest_naming_another_plugin_is_reported(surface: Path) -> None:
    manifest = _manifest()
    manifest["name"] = "some-other-plugin"
    _write_manifest(root=surface, manifest=manifest)
    assert any(
        "expected 'livespec-orchestrator-beads-fabro'" in v for v in _CHECK.violations(root=surface)
    )


def test_a_manifest_without_the_pi_package_keyword_is_reported(surface: Path) -> None:
    manifest = _manifest()
    manifest["keywords"] = ["something-else"]
    _write_manifest(root=surface, manifest=manifest)
    assert any(
        "must include 'pi-package'" in violation for violation in _CHECK.violations(root=surface)
    )


def test_a_manifest_without_a_pi_block_is_reported(surface: Path) -> None:
    manifest = _manifest()
    del manifest["pi"]
    _write_manifest(root=surface, manifest=manifest)
    assert any(
        "carries no `pi` manifest block" in violation
        for violation in _CHECK.violations(root=surface)
    )


def test_a_manifest_declaring_pi_extensions_is_reported(surface: Path) -> None:
    manifest = _manifest()
    manifest["pi"] = {"skills": [_SKILLS_PATH], "extensions": ["./extensions"]}
    _write_manifest(root=surface, manifest=manifest)
    assert any(
        "declares pi.extensions" in violation for violation in _CHECK.violations(root=surface)
    )


def test_a_manifest_naming_the_wrong_skills_path_is_reported(surface: Path) -> None:
    manifest = _manifest()
    manifest["pi"] = {"skills": ["./skills"]}
    _write_manifest(root=surface, manifest=manifest)
    assert any(
        "pi.skills is ['./skills']" in violation for violation in _CHECK.violations(root=surface)
    )


def test_a_manifest_naming_an_absent_skills_directory_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_manifest(root=tmp_path, manifest=_manifest())
    found = _CHECK.manifest_violations(root=tmp_path)
    assert any("which does not exist" in violation for violation in found)


def test_main_returns_zero_against_the_live_repository(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    assert _CHECK.main() == 0


def test_main_returns_one_when_the_surface_is_broken(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_CHECK, "_REPO_ROOT", tmp_path)
    assert _CHECK.main() == 1
