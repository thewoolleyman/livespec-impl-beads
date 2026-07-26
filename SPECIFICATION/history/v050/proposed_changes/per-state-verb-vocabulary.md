---
topic: per-state-verb-vocabulary
author: claude-opus-5
created_at: 2026-07-26T08:42:16Z
---

## Proposal: Per-state operator verb vocabulary for impl-side lanes

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Define the normative per-lane operator verb vocabulary this repository already
claims to own. Each impl-side lane gets an explicit valid-verb set; each lane
transition gets exactly ONE journaled owner (no unjournaled duplicate doors); a
policy dial is valid only while the decision it governs is still ahead; and a new
`driver-dispatch:<id>` drive surface is defined for the `ready` items the
dispatch-admission host-only refusal already declines to sandbox.

### Motivation

`livespec-console-beads-fabro`'s `SPECIFICATION/contracts.md` states that
per-item verb suppression "depends on the per-state valid-verb vocabulary, which
is **owned by `livespec-orchestrator-beads-fabro`** and not yet consumed here."
That vocabulary has never been authored here, so the console cannot implement
verb suppression without inventing a vocabulary it does not own — and in the
meantime its surface offers verbs that are meaningless or actively wrong for the
selected item's state. Verified 2026-07-26: `approve`, `accept` and `reject` all
open confirm modals on a `backlog` item, and the only state-aware verb anywhere is
the console's `status_move_targets`.

This proposal authors the vocabulary here so the console can consume it. Console-
side changes (hint suppression, move-table narrowing, groom and driver-dispatch
presentation, keybindings) follow as console-side proposals AFTER this ratifies
and are explicitly OUT of scope here.

**Provenance.** Every rule below is a maintainer decision taken in the Stage-1
brainstorm of `livespec-console-beads-fabro` `plan/operator-surface-redesign/`
(2026-07-21..26), recorded with per-point verification in that repo at
`plan/console-happy-path-mvp/research/verb-vocabulary-brainstorm.md`. The body was
drafted there as `plan/operator-surface-redesign/research/verb-vocabulary-propose-change-draft.md`
and is filed here unchanged in substance.

### Proposed normative content

#### The per-lane operator verb sets (impl-side lanes)

| Lane | Valid operator verbs |
|---|---|
| `backlog` | **groom** (every backlog item, uniformly); move→ready (admission); move→blocked; set-admission; set-acceptance; merge-on-review-cap; review-fix-cap; acceptance-rework-cap |
| `pending-approval` | **approve** (the single door toward `ready`); reject (rework \| regroom); set-admission; move→backlog (withdraw); move→blocked (park); set-acceptance; review caps per the window rule |
| `ready` | move→backlog (withdraw); move→blocked (park); **driver-dispatch** (factory-unsafe items only); set-acceptance; acceptance-rework-cap; merge-on-review-cap; review-fix-cap |
| `active` | observe only — no operator verbs beyond set-acceptance / acceptance-rework-cap per the window rule |
| `acceptance` | **accept** (the single door into `done`); reject (rework \| regroom); move→backlog (de-scope); move→blocked (park) |
| `blocked` | move→ready (unblock); move→backlog (an item needing decomposition routes here first — groom is `backlog`-only) |
| `done` | nothing |

#### The door rules — each transition has exactly one journaled owner

- `ready` is entered by **approve** (from `pending-approval`, journaled
  `human-valve-approve`) or by an operator **move** from `backlog`/`blocked`. The
  `s`-move from `pending-approval` to `ready` is REMOVED — it is an unjournaled
  duplicate of the valve.
- `active` is entered ONLY by a journaled dispatch: **factory dispatch**
  (Dispatcher drain / `drive impl:<id>`, carrying a fabro run ref) or
  **driver-dispatch** (below). Bare operator moves into `active` are removed from
  every lane.
- `done` is entered ONLY by **accept**. The `s`-move `acceptance → done` is
  REMOVED. It exists in code today (console `status_move_targets`,
  `lib.rs:483-489`) and contradicts the shipped walkthrough's ship-guard prose;
  this rule makes that prose true.
- `pending-approval` is never a move target (existing rule, unchanged) — it is
  entered only by intake DoR routing.
- reject (rework | regroom) is valid at the two human valves ONLY —
  `pending-approval` and `acceptance`. Mid-flight abort of an `active` run is
  PARKED: it needs run-cancellation semantics, and journaling a rejection while
  the run continues would be a new lie rather than a fix.

#### The dial window rule

A policy dial is valid only while the decision it governs is still ahead:

- set-admission — through `pending-approval`
- merge-on-review-cap and review-fix-cap — through `ready`. Both are snapshotted
  into the run at dispatch (`_dispatcher_loop.py:125-128`), so a dial change on an
  `active` item can never reach the in-flight run; offering it there would be
  inert.
- set-acceptance and acceptance-rework-cap — through `active`
- nothing on `done`

#### New drive surface: `driver-dispatch:<id>`

Valid on `ready` items whose `factory_safety` is non-null — exactly the set the
dispatch-admission host-only refusal already declines to sandbox
(`_dispatcher_admission.py:82-86`), whose refusal text already says "Host-route it
to a host sub-agent instead; the item remains open for that route." So the
orchestrator already anticipates this route; this names it.

It journals the actor and a driver-session reference and moves `ready → active`.
The driver session parks its result at `acceptance`, where the normal accept valve
applies. Because the eligible set is exactly the set the Dispatcher refuses, there
is no dispatcher/driver race by construction — no claim mechanism is required.
Extending it to any `ready` item WOULD require one, and is deliberately not
proposed.

**Groom needs no door.** A groomed item stays `backlog` throughout the drafting
conversation (`regroom.py`: groom targets are backlog-only), and the groom exit is
close-regroomed-out into replacement slices.

### Grounding for the reviewer

The console's `status_move_targets` (`lib.rs:477-493`) is the only state-aware
verb that exists today and is the generalization model. Every narrowing above was
verified against master 2026-07-25..26; per-point citations are in the brainstorm
record named under Provenance.

Two consequences a reviewer should weigh explicitly:

1. Three currently-legal transitions are REMOVED (`pending-approval → ready` by
   move, operator moves into `active`, `acceptance → done` by move). Each is
   removed because it duplicates a journaled door with an unjournaled one, so the
   ledger cannot attribute the transition. Any consumer relying on them breaks by
   design.
2. `driver-dispatch` is new surface area. It is scoped to the host-only-refused
   set precisely so it needs no locking; a future widening must not treat that
   scope as incidental.
