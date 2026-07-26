# Prior work, the originating track, and live collisions

Written 2026-07-26. Read `root-cause.md` first for the defect itself; this
file covers WHO shipped it, what is already filed, and what live work this
thread collides with.

## The originating track — closed and archived, so there is nobody to hand back to

| | |
|---|---|
| Epic | **`bd-ib-24j5uy`** — "Realize the ratified v034 dispatcher policy settings (retire Full autonomous mode)" — **CLOSED 2026-07-20**, all 15 children closed |
| Defective slice | **`bd-ib-24j5uy.4`** ("D1"), P1 bug, CLOSED |
| Commit / PR | **`952d874`** / **PR #839**, branch `feat/bd-ib-24j5uy.4`, release 0.45.14 |
| Narrative record | **`livespec` repo → `plan/archive/autonomous-mode-retirement/`** — **ARCHIVED** (`handoff.md` 140 KB, `supervisor-handoff.md`) |
| Author | Fabro dark-factory dispatch, not a hand edit |

**Both the epic and its plan thread are closed and archived.** There is no
live thread to route this back into, which is why it needs a new thread
rather than a hand-back. Reopening `autonomous-mode-retirement` would be
wrong: that programme's stated acceptance was fleet-wide retirement of
autonomous mode, which genuinely completed. This is a residual defect in
one of its slices, not an incomplete programme.

### What the closed epic ASSERTED, and why it was not enough

`bd-ib-24j5uy`'s close reason claims acceptance criterion (3):

> "a per-item label beats the global for every override-capable setting AND
> an unlabeled item inherits the global — the second half was BROKEN when
> the sweep started (D1) and is now fixed on master"

That claim is TRUE for the two enforcement paths D1 swept and FALSE as a
statement about the system's observable behavior: the advertiser still
behaves as though the global does not exist. The epic's own close was
verified by "three independent read-only adversarial verifiers" and still
missed this, because all three inherited D1's framing of the problem as
"which callers of `effective_admission_policy` omit `cwd`".

That is the strongest available argument that the fix here must be a
MECHANICAL check rather than another careful human sweep: careful human
sweeps have already failed on this exact defect, four times over (D1's
author plus three adversarial verifiers).

## Already filed — do NOT duplicate

**`bd-ib-4m5f`** (P2, BUG, **BLOCKED**, filed 2026-07-21) — "next and the
Dispatcher disagree on the candidate SET: a pending-approval item is
invisible to `next` but selectable by the drain."

Adjacent but **distinct**, and the distinction matters for scoping:

- `-4m5f` is about **visibility**: `next` and the Dispatcher compute
  different candidate SETS for the same ledger
  (`_dispatcher_loop_selection.is_dispatch_candidate` re-tests a
  `pending-approval` item under a ready projection; `next` does not).
- THIS thread is about an **offered action that cannot fire**: the
  advertiser and the enforcer of the SAME action disagree on its
  precondition.

They share a theme — surfaces disagreeing about what `pending-approval`
means — and a fix for either could plausibly generalize. Whether they
should be unified is an open question for the groom, recorded in
`handoff.md`. They must not be filed as duplicates of each other.

## LANDED collision — the `per-state-verb-vocabulary` door rule, ratified as v050

**This already happened.** The proposal was ratified as **v050** at
2026-07-26T17:26:19Z (`27980bb`, decision `modify`), while this thread was
being written. It is no longer preventable; the remedy is now a
propose-change against a RATIFIED contract.

The ratified text, live in `SPECIFICATION/contracts.md`
§"Door rules — every transition has exactly one journaled owner":

> - `ready` is entered by `approve` (from `pending-approval`) or by an
>   operator move from `backlog`/`blocked`. **The move from
>   `pending-approval` to `ready` is REMOVED: it is an unjournaled
>   duplicate of the `approve` valve, so the ledger cannot attribute the
>   transition.**

**The v050 revision corrected a DIFFERENT door rule, not this one.** Its
`## Modifications` fixed the `active`-entry rule to name the two rework
returns — the finding the `dispatch-claim-liveness` session reported. It
then states explicitly: *"Everything else lands as proposed: the per-lane
verb table, **the removal of the three unjournaled duplicate doors**, the
dial-window rule, and driver-dispatch…"*. So the `pending-approval → ready`
removal landed untouched, and its false rationale is now ratified contract
text.

Record: `SPECIFICATION/history/v050/proposed_changes/per-state-verb-vocabulary-revision.md`.

**ONE half of the ratified rationale is false. The other half is CORRECT.**
An earlier draft of this file claimed both were false; that was an error,
corrected here 2026-07-26 after this thread's own cold-open review caught it.

1. **"Unjournaled" is CORRECT — do not contest it.** The earlier draft argued
   the move journals, citing the `journal: {actor: "operator", stage:
   "human-valve-move", ...}` object returned by
   `drive --action move:<id>:ready`. That object is a field of the CLI's
   RESPONSE PAYLOAD, not evidence of a durable write. Verified at source
   2026-07-26: `_drive_valve_result.py:29` `valve_success` merely builds that
   key into the returned dict; `_drive_valves.py` contains ZERO references to
   `JournalFile` / `append_journal`; and the dispatch journal contains ZERO
   `human-valve-move` records. Reading a response field as a journal write was
   the mistake. v050 is right: the move's transition is durably attributable
   nowhere.
