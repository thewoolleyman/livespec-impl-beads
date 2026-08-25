---
topic: loop-probe
author: claude-fable-5
created_at: 2026-08-25T11:41:49Z
---

## Proposal: A loop probe that takes a pre-filed item, confines its blast surface, and scopes its residue assertions

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Adds a Dispatcher `probe` subcommand that demonstrates the steady-state loop live — one designated work-item driven ready -> admitted -> factory run -> merged PR -> acceptance -> `done`, with per-stage assertions — WITHOUT crossing the ratified consent boundary: the probe TAKES an already-filed `--item` created through `capture-work-item` (where consent is native) and MUST NOT create net-new work-items, resolving reviewer sol's Blocker by construction rather than by carve-out. The contract names the sanctioned probe target path (the probe's synthetic change MUST confine itself to a dedicated `.livespec-probe/` directory in the governed repository, and the probe FAILS if the merged diff escapes it), the cleanup obligation (the directory holds at most the latest probe artifact; a later probe replaces it, and removing it never breaks anything), and residue assertions scoped to the probe's OWN identifiers and before/after delta — global attention emptiness is FORBIDDEN as an assertion, unrelated pre-existing attention items MUST be preserved, and an unavailable attention source FAILS the probe rather than reading as clear. The probe asserts a NON-DEFAULT invoker attribution, a non-empty effective-criteria parse, clean journaled preflight/post-merge step outcomes, an evidence-grounded acceptance verdict, terminal `done`, and the scoped residue delta. Fixture-CREATING probes run only against the hermetic fake backend or a disposable tenant, never the live Dispatcher. Adds Scenarios 74-75.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the Phase 2 charge of homelab's `steady-state-loop-hardening` program: the section-12 filing bound by that program's research/007 (findings fable 7 — Major — and sol 3 — Blocker — of this repository's commissioned adversarial reviews, homelab PR #1027), carrying the console review's repaired completion semantics (research/009 R3, applied to `homelab/hl-mfz6ig`'s criteria the same day).

THE PROBLEM THE PROBE EXISTS FOR (matrix section 12). Steady-state loop ownership was declared from documents: no one had watched one work item travel the entire composed cycle under the machinery the documents named, and the only item that had tried was already stuck at acceptance when the claim was made. The probe is the standing demonstration primitive: one designated item, the REAL machinery (the published admission, dispatch, merge, and acceptance paths — never a parallel code path), assertions at every stage, and a scoped residue check at the end. Its consumers (the foreman treating a passing probe as the precondition for reporting the loop live; a console health view) file in their owning repositories and consume what is ratified here.

THE CONSENT BOUNDARY IS RESOLVED BY CONSTRUCTION, NOT BY CARVE-OUT. `contracts.md` §"Consent boundary" ("The Dispatcher MUST NOT create net-new work-items on its own initiative", restated in `constraints.md`) is preserved verbatim: the probe REFUSES to run without a designated `--item`, and the designated item is filed by the operator through `capture-work-item` — heavyweight authored intake with Definition-of-Ready evaluation and explicit consent, exactly as sol 3 recommends and fable 7's parenthetical ("or takes") prefers. No probe path files anything. A probe that needs to CREATE its fixture (defect-seeding negative controls included) runs only against the sanctioned hermetic fake backend or a disposable test tenant — never through the live Dispatcher.

