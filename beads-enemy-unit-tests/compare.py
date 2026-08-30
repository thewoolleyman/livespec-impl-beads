"""Compare Beads Enemy Unit Test results across two `bd` binary / store pairs.

Mirrors `fabro-enemy-unit-tests/compare.py`. This module owns RUNNING the two
tier-0 pytest legs (control binary vs candidate) and reading their JUnit output
into per-assertion statuses; the sibling `_comparison_report` owns the delta,
the artifact, and the verdict.

Exit code contract: 0 iff BOTH pytest legs exited 0 AND the rendered comparison
recorded no delta of any category. `just beads-enemy-compare` gates on it, so a
skip that differs across the two binaries (a capability present in one, absent
in the other) moves the verdict, not just an outright failure.
"""

# pyright: reportImplicitStringConcatenation=false, reportUnusedCallResult=false
# The testcase regex is an intentional multi-line implicit concatenation, and
# `argparse.add_argument` results are discarded by design.

import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path

from _comparison_report import Comparison, RunResult, Target, build_report

__all__: list[str] = []

_TEST_ROOT = Path("beads-enemy-unit-tests")
_TESTCASE_PATTERN = re.compile(
    r"<testcase\b(?P<empty_attrs>[^>]*)/>|"
    r"<testcase\b(?P<body_attrs>[^>]*)>(?P<body>.*?)</testcase>",
    re.DOTALL,
)


def main(*, argv: list[str] | None = None) -> int:
    args = _parse_args(argv=argv)
    comparison = _run_comparison(
        pinned=Target(
            label="pinned",
            bd_bin=args.pinned_bin,
            cwd=args.pinned_cwd,
            database=args.pinned_database,
        ),
        candidate=Target(
            label="candidate",
            bd_bin=args.candidate_bin,
            cwd=args.candidate_cwd,
            database=args.candidate_database,
        ),
    )
    report = build_report(comparison=comparison)
    _ = args.artifact.write_text(report.markdown)
    return report.exit_code


def _parse_args(*, argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Beads Enemy Unit Tests against pinned and candidate binary/store pairs.",
    )
    parser.add_argument("--pinned-bin", default=_env(primary="PINNED_BIN", fallback="BIN"))
    parser.add_argument("--pinned-cwd", default=_env(primary="PINNED_CWD", fallback="CWD"))
    parser.add_argument("--candidate-bin", default=_env(primary="CANDIDATE_BIN", fallback="BIN"))
    parser.add_argument("--candidate-cwd", default=_env(primary="CANDIDATE_CWD", fallback="CWD"))
    parser.add_argument(
        "--pinned-database", default=_env(primary="PINNED_DATABASE", fallback="DATABASE")
    )
    parser.add_argument(
        "--candidate-database", default=_env(primary="CANDIDATE_DATABASE", fallback="DATABASE")
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        default=Path("beads-enemy-unit-tests/comparison.md"),
    )
    return parser.parse_args(argv)


def _env(*, primary: str, fallback: str) -> str:
    return os.environ.get(f"BEADS_EUT_{primary}", os.environ.get(f"BEADS_EUT_{fallback}", ""))


def _run_comparison(*, pinned: Target, candidate: Target) -> Comparison:
    with tempfile.TemporaryDirectory(prefix="beads-eut-compare.") as temp_dir:
        temp_path = Path(temp_dir)
        return Comparison(
            pinned=_run_target(target=pinned, junit_path=temp_path / "pinned.xml"),
            candidate=_run_target(target=candidate, junit_path=temp_path / "candidate.xml"),
        )


def _run_target(*, target: Target, junit_path: Path) -> RunResult:
    test_paths = _tier0_test_paths(test_root=_TEST_ROOT)
    completed = subprocess.run(
        args=["uv", "run", "pytest", *test_paths, "-q", f"--junitxml={junit_path}"],
        env=_target_env(target=target),
        check=False,
    )
    return RunResult(
        target=target,
        exit_code=completed.returncode,
        assertions=_read_assertions(junit_path=junit_path),
    )


def _tier0_test_paths(*, test_root: Path) -> list[str]:
    paths = sorted(test_root.glob("test_tier0_*.py"))
    if not paths:
        msg = f"no Beads Enemy Unit Test files matched {test_root / 'test_tier0_*.py'}"
        raise FileNotFoundError(msg)
    return [str(path) for path in paths]


def _target_env(*, target: Target) -> dict[str, str]:
    env = dict(os.environ)
    env["BEADS_EUT_BIN"] = target.bd_bin
    env["BEADS_EUT_CWD"] = target.cwd
    if target.database:
        env["BEADS_EUT_DATABASE"] = target.database
    return env


def _read_assertions(*, junit_path: Path) -> dict[str, str]:
    assertions: dict[str, str] = {}
    for match in _TESTCASE_PATTERN.finditer(junit_path.read_text()):
        attrs = match.group("empty_attrs") or match.group("body_attrs") or ""
        body = match.group("body") or ""
        assertions[_assertion_id(attrs=attrs)] = _status(body=body)
    return assertions


def _assertion_id(*, attrs: str) -> str:
    classname = _attribute(attrs=attrs, name="classname")
    name = _attribute(attrs=attrs, name="name")
    return f"{classname}::{name}".strip(":")


def _attribute(*, attrs: str, name: str) -> str:
    prefix = f' {name}="'
    start = attrs.index(prefix) + len(prefix)
    end = attrs.index('"', start)
    return attrs[start:end]


def _status(*, body: str) -> str:
    """Classify one JUnit testcase body as passed, failed, or skipped."""
    if "<skipped" in body:
        return "skipped"
    if "<failure" in body or "<error" in body:
        return "failed"
    return "passed"


if __name__ == "__main__":
    raise SystemExit(main())
