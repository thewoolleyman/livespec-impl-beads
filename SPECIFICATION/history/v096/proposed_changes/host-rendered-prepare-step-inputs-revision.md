---
proposal: host-rendered-prepare-step-inputs.md
decision: accept
revised_at: 2026-09-04T16:30:33Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8[1m]
---

## Decision and Rationale

Accept as authored. The proposal closes a ratified-wording vs shipped-behaviour gap that hid a multi-day dispatch outage: the clause demanded every inputs.* token sit in a position the ENGINE renders, but fabro 0.254.0 leaves run.prepare commands verbatim, and 79066c79 made the correct behaviour host-side overlay substitution. Widening the criterion to 'a position resolved before the sandbox executes it' with exactly two admitted resolvers (engine at run-create time; Dispatcher run-config overlay host-side) matches the evidence and reinforces the neighbouring 'Resolve once, project everywhere' clause (overlay substitution is a projection of the same ResolvedIntegrationContract). Correctly placed in this repo's contracts.md + scenarios.md (Dispatcher realization mechanism, not core); respects the behavior->clause+scenario split (co-edited atomically); set-equality and closed-set obligations left unchanged. No design record is contradicted, so no intent-preservation floor fires.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-04T16:29:57Z
verdict: NO BLOCKERS
proposal_stem: host-rendered-prepare-step-inputs
content_digest: 7cd55bca028d52ab9e2a67adb94a2e4d4049d6baef41e369e08dd0b2c9d42658
