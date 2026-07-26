---
topic: rework-return-door-attribution
author: claude-opus-5
created_at: 2026-07-26T17:42:47Z
---

## Proposal: Narrow the active-entry door rule's journaling justification to the disposition that is actually journaled

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The v050 active-entry door rule justifies naming the two rework returns with the sentence "Both rework returns are journaled, so the attribution rule holds". That is false for one of the two: the `reject:rework` human valve writes no journal record at all. The clause MUST be narrowed so the justification covers only `acceptance-auto-rework`, which is genuinely journaled, and states plainly that `reject:rework` is not.

### Motivation

Verified at source and against the runtime journal on 2026-07-26. `_drive_valves.py` `_reject_item` performs the `acceptance -> active` transition via `store.update_work_item_status` and returns `valve_success(stage="human-valve-reject-rework", ...)`. That helper (`_drive_valve_result.py:29`) places a `"journal": {"actor": "operator", "stage": ..., "work_item_id": ...}` object inside the drive CLI's RESPONSE PAYLOAD; it is the only occurrence of that key anywhere in the tree. Neither `_drive_valves.py` nor `_drive_policy_valves.py` nor `drive.py` references a JournalFile. The dispatch journal's full stage tally over 134 dispatches contains ZERO `human-valve-*` records of any kind, while `acceptance-auto-rework` appears 4 times across 3 work-items. The looser reading does not rescue it either: `update_work_item_status` writes only `status` and `assignee` through `client.update_issue`, with no actor and no AuditRecord (that path exists only for the `done` terminal). So the valve's transition is attributable nowhere, which is precisely the property for which this same proposal removed three other doors. The clause's own stated standard - that a door rule omitting a shipped writer is false, not merely incomplete - applies to the justification as well as to the enumeration. Recorded honestly: this error is partly ours. The dispatch-claim-liveness thread found the original self-contradiction and handed it back naming BOTH rework doors as writers of `active`, without stating that only one of them is journaled; the ratifying pass then supplied the reasonable-looking inference that both were. The enumeration our hand-back asked for was correct; the justification it invited was not.

### Proposed Changes

The active-entry door rule in `SPECIFICATION/contracts.md` MUST NOT assert that the `reject:rework` valve is journaled. The justification clause MUST be narrowed to the `acceptance-auto-rework` disposition, and the `reject:rework` valve's attribution gap MUST be stated rather than elided. The enumeration of both doors as writers of `active` MUST be retained - it is accurate, and removing it would restore the omission the v050 correction fixed.

```diff
 - `active` is entered ONLY by a journaled dispatch — factory dispatch or
   `driver-dispatch` — OR by a rework return from `acceptance`, which is
   either the `reject:rework` valve or the Dispatcher's own
   `acceptance-auto-rework` disposition. Bare operator moves into
-  `active` are removed from every lane. Both rework returns are
-  journaled, so the attribution rule holds; they are named here because
-  a door rule that omits a shipped writer is false, not merely
-  incomplete.
+  `active` are removed from every lane. Of the two rework returns only
+  `acceptance-auto-rework` is journaled, so the one-journaled-owner
+  rule holds for it alone; the `reject:rework` valve writes no journal
+  record today, and its transition is therefore unattributable. Both
+  are named here because a door rule that omits a shipped writer is
+  false, not merely incomplete — and the same standard forbids
+  asserting an attribution that does not exist.
```

This finding is deliberately confined to the truth of the justification. Whether the unattributable door SHOULD be given attribution or removed is a separate normative decision, proposed as its own finding in this file so the two MAY be ratified independently.

## Proposal: Give the reject:rework valve the journal attribution its own door rule demands

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

By the per-state verb vocabulary's own standard, a door is removed when it duplicates a journaled transition with an unjournaled one, because the ledger cannot attribute it. The `reject:rework` valve meets that description exactly: it performs the same `acceptance -> active` transition as the journaled `acceptance-auto-rework` disposition, and writes no journal record. This proposal resolves the inconsistency by ADDING the missing attribution rather than removing the door, and requires a Gherkin scenario for the new behavior.

### Motivation

The v050 vocabulary removed `pending-approval -> ready` by move, bare operator moves into `active`, and `acceptance -> done` by move, each on the ground that an unjournaled door duplicating a journaled one leaves the ledger unable to attribute the transition. Applying that rule consistently, `reject:rework` is in the same position - and the inconsistency is not cosmetic, because this repository's Dispatcher reads `active` as a claim. The dispatch-claim-liveness thread's S3 slice (`bd-ib-pme57n`) must distinguish an abandoned dispatch claim from an item parked in `active` for rework, and the auto-rework door can be recognised from its journal record while the valve door cannot be recognised at all; the slice's approved predicate has to fall back on inspecting the item's most recent terminal outcome precisely because this door leaves no trace. Attribution here is load-bearing, not bookkeeping. Addition is preferred to removal on the evidence: the Dispatcher already performs this exact transition automatically under `acceptance-auto-rework`, so the capability is plainly wanted; and `reject:rework` is the only operator route from `acceptance` back into work, since `reject:regroom` routes to `backlog`. Removing it would leave a human-rejected, already-merged item with no route back to work at all, and `backlog` is the wrong destination for merged work because it makes the item admission-eligible and invites the Dispatcher to redo shipped work. The alternative - removing the door as the bare moves were removed - is recorded here with its consequences so the ratifying pass MAY select it instead on an informed basis.

### Proposed Changes

The `reject:rework` human valve MUST write a journal record for the `acceptance -> active` transition it performs, carrying at minimum the acting party, the stage identifier, and the work-item id, symmetric with the Dispatcher's `acceptance-auto-rework` record. Emitting that object solely in the drive CLI's response payload MUST NOT be treated as satisfying this requirement: a response is transient and unattributable after the invocation returns, whereas the door rule's one-journaled-owner guarantee requires a durable record. Once this lands, the active-entry door rule MAY state without qualification that every rework return into `active` is journaled.

Because this introduces observable behavior, the revise pass applying it MUST co-edit a new Gherkin scenario in `SPECIFICATION/scenarios.md` (the next free number is 51) asserting that a `reject:<id>:rework` invocation against an `acceptance` item leaves a durable journal record naming the actor, the stage, and the work-item id - and MUST include `tests/heading-coverage.json` in the same change so the heading-coverage map stays in lockstep with the new `## Scenario` heading, per this repository's revise co-edit discipline.

An implementation item for the shipped-code half SHOULD be filed against the orchestrator ledger rather than carried by this proposal; the spec change defines the requirement, not the patch.

If the ratifying pass instead rules that the door SHOULD be removed for symmetry with the three doors v050 already removed, then `SPECIFICATION/contracts.md` MUST also state where a human rejection of an already-merged item routes instead, because `backlog` restores admission eligibility for work that has already shipped and `acceptance -> active` would no longer be reachable by any operator verb.
