---
topic: positive-floor-complement
author: claude-unattended-plan-operation
created_at: 2026-08-20T10:42:03Z
---

## Proposal: An enumerated not-human-gated decision set complements the escalation floor

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Add a `## Not-human-gated decision constraints` section to constraints.md carrying a governing test — a decision is design-human-gated only when it changes what the specification REQUIRES, and making an implementation match what the spec already requires is conformance — plus an enumerated list of five decision classes a session MUST take itself with a recorded rationale: conformance fixes to unratified behavior, priority edits, plan-child re-parenting, error semantics inside an existing ratified rule, and cost estimates.

### Motivation

The design-human-gated set in `## Dispatcher policy settings constraints` ("Still escalate the unresolvable") enumerates what MUST escalate and names nothing that must not. A rule that only ever says "escalate" is over-applied, because a session facing an unlisted decision reads the absence as doubt and escalates anyway; the cost is a parked item and a maintainer interrupt for work the session was always allowed to do. Measured on 2026-08-20 in the stalled livespec-dev-tooling fleet: removing an unratified filter from inside a check — no ratified clause required that filter, so deleting it made the implementation match the spec — was escalated three times as a ratification decision (livespec-dev-tooling-8zv3.5). That is conformance, not a spec change, and nothing in the specification said so. The same investigation found sessions treating plan-child re-parenting as a maintainer call, which deadlocks the plan archive gate for any epic with scope creep. The floor needs a positive complement stated as normative text, not as tribal knowledge.

### Proposed Changes

In `SPECIFICATION/constraints.md`, add a new section `## Not-human-gated decision constraints`, placed immediately after `## Dispatcher policy settings constraints` so the complement sits beside the floor it complements.

The section MUST open by naming what it complements: the design-human-gated set of `## Dispatcher policy settings constraints` ("Still escalate the unresolvable") enumerates decisions that MUST escalate and names none that must not, and this section supplies that complement.

The section MUST state the governing test: a decision is design-human-gated ONLY when it changes what the specification REQUIRES. Making an implementation match what the specification ALREADY requires is conformance, and conformance is never a spec-change decision. A session MUST apply this test before escalating, and MUST NOT escalate on the sole ground that a decision class is not enumerated here — absence from the list is not evidence that a decision is gated.

The section MUST then enumerate the following decision classes. Each MUST be taken by the session that encounters it, with its rationale recorded durably, and MUST NOT be escalated as a spec-change, regroom, or acceptance decision:

- **Conformance fixes to unratified behavior** — removing, correcting, or narrowing implementation behavior that NO ratified clause requires, so that the implementation matches the ratified specification. Deleting an unratified filter inside a check is conformance; it is not ratification.
- **Priority edits** — changing a work-item's priority or rank.
- **Plan-child re-parenting** — moving a plan child to a different parent.
- **Error semantics inside an existing ratified rule** — choosing the exception type, exit code, or message for a failure an already-ratified rule mandates, where that rule does not itself fix them.
- **Cost estimates** — producing or revising an estimate of the token, wall-clock, or currency cost of a candidate action.

The section MUST close with the precedence rule: a decision that is on this list AND independently changes what the specification requires REMAINS design-human-gated. The list admits a decision CLASS; it MUST NOT be read as overriding the governing test for a particular decision.

The section MUST carry a `**Verification.**` paragraph, matching the file preamble's requirement that each constraint name what decides it: the rule is decided by the Gherkin scenario proposed for `scenarios.md` below, exercised through `just check`; an individual session's application of it is decided at review time by comparing the session's recorded rationale for taking or escalating a decision against the governing test stated above.

## Proposal: A scenario exercises the not-human-gated set alongside the escalation floor

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

Add a `## Scenario 56` Feature to scenarios.md covering the positive complement: a conformance fix to unratified behavior is taken by the session without a human valve, an unlisted decision is resolved by the governing test rather than escalated for being unlisted, and a listed decision that also changes what the spec requires still escalates.

### Motivation

Behavior stated only as constraint prose is not load-bearing in this project: the authoring discipline requires an observable rule to have both a BCP14 clause and a Gherkin scenario, and the existing escalation floor already carries one (`## Scenario 36 — Every needs-human block always escalates`). Its complement MUST be exercised the same way, or the enumerated not-human-gated set would rest on prose alone while the set it complements is scenario-backed — exactly the asymmetry that let the floor be over-applied in the first place. The scenario also pins the two edges that make the rule safe to apply autonomously: absence from the list does not imply escalation, and presence on the list does not override the governing test.

### Proposed Changes

In `SPECIFICATION/scenarios.md`, add a new section `## Scenario 56 — A not-human-gated decision is taken by the session, never escalated`, after the last existing scenario, carrying a fenced `gherkin` block.

The Feature MUST be stated as the complement of `## Scenario 36`: no session escalates a decision the design leaves to it.

The block MUST carry at least these three scenarios:

- A conformance fix to unratified behavior is taken without a human valve. GIVEN implementation behavior that no ratified clause requires, and a change that removes it so the implementation matches the ratified specification, WHEN a session evaluates the change, THEN it takes the change itself, AND it records the rationale naming the change as conformance, AND it does not route the change to `/livespec:propose-change` and does not escalate it as a spec-change decision.
- An unlisted decision is resolved by the governing test, not by its absence from the list. GIVEN a decision whose class is not enumerated in the not-human-gated set, WHEN a session evaluates it, THEN it applies the governing test — whether the decision changes what the specification requires — AND it MUST NOT escalate on the sole ground that the class is unlisted.
- A listed decision that also changes what the specification requires still escalates. GIVEN a decision on the not-human-gated list that would ALSO change what a ratified clause requires, WHEN a session evaluates it, THEN it escalates on the design-human-gated path, AND the escalation is queryable from the journal, because the list admits a decision class and MUST NOT override the governing test.

The accompanying `tests/heading-coverage.json` entries for both this new scenario heading and the new `constraints.md` heading MUST be added atomically with the revision that lands them, per the project's revise co-edit discipline.
