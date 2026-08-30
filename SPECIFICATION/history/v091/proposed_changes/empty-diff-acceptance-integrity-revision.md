---
proposal: empty-diff-acceptance-integrity.md
decision: accept
revised_at: 2026-08-30T06:09:41Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: empty-diff-acceptance-integrity
---

## Decision and Rationale

Charter C1-C4 ratified by the maintainer 2026-08-30. The four contracts.md clauses and Scenario 96 realize the accepted proposal: an empty merged diff for a change-implying item is ungradeable -> NEEDS_ATTENTION (never PASS, never NO_CHANGE_NEEDED); a file-scoped check matching zero files reports vacuous-match a gate counts toward neither passing nor failing; the zero-change parked run composes into needs-attention naming the empty-diff leg; gradeable criteria are change-implying by default with a declared change-optional escape hatch. Additive to the existing evidence rule; no design-record contradiction. Independent read-only sonnet ratification review returned NO BLOCKERS on the exact resulting bytes.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-30T06:09:31Z
verdict: NO BLOCKERS
proposal_stem: empty-diff-acceptance-integrity
content_digest: eb7e6435529490459b0827c405af9e953a1440efbb27f07aaa1f963babc08537
