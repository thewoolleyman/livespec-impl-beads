---
proposal: consensus-gated-automated-groom-cut.md
decision: modify
revised_at: 2026-09-06T17:15:56Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5-1 (pluggable-factory-workflow-configs)
---

## Decision and Rationale

Accepted with one deferred co-edit; every normative edit lands verbatim, and the deferral is recorded under Modifications. The proposal carries livespec's already-resolved values call on the groom cut (the spec-side-autonomy plan's brainstorm record, "Values calls" item 2) rather than re-deciding it, and it takes the report-only shape livespec core's own Increment 3 took, because core has not ratified the consensus tier: the automated cut is permitted in principle and stays human-decided in fact until that tier and its evidence exist. It respects all three authoring splits. The behavior is stated as MUST clauses AND as a Gherkin scenario co-edited with tests/heading-coverage.json; the material is user-observable wire contract, so it lands in contracts.md, the one spec.md edit being a stale count in a sentence that cites a retitled subsection; and it describes this orchestrator's own Dispatcher and groom front-end, so it belongs in this repository's specification rather than in core. The mechanism does not contradict the design record it builds on: a factory run never awaits a human, so the propose phase terminates at needs-human carrying the draft, the approval arrives through the resolve-blocked valve as a ledger comment, and a second dispatch applies it. Three independent objective doctor passes over the draft returned findings that were discharged before filing, the last reporting zero blockers. Independent read-only ratification review of the final bytes returned NO BLOCKERS with an independently recomputed matching digest. Decision delegated per spec_governance.revise_decision_mode. This is a narrowed single-proposal pass: the pending live-exercise-acceptance-admission proposal belongs to another thread and is deliberately left in place.

## Modifications

One co-edit is deliberately deferred; every normative edit lands verbatim. Edit 9 says the `reason` field of the `## Dispatcher policy settings` entry for contracts.md in tests/heading-coverage.json SHOULD be updated to follow the two H3 retitles this revision performs. That update is NOT applied here. That registry entry is an UNOWNED TODO — it carries `test: "TODO"` and no `work_item` — and this repository's `check-no-todo-registry` gate arms its release tier for any staged changeset that authors OR MODIFIES an unowned TODO entry, then fails on every pre-existing unowned entry in the registry. Measured 2026-09-06 on this revision's own commit attempt: applying the reason update refused the commit with more than forty findings, none of them about this change, while the new Scenario 118 entry was accepted because it carries `work_item: bd-ib-yqpdrt`. Giving the policy-settings entry an owner to satisfy the gate would be false ownership: this plan does not own the dispatcher-policy-settings coverage. Edit 9 is worded as a SHOULD and already defers its sibling cleanup — the committed .livespec.jsonc comment citing the old subsection title — to the implementation child; the registry `reason` update joins it there, in the policy-settings child filed under bd-ib-yqpdrt at this revise pass. Nothing normative is affected: the two H3 retitles, every MUST clause, Scenario 118 and its owned coverage entry all land exactly as filed.

## Resulting Changes

- contracts.md
- scenarios.md
- spec.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T17:14:54Z
verdict: NO BLOCKERS
proposal_stem: consensus-gated-automated-groom-cut
content_digest: 9f21d697403d7aa98d9b5dbc5ee8765d888efe71743a9762f35af42fca781764
