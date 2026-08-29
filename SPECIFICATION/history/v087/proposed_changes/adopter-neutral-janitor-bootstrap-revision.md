---
proposal: adopter-neutral-janitor-bootstrap.md
decision: accept
revised_at: 2026-08-29T01:37:50Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8:homelab-loop-hardening-orchestrator
---

## Decision and Rationale

Accept. The amendment faithfully realizes the proposal: the janitor-bootstrap step's integration point becomes the governed repository's DECLARED dispatcher.janitor_bootstrap.recipe with a fleet default convention (just install-commit-refuse-hooks), mirroring the v074 master-ci declaration-over-assumed-tooling shape, and a one-pass audit subsection disposes every step/preflight obligation against members-and-adopters-identical. Scenario 93 carries the behavior; the committed-configuration-only class and waiver escape are preserved unchanged. Ratified through delegated decision mode with an independent read-only sonnet reviewer returning NO BLOCKERS on the exact resulting bytes.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-29T01:33:00Z
verdict: NO BLOCKERS
proposal_stem: adopter-neutral-janitor-bootstrap
content_digest: 783d6ce239c215dc4deb362914fc80e6cf0c5a89bdd36d77e7830b3d91994610
