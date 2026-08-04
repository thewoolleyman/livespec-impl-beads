---
proposal: plan-thread-tombstone-ban.md
decision: accept
revised_at: 2026-08-04T16:26:54Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted after three review rounds, the last of which verified the LANDED BYTES mechanically. Round 1's two blockers discharged (seam qualifier scoped to the work-item leg; disposition 1 states the epic stays OPEN). Round 2 corrected a factual premise — the fleet's one tombstone was the WORKER handoff.md stub, not a supervisor respawn prompt — and verified against the code that totality breaks no supervisor contract. Round 3 rejected the first landing for two RENDERING defects: a line-wrap split the `capture-work-item` code span, which CommonMark renders as a space so the contract would have named the operation 'capture- work-item'; and the prose dropped the contract's CONDITIONAL on epic reopening, which would have offered an agent a free way to steal a retired slug for unrelated work. Both fixed, and the reviewer then confirmed the corrected bytes by whitespace-normalized word-for-word comparison against the clause. reviewed_at below is that confirming review, so the evidence names the review that actually saw these bytes rather than an earlier round. DELIBERATELY SCOPED partial revise pass: the payload names only this topic.

## Resulting Changes

- contracts.md
- ../.claude-plugin/prose/plan.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-04T16:24:51Z
verdict: NO BLOCKERS
proposal_stem: plan-thread-tombstone-ban
content_digest: 336d712c6f6e01fbc2695743b6beec6369411a67b97ba68641d15a1f023fa65e
