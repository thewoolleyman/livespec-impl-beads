"""Acceptance criteria parsing and deterministic evidence checks."""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__: list[str] = [
    "CriterionCheck",
    "criteria_checks",
    "criteria_lines",
]

_DIFF_EVIDENCE_MINIMUM_TERMS = 2
_HEADER_MAX_WORDS = 4
_EXTERNAL_VERIFICATION_TERMS = frozenset(
    {
        "check",
        "checks",
        "green",
        "test",
        "tests",
        "verify",
        "verified",
        "verification",
        "validation",
    }
)
_STOP_WORDS = frozenset(
    {
        "acceptance",
        "against",
        "branch",
        "computed",
        "criteria",
        "criterion",
        "direction",
        "effective",
        "either",
        "every",
        "field",
        "human",
        "item",
        "journaled",
        "minimum",
        "mode",
        "policy",
        "produces",
        "status",
        "their",
        "under",
        "work",
    }
)
_MARKER = re.compile(r"^\s*(?:[-*]|\d+[.)]|\([a-z0-9]+\)|[a-z][.)])\s*")


@dataclass(frozen=True, kw_only=True)
class CriterionCheck:
    """One acceptance criterion's deterministic read-and-judge result."""

    text: str
    passed: bool
    reason: str

    def as_record(self) -> dict[str, object]:
        return {"text": self.text, "passed": self.passed, "reason": self.reason}


def criteria_checks(
    *, criteria_text: str | None, merged_diff: str | None, telemetry_passed: bool
) -> tuple[CriterionCheck, ...]:
    criteria = criteria_lines(criteria_text=criteria_text)
    if not criteria:
        return ()
    normalized_diff = "" if merged_diff is None else merged_diff.lower()
    return tuple(
        _judge_criterion(
            criterion=criterion,
            normalized_diff=normalized_diff,
            telemetry_passed=telemetry_passed,
        )
        for criterion in criteria
    )


def criteria_lines(*, criteria_text: str | None) -> tuple[str, ...]:
    if criteria_text is None:
        return ()
    lines: list[str] = []
    current: list[str] = []
    for raw in criteria_text.splitlines():
        stripped = raw.strip()
        if not stripped:
            _flush_criterion(lines=lines, current=current)
            continue
        line = _strip_marker(text=raw).strip()
        if _has_marker(text=raw):
            _flush_criterion(lines=lines, current=current)
            current.append(line)
            continue
        if current and raw[:1].isspace():
            current.append(line)
            continue
        _flush_criterion(lines=lines, current=current)
        current.append(line)
    _flush_criterion(lines=lines, current=current)
    return tuple(lines)


def _flush_criterion(*, lines: list[str], current: list[str]) -> None:
    if not current:
        return
    criterion = " ".join(current).strip()
    current.clear()
    if criterion and not _is_non_assertion_line(text=criterion):
        lines.append(criterion)


def _strip_marker(*, text: str) -> str:
    return _MARKER.sub("", text, count=1)


def _has_marker(*, text: str) -> bool:
    return _MARKER.match(text) is not None


def _is_non_assertion_line(*, text: str) -> bool:
    terms = _significant_terms(text=text)
    words = re.findall(r"[A-Za-z0-9_]+", text)
    upper_words = tuple(word for word in words if word.upper() == word)
    return (
        text.endswith(":")
        or not terms
        or (len(words) <= _HEADER_MAX_WORDS and len(upper_words) == len(words))
    )


def _judge_criterion(
    *, criterion: str, normalized_diff: str, telemetry_passed: bool
) -> CriterionCheck:
    terms = _significant_terms(text=criterion)
    if _has_diff_evidence(terms=terms, normalized_diff=normalized_diff):
        return CriterionCheck(text=criterion, passed=True, reason="matched merged diff evidence")
    if telemetry_passed and any(term in _EXTERNAL_VERIFICATION_TERMS for term in terms):
        return CriterionCheck(
            text=criterion, passed=True, reason="matched green dispatch telemetry"
        )
    return CriterionCheck(
        text=criterion,
        passed=False,
        reason=_failure_reason(terms=terms, normalized_diff=normalized_diff),
    )


def _has_diff_evidence(*, terms: tuple[str, ...], normalized_diff: str) -> bool:
    matched = tuple(term for term in terms if term in normalized_diff)
    return len(matched) >= _DIFF_EVIDENCE_MINIMUM_TERMS and len(matched) == len(terms)


def _failure_reason(*, terms: tuple[str, ...], normalized_diff: str) -> str:
    if any(term in normalized_diff for term in terms):
        return "insufficient merged diff evidence"
    return "no merged diff or telemetry evidence"


def _significant_terms(*, text: str) -> tuple[str, ...]:
    terms: list[str] = []
    for term in re.findall(r"[a-z0-9_]{4,}", text.lower()):
        if term not in _STOP_WORDS:
            terms.append(term)
    return tuple(terms)
