---
proposal: plan-slug-anchor-and-typed-next-action.md
decision: modify
revised_at: 2026-09-04T16:18:43Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4.8 (console-control-plane-primitives revise)
---

## Decision and Rationale

Ratify the D6 plan-identity contract (console decision D6; plan console-control-plane-primitives epic bd-ib-w3nwz5 child bd-ib-w3nwz5.1). Landed as modify rather than accept for two authored refinements: (1) a reconciling sentence in the plan-identity subsection making explicit that the associated_work_item_id anchor names the epic id from plan-open onward and the literal unassigned is only the pre-open standalone-research state, so there is no contradiction with the anchor-names-the-epic-id rule; the Planning Lane restraint-budget clause is correspondingly amended to describe the new bounded epic-metadata keys instead of the stale 'no new ledger state' claim; (2) scenario coverage added beyond the proposal's literal Scenarios 109-112 — a plan_slug_canonical case in Scenario 109 and a new Scenario 113 for plan_close_evidence — because both are error-verdict behaviors the proposal's own authoring discipline requires to be scenario-backed; an independent read-only sonnet ratification review flagged exactly those two gaps and confirmed NO BLOCKERS once covered.

## Modifications

contracts.md: added the pre-open/post-open reconciliation sentence to the anchor paragraph; amended the restraint-budget clause. scenarios.md: added Scenario 109 case 'a non-canonical slug is reported' (plan_slug_canonical) and Scenario 113 'A plan epic closed without completeness-review evidence is reported' (plan_close_evidence, with evidenced-closed and open-epic negative controls). tests/heading-coverage.json co-edited to add the Scenario 113 entry (owned by bd-ib-w3nwz5.1).

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-04T16:18:13Z
verdict: NO BLOCKERS
proposal_stem: plan-slug-anchor-and-typed-next-action
content_digest: a23ce70b76bc7129ab3da45f6ffda47a947526e8cdd4fd9156709896d0058a2d
