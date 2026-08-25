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

Completes the needs-attention snapshot's composition of ORCHESTRATOR-OWNED operational facts — matrix sections 03, 10, and 11 of homelab's steady-state-loop-hardening program, filed now that the livespec-runtime attention-surface baseline (v012) and this repository's machine envelope (v077) are both ratified. Three fact families: CAPACITY (the admission accounting's verdict composed as data — free slots, each held slot with its holder and WHY it counts, each excluded stale claim and each rework-pending parked item as its own attention item — so capacity truth is read, never re-derived); READY-WORK AGING (an attention fact when ready items exceed the new API-configurable `dispatcher.ready_aging_threshold_hours`, default 24, with nothing in flight, carrying the ages and an unblock handoff); and WAIT COMPLETENESS (every wait state the orchestrator itself creates — capacity-deferred, NEEDS_ATTENTION-parked acceptance, `blocked`/`needs-human`, `pending-approval` — composes with its unblock handoff). Every new fact rides the RATIFIED runtime ID grammar's three-part `hygiene:<type>:<resource>` form with existing kinds — NO runtime change, per the v077 ownership cut; a dedicated fact kind, if ever wanted, ratifies in livespec-runtime first. The snapshot composes ONLY orchestrator-owned waits: foreman and overseer wait states publish as ledger state on their owning plan epics and reach the operator through the already-composed plan and blocked classes — the orchestrator stays overseer-unaware (homelab research/009 R1). Adds Scenarios 83-84.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the final deliverable of the Phase 2 charge: the needs-attention completeness fact package deliberately deferred (research/002-phase-2-filings-and-decisions.md) until the livespec-runtime attention-surface baseline existed. That gate is satisfied — livespec-runtime v012 is ratified (master 970eea1) and this repository's machine envelope ratified against it as v077 — and the fact-class decision the deferral existed to make correctly is now made against ratified text: all three families fit the RATIFIED grammar's `hygiene:<type>:<resource>` three-part form under the existing `hygiene` kind, so no runtime kind, grammar, or field changes — exactly the outcome the v077 ownership cut prefers ("new fact classes PREFER existing broad kinds with additive stable-ID forms").

THE THREE INCIDENT FACTS THESE CLOSE (homelab research/001-002, corrected by research/007-009). Section 03: three separate surfaces asserted a capacity slot was taken for 26+ hours while the admission accounting's own verdict — which correctly excluded the stale claim — sat unread inside the admission path; every observer re-derived capacity from raw statuses and got it wrong together. Section 10: four items sat `ready` for 26+ hours with no factory run in flight and no surface said so. Section 11: the waiting-on-a-person states lived in four places with no composed view. The composition classes for waits largely EXIST already (a parked acceptance composes today; `blocked`/`needs-human` and `pending-approval` compose today); what this proposal adds is the COMPLETENESS obligation (every orchestrator-owned wait, each with its unblock handoff), the capacity facts, and the aging fact.