THE BLAST SURFACE IS NAMED (fable 7's second requirement). The probe merges a synthetic change into the governed repository's default branch BY DESIGN — that is the only honest way to exercise merge-on-green and post-merge acceptance. The contract therefore names the sanctioned target path: the probe item's change MUST confine itself to the dedicated `.livespec-probe/` directory, the probe FAILS when the merged diff touches anything outside it, and the cleanup obligation is stated (at most the latest artifact is retained; artifacts are inert and removable at any time).

RESIDUE IS SCOPED TO THE PROBE'S OWN IDENTIFIERS (sol 3's under-scoping finding, and research/009 R3's repaired semantics). The matrix's "no unexplained attention items left behind" is unsatisfiable in a live repository, which legitimately holds unrelated human valves, blocked work, and aging ready work: a global-emptiness assertion can never distinguish probe residue from valid concurrent attention. The ratified assertions are therefore: a BEFORE and AFTER snapshot; the delta explained entirely by the probe item's own lifecycle; no remaining attention item referencing the probe's reserved identifiers; unrelated pre-existing items PRESERVED (their disappearance is a probe FAILURE, not a success); and an attention source that cannot be read FAILS the probe — unavailability never reads as emptiness or as resolution.

COMPOSITION WITH THE SIBLING FILINGS FROM THIS PLAN THREAD. The probe's stage assertions consume the surfaces the sibling proposals ratify — the invoker attribution input (`proposed_changes/journal-invoker-attribution.md`: the probe MUST run with an asserted, NON-fallback identity and FAILS if its journal records resolve `invoker_source: fallback`), the effective-criteria primitive and walls (`proposed_changes/needs-attention-verdict.md`: the designated item's criteria MUST parse non-empty, and the acceptance verdict MUST be evidence-grounded), and the executable rework contract (`proposed_changes/acceptance-rework-state-machine.md`: a probe FAIL leg that routes to rework leaves a marked, selectable item — never an invisible one). This proposal ratifies LAST in the thread's stated order: its invoker assertion consumes §"Journal invoker attribution" (`invoker_source`, the fallback marking) and its criteria assertion consumes §"Effective acceptance criteria" — the accepting revise MUST NOT ratify this proposal before both siblings are ratified, and were either rejected, the dependent assertion would need a `modify` decision before acceptance. The failure leg strands nothing silently: on any stage failure the probe reports the stage reached, the item's current lifecycle state, and the named remedy, and leaves the item disposable through the normal machinery — the item is ordinary ledger state, never a hidden fixture.

### Proposed Changes

All changes use BCP14 normative language and land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the two new `## Scenario` H2 headings.

#### 1. `contracts.md` — new subsection `### The loop probe (`probe --item`)`, placed after §"Per-repo WIP cap" among the Dispatcher's operational surfaces

Full text:

> ### The loop probe (`probe --item`)
>
> `probe --repo <path> --item <work-item-id> [--json]` demonstrates the steady-state loop by driving ONE designated, ALREADY-FILED work-item through the entire cycle — admission, factory run, merge, post-merge acceptance, terminal `done` — through the SAME published machinery every ordinary dispatch uses, never a parallel path, with assertions at each stage. The probe:
>
> - MUST refuse to run without `--item`, and MUST NOT create, file, or clone any work-item under any circumstances: the designated item is filed by the operator through `capture-work-item`, where consent and Definition-of-Ready evaluation are native. §"Consent boundary" applies to the probe unchanged and without exception.
> - MUST refuse a designated item whose EFFECTIVE `acceptance_policy` is not `ai-only`, naming the label to set at filing: under the default `ai-then-human` (and under `human-only`) a passing item PARKS in `acceptance` awaiting the human `accept` valve, so terminal `done` is machine-reachable only for an `ai-only` item. The operator grants that policy when filing the probe item — the probe itself sets nothing.
> - Each invocation CONSUMES its designated item (driven to terminal `done`); a standing health cadence therefore files a fresh probe item per run through `capture-work-item` — the per-run filing consent is intended, not incidental — and consumers report against the LATEST probe outcome.
> - MUST run with an asserted invoker identity and MUST FAIL when its own journaled records resolve to a fallback-derived identity — a probe is an operator act, and an unattributed probe proves nothing about attribution.
> - MUST assert, in stage order: the designated item's effective acceptance criteria parse non-empty BEFORE dispatch; every journaled preflight and post-merge step outcome in the probe cycle is a pass (any warn-and-proceed, skipped-step, or failed-step record FAILS the probe); the acceptance verdict is grounded in observed evidence; and the item reaches `done`.
> - **Reserved identifiers.** At start the probe MUST journal a probe run identifier of the form `probe:<work-item-id>:<utc-start-timestamp>`; the probe's reserved identifier set is that run identifier plus the designated item's id, and every hard residue assertion below keys on that set.
> - **Sanctioned target path.** The designated probe item's change MUST confine itself to the `.livespec-probe/` directory at the governed repository's root. Confinement is asserted BEFORE the merge: the driven cycle MUST verify the change's paths and FAIL WITHOUT MERGING when the change escapes the directory. The post-merge diff check remains as the backstop; if an escaping change nonetheless merged, the probe MUST FAIL naming the merged commit and the revert obligation (the operator reverts it — the probe mutates nothing beyond its cycle). Probe artifacts are inert: the artifact is a single file the next probe's change replaces, deleting the directory MUST never break the governed repository, and the operator MAY remove it at any time — removal after a pass is the sanctioned cleanup and no surface may complain about its absence. This is what makes the merge-by-design safe to aim at a real default branch.
> - **Residue assertions, scoped.** The probe MUST snapshot the attention surface and the ledger state BEFORE the cycle and again AFTER. HARD assertions key on the reserved identifier set only: the designated item reached `done`, and no attention item referencing the reserved identifiers remains. The unrelated before/after delta is REPORTED, never asserted: over a cycle spanning admission to acceptance, unrelated attention items legitimately appear and resolve through concurrent operator activity, and failing on their movement would be the mirror image of the global-emptiness assertion this contract forbids. The probe MUST NOT assert global attention emptiness, MUST NOT require any unrelated state to be absent, and MUST NOT require any unrelated state to be preserved — it reports the unrelated delta for the operator. An attention or ledger source that cannot be read at either snapshot FAILS the probe with a source-unavailable outcome: unavailability MUST NOT be read as emptiness, resolution, or success.
> - **Failure leg.** On any stage failure the probe MUST report the stage reached, the item's current lifecycle state, and the named remedy, and MUST leave the item in whatever state the ordinary machinery put it — visible and disposable through the normal valves and recovery surfaces, never auto-deleted, never auto-closed, never hidden.
> - **Fixture-creating probes.** Any probe variant that CREATES its fixture — including defect-seeding negative controls such as an empty-criteria item — MUST run only against the hermetic fake backend or a disposable test tenant, never through the live Dispatcher against a live tenant.
>
> The probe is a demonstration and health primitive: a passing probe is evidence the composed loop is live; consumers that report loop liveness SHOULD condition on a passing probe rather than on documents.

