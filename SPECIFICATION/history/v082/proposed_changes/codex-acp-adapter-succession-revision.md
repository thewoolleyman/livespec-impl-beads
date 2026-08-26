---
proposal: codex-acp-adapter-succession.md
decision: accept
revised_at: 2026-08-26T09:57:16Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: homelab-loop-hardening-orchestrator
---

## Decision and Rationale

Accepted under this plan epic's recorded delegated-revise authority, the same authority that cut v080 and v081. The premise is a MEASUREMENT, not a preference: npx resolves a package's bin through the shared global bin link, so with both codex-acp packages installed, invoking either package NAME runs whichever owns the link. A renderer identifying the adapter by name can emit a string naming one package while executing another, defeating this section's opening claim that a reader can predict the literal adapter string and check it against run_turn.command. Re-verified against the RELEASED image rather than the transitional layer: on python-agent-v1.35.0, pulled on both hp and vps, the baked path reports @agentclientprotocol/codex-acp 1.6.2 while npx-by-name still runs the predecessor, so the two coexist and the current renderer is unaffected until implementation. Upstream is ratified as livespec-dev-tooling v053. The no-environment-override clarification is necessary rather than cosmetic: without it this section forbids the very channel the succession adopts. The stale reachable-tier table is retired rather than updated because it was measured against an adapter version the image no longer bakes, and a table that reads as current is worse than no table when a pin chosen from it fails at dispatch. TWO BLOCKERS from the independent review were fixed before acceptance: the un-pinned base string had no single referent once the posture keys moved into CODEX_CONFIG, and a stale -c model args example contradicted the corrected sentence three before it in the same paragraph. Both are fixed and the reviewer re-reviewed the fixed text.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-26T09:49:00Z
verdict: NO BLOCKERS
proposal_stem: codex-acp-adapter-succession
content_digest: b831d80dda50114460649cf68567f9df5d291c00d69facc06c3271b55e199096
