---
proposal: retroactive-codex-cover.md
decision: accept
revised_at: 2026-08-23T10:22:05Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Ratified on the foreman's delegated maintainer authority (seat epic bd-ib-1mjt, 2026-08-23T08:54:15Z; scheduling per FOREMAN RULING 3 on plan epic bd-ib-yhbsd4). Retroactive cover for two behaviours already live fleet-wide and carrying no specification commitment: the per-node Codex model pins of PR #1711 (requirement R1, ledger bd-ib-var6) and the provider-limit permanence and root-cause surfacing of PR #1732 (requirement R2, ledger bd-ib-qpuu). Combined into one pass per that ruling, because both are retroactive cover, both land in contracts.md, and neither gates other work. Each obligation was verified against the running code before drafting, so the ratified text describes the factory that actually runs -- C1's stated acceptance. The scope boundary the C2 rider raised is stated explicitly rather than elided: the Dispatcher-side obligation does NOT bind Fabro's in-sandbox node classifier, which still calls a provider ceiling transient and retries once, so the text says so and points at the admission gate as the thing that prevents the dispatch instead.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-23T10:20:23Z
verdict: NO BLOCKERS
proposal_stem: retroactive-codex-cover
content_digest: 0a2c382e2c90369b0742c0146f2dd9d6880dbade31dd3cc071ee24c324b2ec0d
