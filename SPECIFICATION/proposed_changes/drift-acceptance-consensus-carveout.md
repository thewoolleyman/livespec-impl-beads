---
topic: drift-acceptance-consensus-carveout
author: claude-opus-5
created_at: 2026-08-04T13:36:18Z
---

## Proposal: Sweep every drift-is-human-only statement so the carve-out lands consistent

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Widen this proposal from contracts.md alone to every statement in this repo's spec tree that reserves drift acceptance unconditionally to a human — the contracts.md floor enumeration, the spec.md Terminology DESIGN-bounded bullet (including its citation of livespec-core law), the constraints.md 'Still escalate the unresolvable' bullet, and the scenarios.md design-human-gated scenario.

### Motivation

The first draft of this proposal swept contracts.md only. Two independent adversarial reviews found that three further statements in this same repo would still assert an unconditional human drift gate after ratification, so the pair could not deliver cross-repo consistency even with both halves accepted. Each was re-verified against `origin/master` before this re-draft.

The spec.md bullet carries a second defect: it cites the exact livespec-core sentence that the paired proposal (repo `thewoolleyman/livespec`, work item livespec-jvdvx4.5) replaces, quoting 'the irreducible human touchpoint'. Left alone it would cite as normative law a sentence that no longer says that — a cross-repo citation rotting silently. The citation is re-anchored to the amended doctrine rather than to a quotation that will no longer exist.

### Proposed Changes

Four exact replacements. Every target below is quoted verbatim from the live file and occurs exactly once. This file is HARD-WRAPPED: the targets span lines and their internal newlines and em-dashes are part of the match. The accepting revise MUST apply pure byte substitution and MUST NOT re-wrap surrounding prose, because re-wrapping would alter bytes of sentences this proposal preserves.

1. `SPECIFICATION/contracts.md` §"Every needs-human escalation still reaches a human" — remove drift acceptance from the unconditional enumeration and give it its own conditional sentence:

OLD:

A decision that
is human-gated BY DESIGN — drift acceptance, a spec-change slice, a regroom /
backlog bounce, or a `human-only` acceptance — MUST stay escalated even when
the Dispatcher is fully confident.

NEW:

A decision that
is human-gated BY DESIGN — a spec-change slice, a regroom / backlog bounce, or
a `human-only` acceptance — MUST stay escalated even when the Dispatcher is
fully confident. Drift acceptance is human-gated by the same default and MUST
stay escalated unless the governed repo has opted in to the consensus tier
through livespec core's `spec_governance.drift_acceptance_mode`; under that
opt-in the consensus tier MAY own a drift acceptance, and only on unanimous
cross-vendor evidence that is present, fresh and conforming. No other setting,
and no `delegated` value, MAY accept drift, and the Dispatcher itself MUST NOT
accept a drift-origin proposal under any setting.

   Every other sentence in that section MUST remain byte-identical: the truly-unresolvable auto-dispose ban, the `blocked_reason: needs-human` auto-resolve ban, the 'no release with zero verification' floor requiring at least one AI pass per acceptance, and the ban on the Dispatcher creating net-new work-items.

2. `SPECIFICATION/spec.md` §"Terminology" — qualify the DESIGN-bounded drift bullet and re-anchor its cross-repo citation. The set remains THREE decisions; one of them becomes conditionally rather than unconditionally human, which the framing sentence MUST say:

OLD:

The second is DESIGN-bounded — three decisions that
stay human even when the Dispatcher is fully confident, because a human, not
the Dispatcher, owns them:

