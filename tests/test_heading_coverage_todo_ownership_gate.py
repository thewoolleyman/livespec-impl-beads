"""Regression tests for staged heading-coverage TODO ownership arming."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "just-check-pre-commit-doc-only.sh"
_FAIL_DIAGNOSTIC = 'heading-coverage.json entry has `test: "TODO"` with no owning `work_item`'
_WARN_DIAGNOSTIC = 'heading-coverage.json entry has `test: "TODO"`'


def _run(
    *,
    argv: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env is not None:
        run_env.update(env)
    return subprocess.run(
        argv,
        cwd=cwd,
        env=run_env,
        check=False,
        capture_output=True,
        text=True,
    )


def _write_json(*, path: Path, entries: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def _diagnostic_events(*, stderr: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stderr.splitlines():
        events.append(cast("dict[str, Any]", json.loads(line)))
    return events


def _unowned_entry(*, heading: str, reason: str = "existing backlog") -> dict[str, object]:
    return {
        "spec_root": "SPECIFICATION",
        "spec_file": "constraints.md",
        "heading": heading,
        "test": "TODO",
        "reason": reason,
    }


def _owned_entry(*, heading: str) -> dict[str, object]:
    entry = _unowned_entry(heading=heading, reason="new owned placeholder")
    entry["work_item"] = "bd-ib-sayzqh"
    return entry


def _install_fake_just(*, repo: Path) -> Path:
    bin_dir = repo / "fake-bin"
    bin_dir.mkdir()
    fake_just = bin_dir / "just"
    fake_just.write_text(
        """#!/usr/bin/env bash
set -uo pipefail
target="${1:-}"
if [[ "${target}" == "check-no-todo-registry" ]]; then
    if [[ -n "${LIVESPEC_FAIL_IF_HEADING_COVERAGE_TODOS_EXIST:-}" ]]; then
        echo "release:${target}:armed" >> just.log
        python - <<'PY'
import json
from pathlib import Path

entries = json.loads(Path("tests/heading-coverage.json").read_text(encoding="utf-8"))
for entry in entries:
    if entry.get("test") == "TODO" and not str(entry.get("work_item", "")).strip():
        print('heading-coverage.json entry has `test: "TODO"` with no owning `work_item`')
        raise SystemExit(1)
raise SystemExit(0)
PY
    else
        echo "release:${target}:unarmed" >> just.log
        echo 'heading-coverage.json entry has `test: "TODO"`'
    fi
else
    echo "target:${target}:ok" >> just.log
