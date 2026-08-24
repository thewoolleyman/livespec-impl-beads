---
proposal: check-anchored-gap-tied-closure.md
decision: accept
revised_at: 2026-08-24T06:08:01Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: honest-gap-detector-and-check-anchored-closure
---

## Decision and Rationale

Resolves the unsatisfiable gap-tied closure gate (F3, F4) by anchoring closure to a check path + negative control, already implemented and tested in PR #1819. First independent review (sonnet) found two real completeness gaps -- no producer specified for gap_check_path, and --for-work-item used but never contracted in capture-spec-drift -- both fixed. Second independent review (sonnet, separate context): NO BLOCKERS, with three non-blocking notes; the dangling 'Step 1-2' reference it flagged has been cleaned up (capture-spec-drift's section is prose, not numbered steps); the other two (baseline-hash metadata key precision, and cataloguing new metadata keys in the Work-item beads-issue mapping section) are house-style polish, not correctness gaps, and are left for a follow-up if the maintainer wants them.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-24T06:07:55Z
verdict: NO BLOCKERS
proposal_stem: check-anchored-gap-tied-closure
content_digest: 36bd8c101fc4103d6192136a69c34a23aa099f26d8589b7765ecb204246304c6
