---
topic: needs-attention-completeness
author: claude-fable-5
created_at: 2026-08-25T13:48:33Z
---

## Proposal: Compose the orchestrator-owned attention facts: capacity, ready-aging, and wait completeness

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Completes the needs-attention snapshot's composition of ORCHESTRATOR-OWNED operational facts — matrix sections 03, 10, and 11 of homelab's steady-state-loop-hardening program, filed now that the livespec-runtime attention-surface baseline (v012) and this repository's machine envelope (v077) are both ratified. Three fact families: CAPACITY (a single-authority rule making the admission accounting's verdict the only source any surface may report capacity from, plus a NARROW attention item for the actionable residue — a reached cap held by a claim no live run backs); READY-WORK AGING (an attention fact when admission-eligible `ready` items exceed the new API-configurable `dispatcher.ready_aging_threshold_hours`, default 24, with nothing in flight, carrying the ages and an unblock handoff); and WAIT COMPLETENESS (an ENUMERATED set of orchestrator-created wait states, each with its unblock handoff, plus a forward-registration rule binding future parking contracts). Every new fact rides the RATIFIED runtime ID grammar's three-part `hygiene:<type>:<resource>` form under the existing `hygiene` kind as FLAT ITEMS — no structured payload, no runtime kind, grammar, or field change, per the v077 ownership cut. The snapshot composes ONLY orchestrator-owned waits: foreman and overseer wait states publish as ledger state on their owning plan epics and reach the operator through the already-composed plan and blocked classes — the orchestrator stays overseer-unaware (homelab research/009 R1). Adds Scenarios 83-85.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the final deliverable of the Phase 2 charge: the needs-attention completeness fact package deliberately deferred (research/002-phase-2-filings-and-decisions.md) until the livespec-runtime attention-surface baseline existed. That gate is satisfied — livespec-runtime v012 is ratified (master 970eea1) and this repository's machine envelope ratified against it as v077 — and the fact-class decision the deferral existed to make correctly is now made against ratified text: all three families fit the RATIFIED grammar's `hygiene:<type>:<resource>` three-part form under the existing `hygiene` kind, so no runtime kind, grammar, or field changes — exactly the outcome the v077 ownership cut prefers ("new fact classes PREFER existing broad kinds with additive stable-ID forms").

THE THREE INCIDENT FACTS THESE CLOSE (homelab research/001-002, corrected by research/007-009). Section 03: three separate surfaces asserted a capacity slot was taken for 26+ hours while the admission accounting's own verdict — which correctly excluded the stale claim — sat unread inside the admission path; every observer re-derived capacity from raw statuses and got it wrong together. Section 10: four items sat `ready` for 26+ hours with no factory run in flight and no surface said so. Section 11: the waiting-on-a-person states lived in four places with no composed view. The composition classes for waits largely EXIST already (a parked acceptance composes today; `blocked`/`needs-human` and `pending-approval` compose today); what this proposal adds is the completeness obligation over an ENUMERATED wait set with a forward-registration rule, the capacity single-authority rule and its residual fact, and the aging fact.

WHY THE CAPACITY REMEDY IS TWO THINGS, NOT ONE. The section 03 incident is a re-derivation failure: the accounting was right and the observers were wrong. The remedy for that is a NORMATIVE single-authority rule, not an attention row — an attention item additionally requires an operator action, and "slots are free" offers none. An unconditional capacity row would also make the renderer's "No attention items." branch unreachable, turning an attention list into a dashboard. So the single-authority rule binds every reporting surface unconditionally, while the attention ITEM is narrowed to the residue an operator can actually act on. That narrowing also keeps every handoff clear of the `bd-ib-dohu2g` shape v077 forbids: no capacity handoff routes through the cap-enforcing path that would refuse at a full cap.

WHY THE FACTS ARE FLAT ITEMS AND NEVER A PAYLOAD. The v077 envelope permits an item exactly `id`, `kind`, `urgency`, a one-line `summary`, `source_ref`, and ONE `handoff`; the ratified runtime v012 `HygieneScanFinding` is equally flat. A promise to carry "every holder with its reason as data" therefore had only three realizations — prose hidden inside `summary`, an invented `summary` parser, or an unratified runtime field contradicting this proposal's own "no runtime field is changed". This proposal takes none of them: per-hold detail rides as its OWN item with its own stable id and handoff, and machines diff by id, which the envelope already guarantees.

