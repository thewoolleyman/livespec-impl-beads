"""Verdict and Markdown artifact for the Beads Enemy Unit Test comparison.

Mirrors `fabro-enemy-unit-tests/_comparison_report.py`. `compare.py` owns
RUNNING the two pytest legs and reading their JUnit output into per-assertion
statuses; this module owns REPORTING what the two runs say about each other --
the delta, the artifact, and the verdict.

The one entry point returns the artifact and the exit code TOGETHER, from a
single delta computation, so the rendered report and the process verdict can
never drift apart: a skipped assertion is a delta to the report and a SUCCESS to
pytest, so reading the two pytest exit codes alone would silently discard the
single most likely real finding -- a capability present in one binary and absent
in the other.
"""

from collections import Counter
from dataclasses import dataclass

__all__: list[str] = [
    "Comparison",
    "Report",
    "RunResult",
    "Target",
    "build_report",
]


@dataclass(frozen=True, kw_only=True)
class Target:
    label: str
    bd_bin: str
    cwd: str
    database: str = ""


@dataclass(frozen=True, kw_only=True)
class RunResult:
    target: Target
    exit_code: int
    assertions: dict[str, str]


@dataclass(frozen=True, kw_only=True)
class Comparison:
    pinned: RunResult
    candidate: RunResult


@dataclass(frozen=True, kw_only=True)
class Report:
    markdown: str
    exit_code: int


def build_report(*, comparison: Comparison) -> Report:
    """Render the comparison artifact and the process verdict from ONE delta pass."""
    rows = _comparison_rows(comparison=comparison)
    return Report(
        markdown=_render_markdown(comparison=comparison, rows=rows),
        exit_code=_exit_code(comparison=comparison, rows=rows),
    )


def _exit_code(*, comparison: Comparison, rows: list[tuple[str, str, str, str]]) -> int:
    """Return the verdict from BOTH pytest exit codes AND the rendered delta."""
    runs_failed = comparison.pinned.exit_code != 0 or comparison.candidate.exit_code != 0
    return 1 if runs_failed or _delta_count(rows=rows) > 0 else 0


def _delta_count(*, rows: list[tuple[str, str, str, str]]) -> int:
    return sum(1 for _assertion_id, _pinned, _candidate, delta in rows if delta != "unchanged")


def _render_markdown(*, comparison: Comparison, rows: list[tuple[str, str, str, str]]) -> str:
    lines = [
        "# Beads Enemy Unit Test Comparison",
        "",
        f"- Pinned: `{comparison.pinned.target.bd_bin}` at `{comparison.pinned.target.cwd}`",
        (
            f"- Candidate: `{comparison.candidate.target.bd_bin}` "
            f"at `{comparison.candidate.target.cwd}`"
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


def _comparison_rows(*, comparison: Comparison) -> list[tuple[str, str, str, str]]:
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
    """Classify one assertion's pinned-versus-candidate status pair.

    A skip DOES count as a delta -- it is how a suite expresses "this capability
    exists on one target and not the other", the exact question a
    pinned-versus-candidate comparison answers -- but it is NOT a regression, so
    it gets its own `skip-delta` category. A testcase skipped on BOTH targets is
    `unchanged`; symmetric absence is not a finding. An assertion present on only
    one side is `pinned-only` / `candidate-only` whatever its status there,
    because the finding is the ASYMMETRY.
    """
    if pinned == "missing":
        return "candidate-only"
    if candidate == "missing":
        return "pinned-only"
    if pinned == candidate:
        return "unchanged"
    if "skipped" in (pinned, candidate):
        return "skip-delta"
    return "improved" if candidate == "passed" else "regressed"


def _delta_lines(*, rows: list[tuple[str, str, str, str]]) -> list[str]:
    """Render the Delta section: one counted line per non-`unchanged` category."""
    counts = Counter(delta for _assertion_id, _pinned, _candidate, delta in rows)
    return [
        "",
        "## Delta",
        "",
        f"- Regressions: {counts['regressed']}",
        f"- Improvements: {counts['improved']}",
        f"- Skip deltas: {counts['skip-delta']}",
        f"- Pinned-only assertions: {counts['pinned-only']}",
        f"- Candidate-only assertions: {counts['candidate-only']}",
        f"- Total deltas: {_delta_count(rows=rows)}",
    ]
