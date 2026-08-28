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
_SENTENCE_TERMINATORS = (".", "!", "?")
# Trailing delimiters a terminator can hide behind — `... (see the note).)` and
# `... reads "no evidence."` both end a sentence.
_CLOSING_DELIMITERS = ")]}\"'`*_"
# Their opening counterparts, stripped off the word BEFORE a terminator so a
# parenthesized abbreviation — `(e.g.` — is still read as one.
_OPENING_DELIMITERS = "([{\"'`*_"
_WORD = re.compile(r"[A-Za-z0-9_]+")
# A sentence ends at a terminator (plus any delimiters hiding it) that another
# word follows. That word's CASE is deliberately NOT consulted: an assertion may
# open with a lowercase token — `just check is green with nothing skipped.` —
# and requiring a capital merged such an assertion into its predecessor, where
# it passed on the predecessor's evidence rather than being judged. The match
# ENDS at the sentence's last character, so the boundary is read off
# `match.end()`.
_SENTENCE_BOUNDARY = re.compile(
    r"[.!?][" + re.escape(_CLOSING_DELIMITERS) + r"]*(?=\s+\S)",
)
_ABBREVIATION_MINIMUM_LENGTH = 2
# An abbreviation is an INITIALISM — single letters joined by dots, as in `e.g.`
# or `i.e.`. Merely CONTAINING a dot does not make a word one: a dotted version
# or filename such as `v0.88.0` or `_dispatcher_acceptance_criteria.py` is
# ordinary prose, so the terminator that follows it ends its sentence.
_INITIALISM = re.compile(r"(?:[A-Za-z]\.)*[A-Za-z]")


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
    """Segment acceptance-criteria text into the assertions the author wrote.

    Segmentation is deliberately a function of the criteria's CONTENT, never of
    the width it happens to be hard-wrapped at. Lines are first gathered into
    BLOCKS, and only three things start a block — a blank line, a list marker,
    and a header line — none of which reflowing a paragraph can introduce or
    remove. Each block is then split into SENTENCES, so a multi-sentence
    assertion yields the same criteria whether the wrap fell inside a sentence
    or exactly on the boundary between two.

    That ordering is what removes the false rework this parser used to cause: a
    hard-wrapped sentence's flush-left continuation is no longer judged on its
    own and failed for lacking merged-diff evidence it could never carry.
    """
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
        if _starts_a_block(current=current, line=line):
            _flush_criterion(lines=lines, current=current)
        current.append(line)
    _flush_criterion(lines=lines, current=current)
    return tuple(lines)


def _starts_a_block(*, current: list[str], line: str) -> bool:
    """Report whether a flush-left line breaks the pending block rather than continuing it.

    Only a HEADER breaks it, and only in the two positions where a header is
    unambiguous — a header cannot swallow the criterion that follows it, and a
    header cannot be swallowed by the completed criterion that precedes it.
    Everything else continues the block, including a line that opens a fresh
    sentence: `_sentences` separates those, and doing it there rather than here
    is what makes the result independent of where the wrap fell.
    """
    pending = " ".join(current).strip()
    if not pending:
        return False
    if _is_header_line(text=pending):
        return True
    return _ends_sentence(text=pending) and _is_header_line(text=line)


def _is_header_line(*, text: str) -> bool:
    """Report whether a line is a block header rather than an assertion.

    A header is SHORT and either shouts or dangles a colon. Both signals are
    required: a lone lowercase sentence tail such as `verdict.` is short but is
    a wrap artifact, and folding it back into its sentence is the whole point of
    this module.
    """
    words = _words(text=text)
    if len(words) > _HEADER_MAX_WORDS:
        return False
    shouts = bool(words) and all(word.upper() == word for word in words)
    return text.endswith(":") or shouts


def _ends_sentence(*, text: str) -> bool:
    return text.rstrip(_CLOSING_DELIMITERS).endswith(_SENTENCE_TERMINATORS)


def _sentences(*, text: str) -> tuple[str, ...]:
    """Split a joined block into its sentences.

    A boundary is a terminator that another word follows, whatever that word's
    case, EXCEPT where the terminator closes an abbreviation — `e.g.` and `i.e.`
    end in a dot without ending a sentence. A dotted VERSION or FILENAME is not
    an abbreviation: `... shipped as v0.88.0.` ends its sentence like any other.
    """
    sentences: list[str] = []
    start = 0
    for match in _SENTENCE_BOUNDARY.finditer(text):
        if _abbreviates(text=text, terminator=match.start()):
            continue
        sentences.append(text[start : match.end()].strip())
        start = match.end()
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return tuple(sentences)


def _abbreviates(*, text: str, terminator: int) -> bool:
    """Report whether the terminator closes an abbreviation rather than a sentence.

    The word must BE an initialism, not merely contain a dot. Reading any dotted
    token as an abbreviation swallowed the sentence break after a version or a
    filename, and the two sentences then fused into one criterion — which passed
    on the first sentence's evidence while the second assertion went unjudged.
    """
    word = re.split(r"\s", text[:terminator])[-1].lstrip(_OPENING_DELIMITERS)
    return len(word) < _ABBREVIATION_MINIMUM_LENGTH or _INITIALISM.fullmatch(word) is not None


def _flush_criterion(*, lines: list[str], current: list[str]) -> None:
    if not current:
        return
    block = " ".join(current).strip()
    current.clear()
    for sentence in _sentences(text=block):
        if not _is_non_assertion_line(text=sentence):
            lines.append(sentence)


def _strip_marker(*, text: str) -> str:
    return _MARKER.sub("", text, count=1)


def _has_marker(*, text: str) -> bool:
    return _MARKER.match(text) is not None


def _words(*, text: str) -> tuple[str, ...]:
    return tuple(_WORD.findall(text))


def _is_non_assertion_line(*, text: str) -> bool:
    terms = _significant_terms(text=text)
    words = _words(text=text)
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
    return len(matched) >= _DIFF_EVIDENCE_MINIMUM_TERMS


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
