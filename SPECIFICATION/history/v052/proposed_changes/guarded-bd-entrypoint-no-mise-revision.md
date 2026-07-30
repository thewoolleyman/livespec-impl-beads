---
proposal: guarded-bd-entrypoint-no-mise.md
decision: accept
revised_at: 2026-07-30T09:15:47Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: codex-gpt-5
---

## Decision and Rationale

The existing stale-shim wording was incident-specific and did not identify the lifecycle guard as the supported public entry point. The accepted wording closes both mise shadowing and direct private-delegate bypasses.

## Resulting Changes

- contracts.md
- constraints.md
- scenarios.md
- ../tests/heading-coverage.json
