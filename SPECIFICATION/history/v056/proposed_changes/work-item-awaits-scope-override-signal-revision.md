---
proposal: work-item-awaits-scope-override-signal.md
decision: modify
revised_at: 2026-08-03T01:30:15Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: codex-gpt-5
---

## Decision and Rationale

Accept the explicit per-item signal because consumers must not re-derive Dispatcher refusal heuristics; modify it by defining its beads-label home and its disjointness from intrinsic factory_safety.

## Modifications

Define awaits_scope_override as a materialized boolean backed by an awaits-scope-override label, including set and clear transitions and Scenario 48 outcomes.

## Resulting Changes

- contracts.md
- scenarios.md
