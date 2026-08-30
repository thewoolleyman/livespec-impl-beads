"""Tests for the Dispatcher post-merge AI acceptance pass."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_acceptance_ai import (
    CriterionCheck,
    run_acceptance_pass,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.types import WorkItem


@dataclass(kw_only=True)
class _Runner:
    result: CommandResult
    calls: list[tuple[list[str], Path, float]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        _ = env
        self.calls.append((argv, cwd, timeout_seconds))
        return self.result


@dataclass(kw_only=True)
class _SequenceRunner:
    results: list[CommandResult]
    calls: list[tuple[list[str], Path, float]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        _ = env
        self.calls.append((argv, cwd, timeout_seconds))
        return self.results.pop(0)


def _item(*, criteria: str | None, description: str = "Do it.") -> WorkItem:
    return WorkItem(
        id="bd-ib-test",
        type="task",
        status="active",
        title="Task",
        description=description,
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee=None,
        depends_on=(),
        captured_at="2026-07-16T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy="ai-only",
        acceptance_criteria=criteria,
    )


def _outcome(
    *, status: str = "green", pr_number: int | None = 7, merge_sha: str | None = "abc123"
) -> DispatchOutcome:
    return DispatchOutcome(
        work_item_id="bd-ib-test",
        status=status,
        stage="done",
        pr_number=pr_number,
        merge_sha=merge_sha,
        detail="merged",
    )


def test_acceptance_pass_reads_diff_and_passes_when_criteria_have_evidence(
    tmp_path: Path,
) -> None:
    diff = "diff --git a/x b/x\n+verdict journaled telemetry watch\n+tests are green\n"
    runner = _Runner(result=CommandResult(exit_code=0, stdout=diff, stderr=""))

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="1. telemetry watch is journaled\n\n2. tests are green"),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "PASS"
    assert [call[0] for call in runner.calls] == [["gh", "pr", "diff", "7", "--patch"]]
    record = result.journal_record(work_item_id="bd-ib-test", policy="ai-only")
    assert record["verdict"] == "PASS"
    assert record["diff"] == {
        "observed": True,
        "bytes": len(diff.encode()),
        "reason": "pull request diff read",
    }
    assert record["telemetry"] == {
        "observed": True,
        "passed": True,
        "reason": "green merged dispatch with PR and merge sha",
    }
    assert record["absent_evidence"] == []
    assert result.absent_evidence == ()


def test_acceptance_pass_fails_when_criteria_lack_diff_or_telemetry_evidence(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(exit_code=0, stdout="diff --git a/x b/x\n+other\n", stderr="")
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="The release notes were updated."),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "FAIL"
    assert result.criteria == (
        CriterionCheck(
            text="The release notes were updated.",
            passed=False,
            reason="no merged diff or telemetry evidence",
        ),
    )


def test_acceptance_pass_ignores_bare_header_lines(tmp_path: Path) -> None:
    runner = _Runner(
        result=CommandResult(
            exit_code=0,
            stdout="diff --git a/x b/x\n+the receipt proves the control tripped once\n",
            stderr="",
        )
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(
            criteria=(
                "ACCEPTANCE CRITERIA\n" "\n" "- The receipt proves the control tripped once.\n"
            )
        ),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "PASS"
    assert result.criteria == (
        CriterionCheck(
            text="The receipt proves the control tripped once.",
            passed=True,
            reason="matched merged diff evidence",
        ),
    )


def test_acceptance_pass_folds_hard_wrapped_fragments_into_one_assertion(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(
            exit_code=0,
            stdout=(
                "diff --git a/x b/x\n" "+journal record names every failing criterion and reason\n"
            ),
            stderr="",
        )
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(
            criteria=("1. The journal record names every failing criterion and\n" "   reason.\n")
        ),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "PASS"
    assert result.criteria == (
        CriterionCheck(
            text="The journal record names every failing criterion and reason.",
            passed=True,
            reason="matched merged diff evidence",
        ),
    )


def test_acceptance_pass_keeps_unmarked_one_assertion_per_line_separate(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(
            exit_code=0,
            stdout=(
                "diff --git a/x b/x\n"
                "+verdict journal records every failing criterion\n"
                "+dispatch telemetry records every merged outcome\n"
            ),
            stderr="",
        )
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(
            criteria=(
                "The verdict journal records every failing criterion.\n"
                "The dispatch telemetry records every merged outcome.\n"
            )
        ),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "PASS"
    assert result.criteria == (
        CriterionCheck(
            text="The verdict journal records every failing criterion.",
            passed=True,
            reason="matched merged diff evidence",
        ),
        CriterionCheck(
            text="The dispatch telemetry records every merged outcome.",
            passed=True,
            reason="matched merged diff evidence",
        ),
    )


_MET_ASSERTION = (
    "The dispatcher releases the ledger claim when a dispatch fails before a fabro "
    "run identifier is recorded."
)
_UNMET_ASSERTION = (
    "The changelog gains an entry describing the escalation ladder an operator "
    "follows once a slice parks."
)
_WRAPPED_EVIDENCE_DIFF = (
    "diff --git a/dispatch.py b/dispatch.py\n"
    "+release the ledger claim when a dispatch fails before a fabro run identifier\n"
    "+is recorded, so a subsequent dispatch of the same slice is admitted normally\n"
)


def _reflowed(*, assertions: tuple[str, ...], width: int) -> str:
    return "\n\n".join(textwrap.fill(assertion, width=width) for assertion in assertions)


def _one_paragraph(*, assertions: tuple[str, ...], width: int) -> str:
    # Every assertion in ONE hard-wrapped paragraph, so the wrap decides where
    # each sentence boundary falls relative to a line break.
    return textwrap.fill(
        " ".join(assertions), width=width, break_on_hyphens=False, break_long_words=False
    )


def test_acceptance_pass_verdict_is_independent_of_criteria_wrap_width(
    tmp_path: Path,
) -> None:
    # The SAME criteria content, hard-wrapped at two authoring widths. Segmenting
    # by line makes the wrap width decide the verdict; folding continuations makes
    # the two indistinguishable.
    assertions = (
        _MET_ASSERTION,
        "A subsequent dispatch of the same slice is admitted normally rather than "
        "refused as unripe.",
    )
    runner = _Runner(result=CommandResult(exit_code=0, stdout=_WRAPPED_EVIDENCE_DIFF, stderr=""))

    narrow = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria=_reflowed(assertions=assertions, width=44)),
        outcome=_outcome(),
        runner=runner,
    )
    wide = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria=_reflowed(assertions=assertions, width=88)),
        outcome=_outcome(),
        runner=runner,
    )

    assert narrow.verdict == wide.verdict == "PASS"
    assert narrow.criteria == wide.criteria
    assert tuple(check.text for check in narrow.criteria) == assertions


def test_acceptance_pass_still_fails_a_genuinely_unmet_wrapped_assertion(
    tmp_path: Path,
) -> None:
    # The discriminating control for the fold: an assertion the merged diff does
    # not carry must still block, whole rather than in fragments.
    runner = _Runner(result=CommandResult(exit_code=0, stdout=_WRAPPED_EVIDENCE_DIFF, stderr=""))

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria=_reflowed(assertions=(_MET_ASSERTION, _UNMET_ASSERTION), width=44)),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "FAIL"
    assert result.criteria == (
        CriterionCheck(
            text=_MET_ASSERTION,
            passed=True,
            reason="matched merged diff evidence",
        ),
        CriterionCheck(
            text=_UNMET_ASSERTION,
            passed=False,
            reason="insufficient merged diff evidence",
        ),
    )


_MULTI_SENTENCE_ASSERTIONS = (
    _MET_ASSERTION,
    "A subsequent dispatch of the same slice is admitted normally rather than refused as unripe.",
)
# Widths that place the paragraph's internal sentence boundary in every position
# a line break can occupy relative to it.
_PARAGRAPH_WIDTHS = tuple(range(56, 160))


def test_acceptance_pass_verdict_is_independent_of_where_a_wrap_falls_inside_a_paragraph(
    tmp_path: Path,
) -> None:
    # The two assertions share ONE paragraph, so at some widths a line ends
    # exactly on the boundary between them and at others it does not. Segmenting
    # by line made that difference decide the verdict.
    runner = _Runner(result=CommandResult(exit_code=0, stdout=_WRAPPED_EVIDENCE_DIFF, stderr=""))

    results = {
        run_acceptance_pass(
            repo=tmp_path,
            item=_item(criteria=_one_paragraph(assertions=_MULTI_SENTENCE_ASSERTIONS, width=width)),
            outcome=_outcome(),
            runner=runner,
        ).criteria
        for width in _PARAGRAPH_WIDTHS
    }

    assert len(results) == 1
    assert tuple(check.text for check in results.pop()) == _MULTI_SENTENCE_ASSERTIONS


def test_acceptance_pass_still_fails_an_unmet_sentence_of_a_wrapped_paragraph(
    tmp_path: Path,
) -> None:
    # The discriminating control for the paragraph case: an assertion the merged
    # diff does not carry must still block at every wrap width, rather than
    # riding in on the evidence of the sentence it shares a paragraph with.
    runner = _Runner(result=CommandResult(exit_code=0, stdout=_WRAPPED_EVIDENCE_DIFF, stderr=""))

    verdicts = {
        run_acceptance_pass(
            repo=tmp_path,
            item=_item(
                criteria=_one_paragraph(assertions=(_MET_ASSERTION, _UNMET_ASSERTION), width=width)
            ),
            outcome=_outcome(),
            runner=runner,
        ).verdict
        for width in _PARAGRAPH_WIDTHS
    }

    assert verdicts == {"FAIL"}


def test_acceptance_pass_fails_when_only_one_term_matches_unrelated_diff(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(
            exit_code=0,
            stdout="diff --git a/x b/x\n+rename plan helper\n",
            stderr="",
        )
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="The plan-rollup invariant no longer reports a seat anchor epic."),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "FAIL"
    assert result.criteria == (
        CriterionCheck(
            text="The plan-rollup invariant no longer reports a seat anchor epic.",
            passed=False,
            reason="insufficient merged diff evidence",
        ),
    )


def test_acceptance_pass_does_not_require_every_significant_term_in_diff(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(
            exit_code=0,
            stdout="diff --git a/x b/x\n+receipt proves the control tripped\n",
            stderr="",
        )
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(
            criteria=(
                "THE RECEIPT BAR: every isolation or verification receipt you ship must "
                "be provable by DELIBERATELY TRIPPING IT ONCE."
            )
        ),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "PASS"
    assert result.criteria == (
        CriterionCheck(
            text=(
                "THE RECEIPT BAR: every isolation or verification receipt you ship must "
                "be provable by DELIBERATELY TRIPPING IT ONCE."
            ),
            passed=True,
            reason="matched merged diff evidence",
        ),
    )


def test_acceptance_pass_reads_multi_commit_pr_diff_not_only_series_tip(
    tmp_path: Path,
) -> None:
    pr_diff = (
        "diff --git a/impl.py b/impl.py\n"
        "+post merge acceptance grades every implementation commit\n"
        "diff --git a/CHANGELOG.md b/CHANGELOG.md\n"
        "+release note only final commit\n"
    )
    runner = _Runner(result=CommandResult(exit_code=0, stdout=pr_diff, stderr=""))

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(
            criteria="Post merge acceptance grades every implementation commit.",
        ),
        outcome=_outcome(pr_number=1809, merge_sha="2e3fab5a"),
        runner=runner,
    )

    assert result.verdict == "PASS"
    assert result.merged_diff == pr_diff
    assert result.diff_reason == "pull request diff read"
    assert [call[0] for call in runner.calls] == [["gh", "pr", "diff", "1809", "--patch"]]


def test_acceptance_pass_empty_pr_diff_falls_through_to_merge_diff(
    tmp_path: Path,
) -> None:
    merge_diff = "diff --git a/x b/x\n+run the tests\n"
    runner = _SequenceRunner(
        results=[
            CommandResult(exit_code=0, stdout="\n", stderr=""),
            CommandResult(exit_code=0, stdout=merge_diff, stderr=""),
        ]
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="Run the tests."),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "PASS"
    assert result.merged_diff == merge_diff
    assert result.diff_reason == "merged diff read"
    assert [call[0] for call in runner.calls] == [
        ["gh", "pr", "diff", "7", "--patch"],
        ["git", "show", "--format=", "--find-renames", "abc123"],
    ]


def test_acceptance_pass_needs_attention_when_patch_has_no_file_changes(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(
            exit_code=0,
            stdout=(
                "From abc Mon Sep 17 00:00:00 2001\n"
                "From: Fabro <fabro@example.test>\n"
                "Subject: fabro(run): implement (succeeded)\n"
            ),
            stderr="",
        )
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="Run the tests."),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "NEEDS_ATTENTION"
    assert result.merged_diff is None
    assert result.diff_reason == "pull request diff has no file changes"


def test_acceptance_pass_needs_attention_when_recorded_pr_lacks_merge_sha(
    tmp_path: Path,
) -> None:
    runner = _SequenceRunner(
        results=[
            CommandResult(
                exit_code=0,
                stdout=(
                    "From abc Mon Sep 17 00:00:00 2001\n"
                    "From: Fabro <fabro@example.test>\n"
                    "Subject: fabro(run): implement (succeeded)\n"
                ),
                stderr="",
            ),
            CommandResult(
                exit_code=0, stdout='["skip", {"number": true}, {"number":1807}]', stderr=""
            ),
        ]
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="Run the tests."),
        outcome=_outcome(pr_number=1809, merge_sha="abc123"),
        runner=runner,
    )

    assert result.verdict == "NEEDS_ATTENTION"
    assert result.merged_diff is None
    assert result.diff_reason == (
        "recorded PR #1809 does not contain merge sha abc123; associated PRs: #1807"
    )
    assert [call[0] for call in runner.calls] == [
        ["gh", "pr", "diff", "1809", "--patch"],
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            "/repos/{owner}/{repo}/commits/abc123/pulls",
        ],
    ]


def test_acceptance_pass_needs_attention_when_pr_association_lookup_fails(
    tmp_path: Path,
) -> None:
    runner = _SequenceRunner(
        results=[
            CommandResult(
                exit_code=0,
                stdout=(
                    "From abc Mon Sep 17 00:00:00 2001\n"
                    "From: Fabro <fabro@example.test>\n"
                    "Subject: fabro(run): implement (succeeded)\n"
                ),
                stderr="",
            ),
            CommandResult(exit_code=1, stdout="", stderr="api unavailable"),
        ]
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="Run the tests."),
        outcome=_outcome(pr_number=1809, merge_sha="abc123"),
        runner=runner,
    )

    assert result.verdict == "NEEDS_ATTENTION"
    assert result.merged_diff is None
    assert result.diff_reason == "pull request diff has no file changes"


def test_acceptance_pass_needs_attention_when_pr_association_payload_is_malformed(
    tmp_path: Path,
) -> None:
    runner = _SequenceRunner(
        results=[
            CommandResult(
                exit_code=0,
                stdout=(
                    "From abc Mon Sep 17 00:00:00 2001\n"
                    "From: Fabro <fabro@example.test>\n"
                    "Subject: fabro(run): implement (succeeded)\n"
                ),
                stderr="",
            ),
            CommandResult(exit_code=0, stdout='{"number":1807}', stderr=""),
        ]
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="Run the tests."),
        outcome=_outcome(pr_number=1809, merge_sha="abc123"),
        runner=runner,
    )

    assert result.verdict == "NEEDS_ATTENTION"
    assert result.merged_diff is None
    assert result.diff_reason == "pull request diff has no file changes"


def test_acceptance_pass_needs_attention_when_diff_is_unobservable(tmp_path: Path) -> None:
    runner = _Runner(result=CommandResult(exit_code=1, stdout="", stderr="fatal"))

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="The acceptance journal records the verdict."),
        outcome=_outcome(),
        runner=runner,
    )

    # A criterion judged against a diff that was never read is judged against
    # absent evidence — that is not the observed failing evidence FAIL needs.
    assert result.verdict == "NEEDS_ATTENTION"
    assert result.absent_evidence == ("merged diff",)
    assert result.merged_diff is None
    assert result.diff_reason == "pull request diff failed; git show failed"


def test_acceptance_pass_needs_attention_on_empty_criteria_with_readable_diff(
    tmp_path: Path,
) -> None:
    runner = _Runner(result=CommandResult(exit_code=0, stdout="diff --git a/x b/x\n", stderr=""))

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria=""),
        outcome=_outcome(),
        runner=runner,
    )

    # Effective criteria that parse to zero gradeable assertions leave nothing
    # to grade; a vacuous `all()` must never read as a PASS.
    assert result.verdict == "NEEDS_ATTENTION"
    assert result.absent_evidence == ("effective criteria",)
    assert result.criteria == ()
    assert result.diff_reason == "pull request diff read"


def test_acceptance_pass_needs_attention_names_every_absent_leg(tmp_path: Path) -> None:
    runner = _Runner(result=CommandResult(exit_code=0, stdout="ignored", stderr=""))

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria=None),
        outcome=_outcome(merge_sha=None),
        runner=runner,
    )

    assert result.verdict == "NEEDS_ATTENTION"
    assert result.absent_evidence == ("merged diff", "effective criteria")
    assert result.criteria == ()
    assert result.diff_reason == "merge sha unavailable"
    assert runner.calls == []
    record = result.journal_record(work_item_id="bd-ib-test", policy="ai-only")
    assert record["absent_evidence"] == ["merged diff", "effective criteria"]


def test_acceptance_pass_uses_description_exit_criteria_when_field_is_empty(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(
            exit_code=0,
            stdout="diff --git a/x b/x\n+acceptance journal records the verdict\n",
            stderr="",
        )
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(
            criteria=None,
            description=(
                "Implement the fix.\n\n"
                "## Exit criteria\n\n"
                "- acceptance journal records the verdict\n\n"
                "## Notes\n\n"
                "- not a criterion\n"
            ),
        ),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.verdict == "PASS"
    assert result.criteria == (
        CriterionCheck(
            text="acceptance journal records the verdict",
            passed=True,
            reason="matched merged diff evidence",
        ),
    )


def test_acceptance_pass_fails_when_dispatch_telemetry_is_not_green(tmp_path: Path) -> None:
    runner = _Runner(
        result=CommandResult(exit_code=0, stdout="diff --git a/x b/x\n+verdict\n", stderr="")
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="verdict is journaled"),
        outcome=_outcome(status="failed"),
        runner=runner,
    )

    # An observed failing outcome IS failing evidence, so FAIL is still right.
    assert result.verdict == "FAIL"
    assert result.telemetry_observed is True
    assert result.absent_evidence == ()
    assert result.telemetry_reason == "dispatch outcome status was 'failed'"


def test_acceptance_pass_needs_attention_when_run_parked_at_a_human_gate(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(exit_code=0, stdout="diff --git a/x b/x\n+verdict\n", stderr="")
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="verdict is journaled"),
        outcome=_outcome(status="blocked"),
        runner=runner,
    )

    # `blocked` is a run that parked rather than reported: never a failure.
    assert result.verdict == "NEEDS_ATTENTION"
    assert result.telemetry_observed is False
    assert result.absent_evidence == ("telemetry",)
    assert result.telemetry_reason == "dispatch outcome status was 'blocked'"


def test_acceptance_pass_needs_attention_when_telemetry_leg_is_unobservable(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(exit_code=0, stdout="diff --git a/x b/x\n+verdict\n", stderr="")
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="verdict is journaled"),
        outcome=_outcome(pr_number=None),
        runner=runner,
    )

    # The merged diff is readable; only the telemetry leg is missing, and an
    # unobservable leg is neither passing nor failing evidence.
    assert result.verdict == "NEEDS_ATTENTION"
    assert result.merged_diff is not None
    assert result.telemetry_observed is False
    assert result.absent_evidence == ("telemetry",)
    assert result.telemetry_reason == "merged PR number unavailable"
    record = result.journal_record(work_item_id="bd-ib-test", policy="ai-only")
    assert record["telemetry"] == {
        "observed": False,
        "passed": False,
        "reason": "merged PR number unavailable",
    }
    assert record["absent_evidence"] == ["telemetry"]


def test_acceptance_pass_journals_the_change_implying_classification_it_used(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(exit_code=0, stdout="diff --git a/x b/x\n+verdict\n", stderr="")
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="verdict is journaled"),
        outcome=_outcome(),
        runner=runner,
    )

    assert result.classification.change_implying
    record = result.journal_record(work_item_id="bd-ib-test", policy="ai-only")
    assert record["change_classification"] == {
        "classification": "change-implying",
        "declared_marker": None,
    }


def test_acceptance_pass_journals_a_declared_change_optional_classification(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        result=CommandResult(exit_code=0, stdout="diff --git a/x b/x\n+verdict\n", stderr="")
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria="verdict is journaled"),
        outcome=_outcome(),
        runner=runner,
        raw_labels=("change-optional:true",),
    )

    # Nothing is silently exempted: the declared exemption is journaled as the
    # classification the pass USED, not merely honoured behind the verdict.
    assert not result.classification.change_implying
    record = result.journal_record(work_item_id="bd-ib-test", policy="ai-only")
    assert record["change_classification"] == {
        "classification": "change-optional",
        "declared_marker": "true",
    }


# The three tests below share one item, one green outcome and one criteria set,
# and vary ONLY the merged diff and the declared marker. That is deliberate: the
# empty-diff refusal is a claim about those two inputs alone, and a control that
# also varied the criteria could not show that the refusal — rather than an
# unmet criterion — is what changed the verdict. The criteria are telemetry
# satisfiable, so the empty-diff cases would BOTH reach PASS if the refusal did
# not exist; the change-optional case proves they still do.
_TELEMETRY_SATISFIABLE_CRITERIA = "The test suite passes green."


def test_acceptance_pass_refuses_an_empty_merged_diff_for_a_change_implying_item(
    tmp_path: Path,
) -> None:
    runner = _SequenceRunner(
        results=[
            CommandResult(exit_code=0, stdout="", stderr=""),
            CommandResult(exit_code=0, stdout="", stderr=""),
        ]
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria=_TELEMETRY_SATISFIABLE_CRITERIA),
        outcome=_outcome(),
        runner=runner,
    )

    # A merge that changed zero files carries no evidence that any
    # change-implying criterion is met, so the merged-diff leg is UNGRADEABLE
    # and the verdict parks rather than judging.
    assert result.verdict == "NEEDS_ATTENTION"
    # Named explicitly because these are the two verdicts an empty diff must
    # never reach: PASS would be manufactured from absent evidence, and
    # NO_CHANGE_NEEDED needs the OBSERVED already-present-or-superseded route
    # that "nothing changed in this merge" is not.
    assert result.verdict not in {"PASS", "NO_CHANGE_NEEDED"}
    assert result.absent_evidence == ("merged diff",)
    assert result.classification.change_implying
    assert result.diff_reason == "merged diff is empty"
    record = result.journal_record(work_item_id="bd-ib-test", policy="ai-only")
    assert record["verdict"] == "NEEDS_ATTENTION"
    assert record["absent_evidence"] == ["merged diff"]


def test_acceptance_pass_grades_a_change_optional_item_with_an_empty_merged_diff(
    tmp_path: Path,
) -> None:
    runner = _SequenceRunner(
        results=[
            CommandResult(exit_code=0, stdout="", stderr=""),
            CommandResult(exit_code=0, stdout="", stderr=""),
        ]
    )

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria=_TELEMETRY_SATISFIABLE_CRITERIA),
        outcome=_outcome(),
        runner=runner,
        raw_labels=("change-optional:true",),
    )

    # The declared exemption routes the identical empty diff to the item's
    # normal grading path: the leg is present, the refusal never fires, and the
    # criteria are judged on the evidence they actually have.
    assert result.absent_evidence == ()
    assert result.verdict == "PASS"
    assert result.criteria == (
        CriterionCheck(
            text=_TELEMETRY_SATISFIABLE_CRITERIA,
            passed=True,
            reason="matched green dispatch telemetry",
        ),
    )


def test_acceptance_pass_grades_a_change_implying_item_with_a_non_empty_merged_diff(
    tmp_path: Path,
) -> None:
    diff = "diff --git a/x b/x\n+the test suite passes green\n"
    runner = _Runner(result=CommandResult(exit_code=0, stdout=diff, stderr=""))

    result = run_acceptance_pass(
        repo=tmp_path,
        item=_item(criteria=_TELEMETRY_SATISFIABLE_CRITERIA),
        outcome=_outcome(),
        runner=runner,
    )

    # The refusal is scoped to the EMPTY diff: a change-implying item whose
    # merge changed files grades normally and PASS stays reachable.
    assert result.verdict == "PASS"
    assert result.absent_evidence == ()
    assert result.classification.change_implying
    assert result.merged_diff == diff
    assert result.diff_reason == "pull request diff read"