THE R1 BOUNDARY, RESTATED AS NORMATIVE TEXT (homelab research/009 R1, the console reviews' shared top finding). The snapshot composes ONLY waits the orchestrator itself owns. Foreman and overseer wait states — an open picker, a raised escalation, a panel in progress — publish as LEDGER STATE on their owning plan epics, which the snapshot's existing plan and blocked classes already compose; the orchestrator remains overseer-unaware, and foreman-origin items reach a console inbox only via a fresh console-side ratification, never as a side effect of this contract.

COMPOSITION WITH THE RATIFIED SIBLINGS. The capacity facts read the v071 claim-accounting classes (live-lock holds, journal-unreadable holds, excluded stale claims, rework-pending parked items) — composed as DATA from the accounting's verdict, never re-derived from raw statuses. The parked-acceptance wait is the v072 NEEDS_ATTENTION disposition's attention leg. Handoffs obey the v077 executable-as-advertised obligation. The aging threshold key follows the per-key declaration discipline: `dispatcher.ready_aging_threshold_hours` is declared API-configurable (an operator attention dial), deliberately triggering the console Settings lockstep whose consumer legs belong to the console charge — the same posture as `drift_capture_merge_threshold` (v078).

### Proposed Changes

Changes land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`; BCP14 throughout. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the two new `## Scenario` H2 headings.

#### 1. `contracts.md` — new subsection `### Orchestrator-owned attention facts`, placed after §"The needs-attention machine envelope"

Full text:

> ### Orchestrator-owned attention facts
>
> The snapshot MUST compose every operational fact family below. Each fact rides the ratified runtime ID grammar's three-part `hygiene:<type>:<resource>` form under the existing `hygiene` kind — no runtime kind, grammar, or field is changed by this section, and a dedicated fact kind, if ever wanted, ratifies in `livespec-runtime` first (§"The needs-attention machine envelope" → ownership cut).
>
> - **Capacity facts (`hygiene:capacity:<repo>`, plus `hygiene:stale-claim:<work-item-id>` per exclusion and `hygiene:rework-pending:<work-item-id>` per parked rework item).** The admission accounting's VERDICT is composed as data: the free-slot count against `wip_cap`; each held slot with its holder and WHY it counts (a live dispatch lock, or an unreadable journal); each excluded stale claim as its own item with the release handoff; each rework-pending parked item (§"Rework-pending re-dispatch") with the re-dispatch handoff. Capacity truth is READ from the accounting, never re-derived from raw statuses — the accounting is the single authority and every surface that reports capacity MUST consume this composition or the accounting directly.
> - **Ready-work aging (`hygiene:ready-aging:<repo>`).** When at least one admission-eligible `ready` item has waited past the effective `dispatcher.ready_aging_threshold_hours` AND no dispatch for this repository is in flight, the snapshot MUST carry an aging fact naming the count of aged items, the oldest age, and an unblock handoff (the drain, or the owning plan's worker). The fact clears when a dispatch is in flight or no eligible item exceeds the threshold.
> - **Wait completeness.** Every wait state the orchestrator itself creates MUST compose, each with its unblock handoff: a capacity-deferred eligible item (waiting on a WIP slot), a NEEDS_ATTENTION-parked acceptance (§"The NEEDS_ATTENTION verdict" — the `accept`/`reject` valves), a `blocked`/`needs-human` item (`resolve-blocked`), and a `pending-approval` item under an effective `manual` admission policy (`approve`). An orchestrator-owned wait absent from the snapshot is a composition defect, not a policy choice.
> - **The ownership boundary.** The snapshot composes ONLY waits the orchestrator itself owns. Foreman and overseer wait states publish as ledger state on their owning plan epics and reach the operator through the snapshot's existing plan and blocked composition classes; the orchestrator MUST NOT read overseer or foreman surfaces, and a foreman-origin item MUST NOT land in any console inbox as a side effect of this section.
> - **`dispatcher.ready_aging_threshold_hours`** (sourced from this repo's `.livespec.jsonc`, positive number, default **24**) — the aging trigger. Declared **API-configurable**: it appears in the console Settings surface per §"API-configurable completeness". No per-item override — aging is a repository property.

#### 2. `scenarios.md` — two new scenarios

```gherkin
## Scenario 83 — Capacity truth is composed from the accounting, never re-derived

Feature: The admission accounting's verdict is readable attention data
  As an operator asking whether a slot is free
  I want the snapshot to carry the accounting's own verdict with each hold explained
  So that three surfaces can never again re-derive capacity from raw statuses and agree on a wrong answer

Scenario: Held, excluded, and parked rows compose as distinct facts
  Given one active item holding a live dispatch lock, one active item whose journal shows a green terminal outcome after its last admit, and one rework-pending parked item
  When needs-attention composes the snapshot
  Then the capacity fact reports one held slot with its holder and reason
  And the excluded stale claim appears as its own item with a release handoff
  And the rework-pending item appears as its own item with a re-dispatch handoff
  And the free-slot count reflects the accounting's verdict

## Scenario 84 — Aged ready work with nothing in flight surfaces an unblock

Feature: Ready-work aging composes when nothing is moving
  As a maintainer whose queue silently stalled for a day
  I want aged ready work surfaced with the unblock named
  So that a stalled repository says so instead of looking busy

Scenario: The aging fact appears past the threshold and clears in flight
  Given admission-eligible ready items older than the effective threshold and no dispatch in flight
  When needs-attention composes the snapshot
  Then an aging fact appears naming the aged count, the oldest age, and an unblock handoff
  And when a dispatch is in flight the fact does not appear
```

#### 3. Revise-time co-edits

The accepting revise pass MUST add `tests/heading-coverage.json` entries for `## Scenario 83` and `## Scenario 84`.
