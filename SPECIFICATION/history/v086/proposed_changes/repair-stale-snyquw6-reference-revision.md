---
proposal: repair-stale-snyquw6-reference.md
decision: accept
revised_at: 2026-08-29T01:04:32Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: fabro-factory-underutilization
---

## Decision and Rationale

Filed and drafted by this session with the exact intended final text; accepted as-is after independent sonnet review found NO BLOCKERS, verified against the real dispatcher code (_dispatcher_claim_reclaim.py, _dispatcher_tenant_checkouts.py): the live-dispatch-lock term is genuinely tenant-scoped via tenant_checkouts(), the journal-unreadable term and its dependents remain per-checkout as the new text states with no overclaim, and nothing here touches or weakens the host-observation prohibition. This corrects a completeness-review finding on the wip-cap-accounting-honesty plan's archive gate: contracts.md described bd-ib-snyquw.6 as an open, tracked divergence an hour after it closed (PR #1969). A prior attempt at this same fix (PR #1971) hand-edited contracts.md directly and was correctly rejected by CI's doctor-out-of-band-edits gate; this decision routes the same content through propose-change/revise so it mints a proper history/vNNN snapshot.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-29T01:04:26Z
verdict: NO BLOCKERS
proposal_stem: repair-stale-snyquw6-reference
content_digest: fd7374a841cd03ff677178d270da2ec7c11f37099eb49da2707134cb8c91f926
