---
topic: empty-diff-acceptance-integrity
author: empty-diff-acceptance-integrity
created_at: 2026-08-30T05:30:20Z
spec_commitments:
  impl_followups:
    - id_hint: acceptance-empty-diff-refusal
      description: |
        Implement C1 in the post-merge acceptance pass: for an AI-dispositive item whose effective acceptance criteria are change-implying, an empty merged diff (zero files changed / zero hunks under the merged ref) resolves the merged-diff evidence leg as UNGRADEABLE and the pass emits NEEDS_ATTENTION, never PASS, journaling the empty-diff leg as the absent-evidence leg. NO_CHANGE_NEEDED stays reachable only through its own OBSERVED already-present/superseded route; an empty diff alone is not that observation. Add the discriminating test that a zero-change merge under a change-implying item parks NEEDS_ATTENTION and the positive test that a real-change merge still grades normally.
    - id_hint: scoped-check-vacuous-match
      description: |
        Implement C2: a janitor/scoped check whose file scope matched ZERO files in the diff under judgment reports a distinct vacuous-match outcome that a gate cannot count toward passing (neither pass nor fail evidence). This is the surface that let PR #1044's check-no-workflow-edits pass vacuously over the empty diff. Add the test that a scoped check with zero matched files yields vacuous-match, and that a gate does not read vacuous-match as green.
    - id_hint: dispatcher-empty-diff-composition
      description: |
        Implement C3: a zero-change merged run whose acceptance parked NEEDS_ATTENTION per C1 composes into the needs-attention surface through the existing NEEDS_ATTENTION-parked-acceptance composition class as exactly one attention item, its summary naming the empty-diff evidence leg alongside the accept/reject dispositions the class already requires — no new composition kind. Add the test that the composed attention item names the empty-diff leg.
    - id_hint: change-implying-criteria-default
      description: |
        Implement C4: every gradeable effective acceptance criterion is change-implying by default (so C1 applies to any AI-dispositive item with a non-empty gradeable criteria set), with the ONLY exemption a declared change-optional / no-change-expected marker on the item, recorded in the acceptance journal so no item is silently exempted. Add the control test that a declared change-optional item with an empty merged diff is not misclassified and grades on its normal path.
---

## Proposal: Acceptance refuses an empty merged diff — a zero-change merge is ungradeable, not delivered

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

For a work item whose effective acceptance criteria imply file changes, the acceptance pass MUST treat an empty merged diff (zero files changed) as an ungradeable merged-diff leg and return NEEDS_ATTENTION, never PASS — an empty diff is a verdict manufactured from absent evidence, the class the evidence rule already forbids. Scoped/janitor checks whose file scope matched zero files MUST report a distinct vacuous-match outcome a gate cannot count toward passing, the zero-change merged run MUST compose into the needs-attention surface naming the empty-diff leg, and every gradeable criterion MUST be change-implying by default with a declared change-optional escape hatch as the only exemption.

### Motivation

homelab PR #1044 merged with ZERO files changed under a title claiming its work item was delivered: the scoped janitor check passed vacuously over the empty diff all four review rounds, and acceptance graded the zero-change merge as a deliverable because nothing between merge and disposition asked whether the merged diff contained any change at all. Fabro deliberately treats zero-change runs as normal success at every version and holds that the CONSUMER owns any refusal (PublishOutcome::NoChanges was added 2026-07-27 and removed 2026-07-28 because no consumer distinguished it), so this orchestrator's acceptance layer — where 'was anything delivered?' is a ratified question under the evidence rule — is the layer that must refuse. The ratified evidence rule, PASS/NEEDS_ATTENTION legs, and effective-criteria gradeability already exist; the gap is that none of that text says what an EMPTY merged diff is, and the shipped pass treated 'diff observed, contains nothing' as gradeable and graded on.

### Proposed Changes

Amend `SPECIFICATION/contracts.md` and add the paired Given/When/Then
scenarios to `SPECIFICATION/scenarios.md` (co-editing
`tests/heading-coverage.json` for any new H2 per the revise co-edit
discipline). The defect class: for a work item whose acceptance criteria
imply file changes, an EMPTY merged diff is not passing evidence, yet the
shipped acceptance pass read "diff observed, contains nothing" as a
gradeable diff and graded PASS — a verdict manufactured from absent
evidence, the exact class the evidence rule was ratified against. Live
instance: homelab PR #1044 merged with zero files changed under a title
claiming its work item was delivered; the scoped janitor check passed
vacuously over the empty diff and acceptance graded the zero-change merge
as a deliverable. Fabro treats zero-change runs as normal success and
holds that the CONSUMER owns any refusal (it added `PublishOutcome::NoChanges`
on 2026-07-27 and removed it on 2026-07-28 because no consumer distinguished
it), so this orchestrator's acceptance layer is the layer that MUST refuse.

