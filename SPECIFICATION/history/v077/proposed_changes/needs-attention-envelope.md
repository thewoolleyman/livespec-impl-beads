---
topic: needs-attention-envelope
author: claude-fable-5
created_at: 2026-08-25T11:51:40Z
---

## Proposal: Ratify the needs-attention machine envelope: per-item stability, loud validation, executable handoffs, recorded ownership cut

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Ratifies the `needs-attention --json` MACHINE ENVELOPE in this producing repository — today the contract names "the machine envelope" and ratifies operator semantics (composes-and-emits, executes nothing, creates no work-items) but NO JSON schema: the shape exists only as the vendored `livespec_runtime` implementation, and three consuming repositories build against a consumer-documented shape, inverting schema ownership. The ratification covers: the envelope object (`{"attention": [...]}`, deterministic serialization); the six per-item fields (`id`, `kind`, `urgency`, `summary`, `source_ref{repo, work_item?, path?}`, `handoff{kind, command, action_id?}`); PER-ITEM field stability with a DECIDED consumer-tolerance posture (consumers skip-and-surface a malformed or unknown-kind ITEM, never discard the envelope — an all-or-nothing parse that a single bad item blinds is forbidden); the producer-side dual (a composition-time validation failure MUST surface loudly, never silently shorten the list — absence must not be manufacturable by validation failure); additive-only wire evolution; the executable-as-advertised obligation with a mechanical advertiser/enforcer binding and negative control (the `bd-ib-dohu2g` lesson); and the recorded shared-runtime ownership cut (the runtime owns item types, kind vocabulary, stable-ID grammar, validator, and any pure normalizer; this repository owns fact derivations, persistence, thresholds, the CLI envelope, and handoff commands). The accepting revise is explicitly GATED on livespec-runtime's attention-surface baseline ratification. Adds Scenarios 79-80.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the Phase 2 charge of homelab's `steady-state-loop-hardening` program: the envelope-ratification EARLY DELIVERABLE bound by that program's research/007 (finding fable 6), refined by the console review (research/009, c-fable 5: per-item field stability and a decided tolerance posture) and the runtime reviews (research/010: the R4 baseline-first sequencing and the rt-sol-2 ownership test). Verified against this repository's primary sources on 2026-08-25.

THE VERIFIED GAP. `contracts.md` §"`needs-attention`" ratifies the CLI surface and the operator semantics and NAMES "the machine envelope" — but no field, no kind, no grammar, no stability guarantee appears anywhere in `SPECIFICATION/` (grep for `source_ref` / `attention[]` returns nothing). The shape ships as implementation: `commands/needs_attention.py` emits `{"attention": [asdict(item)...]}` with sorted keys over the vendored `livespec_runtime.attention_item.AttentionItem` (fields `id`, `kind`, `urgency`, `summary`, `source_ref`, `handoff`; `AttentionKind` a closed 7-value Literal; `HandoffKind` `drive`/`livespec-op`/`plan`/`shell`; a stable-ID grammar in `validate_attention_item_id`). The console's spec documents its CONSUMPTION of this shape — a consumer-documented contract for a producer-owned surface, which is the inversion finding fable 6 names.

