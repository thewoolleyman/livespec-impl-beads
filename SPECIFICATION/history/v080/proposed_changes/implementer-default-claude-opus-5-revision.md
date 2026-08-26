---
proposal: implementer-default-claude-opus-5.md
decision: accept
revised_at: 2026-08-26T04:27:03Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: homelab-loop-hardening-orchestrator
---

## Decision and Rationale

Ratified as filed. The maintainer's 2026-08-26 commission, relayed verbatim through the homelab coordinator, orders the implementer default switched to Claude Opus 5 ASAP as its own item ahead of the configurability work; the ratified section bound the implementer default to the literal Codex gpt-5.5/low string, so the switch is a spec change before it is a code change. The amendment is the minimal honest shape: the implementer class defaults to the Claude ACP adapter pinned to claude-opus-5 at high effort in the exact env-prefixed form the review adapter already uses; an explicit dispatcher.codex_models implementer entry still routes the class to Codex under the unchanged pin rules; the publish class is untouched; the first post-change dispatch is a transcript-verified run because earlier adapter versions silently ignored ANTHROPIC_MODEL. Scenario 64's no-configuration scenario is corrected to the new default and Scenario 86 adds the default rendering, the explicit-Codex-pin negative control and the unaffected publish class, with its coverage entry bound to the implementing item bd-ib-rcl7. Per-node configurability at every layer is deliberately out of scope here and tracked as bd-ib-tsna, as the section now says. No design record is contradicted: the section's own rationale for pinning (spend as a decision, not a decode residue) is preserved, and the no-environment-override rule is untouched.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-26T04:26:48Z
verdict: NO BLOCKERS
proposal_stem: implementer-default-claude-opus-5
content_digest: 8f00e0e98fe3e0cf7162c5ef8a96f2aba799f8402108ced4a8585c7131f6bd31