COMPOSITION WITH THE RATIFIED SIBLINGS. The capacity facts read the v071 claim-accounting classes through a side-effect-free projection, never re-derived from raw statuses. The parked-acceptance wait is the v072 NEEDS_ATTENTION disposition's attention leg, composed through the EXISTING classes exactly as v072 requires — this proposal introduces no new attention kind. Handoffs obey the v077 executable-as-advertised obligation. The aging threshold key follows the per-key declaration discipline: `dispatcher.ready_aging_threshold_hours` is declared API-configurable (an operator attention dial), deliberately triggering the console Settings lockstep whose consumer legs belong to the console charge — the same posture as `drift_capture_merge_threshold` (v078).

ORDERING DEPENDENCIES THIS PROPOSAL DECLARES RATHER THAN ASSUMES. Three clauses below name work that must land before the clause can be implemented: a side-effect-free accounting projection, the v071 rework-class materialization (`bd-ib-mrsply`), and a durable ready-dwell instant. Each is stated in the normative text as a prerequisite so that no implementation can satisfy the clause by re-deriving what it cannot yet read.

### Proposed Changes

Changes land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`; BCP14 throughout. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the three new `## Scenario` H2 headings.

#### 1. `contracts.md` — new subsection `### Orchestrator-owned attention facts`, placed after §"The needs-attention machine envelope"

Full text:

> ### Orchestrator-owned attention facts
>
> The snapshot MUST compose every operational fact family below. Each fact rides the ratified runtime ID grammar's three-part `hygiene:<type>:<resource>` form under the existing `hygiene` kind, as a FLAT item conforming to §"The needs-attention machine envelope" — no runtime kind, grammar, or field is changed by this section, and a dedicated fact kind, if ever wanted, ratifies in `livespec-runtime` first (§"The needs-attention machine envelope" → ownership cut). No fact in this section carries a structured payload: where per-subject detail is required, it composes as its OWN item with its own stable `id`, `summary`, and `handoff`, and a consumer diffs by `id`.
>
> - **Capacity single authority (normative, unconditional).** The admission accounting's verdict is the SINGLE authority on this repository's capacity. Every surface that reports capacity — status, doctor, attention, or a refusal message — MUST read that verdict and MUST NOT re-derive capacity from raw work-item statuses. The verdict MUST be read through a SIDE-EFFECT-FREE projection: the thin-transport surfaces are query-only by contract, and the shipped accounting entry point appends a `dispatch-claim-abandoned` journal record on every call, so composing from it would put audit records in the published journal behind which no dispatcher decision stands (§"Control surface and audit"). Such a projection is a PREREQUISITE for the attention fact below; until it exists the fact MUST NOT be composed from a mutating path. What counts is COUNTED CLAIMS, not rows at status `active` (§"Per-repo WIP cap"). A surface reporting the count MUST identify the value as the cap that §"Per-repo WIP cap" defines, MUST state that host-run concurrency is governed separately (§"Host concurrency belongs to the Fabro scheduler") and is not what it reports, and MUST scope the count to the cap-enforcing admission paths — a hand-picked `dispatch --item` bypasses the cap and is not counted against it.
> - **Capacity residue fact (`hygiene:capacity:<repo>`, plus `hygiene:capacity-hold:<work-item-id>` per actionable hold).** The snapshot MUST carry a capacity fact when, and only when, the cap is reached AND at least one counted hold is not backed by a live, watchable run. The aggregate item's `summary` MUST be a deterministic one-line statement of the counted holds and the free-slot count; each actionable hold composes as its own item naming the holder and WHY it counts, with an inspection handoff. Where every counted hold is backed by a live watchable run, capacity is legitimately busy and NO capacity item is emitted — an attention list is not a dashboard. This fact MUST NOT re-compose the lock-less stranded population, which §"Rework-pending re-dispatch" → "Stranded-state discrimination" already composes under its own kind and stable id with its own owner; one work-item MUST NOT produce two ids of two kinds for the same underlying fact. No capacity handoff MAY advertise a status-move action against a claim whose dispatch evidence shows a merged pull request — the ratified reconciliation route is `reconcile-merged`, and a move-to-`ready` handoff would re-queue merged work.
> - **The accounting's exposed classes, and the rework ordering dependency.** The accounting today exposes THREE hold-and-exclusion classes: a live dispatch lock, an unreadable dispatch journal, and a green-terminal exclusion. The `rework:pending` class ratified by §"Rework-pending re-dispatch" is not yet materialized. When it is, the ACCOUNTING MUST expose it and the snapshot MUST consume that verdict; the snapshot MUST NOT re-derive the rework class from the raw ledger label, which would breach the single authority above. A clause of this section that names an accounting class the accounting does not expose is unimplementable and MUST NOT be satisfied by re-derivation.
> - **Ready-work aging (`hygiene:ready-aging:<repo>`).** When at least one admission-eligible `ready` item has waited past the effective `dispatcher.ready_aging_threshold_hours` AND no dispatch for this repository is in flight, the snapshot MUST carry an aging fact naming the count of aged items, the oldest age, and an unblock handoff (the drain, or the owning plan's worker). The fact clears when a dispatch is in flight or no eligible item exceeds the threshold. THE CLOCK: the age is measured from the item's latest transition INTO `ready`, which MUST be read from a durable, clone-independent record. The machine-local dispatch journal MUST NOT be that source — it is absent on a fresh clone, and its absence is silent, so an aging fact that depended on it would vanish while items aged, the absence-reads-as-resolution direction §"The needs-attention machine envelope" forbids. A durable ready-dwell instant is a PREREQUISITE for this fact. AGE-UNKNOWABLE POSTURE: where the instant cannot be determined for an admission-eligible `ready` item, the snapshot MUST report that item as age-unknown and MUST NOT omit it. IN FLIGHT means a live dispatch lock or a watchable run for this repository — not a journal record, and not an ad-hoc process query.
> - **Wait completeness (enumerated, with forward registration).** Each orchestrator-created wait state below MUST compose, each with its unblock handoff: a capacity-deferred eligible item (waiting on a counted slot); a NEEDS_ATTENTION-parked acceptance (§"The NEEDS_ATTENTION verdict"); a `blocked`/`needs-human` item (`resolve-blocked`); a `pending-approval` item under an effective `manual` admission policy (`approve`); a factory-unsafe item surfaced for host routing, which stays `ready` and is not `blocked` (§"Dispatcher admission"); and an item held by an unexpired observed provider-exhaustion record, which likewise stays `ready` (§"Provider spend containment"). An enumerated wait absent from the snapshot is a composition defect, not a policy choice. FORWARD REGISTRATION: any future contract that leaves work parked on a person or a resource MUST register, in that contract, its attention derivation and its unblock handoff. This enumeration is deliberately closed rather than universal; a universal claim over an open population cannot be checked. EXPLICITLY NOT A WAIT: a non-convergence `backlog` bounce, which routes to re-decomposition (§"Grooming") rather than waiting on a person or a slot.
> - **Parked-acceptance arity and distinguishability.** A NEEDS_ATTENTION-parked acceptance composes as exactly ONE attention item, through the existing composition classes and introducing no new kind, per §"The NEEDS_ATTENTION verdict". Its single `handoff` carries the `accept:<work-item-id>` action; its `summary` MUST name both `reject:<work-item-id>:rework` and `reject:<work-item-id>:regroom` as the alternative dispositions, and MUST distinguish a NEEDS_ATTENTION park from a routine parking in `acceptance` by naming the verdict and the absent evidence leg(s).
> - **The ownership boundary.** The snapshot composes ONLY waits the orchestrator itself owns. Foreman and overseer wait states publish as ledger state on their owning plan epics and reach the operator through the snapshot's existing plan and blocked composition classes. The orchestrator MUST NOT read overseer or foreman surfaces, and MUST NOT emit an item whose derivation required one; whether such an item lands in a console inbox is the console's own contract to ratify, and this section creates no such route. A HOLDER is the work-item whose claim occupies a counted slot, identified by its own id — never by an actor identity read from another repository's surface. Rendering a foreman-attributed assignee or invoker read from THIS repository's own journal is INSIDE the boundary.
> - **`dispatcher.ready_aging_threshold_hours`** (sourced from this repo's `.livespec.jsonc`, positive integer, default **24**) — the aging trigger. Declared **API-configurable**: it appears in the console Settings surface per §"API-configurable completeness". No per-item override — aging is a repository property.
> - **The declared-API-configurable class.** A policy setting is API-configurable when, and only when, this specification DECLARES it so at the point it is defined. §"API-configurable completeness" and its console lockstep bind that declared set alone; a key that is neither declared API-configurable nor in the committed-only class is committed-only by default. This clause defines the class the lockstep already refers to.

#### 2. `scenarios.md` — three new scenarios

```gherkin
## Scenario 83 — Capacity truth is composed from the accounting, never re-derived

Feature: The admission accounting's verdict is readable attention data
  As an operator asking whether a slot is free
  I want the accounting's own verdict composed with each actionable hold explained
  So that three surfaces can never again re-derive capacity from raw statuses and agree on a wrong answer

Scenario: A reached cap with an unreadable-journal hold composes the residue fact
  Given a wip_cap of 2
  And one active item holding a live dispatch lock backed by a watchable run
  And one active item whose dispatch journal cannot be read
  And one active item whose journal shows a green terminal outcome after its last admit
  And one rework-pending parked item
  When needs-attention composes the snapshot
  Then the capacity fact reports 2 counted holds and 0 free slots
  And the unreadable-journal hold appears as its own item naming the holder and an inspection handoff
  And the live-lock item is not reported as a stale claim
  And the rework-pending item is not reported as abandoned
  And no capacity item advertises a status-move handoff for the green-terminal claim
  And composing the snapshot appends no record to the dispatch journal

Scenario: A busy cap backed entirely by live runs emits no capacity item
  Given a wip_cap of 2 and two active items each holding a live dispatch lock backed by a watchable run
  When needs-attention composes the snapshot
  Then no capacity item appears

## Scenario 84 — Aged ready work with nothing in flight surfaces an unblock

Feature: Ready-work aging composes when nothing is moving
  As a maintainer whose queue silently stalled for a day
  I want aged ready work surfaced with the unblock named
  So that a stalled repository says so instead of looking busy

Scenario: The aging fact appears past the threshold and clears in flight
  Given admission-eligible ready items whose latest transition into ready is older than the effective threshold
  And no live dispatch lock and no watchable run for this repository
  When needs-attention composes the snapshot
  Then an aging fact appears naming the aged count, the oldest age, and an unblock handoff
  And when a dispatch is in flight the fact does not appear

Scenario: An item whose ready instant is unknowable is reported, never omitted
  Given an admission-eligible ready item whose latest transition into ready cannot be determined
  When needs-attention composes the snapshot
  Then that item is reported as age-unknown
  And an item that only recently entered ready after a long time captured does not count as aged

## Scenario 85 — Every enumerated orchestrator-owned wait composes with its unblock

Feature: The enumerated wait set is complete and each wait is actionable
  As an operator scanning one list for everything that is stuck
  I want each orchestrator-created wait present with the action that clears it
  So that a wait cannot hide by living in a surface nobody reads

Scenario: All six enumerated waits compose, and a non-wait does not
  Given a capacity-deferred eligible item
  And a NEEDS_ATTENTION-parked acceptance
  And a blocked item whose blocked reason is needs-human
  And a pending-approval item under an effective manual admission policy
  And a factory-unsafe ready item awaiting host routing
  And a ready item held by an unexpired observed provider-exhaustion record
  And one healthy ready item admitted for dispatch
  When needs-attention composes the snapshot
  Then each of the six waits appears with an unblock handoff
  And the parked acceptance appears as exactly one item whose handoff carries the accept action
  And that item's summary names both reject dispositions
  And the healthy admitted item produces no wait item
```

#### 3. Revise-time co-edits

The accepting revise pass MUST add `tests/heading-coverage.json` entries for `## Scenario 83`, `## Scenario 84`, and `## Scenario 85`. Each entry is owned by `bd-ib-w3if5j` (the Phase 2 scenario-test binding item) at the INTEGRATION tier, with the same reason phrasing the v078 entry uses — the binding lands with that item's exercising tests, not with this revise.
