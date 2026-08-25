---
topic: acceptance-rework-state-machine
author: claude-fable-5
created_at: 2026-08-25T11:29:02Z
---

## Proposal: Make the ratified fix-forward rework contract executable: rework-pending selection for active items

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Keeps `acceptance -> active` as the single rework destination for BOTH ratified rework entries — the failing AI acceptance pass under an AI-dispositive policy, and the human `reject:<work-item-id>:rework` valve — and makes the bounded fix-forward contract EXECUTABLE rather than aspirational. Today both entries route an item to `active` and stop: `loop` selects only `ready` items, `dispatch --item` refuses any non-`ready` item, and `reconcile-merged` exists for a different failure, so a rework-routed item parks invisibly forever. This proposal adds a ledger-held `rework:pending` marker stamped by exactly the two rework entries, a Dispatcher re-dispatch obligation that drives marked items into free capacity BEFORE admitting new `ready` work, a `dispatch --item` operator override for marked items, a `reconcile-merged` refusal for marked items, a claim-accounting classification that stops a parked marked item from being mislabelled an abandoned claim, and an explicit NON-extension of the `blocked_reason` / rendered `lane_reason` vocabulary (no `needs-rework`), which keeps the whole change inside this repository. Co-edits the ratified `active` definition, the per-state operator verb vocabulary, the loop-invocation eligibility clause, both admission capacity clauses, the beads-issue field map, and the stale door-rules attribution sentences, so no two meanings of `active` are ratified simultaneously. Updates Scenario 35 and adds Scenarios 66-68.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the Phase 2 charge of homelab's `steady-state-loop-hardening` program: this is the ONE state-machine propose-change that program's research/007 triage binds on whoever files (findings fable 3 and sol 6 of this repository's own commissioned adversarial reviews, homelab PR #1027). Every claim below was RE-VERIFIED against this repository's primary sources on 2026-08-25 before filing, per research/007's re-verification instruction.

THE VERIFIED DEAD END. `contracts.md` §"Post-merge acceptance (`acceptance → done`)" ratifies both rework entries into `active`: a dispositive FAIL under the cap "routes the item back to `active` for fix-forward rework automatically — no human is consulted for a fail", and the human valve `reject:<work-item-id>:rework` performs `acceptance -> active` fix-forward. The implementation matches: `commands/_dispatcher_acceptance_rework.py::rework_or_block_failed_acceptance` sets `status="active"`, journals `acceptance-auto-rework`, and RETURNS — the dispatch process then exits. Nothing anywhere re-drives the item: `commands/_dispatcher_loop_selection.py::ready_items` selects only `ready` rows (plus `pending-approval` rows projected for auto-approve consideration -- never `active` ones); `dispatch --item` refuses a non-`ready` item as a precondition error; `reconcile-merged` exists "only for a dispatch whose merged PR did not complete post-run disposition" — and a rework-routed item HAS completed disposition. The word "automatically" in the ratified FAIL-route clause therefore promises an execution that has no executor. The live consequence was measured in the homelab deployment on 2026-08-23/24 (homelab `steady-state-loop-hardening` research/001-002 section 02): a first-failure item sat at `active` indefinitely, indistinguishable from "a factory run is executing right now", while its repository stalled.

WHY KEEP `active` (the chosen transition, per the reviews' shared default). Reviewer sol's finding 6 requires choosing ONE transition before filing and prefers "extending the existing bounded `active` fix-forward contract unless evidence demonstrates why it cannot be made selectable". No such evidence exists, and the alternatives are each worse:

- Routing rework to `ready` + marker re-enters the approval identity ("being in `ready` MEANS approved-to-start" — approval == `ready` membership, §"Work-item state semantics") for an item whose rework is a MACHINE-PATH continuation that must not imply a fresh human decision, and it changes WIP semantics ambiguously (sol finding 6: "whether rework retains a work-in-progress slot and whether another approval/admission cycle is implied").
- Routing under-cap rework to `blocked` / `blocked_reason: needs-rework` contradicts §"Work-item state semantics" (`blocked` is reserved for external impediments, `needs-human` | `infra-external` only), contradicts the ratified "no human is consulted for a fail", and extends the rendered `lane_reason` vocabulary — which is computed by the SHARED `livespec_runtime.work_items.lifecycle.lane_of` authority and consumed cross-repo by the console under consume-don't-recompute (§"`list-work-items`"). Extending it is a shared-runtime + console change; this proposal deliberately needs neither (the program's shared-runtime routing rule, homelab research/008/010: prefer the cut that avoids reversing dependency direction or widening shared vocabulary).

Keeping `active` also preserves the surfaces reviewer fable's finding 3 enumerates as load-bearing: `reconcile-merged`'s active-item precondition and the over-cap escalation to `blocked` / `needs-human`. (The ratified text self-contradicts on whether `drive`'s guarded `move` may target `active` -- §"`drive`" allows it while the loop-invocation surface, the door rules, and the per-lane verb sets forbid or omit it; this proposal neither relies on nor resolves that conflict, recorded as prior art in the plan thread's research/003.)

COORDINATION WITH `bd-ib-zp3u7y` (required by fable finding 3). That live item (status `active`, being worked in the factory now) covers the SIBLING population: an `active` item whose dispatch died BEFORE publishing a branch, invisible to every attention surface. Its own record rules "LEAVE THE ITEM'S STATUS UNTOUCHED" precisely because `reconcile-merged` refuses non-`active` items — this proposal keeps that invariant intact. The `rework:pending` marker HELPS that fix rather than colliding with it: today "active with no live dispatch lock" is one undifferentiated population; after this proposal the marker discriminates the sanctioned parked-for-rework state from the stranded-dispatch state, and the marker-semantics clause below binds any stranded-detection surface to honor that discrimination. Ratification of this proposal must be sequenced by the accepting revise pass with `bd-ib-zp3u7y`'s owner aware (the item is assigned to the factory; its fix reads the same journal shapes this proposal extends).

IN-FLIGHT ALIGNMENT. Three pending proposals were surveyed before authoring; this proposal ALIGNS with all three and conflicts with none. In particular `proposed_changes/wip-cap-bound-honesty.md` establishes that `wip_cap` bounds COUNTED CLAIMS (rows holding a live local dispatch lock plus journal-unreadable rows), not rows at status `active`. This proposal's capacity clause is stated in the ratified `count(active)` terms and CO-EDITS the two ratified capacity clauses directly (the Capacity bullet below and co-edit 2b), so it is genuinely self-contained: it does not depend on `wip-cap-bound-honesty`'s acceptance, and remains consistent with it if accepted -- under counted-claims semantics a parked row holds no live dispatch lock, and the same behavior follows. Without the co-edit, the literal `count(active) < wip_cap` reading would let a single parked rework item at `wip_cap: 1` deadlock its own re-dispatch forever, since the parked item inflates the count that must be under the cap. `wip-cap-naming-collision.md` (reporting vocabulary) and `factory-headroom-preflight.md` (an additional admission precondition, which a rework re-dispatch inherits like every other mechanical condition) are orthogonal and unaffected.

### Proposed Changes

All changes use BCP14 normative language and land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the three new `## Scenario` H2 headings, per the repository's revise co-edit discipline.

#### 1. `contracts.md` §"Post-merge acceptance (`acceptance → done`)" — stamp the marker at both rework entries

In the bullet "A FAILING AI acceptance pass under an AI-dispositive policy", after "routes the item back to `active` for **fix-forward rework automatically — no human is consulted for a fail** — mirroring `reject (rework)`, but AI-initiated", add:

> The under-cap FAIL disposition MUST stamp the ledger-held `rework:pending` label on the item in the same disposition, and the dispatch process then ends; EXECUTING the rework is owned by §"Rework-pending re-dispatch". "Automatically" in this clause means no human is consulted for the ROUTING decision — it does not mean the disposing process performs the rework itself.

In the bullet "`reject` from `acceptance`", after "`reject (rework) -> active` is **fix-forward** (patch on top of the live change)", add:

> The `reject:rework` valve MUST stamp the same `rework:pending` label, so the human rework path is selectable by the identical machinery — the two rework entries MUST NOT diverge in selectability. (The valve's existing durable journal record carries the provenance; the label itself is a presence marker and does not encode which entry stamped it.)

#### 1a. `contracts.md` §"Work-item state semantics" → "Door rules" — refresh the stale attribution sentences

The ratified door rules still assert twice that the `reject:rework` valve is unattributable ("the `reject:rework` valve writes no journal record today, and its transition is therefore unattributable"; "This requirement is NOT met by the shipped valve today"). Both sentences are STALE: the valve's durable `human-valve-reject-rework` journal record shipped as `bd-ib-ktxb` (closed, PR #1048) and is integration-tested. The accepting revise MUST replace both with the met-state text the ratified clause itself anticipates ("Once it is met, the `active`-entry rule MAY state without qualification that every rework return into `active` is journaled") — stating without qualification that every rework return into `active` is journaled, citing `bd-ib-ktxb`. This co-edit is load-bearing for this proposal: the marker's provenance rests on that record.

#### 2. `contracts.md` — new subsection `### Rework-pending re-dispatch`, placed immediately after §"Admission valve (`ready → active`)"

Full text of the new subsection:

> ### Rework-pending re-dispatch
>
> The two rework entries of §"Post-merge acceptance" (the under-cap dispositive FAIL, and the human `reject:<work-item-id>:rework` valve) route an item to `active` and stamp the ledger-held **`rework:pending`** label. That label is the Dispatcher's selection input for executing the promised fix-forward rework; the dispatch journal remains the audit trail of WHICH entry stamped it. Exactly those two entries MAY stamp the label; no other machinery may.
>
> - **Selection.** On every drain pass, the Dispatcher MUST drive `active` items carrying `rework:pending` into available capacity BEFORE admitting any new `ready` item, in `rank` order (ties by `id` — the same ordering authority as admission). The rework dispatch is **fix-forward**: it patches on top of the already-merged, live change; it MUST NOT revert the merged change (reverting belongs to `reject:regroom`).
> - **Marker lifecycle.** Starting a rework dispatch MUST journal the rework admission before launching the run and MUST NOT clear the `rework:pending` label at launch: the label clears only at the rework dispatch's TERMINAL disposition (the completion path that moves the item to `acceptance`, an over-cap escalation, or a terminal close). The double-selection guard is the live dispatch lock, never the label: a marked item holding a live dispatch lock MUST NOT be re-selected. A rework dispatch that dies BEFORE publishing therefore leaves the item marked and lock-less -- re-selectable by a later drain, self-healing rather than re-stranded. Any transition that moves the item out of `active` MUST also clear the label; the standing invariant is that an item whose status is not `active` MUST NOT carry it.
> - **Mechanical preconditions.** A rework re-dispatch MUST satisfy the same mechanical eligibility conditions as the admission valve — a resolvable assignee, `factory_safety` null, no unexpired observed provider-exhaustion record, and every other ratified admission precondition — EXCEPT `ready` membership and the status transition: the item is already `active` and already approved. Rework is a machine-path CONTINUATION of the admitted work; it MUST NOT re-enter `pending-approval`, MUST NOT require a fresh `approve`, and no `admission_policy` value plays any part in it.
> - **Capacity.** A rework re-dispatch re-occupies the WIP slot the item's own `active` row already holds, so the capacity condition EXCLUDES that row: the re-dispatch MUST NOT start unless the count of `active` items other than the re-dispatched item is below `wip_cap`. The sanctioned `wip_cap: 0` dispatch-off posture is preserved (no count is below zero), and the `wip_cap: 1` self-deadlock -- where the parked item's own row saturates the count that must be under the cap -- cannot arise. Compatibility note: under the pending `wip-cap-bound-honesty` counted-claims formulation the same behavior follows naturally (a parked row holds no live dispatch lock and is not a counted claim); this clause neither depends on nor conflicts with that proposal.
> - **Operator override.** `dispatch --item` MUST accept an item carrying `rework:pending` -- driving its rework immediately, subject to the SAME mechanical eligibility and capacity conditions as the drain path (per §"Dispatcher loop invocation surface", `--item` narrows the selection and never bypasses it) -- and MUST continue to refuse every other non-`ready` item as a precondition error. The refusal for a bare `active` item SHOULD name the rework route when the item's journal shows an unactioned rework disposition but the label is absent (a repair hint, not a selection input).
> - **`next` is deliberately unchanged.** The `next` surface remains a ready-only ranking (§"`next`"); it MUST NOT include rework-pending items. The Dispatcher composes rework sequencing externally, per the existing "the Dispatcher consumes this ranking and handles sequencing externally" cross-reference. Pending rework is visible via `list-work-items` (the label rides the existing `labels` projection) and via the attention surface's composition of orchestrator-owned waits.
> - **Claim accounting.** An `active` item carrying `rework:pending` with no live dispatch lock MUST be classified by the admission accounting as **rework-pending**: excluded from the capacity count AND NOT recorded as an abandoned claim. It is a sanctioned parked state, not a leak.
> - **Stranded-state discrimination.** Any surface that derives a stranded, abandoned, or leaked-claim finding from "`active` with no live dispatch lock" MUST treat `rework:pending` as a discriminator and MUST NOT report a marked item as stranded. (Coordination: `bd-ib-zp3u7y` owns the stranded-dispatch population; the marker partitions the two populations cleanly.)
> - **Vocabulary non-extension.** `blocked_reason` remains exactly `needs-human` | `infra-external`, and the rendered `lane_reason` vocabulary (`needs-human` / `infra-external` / `dependency`, computed by the shared `livespec_runtime.work_items.lifecycle.lane_of` authority) MUST NOT gain a `needs-rework` member. Rework-pending is an `active`-lane condition, not a block: `blocked` stays reserved for external impediments, and the shared runtime and console vocabularies stay untouched.

#### 2a. `contracts.md` §"Admission valve (`ready → active`)" — sequence the freed slot

The final paragraph's sentence "The Dispatcher MUST, when a WIP slot frees, admit the **top-ranked** (lexicographically earliest `rank`, per §"Work-item beads-issue mapping") admission-eligible `ready` item" gains the qualifier:

> ..., AFTER any rework-pending re-dispatch has consumed the freed capacity (§"Rework-pending re-dispatch" — finishing admitted work precedes admitting new work). The admission obligation applies to the capacity remaining once eligible rework re-dispatches have been driven.

Without this co-edit the two clauses would contradict: a freed slot cannot be simultaneously owed to the top-ranked `ready` item and to a parked rework item.

Merge instruction for the accepting revise: the pending `factory-headroom-preflight` proposal amends the SAME sentence's eligibility parenthetical (adding its headroom condition) and dictates its merged parenthetical form. The two edits compose without conflict: apply that proposal's parenthetical form where accepted, and append this proposal's trailing qualifier to the sentence either way.

#### 2b. `contracts.md` — co-edits that keep ONE meaning of `active` ratified

The accepting revise MUST apply these atomically with #### 2 — without them, two contradictory meanings of `active` would be ratified simultaneously:

- §"Work-item state semantics", the `active` bullet: append " — or parked rework-pending: routed back from `acceptance` by a rework entry and awaiting its fix-forward re-dispatch (§"Rework-pending re-dispatch")".
- §"Per-state operator verb vocabulary", the `active` row: append to the verb cell "; for an item carrying `rework:pending`, `dispatch --item` (the `drive` `impl:<work-item-id>` action) drives the pending rework".
- §"Dispatcher loop invocation surface", the `--item` bullet: the dispatch-eligibility parenthetical gains ", or — for an item carrying `rework:pending` — the rework re-dispatch eligibility of §"Rework-pending re-dispatch"", so a marked item is eligible THROUGH that section's conditions rather than as an exception to the never-bypasses rule.
- §"Admission valve (`ready → active`)", the Capacity bullet: append "(a rework re-dispatch's capacity condition excludes the item's own parked row — §"Rework-pending re-dispatch")".
- §"Per-repo WIP cap", the sentence "The Dispatcher MUST NOT drive more than `wip_cap` items into the `active` state at once": append "(a rework re-dispatch of an already-`active` parked item drives no ADDITIONAL item into `active`; it is bounded by §"Rework-pending re-dispatch"'s capacity condition)".
- §"Work-item beads-issue mapping": the authoritative field map gains a **`rework_pending`** logical field, derived from the `rework:pending` label and carried on the materialized work-item, so the selection, accounting, and discrimination clauses of #### 2 read a first-class field rather than a raw label the materialization discards today.

#### 3. `contracts.md` — `reconcile-merged` precondition sharpening

In the paragraph beginning "The Dispatcher's guarded recovery surface for an already-merged item is `reconcile-merged` ...", after "It MUST refuse unless the named item is currently `active`, because this valve exists only for a dispatch whose merged PR did not complete post-run disposition", add:

> It MUST additionally refuse ANY item carrying the `rework:pending` label, whatever its status (the shipped valve already accepts a wider status set than the ratified active-only sentence — a pre-existing spec/implementation divergence recorded in the plan thread's research/003 and deliberately not resolved here): such an item's dispatch COMPLETED its post-run disposition — the disposition's outcome was rework — and the remedy is the rework route of §"Rework-pending re-dispatch" (the next drain pass, or `dispatch --item`), which the refusal message MUST name. `--force` MUST NOT bypass this refusal: reconciling a rework-pending item would re-run a disposition that already ran.

#### 4. `scenarios.md` — update `## Scenario 35`

In the first scenario block ("An AI-dispositive item is auto-reworked on a failing pass"), after "Then the item transitions to active for fix-forward rework without a human", add the lines:

```gherkin
  And the item carries the rework:pending label
  And the disposing dispatch does not itself perform the rework
```

#### 5. `scenarios.md` — three new scenarios

```gherkin
## Scenario 66 — A parked rework item is re-dispatched before new ready work

Feature: The fix-forward rework contract is executable
  As a maintainer relying on the acceptance valve
  I want a rework-routed item to be picked up by the next drain
  So that rework parks visibly and briefly instead of invisibly forever

Scenario: The drain drives a rework-pending item before admitting new ready work
  Given an active item carrying the rework:pending label and holding no live dispatch lock
  And ready items exist in the queue
  And the items counted against wip_cap are below the cap
  When the Dispatcher drain runs
  Then a fix-forward rework dispatch starts for the marked item before any new ready item is admitted
  And starting the rework journals the rework admission and leaves the label in place until the rework dispatch's terminal disposition
  And the merged change is not reverted

Scenario: A rework dispatch that dies before publishing leaves the item re-selectable
  Given a marked item whose rework dispatch acquired a dispatch lock and died before publishing a branch
  When a later drain runs and the lock is no longer live
  Then the item is still marked and is selected for rework again

Scenario: A parked rework item neither holds capacity nor reads as an abandoned claim
  Given an active item carrying the rework:pending label and holding no live dispatch lock
  When the admission accounting runs
  Then the item is classified rework-pending
  And it is excluded from the capacity count
  And it is not recorded as an abandoned claim
  And no stranded-dispatch surface reports it as stranded

## Scenario 67 — The human rework reject parks the same selectable state

Feature: The two rework entries do not diverge in selectability
  As an operator using the reject valve
  I want a human rework reject to be picked up exactly like an AI-fail rework
  So that the valve I am offered is not a dead end

Scenario: reject:rework stamps the marker and the operator can drive it immediately
  Given an item parked in acceptance
  When the operator performs reject rework via the drive valve
  Then the item transitions to active carrying the rework:pending label
  And dispatch --item on that item is accepted and drives the fix-forward rework
  And dispatch --item on an active item without the label is refused as a precondition error

## Scenario 68 — reconcile-merged refuses a rework-pending item

Feature: The recovery valve stays scoped to dispatches that died mid-flight
  As an operator recovering a stranded dispatch
  I want reconcile-merged to refuse an item whose disposition already completed
  So that a completed rework disposition is never re-run as a recovery

Scenario: A rework-pending item is refused with the rework route named
  Given an active item carrying the rework:pending label whose merged PR completed post-run disposition
  When the operator invokes reconcile-merged for that item
  Then the invocation is refused
  And the refusal names the rework re-dispatch route as the remedy
  And force does not bypass the refusal

Scenario: An unmarked merged item remains recoverable
  Given an active item without the rework:pending label whose dispatch died after its PR merged without completing disposition
  When the operator invokes reconcile-merged for that item
  Then it is accepted, because that is the recovery this valve exists for
```

#### 6. Revise-time co-edits

The accepting revise pass MUST add `tests/heading-coverage.json` entries for the new H2 headings `## Scenario 66`, `## Scenario 67`, and `## Scenario 68` (the `test` value MAY be the literal "TODO" with a non-empty reason naming the implementation work-items this ratification will cut), MUST apply the co-edits of #### 1a and #### 2b atomically with #### 2, and MUST verify no existing H2 heading changed.
