# Review-to-disposition context propagation

## Problem observed

Fabro's `ImplementWorkItem` workflow can complete implementation, janitor,
review, and review-fix stages, then enter a disposition stage that cannot see
the latest review findings. In the observed run `01KZYKV6P9EJ`, the second
review emitted two blocking findings about Codex cache alias production wiring
and ledger retention, but the disposition prompt contained only the first-round
`finding_dispositions_r1` context. The findings were present in Fabro's event
log, but not in the structured context handed to disposition. The agent
correctly refused to guess, escalated for human input, and the run became
unattended/terminated without a PR.

Existing prior-art ledger item `bd-ib-hote` records the same defect from run
`01KZ3BEWTS5H` and broadens the impact: round-one behavior can appear correct
because the agent re-derives findings, while later rounds can silently lose
findings; the human prompt is not reliably observable; and the offered retry /
reimplement / abandon choices do not address a harness propagation failure.
This plan supersedes neither item nor its history; implementation must reconcile
with it and either adopt it as the child or explicitly link the follow-up.

## Intended fix

1. Trace the workflow graph and context contracts from every review round into
disposition. Persist each round's structured review findings under a stable,
round-indexed key (or an explicit `latest_review_findings` plus complete history)
and make the disposition prompt consume the latest complete set, not merely the
first-round disposition record.
2. Add a fail-closed precondition at disposition: if review was required but no
findings are available, stop with a machine-readable diagnostic identifying the
missing context key and the producing stage. Do not invite an unanswerable
interactive decision or claim the run is complete.
3. Preserve all finding classes and dispositions across retries (blocking,
advisory, accepted, rejected, deferred) and make the dataflow testable without
scraping human-readable logs. The event log remains observability; the workflow
context is the stage input.
4. Make the external drive/dispatcher result distinguish `blocked` awaiting
human input from terminal `failed`, so supervisors do not mistake an unattended
interview for a completed run. If that surface is outside this repository's
safe scope, record it as a separately routed follow-up rather than silently
omitting it.
5. Add regression coverage for one review round, review-fix plus second review,
multiple review rounds, missing findings, malformed findings, and the exact
reproduction where findings exist in the event log but are absent from context.
Include an end-to-end workflow/mock assertion that disposition sees the second
round's blocking finding and cannot proceed with an empty review context.

## Boundaries and verification

This plan targets the orchestrator workflow/context and its Python driver
surface. It does not change Fabro itself or make disposition scrape raw event
logs. It does not alter review policy, permit bypassing findings, or merge work
when the review input is incomplete. Verify with the repository's full checks,
focused workflow/context tests, and a deterministic replay of run `01KZYKV6P9EJ`
(or an equivalent fixture) proving that the second review findings reach
 disposition and that missing input fails closed with an actionable result.