fi
""",
        encoding="utf-8",
    )
    fake_just.chmod(fake_just.stat().st_mode | stat.S_IXUSR)
    return bin_dir


def _init_repo(*, tmp_path: Path) -> tuple[Path, dict[str, str]]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(argv=["git", "init"], cwd=repo)
    _run(argv=["git", "config", "user.email", "test@example.com"], cwd=repo)
    _run(argv=["git", "config", "user.name", "Test User"], cwd=repo)
    _write_json(
        path=repo / "tests" / "heading-coverage.json",
        entries=[_unowned_entry(heading="## Existing backlog")],
    )
    (repo / "SPECIFICATION").mkdir()
    (repo / "SPECIFICATION" / "constraints.md").write_text(
        "## Existing backlog\n",
        encoding="utf-8",
    )
    _run(argv=["git", "add", "."], cwd=repo)
    baseline = _run(argv=["git", "commit", "-m", "baseline"], cwd=repo)
    assert baseline.returncode == 0, baseline.stderr

    hook = repo / ".git" / "hooks" / "pre-commit"
    shutil.copy2(_SCRIPT, hook)
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    fake_bin = _install_fake_just(repo=repo)
    return repo, {"PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"}


def _commit(*, repo: Path, env: dict[str, str], message: str) -> subprocess.CompletedProcess[str]:
    return _run(argv=["git", "commit", "-m", message], cwd=repo, env=env)


def test_doc_only_heading_coverage_edit_with_only_owned_new_todo_commits_from_staged_blob(
    *,
    tmp_path: Path,
) -> None:
    repo, env = _init_repo(tmp_path=tmp_path)
    staged_entries = [
        _unowned_entry(heading="## Existing backlog"),
        _owned_entry(heading="## New owned placeholder"),
    ]
    _write_json(path=repo / "tests" / "heading-coverage.json", entries=staged_entries)
    _run(argv=["git", "add", "tests/heading-coverage.json"], cwd=repo)

    unstaged_entries = [*staged_entries, _unowned_entry(heading="## Unstaged new backlog")]
    _write_json(path=repo / "tests" / "heading-coverage.json", entries=unstaged_entries)
    result = _commit(repo=repo, env=env, message="doc-only staged owned TODO")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "staged changeset edits tests/heading-coverage.json" in result.stderr
    assert "authors an unowned" not in result.stderr
    assert "release:check-no-todo-registry:unarmed" in (repo / "just.log").read_text(
        encoding="utf-8"
    )


def test_doc_only_heading_coverage_edit_adding_unowned_todo_is_refused(
    *,
    tmp_path: Path,
) -> None:
    repo, env = _init_repo(tmp_path=tmp_path)
    _write_json(
        path=repo / "tests" / "heading-coverage.json",
        entries=[
            _unowned_entry(heading="## Existing backlog"),
            _unowned_entry(heading="## New unowned placeholder"),
        ],
    )
    _run(argv=["git", "add", "tests/heading-coverage.json"], cwd=repo)

    result = _commit(repo=repo, env=env, message="doc-only unowned TODO")

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "authors an unowned heading-coverage TODO" in output
    assert _FAIL_DIAGNOSTIC in output
    assert "release:check-no-todo-registry:armed" in (repo / "just.log").read_text(encoding="utf-8")


def test_doc_only_heading_coverage_edit_modifying_unowned_todo_is_refused(
    *,
    tmp_path: Path,
) -> None:
    repo, env = _init_repo(tmp_path=tmp_path)
    _write_json(
        path=repo / "tests" / "heading-coverage.json",
        entries=[_unowned_entry(heading="## Existing backlog", reason="modified backlog")],
    )
    _run(argv=["git", "add", "tests/heading-coverage.json"], cwd=repo)

    result = _commit(repo=repo, env=env, message="doc-only modified unowned TODO")

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "authors an unowned heading-coverage TODO" in output
    assert _FAIL_DIAGNOSTIC in output
    assert "release:check-no-todo-registry:armed" in (repo / "just.log").read_text(encoding="utf-8")


def test_genuine_release_tier_still_fails_unowned_todo_with_existing_diagnostic(
    *,
    tmp_path: Path,
) -> None:
    _write_json(
        path=tmp_path / "tests" / "heading-coverage.json",
        entries=[_unowned_entry(heading="## New unowned placeholder")],
    )

    result = _run(
        argv=[sys.executable, "-m", "livespec_dev_tooling.checks.no_todo_registry"],
        cwd=tmp_path,
        env={"LIVESPEC_FAIL_IF_HEADING_COVERAGE_TODOS_EXIST": "true"},
    )

    assert result.returncode == 1
    assert any(
        event.get("event") == _FAIL_DIAGNOSTIC for event in _diagnostic_events(stderr=result.stderr)
    )


def test_unarmed_whole_file_scan_still_warns_and_exits_zero(*, tmp_path: Path) -> None:
    _write_json(
        path=tmp_path / "tests" / "heading-coverage.json",
        entries=[_unowned_entry(heading="## Existing backlog")],
    )

    result = _run(
        argv=[sys.executable, "-m", "livespec_dev_tooling.checks.no_todo_registry"],
        cwd=tmp_path,
    )

    assert result.returncode == 0
    events = _diagnostic_events(stderr=result.stderr)
    assert any(event.get("event") == _WARN_DIAGNOSTIC for event in events)
    assert all(event.get("event") != _FAIL_DIAGNOSTIC for event in events)
