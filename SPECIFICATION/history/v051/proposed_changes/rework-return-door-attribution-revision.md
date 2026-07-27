---
proposal: rework-return-door-attribution.md
decision: accept
revised_at: 2026-07-27T19:17:23Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Both findings accepted. Finding 1 is a matter of fact and was verified at source: ratified contracts.md asserts 'Both rework returns are journaled', yet `_drive_valves._reject_item` returns `valve_success(...)`, whose `journal` object (`_drive_valve_result.py:29`) is placed in the drive CLI's RESPONSE PAYLOAD; no drive module references a JournalFile, and the dispatch journal holds ZERO `human-valve-*` records across its whole history while `acceptance-auto-rework` appears 4 times. The clause's own stated standard — that a door rule omitting a shipped writer is false, not merely incomplete — applies to its justification too. Finding 2 is the normative call the proposal deliberately left open, and the maintainer selected ADD ATTRIBUTION over removing the door: the Dispatcher already performs this exact transition automatically under `acceptance-auto-rework`, so the capability is plainly wanted, and `reject:rework` is the only operator route from `acceptance` back into work — `reject:regroom` routes to `backlog`, which would restore admission eligibility for already-merged work. The attribution is load-bearing rather than bookkeeping: this repository's Dispatcher reads `active` as a claim, and the S3 slice's reclaim predicate had to fall back on inspecting each item's most recent terminal outcome precisely because this door leaves no trace.

## Resulting Changes

- contracts.md
- scenarios.md
- ../tests/heading-coverage.json