- **Drift acceptance** — the Dispatcher MAY file impl→spec drift (the machine
  path), but only a human accepts it. This is normative livespec-core law
  (`livespec/SPECIFICATION/spec.md` §"Contract + reference implementations
  architecture": "the irreducible human touchpoint that survives even a
  fully autonomous orchestrator").

NEW:

The second is DESIGN-bounded — three decisions that
stay human even when the Dispatcher is fully confident, because a human, not
the Dispatcher, owns them (drift acceptance conditionally so, per its bullet):

- **Drift acceptance** — the Dispatcher MAY file impl→spec drift (the machine
  path), and acceptance is human BY DEFAULT. Under an explicit per-repo opt-in
  via livespec core's `spec_governance.drift_acceptance_mode`, the unanimous
  cross-vendor consensus tier MAY own the acceptance instead; the Dispatcher
  MUST NOT accept it under any setting. This tracks normative livespec-core law
  (`livespec/SPECIFICATION/spec.md` §"Contract + reference implementations
  architecture", the drift-doctrine paragraph, as amended to admit the
  consensus tier).

3. `SPECIFICATION/constraints.md` — the 'Still escalate the unresolvable' bullet:

OLD:

- **Still escalate the unresolvable.** No policy setting MAY auto-dispose a
  truly-unresolvable decision — one the LLM cannot confidently resolve, or one
  human-gated by design: drift acceptance, a spec-change slice, a regroom /
  backlog bounce, or a `human-only` acceptance (`contracts.md` §"Dispatcher
  policy settings", `spec.md` §"Terminology"); every such decision MUST block
  and surface to a human.

NEW:

- **Still escalate the unresolvable.** No policy setting MAY auto-dispose a
  truly-unresolvable decision — one the LLM cannot confidently resolve, or one
  human-gated by design: a spec-change slice, a regroom / backlog bounce, or a
  `human-only` acceptance (`contracts.md` §"Dispatcher policy settings",
  `spec.md` §"Terminology"); every such decision MUST block and surface to a
  human. Drift acceptance MUST block and surface to a human by the same
  default, and MAY be owned by the unanimous cross-vendor consensus tier only
  under an explicit per-repo opt-in via livespec core's
  `spec_governance.drift_acceptance_mode`.

4. `SPECIFICATION/scenarios.md` — the design-human-gated scenario currently lists drift acceptance among decisions the design 'reserves to a human'. Split the drift leg into its own scenario so the remaining enumeration stays unconditionally true and the drift routing (which is unchanged Dispatcher-side) is stated accurately:

OLD:

Scenario: A design-human-gated decision escalates by design even at high confidence
  Given a design-human-gated decision — a drift acceptance, a spec-change slice, a regroom/backlog bounce, or a human-only acceptance — that the LLM could resolve with high confidence
  When the Dispatcher evaluates it
  Then it does not auto-dispose the decision, because the design reserves it to a human
  And the decision is left on its human path — a spec-change to `/livespec:propose-change`, a drift acceptance to the Spec-Plane revise path, a bounce resting in backlog — and surfaced to a human

NEW:

Scenario: A design-human-gated decision escalates by design even at high confidence
  Given a design-human-gated decision — a spec-change slice, a regroom/backlog bounce, or a human-only acceptance — that the LLM could resolve with high confidence
  When the Dispatcher evaluates it
  Then it does not auto-dispose the decision, because the design reserves it to a human
  And the decision is left on its human path — a spec-change to `/livespec:propose-change`, a bounce resting in backlog — and surfaced to a human
  And the escalation is queryable from the journal

Scenario: A drift acceptance is routed to the spec lifecycle, never auto-disposed
  Given a drift acceptance that the LLM could resolve with high confidence
  When the Dispatcher evaluates it
  Then it does not auto-dispose the decision
  And the decision is left on the Spec-Plane revise path, where acceptance is human by default and MAY be owned by the consensus tier only under an explicit per-repo `spec_governance.drift_acceptance_mode` opt-in
  And the escalation is queryable from the journal

   This adds a `Scenario:` line inside an existing fenced gherkin block; it adds NO `## ` heading, so no heading-coverage co-edit is owed. Confirm that against this repo's own heading-coverage obligation before accepting.

This amendment and livespec core's `livespec-jvdvx4.5` MUST agree, and neither MUST ratify on the assumption that the other already did.
