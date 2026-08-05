---
topic: drift-acceptance-consensus-carveout
author: claude-opus-5
created_at: 2026-08-04T13:57:44Z
---

## Proposal: Sweep every drift-is-human-only statement so the carve-out lands consistent

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Amend every statement in this repo's spec tree that reserves drift acceptance unconditionally to a human: the contracts.md floor enumeration, the spec.md Terminology DESIGN-bounded bullet and its three wrapper statements, the constraints.md 'Still escalate the unresolvable' bullet, and the scenarios.md design-human-gated scenario.

### Motivation

Third draft. Round-2 adversarial review found two defects in the second, both re-verified before this draft.

(1) The scenarios.md replace-target was UNIQUE but WRONGLY BOUNDED: it stopped one line short of the live scenario's final step, so the mandated pure byte substitution produced that step TWICE in a row. Confirmed by simulating the substitution. Uniqueness is not correctness — a target can occur exactly once and still under-quote. The target is now extended to the scenario's true end, and the payload builder asserts the following live line is not another Gherkin step.

(2) Three wrapper statements in spec.md still asserted the unconditional human gate over a set that retains drift acceptance. The sharpest is 'no dispatcher policy setting may auto-dispose them; they MUST stay escalated as needs-attention', which flatly contradicts the amended contracts.md sentence. All three are swept here, each preserving the Dispatcher-side behavior that genuinely does not change: the Dispatcher still never accepts drift and still routes it to the Spec-Plane revise path. What moves is the ACCEPTANCE authority on that path, which the Spec Plane owns.

### Proposed Changes

Seven exact replacements. Every target below is quoted verbatim from the live file, occurs exactly once, and was checked to end at a real construct boundary. This tree is HARD-WRAPPED: internal newlines and em-dashes are part of each match. The accepting revise MUST apply pure byte substitution and MUST NOT re-wrap surrounding prose.

1. `SPECIFICATION/contracts.md` §"Every needs-human escalation still reaches a human":

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

   Every other sentence in that section MUST remain byte-identical: the truly-unresolvable auto-dispose ban, the `blocked_reason: needs-human` auto-resolve ban, the 'no release with zero verification' floor, and the ban on the Dispatcher creating net-new work-items.

2. `SPECIFICATION/spec.md` §"Terminology" — the DESIGN-bounded bullet, with its cross-repo citation re-anchored to the amended doctrine rather than to a byte-quote that the paired amendment removes:

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

3. `SPECIFICATION/spec.md` — wrapper statement 1:

OLD:

Truly-unresolvable decisions are the
residual escalation class the Dispatcher always surfaces to a human,
regardless of the policy settings in force.

NEW:

Truly-unresolvable decisions are the
residual escalation class the Dispatcher always surfaces to a human,
regardless of the policy settings in force — except a drift acceptance in a
repo that has explicitly opted in to the consensus tier via livespec core's
`spec_governance.drift_acceptance_mode`, which the Dispatcher still never
accepts and still routes to the Spec-Plane revise path.

4. `SPECIFICATION/spec.md` — wrapper statement 2. As written it flatly contradicts the amended contracts.md:

OLD:

All three are truly-unresolvable BY DESIGN,
not by low confidence: no dispatcher policy setting may auto-dispose them;
they MUST stay escalated as needs-attention.

NEW:

All three are truly-unresolvable BY DESIGN,
not by low confidence: no dispatcher policy setting may auto-dispose them;
they MUST stay escalated as needs-attention. Drift acceptance is escalated on
the same terms, and its ACCEPTANCE authority — human by default, the consensus
tier only under an explicit per-repo `spec_governance.drift_acceptance_mode`
opt-in — is owned by the Spec Plane, never by a dispatcher policy setting.

5. `SPECIFICATION/spec.md` — wrapper statement 3:

OLD:

every
truly-unresolvable decision (see §"Terminology") still escalates and is
surfaced to a human, never guessed

NEW:

every
truly-unresolvable decision (see §"Terminology") still escalates and is
surfaced to a human, never guessed (a drift acceptance still escalates and is
still never guessed; under an explicit per-repo opt-in its acceptance MAY be
owned by the consensus tier on the Spec-Plane revise path)

6. `SPECIFICATION/constraints.md`:

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

7. `SPECIFICATION/scenarios.md` — split the drift leg into its own scenario. The OLD block spans the WHOLE live scenario through its final `And the escalation is queryable from the journal` step; quoting one line less duplicates that step:

OLD:

Scenario: A design-human-gated decision escalates by design even at high confidence
  Given a design-human-gated decision — a drift acceptance, a spec-change slice, a regroom/backlog bounce, or a human-only acceptance — that the LLM could resolve with high confidence
  When the Dispatcher evaluates it
  Then it does not auto-dispose the decision, because the design reserves it to a human
  And the decision is left on its human path — a spec-change to `/livespec:propose-change`, a drift acceptance to the Spec-Plane revise path, a bounce resting in backlog — and surfaced to a human
  And the escalation is queryable from the journal

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

   This adds a `Scenario:` inside the existing fenced block and adds NO `## ` heading, so no heading-coverage co-edit is owed.

RATIFICATION ORDER: every `spec_governance.drift_acceptance_mode` reference here is true only once the paired core amendment ratifies (repo `thewoolleyman/livespec`, work item livespec-jvdvx4.5). Accept the core half FIRST or in the same sitting; if the core half is rejected, this proposal MUST NOT ratify.
