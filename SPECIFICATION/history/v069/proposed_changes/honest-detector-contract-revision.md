---
proposal: honest-detector-contract.md
decision: accept
revised_at: 2026-08-24T05:42:18Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: honest-gap-detector-and-check-anchored-closure
---

## Decision and Rationale

Resolves the self-contradiction identified in homelab findings F1/F2/F5 (measured live against homelab's SPECIFICATION on 2026-08-24: two demonstrably-honored rules still reported as gaps). Prose-only change; independent ratification review (sonnet model, per maintainer direction 2026-08-24 to not use fable after it returned 529 Overloaded) returned NO BLOCKERS, noting one nuance: the --since-version 'Caller caution' paragraph's MUST NOT sentence is new normative text, though it restates behavior the mechanism paragraph above it already implies rather than creating a new system requirement.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-24T05:41:56Z
verdict: NO BLOCKERS
proposal_stem: honest-detector-contract
content_digest: 937496449b360d653b5d56ce9ec737952ffd697b7f55227463d07b8170c9c23b
