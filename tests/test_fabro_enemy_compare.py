"""Tests for the Fabro Enemy Unit Test comparison harness."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

__all__: list[str] = []


def test_comparison_harness_writes_per_assertion_delta(
    *,
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    module_path = Path("fabro-enemy-unit-tests/compare.py")

    assert module_path.is_file()
    compare = _load_compare_module(module_path=module_path)
    calls: list[tuple[str, str, list[str], Path]] = []

    def fake_run(
        *, args: list[str], env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert check is False
        junit_path = _junit_path(args=args)
        calls.append((env["FABRO_EUT_BIN"], env["FABRO_EUT_SERVER"], args, junit_path))
        if len(calls) == 1:
            _write_junit(
                path=junit_path,
                cases={
                    "test_tier0_fabro.py::test_version": "passed",
                    "test_tier0_fabro.py::test_validate": "failed",
                },
            )
            return subprocess.CompletedProcess(args=args, returncode=1)
        _write_junit(
            path=junit_path,
            cases={
                "test_tier0_fabro.py::test_version": "passed",
                "test_tier0_fabro.py::test_validate": "passed",
                "test_tier0_fabro.py::test_new_candidate_case": "failed",
            },
        )
        return subprocess.CompletedProcess(args=args, returncode=1)

    monkeypatch.setattr(compare.subprocess, "run", fake_run)
    artifact_path = tmp_path / "comparison.md"

    exit_code = compare.main(
        argv=[
            "--pinned-bin",
            "/opt/fabro-pinned",
            "--pinned-server",
            "http://127.0.0.1:32276",
            "--candidate-bin",
            "/opt/fabro-candidate",
            "--candidate-server",
            "http://127.0.0.1:32286",
            "--artifact",
            str(artifact_path),
        ]
    )

    assert exit_code == 1
    assert [(call[0], call[1]) for call in calls] == [
        ("/opt/fabro-pinned", "http://127.0.0.1:32276"),
        ("/opt/fabro-candidate", "http://127.0.0.1:32286"),
    ]
    test_args = [arg for arg in calls[0][2] if arg.startswith("fabro-enemy-unit-tests/")]
    assert test_args == [
        "fabro-enemy-unit-tests/test_tier0_fabro.py",
        "fabro-enemy-unit-tests/test_tier0_watchdog_gap.py",
    ]
    artifact = artifact_path.read_text()
    assert "| Assertion | Pinned | Candidate | Delta |" in artifact
    assert "| `test_tier0_fabro.py::test_validate` | failed | passed | improved |" in artifact
    assert (
        "| `test_tier0_fabro.py::test_new_candidate_case` | missing | failed | candidate-only |"
        in artifact
    )
    assert "## Delta" in artifact
    assert "- Regressions: 0" in artifact
    assert "- Improvements: 1" in artifact
    assert "- Candidate-only assertions: 1" in artifact


def test_comparison_harness_reports_empty_delta_for_pinned_vs_pinned(
    *,
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    module_path = Path("fabro-enemy-unit-tests/compare.py")

    assert module_path.is_file()
    compare = _load_compare_module(module_path=module_path)

    def fake_run(
        *, args: list[str], env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert check is False
        assert env["FABRO_EUT_BIN"] == "fabro"
        assert env["FABRO_EUT_SERVER"] == "http://127.0.0.1:32276"
        _write_junit(
            path=_junit_path(args=args),
            cases={
                "test_tier0_fabro.py::test_version": "passed",
                "test_tier0_fabro.py::test_validate": "passed",
            },
        )
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr(compare.subprocess, "run", fake_run)
    artifact_path = tmp_path / "comparison.md"

    exit_code = compare.main(argv=["--artifact", str(artifact_path)])

    assert exit_code == 0
    artifact = artifact_path.read_text()
    assert "| `test_tier0_fabro.py::test_version` | passed | passed | unchanged |" in artifact
    assert "- Regressions: 0" in artifact
    assert "- Improvements: 0" in artifact
    assert "- Pinned-only assertions: 0" in artifact
    assert "- Candidate-only assertions: 0" in artifact


def test_comparison_harness_leaves_unset_expected_values_absent(
    *,
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    module_path = Path("fabro-enemy-unit-tests/compare.py")

    assert module_path.is_file()
    compare = _load_compare_module(module_path=module_path)
    expected_keys = [
        "FABRO_EUT_EXPECTED_CLIENT_VERSION",
        "FABRO_EUT_EXPECTED_CLIENT_COMMIT",
        "FABRO_EUT_EXPECTED_CLIENT_DATE",
        "FABRO_EUT_EXPECTED_SERVER_VERSION",
        "FABRO_EUT_EXPECTED_SERVER_COMMIT",
        "FABRO_EUT_EXPECTED_SERVER_DATE",
    ]
    for key in expected_keys:
        monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv(key.replace("FABRO_EUT_", "FABRO_EUT_PINNED_", 1), raising=False)
        monkeypatch.delenv(key.replace("FABRO_EUT_", "FABRO_EUT_CANDIDATE_", 1), raising=False)

    def fake_run(
        *, args: list[str], env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert check is False
        assert all(key not in env for key in expected_keys)
        _write_junit(
            path=_junit_path(args=args), cases={"test_tier0_fabro.py::test_version": "passed"}
        )
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr(compare.subprocess, "run", fake_run)

    assert compare.main(argv=["--artifact", str(tmp_path / "comparison.md")]) == 0


def test_comparison_harness_maps_target_specific_expected_values(
    *,
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    module_path = Path("fabro-enemy-unit-tests/compare.py")

    assert module_path.is_file()
    compare = _load_compare_module(module_path=module_path)
    monkeypatch.setenv("FABRO_EUT_PINNED_EXPECTED_CLIENT_VERSION", "0.254.0")
    monkeypatch.setenv("FABRO_EUT_CANDIDATE_EXPECTED_CLIENT_VERSION", "0.255.0")
    seen_versions: list[str] = []

    def fake_run(
        *, args: list[str], env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert check is False
        seen_versions.append(env["FABRO_EUT_EXPECTED_CLIENT_VERSION"])
        _write_junit(
            path=_junit_path(args=args),
            cases={"test_tier0_fabro.py::test_version": "passed"},
        )
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr(compare.subprocess, "run", fake_run)

    assert compare.main(argv=["--artifact", str(tmp_path / "comparison.md")]) == 0
    assert seen_versions == ["0.254.0", "0.255.0"]


def test_comparison_harness_fails_clearly_when_tier0_tests_are_absent(
    *,
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    module_path = Path("fabro-enemy-unit-tests/compare.py")

    assert module_path.is_file()
    compare = _load_compare_module(module_path=module_path)
    monkeypatch.setattr(compare, "_TEST_ROOT", tmp_path)

    with pytest.raises(FileNotFoundError) as error:
        compare.main(argv=["--artifact", str(tmp_path / "comparison.md")])

    assert (
        str(error.value) == f"no Fabro Enemy Unit Test files matched {tmp_path / 'test_tier0_*.py'}"
    )


def _load_compare_module(*, module_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("fabro_enemy_compare", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _junit_path(*, args: list[str]) -> Path:
    return Path(
        next(arg.removeprefix("--junitxml=") for arg in args if arg.startswith("--junitxml="))
    )


def _write_junit(*, path: Path, cases: dict[str, str]) -> None:
    testcase_xml = "\n".join(
        _testcase_xml(assertion_id=key, status=value) for key, value in cases.items()
    )
    path.write_text(f'<testsuite tests="{len(cases)}">\n{testcase_xml}\n</testsuite>\n')


def _testcase_xml(*, assertion_id: str, status: str) -> str:
    if status == "passed":
        return f'  <testcase classname="{assertion_id}" name="" />'
    return f'  <testcase classname="{assertion_id}" name=""><failure /></testcase>'
