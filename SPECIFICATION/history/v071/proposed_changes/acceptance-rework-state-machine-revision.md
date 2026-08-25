---
proposal: acceptance-rework-state-machine.md
decision: accept
revised_at: 2026-08-25T12:40:50Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted under the delegated revise authority recorded on epic bd-ib-ujihbw (standing maintainer directive via homelab/hl-nkuzaz; spec_governance arms revise_decision_mode: delegated with auto-spawn ratification review). The proposal closes the verified dead end where both ratified rework entries route to `active` with no executor: a ledger-held rework:pending marker, drain-before-ready selection guarded by the live dispatch lock, a marker-keyed reconcile-merged refusal, and one-meaning-of-active co-edits across the state semantics, verb vocabulary, loop invocation, both capacity clauses, the beads field map, and the stale door-rules attribution sentences (bd-ib-ktxb shipped). Two commissioned adversarial reviews (claude + codex, plan research/003) were triaged and every repaired-in-place disposition applied before this acceptance; the independent sonnet ratification review returned NO BLOCKERS on the exact final bytes. Coordination note per the proposal: bd-ib-zp3u7y (active, factory-assigned) owns the stranded-dispatch sibling population; the marker partitions the two populations and its owner is coordinated through the plan thread's records.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-25T12:40:29Z
verdict: NO BLOCKERS
proposal_stem: acceptance-rework-state-machine
content_digest: 5933344ea102a2412a8810dfa0d7fdb285a806086ceb887539db77dfe6b7062e
