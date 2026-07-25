# Handoff — dispatch-claim-liveness

## What this thread is

A work-item admitted to `active` by a dispatcher whose process then dies is left
in `active` with `assignee: fabro` **forever**, permanently consuming a WIP slot.
The failure is silent — a full cap is indistinguishable from a busy factory — and
it is monotonic: every abandonment costs a slot that never comes back.

**Ledger anchor:** epic **`bd-ib-waov`** (P1). Status is READ from the ledger
(`list-work-items` / `next`), never stored here.

**Supersedes `livespec-console-beads-fabro-6ma`** (P1, filed 2026-07-20 in the
CONSOLE tenant, closed as superseded + mis-filed). That item diagnosed the
symptom correctly and cited the exact admission arithmetic, but the defect is
entirely orchestrator-side, so it sat six days in a backlog whose owners could not
fix it. Beads has no cross-tenant edge; this prose IS the link, and `-6ma`'s close
reason points back to `bd-ib-waov`.

## ▶ CURRENT STATE + NEXT ACTION (read this first)

**Status: NOTHING STARTED. Nothing is in flight.** The epic exists; it has no
children.

**Next action:** settle the open question below, THEN groom `bd-ib-waov` into
dependency-layered slices via `/livespec-orchestrator-beads-fabro:groom` — a
read-only drafting conversation in which the **maintainer owns every cut and every
acceptance**. Do not file slices before the groom.

## Evidence — measured 2026-07-26

In the `livespec-console-beads-fabro` tenant, FOUR items sat at `active`/`fabro`
since 2026-07-21 with no run behind any of them: `-sreeqc`, `-276inb`, `-qwjfsw`,
`-ogpok4`. At the default `wip_cap` of 5 that is **4 of 5 slots**, leaving that
tenant one abandonment from a dispatcher that could never admit anything again.

Those four rows are the **only surviving reproduction** and are deliberately being
left stranded until captured verbatim; the capture lands under
`livespec-console-beads-fabro`'s `plan/console-happy-path-mvp/`. Verify against
that capture, not against the live ledger, once the un-stranding happens.

## Root cause — a designed behavior with an unaccounted consequence

`active` is written BEFORE the run (`_dispatcher_admission.py:114`) and cleared
AFTER it (`_dispatcher_completion.py` — `complete_and_accept` → `acceptance`,
`bounce_non_convergence_to_backlog` → `backlog`, `_close_item` → `done`), both
inside ONE transient dispatcher CLI invocation. If that process does not survive
to the second half, nothing ever moves the item.

**That is intentional.** `_dispatcher_engine.py` documents it: "`fabro resume`
only when the engine died — the Dispatcher never auto-resumes … treated as a
failure, never auto-resumed, item left open." The item is deliberately held for
human recovery.

So the defect is not a missing cleanup. It is that **`active` conflates "a run is
executing" with "a dead run awaits human recovery", and the WIP cap counts both** —
with no lease, no liveness reconcile at the gate, and no attention surface. A
deliberate "leave it for a human" degrades into a permanent silent capacity leak
whenever no human is told.

The sharp irony: the liveness machinery already exists HERE. `fabro inspect
--json`, `HeartbeatSink`, `LayeredLivenessProbe`, `decide_stall` — the watchdog
uses all of it to judge whether a run is alive DURING a supervised run. The
admission gate, the one place where the answer changes a decision, never asks. It
counts rows:

```
active_count = sum(1 for item in items if item.status == "active")   # :88
free_slots   = max(0, resolve_wip_cap(cwd=repo) - active_count)      # :89
```

## Requirements — all four; the cut into slices is the maintainer's at groom

1. **Reconcile at the gate.** Before computing `active_count`, establish whether
   each `active` item's run is still alive, reusing the EXISTING liveness
   primitives rather than inventing a signal. A dead run is journaled as an
   abandonment and the item moved out of `active`, following the existing
   `bounce_non_convergence_to_backlog` precedent. Self-healing, no new lifecycle
   vocabulary, and it runs exactly when the answer matters.
