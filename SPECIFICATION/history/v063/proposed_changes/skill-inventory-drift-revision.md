---
proposal: skill-inventory-drift.md
decision: accept
revised_at: 2026-08-16T01:30:10Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5-bootstrap-pi-driver-orch
---

## Decision and Rationale

Repairs the fleet's skill-surface inventory drift (spec 11 vs 12 shipped, missing needs-attention) by making the inventory derived rather than restated. Two independent Fable-model review rounds: round 1 BLOCKERS(3) (three dangling section citations left by a heading retitle; an Out-of-scope-surfaces enumeration excluding needs-attention despite it being genuinely query-only; constraints.md's zero-orchestration enumeration left unamended), repaired via PR #1423; round 2 NO-BLOCKERS at e8b69640 with one cosmetic observation (a stale edit-count preamble), fixed via PR #1424. Separate Fable attestation independently re-derived all 12 edits (order-independent, verified both directions) and confirmed the exact resulting bytes and canonical digest. Repo-root README.md ride-along (the dead core-section citation and the stale eleven-skill count) landed in the same ratification commit, outside resulting_files.

## Resulting Changes

- contracts.md
- constraints.md
- README.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-16T01:23:44Z
verdict: NO BLOCKERS
proposal_stem: skill-inventory-drift
content_digest: 8dd31abba8b201698b483db2c26598a02378cd0fec8066ee5372b2005e737439
