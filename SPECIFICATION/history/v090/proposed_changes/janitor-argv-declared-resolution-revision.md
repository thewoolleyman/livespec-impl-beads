---
proposal: janitor-argv-declared-resolution.md
decision: accept
revised_at: 2026-08-30T05:40:29Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: janitor-argv-declared-resolution
---

## Decision and Rationale

Both proposals faithfully extend the ratified declaration-over-assumed-tooling pattern (v074 master-ci, v087 janitor-bootstrap) to the whole adopter-coupling class and fix the I7 reconcile-venue deadlock. Instances re-verified at HEAD; the clauses are internally consistent with the existing step-discipline section and Target-local-workflow / Default-branch-resolution rules, and each new behavior is paired with a Given/When/Then scenario (96, 97, 98). Independent sonnet ratification review returned NO BLOCKERS over the exact resulting bytes.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-30T05:39:28Z
verdict: NO BLOCKERS
proposal_stem: janitor-argv-declared-resolution
content_digest: bf86e976695a07fe5e384be351d07d9ad3139c85b1049ec6968afa2b321a5665