The clauses to add:

(C1) EMPTY MERGED DIFF IS NOT PASSING EVIDENCE. Amend §"Post-merge
acceptance (`acceptance -> done`)" → "The evidence rule". For a work item
whose effective acceptance criteria are change-implying (C4), an empty
merged diff — zero files changed, zero hunks, under the merged ref — MUST
be treated as an UNGRADEABLE merged-diff leg, not as an observed gradeable
diff. The acceptance verdict MUST be NEEDS_ATTENTION (the merged-diff leg
observed empty, therefore ungradeable against change-implying criteria),
and MUST NOT be PASS. This is a direct application of the existing rule
that "a verdict MUST NOT be manufactured from absent evidence" and that
NEEDS_ATTENTION is the verdict "when the pass CANNOT OBSERVE what a
judgment needs". NO_CHANGE_NEEDED MUST remain reachable ONLY through its
own ratified OBSERVED-evidence route (the item's change is already present
on the default branch, or superseded); an empty diff alone MUST NOT be
read as that observation, because "nothing changed in this merge" is not
"the change already exists elsewhere".

(C2) SCOPED CHECKS REPORT VACUITY, NOT SUCCESS. Amend §"Dispatch preflight
and post-merge step discipline" (the janitor check-suite surface). A
janitor or otherwise scoped check whose file scope matched ZERO files in
the diff under judgment MUST report a distinct vacuous-match outcome, and
a gate MUST NOT count a vacuous-match outcome toward passing. A
vacuous-match outcome is not failure evidence either; it composes as "this
check observed nothing", so absence of matched files can neither pass nor
fail a gate on its own. Zero matches rendering as success is precisely how
PR #1044's scoped `check-no-workflow-edits` passed over the empty diff all
four review rounds.

(C3) DISPATCHER COMPOSITION NAMES THE EMPTY-DIFF LEG. Amend §"Wait
completeness" / "Parked-acceptance arity and distinguishability". A
zero-change merged run whose acceptance parks NEEDS_ATTENTION per C1 MUST
compose into the needs-attention surface through the existing
NEEDS_ATTENTION-parked-acceptance composition class as exactly ONE
attention item, and its `summary` MUST name the empty-diff evidence leg as
the absent-evidence leg (alongside the `accept`/`reject` dispositions the
class already requires), so the condition surfaces as one attention item
with a handoff rather than a silent `done`. This introduces no new
composition kind.

(C4) HOW "CRITERIA IMPLY FILE CHANGES" IS DETERMINED. Amend §"Effective
acceptance criteria". Every gradeable effective acceptance criterion MUST
be treated as change-implying by DEFAULT, so the empty-diff refusal (C1)
applies to any AI-dispositive item with a non-empty gradeable criteria
set. The ONLY escape hatch is an item explicitly declared as
change-optional — a `human-only`/no-change-expected marker on the item —
for which an empty merged diff MUST route to the normal grading path
rather than to the C1 refusal. An item MUST NOT be silently exempted; the
exemption MUST be a declared property the acceptance journal records.

Controls to add as scenarios in `scenarios.md`:
- POSITIVE: a real-change merge (non-empty gradeable diff) still grades
  normally and MAY reach PASS — C1 changes nothing for it.
- DISCRIMINATING: replaying the PR #1044 shape (a zero-change merge under a
  change-implying item) MUST park NEEDS_ATTENTION with the empty-diff leg
  named, and the scoped check's vacuous-match outcome MUST be visible.
- CONTROL: an item declared change-optional (pure verification /
  telemetry-watch, if any exist) with an empty merged diff MUST NOT be
  misclassified — it grades on its normal path.

Non-overlap with the sibling proposal `janitor-argv-declared-resolution`
(prevention at prepare/validation time): this proposal owns REFUSAL at
acceptance time. Even with every prevention in place, a zero-change merge
that slips through for any future reason MUST NOT be accepted. Different
clauses, different pipeline stage; the two amendments MAY land
independently.