THE OWNERSHIP CUT, RECORDED (the rt-sol-2 routing test, ruled into the program by the maintainer's shared-runtime directive). `livespec-runtime` owns what is pure, consumer-neutral, and needed identically by at least two producers: the item TYPES, the `kind` vocabulary, the stable-ID grammar, the validator, and any pure normalizer over injected facts. THIS repository owns everything that knows what the facts MEAN or where they come from: the fact derivations (capacity, aging, waits, staleness), persistence, thresholds, the `--json` CLI envelope, and the handoff commands. Consumer vocabulary (beads/Dolt, dispatcher, journal, foreman, homelab) is banned from runtime contracts; duplicated thin adapters are acceptable; DRY never justifies reversing the dependency direction. New fact classes PREFER existing broad kinds with additive stable-ID forms over new kinds; ANY change to the runtime-owned pieces ratifies in `livespec-runtime` FIRST and reaches this repository as a ratified release consumed by vendor-pin bump.

THE SEQUENCING GATE (research/010 R4, restated as a binding condition on the accepting revise). The runtime baseline that declares the current attention surface is being ratified in `livespec-runtime` under the parallel plan thread `homelab-loop-hardening-runtime` (epic `livespec-runtime/livespec-runtime-mqsxsu`; baseline propose-change PR thewoolleyman/livespec-runtime#606). "Ratified there" means an ACCEPTED REVISE with a new history snapshot in that repository — not the proposal's merge. The accepting revise of THIS proposal MUST NOT run before that baseline snapshot exists, and MUST re-verify every type/kind/grammar citation in this proposal against the ratified baseline text, correcting this proposal's citations where the baseline ratified something different from today's vendored v0.21.1 surface.

THE TOLERANCE POSTURE IS A DECISION, NOT AN INHERITANCE (c-fable 5). The console's current all-or-nothing parse means one malformed item blinds the whole inbox — including any staleness backstop riding it. The posture ratified here is per-item: field stability is guaranteed PER ITEM, consumers skip-and-surface what they cannot parse, and the envelope survives. The producer-side dual is the rt-fable 3 lesson one layer down: the composer MUST NOT silently drop an invalid candidate — a validation failure at composition time surfaces loudly (the negative control: one invalid plus one valid candidate yields a visible failure plus the valid item, never a silently shorter list). Absence of an attention item must never be manufacturable by a validation failure, because absence reads as resolution to every downstream consumer.

EXECUTABLE AS ADVERTISED (the `bd-ib-dohu2g` lesson, carried with its negative control). That live epic records `needs-attention` advertising `valve:approve:<id>` handoffs that `drive` refuses BY CONSTRUCTION (the advertiser branches on stored status; the enforcer honors `effective_admission_policy`) — and records that four careful human sweeps missed it, so the binding must be mechanical. This proposal ratifies the obligation and the control; the mechanical binding's implementation is that epic's deliverable, not re-scoped here.

### Proposed Changes

Changes land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`; BCP14 throughout. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the two new `## Scenario` H2 headings, and MUST honor the sequencing gate stated in the Motivation (no ratification before the livespec-runtime baseline snapshot exists; re-verify citations against it).

#### 1. `contracts.md` — new subsection `### The needs-attention machine envelope`, placed under §"`needs-attention`"

Full text:

> ### The needs-attention machine envelope
>
> `needs-attention --json` MUST emit a single JSON object `{"attention": [<item>...]}` with deterministic serialization (stable key ordering). Each item carries exactly these fields, whose TYPES, `kind` vocabulary, and stable-`id` grammar are owned by the `livespec-runtime` attention-surface baseline and consumed here by vendored release — this section ratifies the WIRE ENVELOPE and its guarantees, never a fork of the runtime-owned definitions:
>
> - `id` — the stable natural key (runtime-owned grammar). Stable across compositions for the same underlying fact; a consumer MAY diff snapshots by `id`.
> - `kind` — the routing category (runtime-owned vocabulary). Consumers MUST treat `kind` as an open string set on the wire: an unknown `kind` is a well-formed item.
> - `urgency` — `high` | `medium` | `low`.
> - `summary` — one-line human-readable statement of the fact.
> - `source_ref` — `{repo, work_item?, path?}`: where the fact came from; `repo` always present.
> - `handoff` — `{kind, command, action_id?}`: the action payload a caller can render without backend knowledge.
>
> **Per-item field stability and the consumer-tolerance posture.** The field guarantees above hold PER ITEM. A consumer MUST be able to skip an item it cannot parse — malformed fields, or an unknown `kind` it chooses not to render — while consuming the rest of the envelope, surfacing what it skipped; a consumer whose parse discards the WHOLE envelope on one bad item is non-conforming (one malformed item blinding the entire inbox is the failure mode this posture exists to forbid). This posture binds this repository's own consuming surfaces and is the producer-declared contract downstream consumers pin.
>
> **Producer-side validation is loud.** The producer MUST NOT emit an item that fails the runtime validator, and MUST NOT silently omit a candidate that failed validation: a composition-time validation failure MUST surface as a visible failure alongside the valid items. Absence of an attention item MUST NOT be manufacturable by a validation failure — absence reads as resolution downstream.
>
> **Wire evolution is additive.** New item fields and new `kind` values MAY appear in a release (consumers tolerate both per the posture above). An existing field's removal, rename, or change of type or meaning is a breaking change that MUST ride a propose-change here plus a coordinated, ratified change to the runtime-owned definitions in `livespec-runtime` FIRST, released and consumed by pin bump — never a plugin-local fork of the shared shape.
>
> **Executable as advertised.** Every emitted `handoff` MUST be executable as advertised at composition time: a `drive`-kind handoff's `action_id` MUST be one `drive` would accept for the item's state, and equivalent fidelity holds for the other handoff kinds. The advertiser and the enforcer MUST be bound mechanically (a test that renders advertised handoffs and proves the enforcer accepts them, with the NEGATIVE control: a state the enforcer refuses is never advertised). Design record: `bd-ib-dohu2g`, whose defect — advertising an `approve` valve the enforcer refuses by construction — survived four careful human sweeps precisely because no mechanical binding existed.
>
> **Ownership cut (recorded).** `livespec-runtime` owns the attention item types, `kind` vocabulary, stable-ID grammar, validator, and any pure normalizer over injected facts. THIS repository owns the fact derivations, their persistence and thresholds, this envelope, and the handoff commands. New fact classes PREFER existing broad kinds with additive stable-ID forms; a new kind, grammar form, or field ratifies in `livespec-runtime` first.

#### 2. `scenarios.md` — two new scenarios

```gherkin
## Scenario 79 — One malformed item never blinds the inbox, and never vanishes silently

Feature: Per-item tolerance on the consumer side, loud validation on the producer side
  As an operator relying on the attention surface
  I want a bad item skipped-and-surfaced by consumers and surfaced loudly by the producer
  So that neither a blinded inbox nor a silently shorter list can read as all-clear

Scenario: A consumer skips and surfaces a malformed item
  Given an envelope holding one malformed item and several well-formed items
  When a conforming consumer parses it
  Then the well-formed items are consumed
  And the malformed item is surfaced as skipped, not silently dropped
  And the envelope is not discarded

Scenario: An unknown kind is a well-formed item
  Given an envelope holding an item whose kind the consumer does not recognize
  When the consumer parses it
  Then the item is treated as well-formed and surfaced generically

Scenario: The producer surfaces a validation failure instead of omitting the candidate
  Given composition inputs holding one candidate that fails the runtime validator and one valid candidate
  When needs-attention composes the envelope
  Then the valid item is emitted
  And the validation failure is surfaced as a visible failure
  And the invalid candidate is not silently absent

## Scenario 80 — Every advertised handoff is executable as advertised

Feature: The advertiser and the enforcer are mechanically bound
  As an operator pasting a handoff command
  I want every advertised action to be one the enforcer accepts
  So that the attention surface never routes me into a refusal by construction

Scenario: An advertised drive handoff is accepted by drive
  Given an attention item carrying a drive-kind handoff for an item state
  When the advertised action id is submitted to drive for that item
  Then drive accepts it

Scenario: A state drive refuses is never advertised
  Given an item state for which drive refuses an action by construction
  When needs-attention composes the envelope
  Then no handoff advertising that action for that item is emitted
```
