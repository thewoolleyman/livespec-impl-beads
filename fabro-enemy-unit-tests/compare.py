"""Compare Fabro Enemy Unit Test results across two client/server pairs."""

import argparse
import os
import re
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

__all__: list[str] = []

_TEST_ROOT = "fabro-enemy-unit-tests/test_tier0_*.py"
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


@dataclass(frozen=True, kw_only=True)
class _Target:
    label: str
    fabro_bin: str
    server_url: str


@dataclass(frozen=True, kw_only=True)
class _RunResult:
    target: _Target
    exit_code: int
    assertions: dict[str, str]


@dataclass(frozen=True, kw_only=True)
class _Comparison:
    pinned: _RunResult
    candidate: _RunResult


def main(*, argv: list[str] | None = None) -> int:
    args = _parse_args(argv=argv)
    comparison = _run_comparison(
        pinned=_Target(label="pinned", fabro_bin=args.pinned_bin, server_url=args.pinned_server),
        candidate=_Target(
            label="candidate",
            fabro_bin=args.candidate_bin,
            server_url=args.candidate_server,
        ),
    )
    args.artifact.write_text(_render_markdown(comparison=comparison))
    return 0 if comparison.pinned.exit_code == 0 and comparison.candidate.exit_code == 0 else 1


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


def _run_comparison(*, pinned: _Target, candidate: _Target) -> _Comparison:
    with tempfile.TemporaryDirectory(prefix="fabro-eut-compare.") as temp_dir:
        temp_path = Path(temp_dir)
        return _Comparison(
            pinned=_run_target(target=pinned, junit_path=temp_path / "pinned.xml"),
            candidate=_run_target(target=candidate, junit_path=temp_path / "candidate.xml"),
        )


def _run_target(*, target: _Target, junit_path: Path) -> _RunResult:
    completed = subprocess.run(
        args=["uv", "run", "pytest", _TEST_ROOT, "-q", f"--junitxml={junit_path}"],
        env=_target_env(target=target),
        check=False,
    )
    return _RunResult(
        target=target,
        exit_code=completed.returncode,
        assertions=_read_assertions(junit_path=junit_path),
    )


def _target_env(*, target: _Target) -> dict[str, str]:
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
        assertions[_assertion_id(attrs=attrs)] = "failed" if _failed(body=body) else "passed"
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


def _failed(*, body: str) -> bool:
    return "<failure" in body or "<error" in body or "<skipped" in body


def _render_markdown(*, comparison: _Comparison) -> str:
    rows = _comparison_rows(comparison=comparison)
    lines = [
        "# Fabro Enemy Unit Test Comparison",
        "",
        f"- Pinned: `{comparison.pinned.target.fabro_bin}` at `{comparison.pinned.target.server_url}`",
        (
            f"- Candidate: `{comparison.candidate.target.fabro_bin}` "
            f"at `{comparison.candidate.target.server_url}`"
        ),
        f"- Pinned exit code: {comparison.pinned.exit_code}",
        f"- Candidate exit code: {comparison.candidate.exit_code}",
        "",
        "## Per-Assertion Results",
        "",
        "| Assertion | Pinned | Candidate | Delta |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| `{assertion_id}` | {pinned_status} | {candidate_status} | {delta} |"
        for assertion_id, pinned_status, candidate_status, delta in rows
    )
    lines.extend(_delta_lines(rows=rows))
    return "\n".join(lines) + "\n"


def _comparison_rows(*, comparison: _Comparison) -> list[tuple[str, str, str, str]]:
    assertion_ids = sorted(set(comparison.pinned.assertions) | set(comparison.candidate.assertions))
    return [
        (
            assertion_id,
            comparison.pinned.assertions.get(assertion_id, "missing"),
            comparison.candidate.assertions.get(assertion_id, "missing"),
            _delta(
                pinned=comparison.pinned.assertions.get(assertion_id, "missing"),
                candidate=comparison.candidate.assertions.get(assertion_id, "missing"),
            ),
        )
        for assertion_id in assertion_ids
    ]


def _delta(*, pinned: str, candidate: str) -> str:
    return {
        (True, False, False, False, False): "candidate-only",
        (False, True, False, False, False): "pinned-only",
        (False, False, False, True, False): "improved",
        (False, False, True, False, False): "regressed",
    }.get(
        (
            pinned == "missing",
            candidate == "missing",
            pinned == "passed",
            candidate == "passed",
            pinned == candidate,
        ),
        "unchanged" if pinned == candidate else "changed",
    )


def _delta_lines(*, rows: list[tuple[str, str, str, str]]) -> list[str]:
    counts = Counter(delta for _assertion_id, _pinned, _candidate, delta in rows)
    return [
        "",
        "## Delta",
        "",
        f"- Regressions: {counts['regressed']}",
        f"- Improvements: {counts['improved']}",
        f"- Changed non-pass statuses: {counts['changed']}",
        f"- Pinned-only assertions: {counts['pinned-only']}",
        f"- Candidate-only assertions: {counts['candidate-only']}",
    ]


if __name__ == "__main__":
    raise SystemExit(main())
