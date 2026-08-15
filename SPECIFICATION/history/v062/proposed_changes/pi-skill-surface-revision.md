---
proposal: pi-skill-surface.md
decision: accept
revised_at: 2026-08-15T20:56:08Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5-bootstrap-pi-driver-orch
---

## Decision and Rationale

Three independent Fable-model adversarial review rounds: round 1 filed 4 blockers (replacement-target and anchor defects), repaired via PR #1410; round 2 re-verified the amended proposal against master 4c667c49 and filed 1 blocker (the load-bearing pi flat-namespace claim lacked the section's pi v0.84.1 version anchor), repaired via PR #1411; round 3 returned NO-BLOCKERS at bc9aea2a. A separate Fable ratification attestation independently re-applied every edit and confirmed the exact resulting bytes and canonical digest (an earlier attestation round ran on an Opus-model agent and was superseded for the model-policy reason; its one finding, ensure_ascii churn in the heading-coverage co-edit, was fixed before the Fable re-attestation).

## Resulting Changes

- contracts.md
- constraints.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-15T20:52:58Z
verdict: NO BLOCKERS
proposal_stem: pi-skill-surface
content_digest: 2daa1a954b016ead5e15684bceb7dd3b736a35a19b606b93fe28030f9b0394f4
