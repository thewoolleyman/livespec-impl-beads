---
proposal: dispatcher-staleness-gate-comparand.md
decision: accept
revised_at: 2026-08-29T12:18:28Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: dispatcher-staleness-gate-comparand
---

## Decision and Rationale

Accept: re-bases the dispatch-admission plugin-currency gate onto the ratified self-update contract. The shipped gate hard-refuses dispatch (exit 3) whenever the executing build != the live refs/heads/release head probed at dispatch time — a blocking form that appears nowhere in SPECIFICATION and contradicts the ratified rule that a host-side dispatch legitimately runs the operator-provisioned release and that detect/canary/surface-restart-due/alarm is the whole of the Dispatcher's self-update responsibility. The accepted clauses forbid blocking on ambient release-staleness, move freshness pressure to a non-blocking dispatcher-currency-staleness needs-attention fact plus the ratified canary restart-due surfacing, and retain a single deliberate blocking form — the operator-configured dispatcher.minimum_release floor. Behavior is carried by both BCP14 clauses in contracts.md and Scenario 95 in scenarios.md; the tests/heading-coverage.json entry is co-edited in the same change. No design record is contradicted (the nearby github-app-auth record governs credentials, not the self-update comparand).

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-29T12:17:53Z
verdict: NO BLOCKERS
proposal_stem: dispatcher-staleness-gate-comparand
content_digest: a2bdcdf233c110482a488698b442cfe0a55287ce257a896543ce984d2ef4fdb7
