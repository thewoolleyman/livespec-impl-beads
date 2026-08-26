---
proposal: acp-node-timeouts.md
decision: accept
revised_at: 2026-08-26T05:08:05Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: homelab-loop-hardening-orchestrator
---

## Decision and Rationale

Ratified as filed. The maintainer's 2026-08-26 commission (item C) orders per-node timeouts configurable with a 30-minute default and an explanation of the 20-minute limit, which the section records as the compaction proxy rather than a timeout. Keys dispatcher.node_timeouts and dispatcher.stall_timeout_seconds default to 1800 and 7200 seconds, resolve through the same three layers, and are rendered as literal durations into the self-contained dispatch payload because the pinned Fabro build silently drops a templated timeout (research on bd-ib-cnkf); the subprocess ceiling derives from the resolved graph; the reduction from the former 14400/3600-second literals is named as deliberate; the Codex compaction limit rides the adapter args of the adapter-configuration section rather than a separate key. Scenario 89 carries the behaviour. Implementing item bd-ib-cnkf.

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
proposal_stem: acp-node-timeouts
content_digest: ef8351823d6df761396f2da82a0d3adeb5b6ff6528cc0b8c2b7ba1c96640115c
