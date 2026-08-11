---
proposal: planning-lane-realization-core-v197-v198.md
decision: accept
revised_at: 2026-08-09T13:44:33Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Maintainer-authorized accept (2026-08-09, brief-18) after a two-round independent adversarial review by a separately-spawned read-only Fable-model agent: round 1 (against 40ce44e5) found one real blocker in section K's heading-coverage guidance, fixed via bd-ib-mrqoy2.7 (PR 1334, merge 9f3d053d); round 2 cleared the amended bytes, verdict recorded 2026-08-09T12:01:11Z on bd-ib-mrqoy2.2's journal. Proposal verified byte-identical between 9f3d053d and origin/master before payload assembly. Resulting files rebuilt from fresh worktree bytes at 9f3d053d; vocabulary sweep returns zero over the live spec (control ~30 pre-edit); H2 delta is exactly the two scenario renames with their heading-coverage entries re-derived carrying integration-tier keywords per amended section K. REPAIRED per brief-19 after the supervisor's independent pre-merge check: the old root-note allowance parenthetical removed from the plan store clause (conforming to core's ratified bullet), Scenario 41's Then line corrected to research-subdirectory placement, and the residual possessive vocabulary at the consented store-writer clause fixed; payload recomposed from a hard reset to 9f3d053d.

## Resulting Changes

- README.md
- contracts.md
- constraints.md
- scenarios.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-09T12:01:11Z
verdict: NO BLOCKERS
proposal_stem: planning-lane-realization-core-v197-v198
content_digest: 86c95993edc891b01ae715642075dae68a97b11d0bab7a6b6449dde0436162ac

## Accepted deviation — the recorded review does not cover the digest-bound bytes

This revision's `reviewed_at` of `2026-08-09T12:01:11Z` timestamps an
independent review of the PROPOSAL bytes only. The `content_digest` recorded
above spans the proposal bytes AND the resulting-file bytes, and those resulting
bytes were recomposed at `revised_at` `2026-08-09T13:44:33Z` during a
payload-fidelity repair. The independent adversarial review that actually covers
the digest-bound bytes was delivered approximately five minutes AFTER this
ratification, and returned `NO BLOCKERS` on content; it is preserved verbatim at
`SPECIFICATION/history/v059/proposed_changes/ratification-review-post-repair.md`.

No conforming correction exists: the contract requires `reviewed_at` to precede
`revised_at`, the covering review postdates it, and a content-identical
re-ratification would fail `doctor-accept-decision-snapshot-consistency`. The
maintainer accepted this as a documented deviation on 2026-08-09 rather than
revert spec content that independent review confirmed correct. The fleet-wide
hardening is tracked as `livespec-yrq4`.