2. **"Duplicate" is FALSE, and this is the whole of the remaining case.**
   Because of the defect in `root-cause.md`, the approve valve refuses every
   item on this repo. The move is not a duplicate of the valve — until the
   valve is fixed it is the ONLY on-demand operator door from
   `pending-approval` to `ready`, journaled or not.

The correction MATTERS for scoping: any amendment must argue "removing this
door leaves no working on-demand door", NOT "the move journals". The second
argument is false and the repo has already refuted it (below).

**Consequence, now realized:** the ratified contract states the operator's
only working manual door is REMOVED, and names as its replacement a valve
that cannot fire on this repo. The sole remaining path is the Dispatcher's
auto-approve at admission (`_dispatcher_admission.py`), which fires on a
loop pass rather than on demand. An operator who needs an item `ready` NOW
has no contract-blessed, on-demand route at all.

Note the irony, and treat it as evidence rather than colour: `bd-ib-wuotqm`
was advanced to `ready` on 2026-07-26 by exactly this move, BECAUSE the
approve valve refused it. That operation is now spec-non-compliant under
v050 — while remaining the only thing that worked.

This is a SECOND, independent problem in that proposal, distinct from the
`active`-entry wording issue the `dispatch-claim-liveness` session reported
and which v050 DID fix. It is not "worse" in kind — both are clauses whose
justification outran the shipped code — but it is the one still standing:
that one was corrected before ratification, this one survived it.

**Affected population, measured 2026-07-26:** exactly two items sit at
`pending-approval` — `bd-ib-pme57n` and `bd-ib-cfgkkk` (both from the
`dispatch-claim-liveness` track). Neither is stranded, because
`auto_approve_ready: true` means the next admission pass advances them. But
they are precisely the population the proposed removal would affect.

**Consequence for this thread, now that it has landed.** The question is no
longer "which order". It is: the ratified contract is wrong on a point of
fact, and the code it describes is also wrong. Two remedies are needed and
they are independent:

1. **Fix the code** (`bd-ib-h57nx4`) so the approve valve is reachable —
   which is what would make the ratified sentence TRUE rather than
   aspirational.
2. **Amend the contract** via `/livespec:propose-change` so the door rule
   stops asserting the move is "unjournaled" (it journals
   `stage: human-valve-move`) and stops implying `approve` is a working
   door on a repo where it refuses everything.

Doing only (1) leaves a ratified sentence that still names a door the
operator cannot use. Doing only (2) leaves the valve broken.

Sequencing is NOT free here, and the earlier draft's "file (2) immediately"
advice was too glib. Two considerations pull against it:

- `rework-return-door-attribution` is pending against the same paragraph. A
  second proposal filed now means two pending amendments to one block, and
  whichever ratifies second must re-derive its verbatim anchor.
- Landing (1) first would make the ratified sentence substantially TRUE —
  `approve` really would become the working door — which may reduce (2) to a
  small wording fix, or remove the need for it entirely.

That argues for (1) first, then re-reading the clause before deciding whether
(2) is still needed. The groom owns the call, but it should be made on those
grounds rather than on "it's cheap".

## Live collision #2 — `rework-return-door-attribution` is pending against the SAME block

`SPECIFICATION/proposed_changes/rework-return-door-attribution.md` was filed
2026-07-26T17:42:47Z and is PENDING as of this writing. It targets the SAME
`contracts.md` §"Door rules" paragraph any amendment from this thread would
touch, and it independently establishes the journaling fact corrected above —
with a fuller measurement than ours:

> "The dispatch journal's full stage tally over 134 dispatches contains ZERO
> `human-valve-*` records of any kind, while `acceptance-auto-rework` appears
> 4 times across 3 work-items."

Its scope is the `active`-entry rule's claim that "Both rework returns are
journaled" — narrowing that justification to `acceptance-auto-rework` alone.
Ours would be the `ready`-entry rule. Same block, adjacent clauses, different
sentences.

**Consequences for this thread, both mandatory:**

- Any amendment we file MUST NOT assert the move journals. That premise is
  already refuted, in the same directory, by a proposal that will be decided
  in the same revise pass.
- Whoever files ours MUST check whether `rework-return-door-attribution` has
  ratified first, and re-derive the verbatim anchor if so — this is exactly
  the anchor-staleness trap that cost the `wip-cap-zero-dispatch-off`
  proposal three days and a full refresh pass (see `SPECIFICATION/history/v049/`).
  Two pending proposals against one paragraph is precisely that setup.

## Other live tracks — checked, no collision

- **`dispatch-claim-liveness`** (epic `bd-ib-waov`, ACTIVE) — reported this
  defect and correctly established it is not theirs. Its two
  `pending-approval` items are the affected population above. No code
  overlap: its product surface is `_dispatcher_dispatch_lock.py`.
- **v049 / `wip-cap-zero-dispatch-off`** (CLOSED 2026-07-26) — the track
  that surfaced this while approving `bd-ib-wuotqm`. Its three work-items
  (`bd-ib-cfcmse`, `bd-ib-6pbt5k` closed; `bd-ib-wuotqm` now `ready`) touch
  `_dispatcher_policy_settings.py` and `_drive_config_schema.py`. No
  overlap with the valve/advertiser surfaces, but note `bd-ib-wuotqm` reached
  `ready` via the `move` this thread is defending — if `move` is removed
  before this is fixed, that route disappears.