#### 2. `scenarios.md` — two new scenarios

```gherkin
## Scenario 74 — The probe demonstrates the loop on a taken item and leaves only explained state

Feature: The loop probe drives one pre-filed item through the whole cycle
  As a maintainer who must report the loop live
  I want a probe that demonstrates the composed cycle with scoped assertions
  So that steady-state ownership is demonstrated, never declared from documents

Scenario: A full probe cycle passes every stage assertion
  Given a work-item filed through capture-work-item with an ai-only acceptance policy, clear dependencies, a resolvable assignee, and a change confined to the .livespec-probe directory
  And a free WIP slot exists
  And the probe is invoked with --item and an asserted invoker identity
  When the probe drives the item through admission, the factory run, merge, and acceptance
  Then every stage assertion passes: non-empty effective criteria, clean journaled step outcomes, an evidence-grounded verdict, and terminal done
  And the probe's journal records carry a non-fallback invoker_source and the probe run identifier
  And no attention item referencing the reserved identifier set remains
  And the unrelated before/after delta is reported without being asserted
  And the operator may then remove the probe artifact without any surface complaining

Scenario: An escaping change fails the probe before the merge
  Given a probe item whose change touches a path outside .livespec-probe
  When the driven cycle verifies confinement before merging
  Then the cycle fails without merging, naming the escaping path

Scenario: A merged escape fails the probe and names the revert obligation
  Given an escaping change that nonetheless merged
  When the probe evaluates the merged diff backstop
  Then the probe fails naming the merged commit and the revert obligation

## Scenario 75 — The probe takes; it never files, and absence of evidence never passes it

Feature: The probe respects the consent boundary and fails closed
  As a maintainer relying on the consent discipline
  I want the probe unable to create work and unable to pass on unread state
  So that a health command can never become an unconsented intake path or a false green

Scenario: The probe refuses to run without a designated item
  Given a probe invocation without --item
  When the probe starts
  Then it refuses without creating any work-item

Scenario: The probe refuses an item it cannot drive to done
  Given a designated item whose effective acceptance policy is not ai-only
  When the probe starts
  Then it refuses naming the acceptance policy label to set at filing

Scenario: An unavailable attention source fails the probe
  Given a probe cycle whose attention source cannot be read at the after snapshot
  When the probe evaluates its residue assertions
  Then the probe fails with a source-unavailable outcome
  And nothing is reported cleared or resolved

Scenario: A defect-seeding probe fixture never touches the live Dispatcher
  Given a probe variant that creates an empty-criteria fixture item
  When it runs
  Then it runs against the hermetic fake backend or a disposable tenant only
```

#### 3. Revise-time co-edits

The accepting revise pass MUST add `tests/heading-coverage.json` entries for `## Scenario 74` and `## Scenario 75`. Consumer legs (the foreman conditioning loop-liveness reports on a passing probe; a console health view of the latest probe outcome) belong to their owning repositories' charges and are deliberately not specified here.