2. **Surface it.** An `active` item whose run is dead MUST reach needs-attention.
   Not optional polish: invisibility is why four items sat five days, and without
   it requirement 1 restores capacity while the human who was supposed to
   `fabro resume` still never learns. **A fix that only reclaims slots re-hides the
   very failure it recovers from.**
3. **Bound the claim.** An `active` claim MUST NOT be able to outlive its run
   without bound. Whether that is a lease/TTL stamped at admission, or is fully
   subsumed by requirement 1, is a design call for the groom — but "unbounded" must
   not survive as the answer, because requirement 1 depends on probe reliability
   and needs a fallback that does not.
4. **Detect it fleet-wide.** A stale-`active` check belongs in the runtime hygiene
   scan — `livespec_runtime/hygiene_scan*.py` has NO `active` check today (verified
   2026-07-26). Explicitly the weakest of the four: detection, not prevention. It
   exists so the class is caught in tenants whose dispatcher path differs.

**A verifier must be able to fail.** Each requirement needs a test whose injected
defect would make it red. For requirement 1 that means a test that actually
strands an item and proves the gate reclaims it — not one asserting a status the
healthy path also produces.

## Settle this FIRST — recovery is inconsistent, not absent

`-6ma` records that an EARLIER identical failure the same day **was** restored to
`ready` between runs. No code path was found that does this automatically
(verified 2026-07-26), which points to a human or a run-side
`drive --action move` that sometimes lands. **"Sometimes recovers" and "never
recovers" imply different fixes**, so settle it before designing. `-6ma` itself
flagged this as worth root-causing rather than assuming.

## Coordination hazards — check both before designing

Two pending spec proposals sit directly in this territory. Re-read
`SPECIFICATION/proposed_changes/` at thread start; both may have moved.

- **`reconcile-merged-dispatch-lock.md`** (TRACKED, pending, 2026-07-19) —
  load-bearing for requirement 1. It argues the heartbeat "is produced only while
  Fabro is running and is silent during the post-merge janitor window, so it is
  not a valid guard for the race this valve" covers. If that holds, a
  heartbeat-based liveness read at the admission gate would classify a run that is
  alive-but-in-its-janitor-window as DEAD and could reclaim its slot mid-flight.
  Requirement 1 must handle that case explicitly.
- **`wip-cap-zero-dispatch-off.md`** (UNTRACKED working-copy draft in another
  session's checkout as of 2026-07-26, so treat its content as VOLATILE and
  re-read it rather than trusting this line) — proposes blessing `wip_cap: 0` as
  the sanctioned dispatch-off value, and touches the same admission condition
  `count(active) < wip_cap`. Coordinate; do not design against a draft that may
  change under you.

## Scope boundary

- The console (`livespec-console-beads-fabro`) is a **consumer** and owns nothing
  in this fix; its only input is `dispatcher.wip_cap`. Do not route any part of
  this into that repo.
- Core `livespec` is involved ONLY if the design elects new lifecycle vocabulary
  or a documented lease semantic. A reconcile-at-admission fix re-derives existing
  statuses and needs neither.

## Read first

1. This file, then `supervisor-handoff.md` beside it.
2. `bd-ib-waov` in the ledger — the requirements are restated there as the durable
   record.
3. `commands/_dispatcher_admission.py` (`:88-89` the arithmetic, `:114` the write).
4. `commands/_dispatcher_completion.py` — the three existing exits from `active`.
5. `commands/_dispatcher_engine.py` — the "never auto-resumes / item left open"
   docstring that makes this a design consequence rather than an oversight.
6. `commands/_dispatcher_heartbeat_probe.py` and the watchdog's `decide_stall` —
   the liveness primitives requirement 1 must reuse.
7. `SPECIFICATION/proposed_changes/` — both hazards above.
