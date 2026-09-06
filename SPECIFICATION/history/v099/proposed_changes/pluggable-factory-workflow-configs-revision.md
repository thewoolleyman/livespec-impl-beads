---
proposal: pluggable-factory-workflow-configs.md
decision: modify
revised_at: 2026-09-06T09:09:20Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5-1 (pluggable-factory-workflow-configs)
---

## Decision and Rationale

Accepted with one mechanical modification. The proposal ratifies the target-local workflow resolution precedence the Dispatcher has run since 2026-07-20 (c8bde4a5) without the amendment this section reserved, and adds the named workflow-variant registry as an optional acp_nodes-class capability with a recorded per-dispatch selector, a ledger pin, pre-run refusals in the adapter-layer shape, and every registered variant held to the reserved workflow's six ACP node names, its typed-input set and its dispatch-path seam discipline. It follows all three authoring splits: the behavior is stated as MUST clauses AND as a scenario co-edited with tests/heading-coverage.json; the material is user-observable wire contract (contracts.md); and it describes this orchestrator's own Dispatcher, so it belongs in this repository's spec. A scoped objective doctor pass on the draft found seven tensions with existing clauses and each is discharged in the filed text, keeping the cited lead-in 'Target-local workflow' resolvable and citing the literal-ban gate where constraints.md ratifies it. No design record is contradicted: the change ratifies shipped behavior and extends it, and the ACP node adapter configuration section it builds on is cited, not departed from. Independent read-only sonnet ratification review returned NO BLOCKERS with a matching recomputed digest. Decision delegated per spec_governance.revise_decision_mode.

## Modifications

The proposal's new scenario is numbered 116, but v098 (cut earlier on 2026-09-06 by the operator-initiated-exhaustion-record-clearance revise) already ratified Scenario 116. The scenario lands as Scenario 117 with its heading text, feature and every sub-scenario otherwise verbatim, and the tests/heading-coverage.json entry names Scenario 117 (test TODO, work_item bd-ib-yqpdrt, reason recording that the exercising test is owed once the three implementation children land). The adopter-dispatch scenario's Given swap is applied at the file's two-space indent rather than the diff block's four. Second, on the independent ratification reviewer's blocker: the proposal's sentence that prepare steps are expressed through typed inputs 'rather than by carrying a workflow copy' contradicted the unmodified Factory-sandbox toolchain disposition bullet, which cites this very paragraph as ratifying that an adopter MAY carry its own workflow with its own prepare chain. The landed sentence affirms both routes: typed inputs express prepare steps without a copy, and an adopter that carries its own workflow keeps its own prepare chain in it, subject to the same integration-input parity the Named workflow variants paragraph requires of a registered variant. Nothing else in the Proposed Changes section was altered.

## Resulting Changes

- contracts.md
- scenarios.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T09:08:50Z
verdict: NO BLOCKERS
proposal_stem: pluggable-factory-workflow-configs
content_digest: 991011c578966e373217405ed39d6322b49eeb8cf2f3567c5f6fb608efa8ba36
