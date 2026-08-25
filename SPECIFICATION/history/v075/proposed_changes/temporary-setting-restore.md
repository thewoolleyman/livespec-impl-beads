---
topic: temporary-setting-restore
author: claude-fable-5
created_at: 2026-08-25T11:47:57Z
---

## Proposal: A temporary setting posture must carry an owned ledger restore item; no generic schema is added

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Closes matrix section 13's failure class — a deliberately lowered dispatcher setting whose restore-it note lives in a JSONC comment that nothing reads — by the LEDGER route reviewer sol's finding 8 recommends when no general schema is justified: a deliberate temporary posture change to any committed dispatcher setting MUST be accompanied by an owned ledger work-item, filed through `capture-work-item` by the operator making the change, naming the setting, the restore target, a named owner, and the restore condition written as gradeable acceptance criteria (the effective-criteria primitive makes that gradeability checkable), with a dependency edge to whatever the restore waits on when that is ledger-tracked. Deliberately NOT added: a generic temporary-setting config schema, a restore-condition evaluation vocabulary, or any new dispatcher settings key — the ledger already owns "work that must happen later, conditioned and owned", a general condition DSL is unjustified by the one observed instance, and adding no key means the console Settings-surface lockstep is not triggered at all. Adds Scenario 78.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the Phase 2 charge of homelab's `steady-state-loop-hardening` program: the section-13 filing bound by that program's research/007 (finding sol 8 of this repository's commissioned adversarial reviews, homelab PR #1027).

THE FAILURE CLASS (matrix section 13, evidence accepted as reported and consistent with homelab's committed history). `dispatcher.wip_cap` was deliberately dropped to 1 on 2026-08-23 for a one-dispatch canary; the canary succeeded the same day; the only carrier of "restore it to 10 afterwards" was a comment inside `.livespec.jsonc` — a surface nothing reads — and nothing would ever surface "the trial ended, the throttle remains". homelab has since repaired its own instance; the ecosystem obligation is to keep the CLASS from recurring in any adopter.

WHY THE LEDGER ROUTE, NOT A GENERIC SETTING (the choice sol 8 requires the filing to make, made here explicitly). The matrix's own fix — owner and restore-condition as config fields, with `needs-attention` deciding when the condition "has passed" — fails two ways sol 8 names: a restore condition like "after the canary succeeds" has no type or evaluation vocabulary, so an orchestrator predicate over it either embeds repository-specific state interpretation upstream (violating the plan's dependency direction) or demands an explicit repository-neutral condition schema; and a new API-configurable key triggers the ratified console Settings-surface lockstep (§"API-configurable completeness"), whose console phase the plan omitted for this section. A general condition DSL is not justified by ONE observed instance — and this repository's ledger ALREADY owns exactly this shape: an owned piece of future work with a condition, an owner, and dependencies IS a work-item with acceptance criteria and edges. The sibling filing `proposed_changes/needs-attention-verdict.md` makes those criteria mechanically gradeable (the effective-criteria primitive and its walls), so the restore item is not prose-in-a-different-pocket: it is first-class, rankable, dispatchable work the existing surfaces already compose.

WHAT THIS DELIBERATELY AVOIDS. No new configuration key, no schema, no evaluator: the console lockstep is untouched (there is no key to expose), the shared runtime is untouched (no new attention fact class — an open restore work-item is ordinary ledger state the existing composition already reaches), and the dependency direction holds (the orchestrator interprets no adopter-specific state; the OPERATOR writes the condition as criteria when they make the change, which is where the knowledge lives). Mechanical enforcement of the pairing (a config-diff check that a settings change carries its restore item) is deliberately NOT part of this proposal: the obligation binds the operator and the review of the committed change, and this proposal records that scoping decision rather than leaving it open.

RUNTIME INDEPENDENCE. This is one of the plan's runtime-independent filings (research/010 R4): no attention kind, no runtime type, no console surface is touched.

### Proposed Changes

Changes land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`; BCP14 throughout. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the new `## Scenario 78` heading. RATIFICATION GATE: this proposal's §"Effective acceptance criteria" reference resolves only once the sibling `needs-attention-verdict` proposal is accepted — the accepting revise MUST ratify that sibling first (this thread's ratification order does so); were the sibling rejected, this proposal would need a `modify` decision replacing the reference before acceptance.

#### 1. `contracts.md` — new subsection `### Temporary setting postures carry an owned restore item`, placed in §"Dispatcher policy settings"

Full text:

> ### Temporary setting postures carry an owned restore item
>
> A deliberate TEMPORARY posture change to any committed dispatcher setting — lowering `wip_cap` for a canary, committing a step waiver intended to be short-lived, tightening a cap for an experiment — MUST be accompanied by an owned ledger work-item, filed through `capture-work-item` by the operator making the change (consent is native there; the Dispatcher itself files nothing, per §"Consent boundary"). The restore item MUST name:
>
> - the setting and the value to restore (the restore target),
> - a named owner, recorded queryably as an `owner:<name>` ledger label on the restore item (prose alone is not queryable),
> - the restore condition, written as gradeable acceptance criteria (§"Effective acceptance criteria" defines gradeability; see the ratification gate below) — the condition lives WITH the obligation, authored by the operator who knows it, never interpreted by the orchestrator,
> - a dependency edge to the ledger item the restore waits on, whenever that trigger is ledger-tracked.
>
> A configuration comment is NOT a carrier for a restore obligation: nothing reads comments, and this rule exists because a committed comment is where exactly this obligation went to die. The restore item is ordinary ledger work — ranked, listed, and composed by the existing status and attention surfaces; no new configuration schema, no restore-condition evaluation vocabulary, and no new dispatcher settings key is added by this contract, and none of the ratified settings gains a "temporary" variant. (Consequently the console Settings-surface lockstep of §"API-configurable completeness" is not triggered: there is no key to expose.)

#### 2. `scenarios.md` — new scenario

```gherkin
## Scenario 78 — A temporary throttle carries its own restore work-item

Feature: Temporary setting postures are owned ledger work, not comments
  As a maintainer lowering a setting for a bounded trial
  I want the restore obligation to be first-class tracked work with an owner and criteria
  So that the trial ending cannot leave the throttle in place silently

Scenario: The lowered cap is paired with an owned restore item
  Given an operator deliberately lowers a committed dispatcher setting for a bounded trial
  When the settings change is reviewed for merge
  Then an owned ledger work-item exists naming the setting and the restore target
  And the item carries an owner label naming the responsible party
  And its restore condition is written as gradeable acceptance criteria
  And it carries a dependency edge to the ledger-tracked trigger where one exists

Scenario: A comment-only restore note is the reviewable violation
  Given a committed settings change that lowers a setting with only a configuration comment as the restore carrier
  When the change is reviewed for merge
  Then the review names the missing restore work-item as a violation of this contract
  And no configuration schema offers a temporary variant or restore-condition field to reach for

(These are operator-process scenarios; per repo precedent their heading-coverage bindings MAY be TODO with a reason — no in-repo test can decide a review obligation mechanically.)
```
