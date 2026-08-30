---
proposal: a-factory-run-never-awaits-a-human.md
decision: accept
revised_at: 2026-08-30T13:16:41Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5 (session fix-fabro-blockages)
---

## Decision and Rationale

Accepted as filed, with one deviation from the proposal's diff text: the dangling cross-reference to a non-existent §"Preserve-by-reference" heading was dropped so the clause reads "the preserve-by-reference pointer" without citing a heading that does not exist. The section ratifies the run half of the needs-human gate — a needs-human outcome terminates the run and preserves work by reference; the Dispatcher reconciles every declared factory's non-terminal run inventory against the ledger, export-then-terminate, journaled; reconciliation never changes blocked_reason or auto-resolves a decision — preserving §"Every needs-human escalation still reaches a human" and Scenario 36 verbatim and staying inside §"Host concurrency belongs to the Fabro scheduler" (reconciliation is not a refusal or a gauge). Exit code 4 is restated to match. Scenarios 103-106 bind every new MUST; heading-coverage carries four TODO entries owned by plan epic bd-ib-n77djm. Independent read-only review (Claude Sonnet 5) over the exact final bytes returned NO BLOCKERS; its non-blocking notes (no Terminology entry for 'preserve-by-reference pointer'; blocked_run_grace_seconds not listed in the closed policy-settings enumeration, consistent with wip_cap precedent) are recorded here for a future pass. Design record: plan/ledger-is-the-only-gate/research/001-design-and-slice-plan.md.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-30T13:16:36Z
verdict: NO BLOCKERS
proposal_stem: a-factory-run-never-awaits-a-human
content_digest: 17251b00b129ed4bce0fdbfad8f2b3ee6cd0b9c8d6613b525cb730ca47329c2f
