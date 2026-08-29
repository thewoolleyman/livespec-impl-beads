"""Verdict and Markdown artifact for the Fabro Enemy Unit Test comparison.

Split out of `compare.py`, which had accreted two concerns: RUNNING the two
pytest legs and reading their JUnit output into per-assertion statuses, and
REPORTING what the two runs say about each other. This module owns the second.

The one entry point deliberately returns the artifact and the exit code
TOGETHER, from a single delta computation, because the defect this module was
carved out to fix was precisely a verdict that disagreed with the report beside
it: `main()` used to derive its exit code from the two pytest exit codes alone
and never consulted the delta it had just rendered. `Report` makes the two
inseparable at the type level, so they cannot drift apart again.
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
    fabro_bin: str
    server_url: str


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
    """Return the verdict from BOTH pytest exit codes AND the rendered delta.

    The harness exists to answer "is the delta between the pinned and candidate
    builds empty?", so the delta it just rendered is part of its verdict. Reading
    the two pytest exit codes alone silently discards it: a skipped assertion is
    a delta to the report and a SUCCESS to pytest, so the single most likely real
    finding -- a capability present in one binary and absent in the other -- was
    exactly the one the exit code could not see.
    """
    runs_failed = comparison.pinned.exit_code != 0 or comparison.candidate.exit_code != 0
    return 1 if runs_failed or _delta_count(rows=rows) > 0 else 0


def _delta_count(*, rows: list[tuple[str, str, str, str]]) -> int:
    return sum(1 for _assertion_id, _pinned, _candidate, delta in rows if delta != "unchanged")


def _render_markdown(*, comparison: Comparison, rows: list[tuple[str, str, str, str]]) -> str:
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

    DISPOSITION -- does a skip count as a delta, and is it a regression?
    A skip DOES count as a delta: skipping is how a suite expresses "this
    capability exists on one target and not the other", which is the exact
    question a pinned-versus-candidate comparison is run to answer, so a skip
    that differs across the two targets must move the verdict. But a skip is NOT
    a regression: nothing failed, and folding it into the regression count makes
    a genuine failure indistinguishable from a capability gap in the one number
    an operator reads. It therefore gets its own `skip-delta` category and its
    own line in the artifact's Delta section. A testcase skipped on BOTH targets
    is `unchanged` -- symmetric absence is not a finding.

    An assertion present on only one side is `pinned-only` / `candidate-only`
    whatever its status there, because the finding is the ASYMMETRY: the
    surviving side's pass or fail does not reclassify it. Whatever remains can
    only be pass-versus-fail, which the candidate's side names.
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
    """Render the Delta section: one counted line per non-`unchanged` category.

    Every category `_delta` can produce is listed, so the artifact stays readable
    as the explanation of a non-zero exit -- a reader can always see WHICH
    category moved the verdict. `Total deltas` is the number the exit code is a
    function of. The old `Changed non-pass statuses` line is gone: with skips
    classified in their own right, a differing pair with neither side missing is
    always one of the four named categories, so that line could only ever have
    reported zero.
    """
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
