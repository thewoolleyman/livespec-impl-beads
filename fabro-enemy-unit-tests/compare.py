"""Compare Fabro Enemy Unit Test results across two client/server pairs.

This module owns RUNNING the two pytest legs and reading their JUnit output into
per-assertion statuses; the sibling `_comparison_report` owns what those two
status maps say about each other -- the delta, the artifact, and the verdict.

Exit code contract: 0 iff BOTH pytest legs exited 0 AND the rendered comparison
recorded no delta of any category. A caller may therefore gate on the exit code
to assert an empty delta, which is what `just fabro-enemy-compare` invites.
"""

import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path

from _comparison_report import Comparison, RunResult, Target, build_report

__all__: list[str] = []

_TEST_ROOT = Path("fabro-enemy-unit-tests")
_DEFAULT_SERVER_URL = "http://127.0.0.1:32276"
_TESTCASE_PATTERN = re.compile(
    r"<testcase\b(?P<empty_attrs>[^>]*)/>|"
    r"<testcase\b(?P<body_attrs>[^>]*)>(?P<body>.*?)</testcase>",
    re.DOTALL,
)
_PER_TARGET_ENV_KEYS = (
    "FABRO_EUT_EXPECTED_CLIENT_VERSION",
    "FABRO_EUT_EXPECTED_CLIENT_COMMIT",
    "FABRO_EUT_EXPECTED_CLIENT_DATE",
    "FABRO_EUT_EXPECTED_SERVER_VERSION",
    "FABRO_EUT_EXPECTED_SERVER_COMMIT",
    "FABRO_EUT_EXPECTED_SERVER_DATE",
    "FABRO_EUT_COMPLETED_RUN_ID",
)


def main(*, argv: list[str] | None = None) -> int:
    args = _parse_args(argv=argv)
    comparison = _run_comparison(
        pinned=Target(label="pinned", fabro_bin=args.pinned_bin, server_url=args.pinned_server),
        candidate=Target(
            label="candidate",
            fabro_bin=args.candidate_bin,
            server_url=args.candidate_server,
        ),
    )
    report = build_report(comparison=comparison)
    args.artifact.write_text(report.markdown)
    return report.exit_code


def _parse_args(*, argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Fabro Enemy Unit Tests against pinned and candidate pairs.",
    )
    parser.add_argument(
        "--pinned-bin", default=_env(primary="PINNED_BIN", fallback="BIN", default="fabro")
    )
    parser.add_argument(
        "--pinned-server",
        default=_env(primary="PINNED_SERVER", fallback="SERVER", default=_DEFAULT_SERVER_URL),
    )
    parser.add_argument(
        "--candidate-bin",
        default=_env(primary="CANDIDATE_BIN", fallback="BIN", default="fabro"),
    )
    parser.add_argument(
        "--candidate-server",
        default=_env(primary="CANDIDATE_SERVER", fallback="SERVER", default=_DEFAULT_SERVER_URL),
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        default=Path("fabro-enemy-unit-tests/comparison.md"),
    )
    return parser.parse_args(argv)


def _env(*, primary: str, fallback: str, default: str) -> str:
    return os.environ.get(f"FABRO_EUT_{primary}", os.environ.get(f"FABRO_EUT_{fallback}", default))


def _run_comparison(*, pinned: Target, candidate: Target) -> Comparison:
    with tempfile.TemporaryDirectory(prefix="fabro-eut-compare.") as temp_dir:
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
        raise FileNotFoundError(
            f"no Fabro Enemy Unit Test files matched {test_root / 'test_tier0_*.py'}"
        )
    return [str(path) for path in paths]


def _target_env(*, target: Target) -> dict[str, str]:
    env = dict(os.environ)
    env["FABRO_EUT_BIN"] = target.fabro_bin
    env["FABRO_EUT_SERVER"] = target.server_url
    prefix = f"FABRO_EUT_{target.label.upper()}_"
    for generic_key in _PER_TARGET_ENV_KEYS:
        target_key = generic_key.replace("FABRO_EUT_", prefix, 1)
        if target_key in env:
            env[generic_key] = env[target_key]
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
    """Classify one JUnit testcase body as passed, failed, or skipped.

    A skip is its OWN status here, not a flavour of failure -- it used to be
    folded in with `<failure` and `<error`. What that then means for the delta
    and for the verdict is the disposition recorded on `_delta` in
    `_comparison_report`.
    """
    if "<skipped" in body:
        return "skipped"
    if "<failure" in body or "<error" in body:
        return "failed"
    return "passed"


if __name__ == "__main__":
    raise SystemExit(main())
