---
proposal: acp-node-adapter-configuration.md
decision: accept
revised_at: 2026-08-26T05:08:05Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: homelab-loop-hardening-orchestrator
---

## Decision and Rationale

Ratified as filed. The maintainer's 2026-08-26 commission (item B) orders every node's model made a configuration value at three layers, generically supporting any model behind any provider protocol with local-llm as the example only; the maintainer withdrew the network, credential, context-cap and capacity obligations a relay had attached. The section expresses a node's adapter as (command, env map, args) so provider identity lives in configuration, resolves per node and per field through workflow defaults, the target's dispatcher.acp_nodes table and a journaled per-dispatch argument, keeps dispatcher.codex_models as the per-repository Codex shorthand so v080's pin rules are unchanged, preserves the no-environment-override rule at every layer, reconciles with the console launcher's no-per-run-flag rule, journals the supplying layer per field, keeps the keys committed-configuration-only, and requires a hermetic per-layer negative control. Scenarios 87 and 88 carry the behaviour. Implementing item bd-ib-tsna; bd-ib-un226z is superseded. No design record is contradicted: the pin section's own rationale is retained by reference.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-26T05:07:15Z
verdict: NO BLOCKERS
proposal_stem: acp-node-adapter-configuration
content_digest: 203a516fe62a5e50278ab922705b661f68ba9df27459773c203d2a6bf6d7c133
