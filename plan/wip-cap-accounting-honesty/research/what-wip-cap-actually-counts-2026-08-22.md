# What `wip_cap` actually counts — measurements of 2026-08-22

## Why this thread exists

The `livespec-overseer-foreman` session reported that dispatch was being
refused while factory hosts sat idle, and handed over a diagnosis: that
`dispatcher.wip_cap` is a single global counter of in-flight Fabro runs
spanning every factory host. That diagnosis is wrong, and the remedy it
proposed is forbidden by ratified specification.

The investigation that falsified it produced a different and sharper
finding, which is what this thread owns: **`wip_cap` counts neither host
load nor runs in flight, and no surface says so.** Everything below was
measured on 2026-08-22 and is re-checkable.

## Notation used in this document

- **Branch 1 / Branch 2** — the two ways `claimed_active_count` can decide
  that a ledger row occupies a WIP slot. They are the two `count += 1`
  sites in that function and nothing else reaches them.
- **Control** — a second measurement deliberately shaped to return the
  OPPOSITE answer if the claim under test were false. A check that cannot
  fail is not evidence.
- **Green-terminal row** — a work-item at ledger status `active` whose
  dispatch journal records a successful (`green`) terminal outcome no
  earlier than its last admit.
- **Counted / uncounted** — whether a row contributes to `active_count`,
  the number compared against `wip_cap`. A row can sit at status `active`
  and be uncounted; the two are not the same thing.

## Finding 1 — the counter is per-repo and ledger-derived, not host-wide

`commands/_dispatcher_admission.py` computes capacity as
`active_count = claimed_active_count(repo=..., items=..., journal=...)`.
That function (`commands/_dispatcher_claim_reclaim.py:26-42`) iterates the
repository's OWN ledger items, and never calls `fabro`, never contacts a
factory, and never learns of another repository.

**Control, all three readings taken inside one minute** (the original
report's readings were eight minutes apart, which is what allowed a
coincidence to look like an identity):

| Reading | Value |
|---|---|
| `livespec-overseer` ledger rows at `active` | 12 |
| `fabro ps --server https://hp-xubuntu…:32276` | 6 runs |
| `fabro ps --server https://vps…:32276` | 3 runs |

No two of those agree. The `vps` listing contains a run belonging to
`livespec-console-beads-fabro`, a repository whose runs the overseer
tenant's counter provably cannot observe. The originally reported
identity (8 on hp plus 2 on vps equalling an `active_count` of 10) was
arithmetic coincidence.

## Finding 2 — Branch 2 counts success, forever

`_claim_still_counts` ends:

```python
return history.last_outcome_status == "green"
```

guarded only by the terminal outcome's journal index being no earlier than
the last admit's. There are **no timestamps anywhere in that function** —
the comparison is purely one of positions in the journal.

The consequence is not the intuitive one. A row does not count because it
is stale, or dead, or stuck. It counts because its run **succeeded** and
the ledger row was never advanced out of `active`. And because nothing in
the predicate is time-bounded, it counts **permanently**, until a human
moves the row.

**Control, and it is the strongest measurement in this thread.** The
foreman disposed three rows and re-ran the identical probe that had been
refused twice across 110 minutes:

- `01:44:50Z` — refused: `active_count=10 wip_cap=10 free_slots=0`
- `02:10:54Z` — admitted: `ledger-admit`, run `01M0KKRPNRH4` executing on hp

Same work-item, same command, same cap. The only change was three ledger
rows. Two of the three (`overseer-5stpf2`, `overseer-zkwf`) were
green-terminal: their runs had **succeeded** and their pull requests had
**merged**, at 23:25:11Z and 01:36:25Z respectively. Those two were doing
the blocking. The third (`overseer-hgq4wi.35`) had no journal history at
all and was almost certainly never counted.

## Finding 3 — Branch 1 counts a local process, not a remote run

`live_dispatch_lock` (`commands/_dispatcher_dispatch_lock.py:82-87`)
returns the lock only when `_lock_holder_matches_pid` holds. That predicate
(`:155-162`) probes `os.kill(pid, 0)` and compares process start time
against the recorded `started_at_epoch`, and the recorded `pid` is written
by `_write_dispatch_lock` as `os.getpid()` — **the dispatching process's
own pid**.

So Branch 1 counts a slot only while the LOCAL dispatcher process is
alive. A detached dispatcher that has exited, or a foreground one killed
by its own timeout, leaves a lock that no longer matches and stops being
counted — while its remote Fabro run continues to execute.

*(Branch 1 was contributed by `livespec-overseer-foreman` and verified
here against source before adoption.)*

## What the two branches mean together

`wip_cap` counts **live local dispatcher processes plus un-advanced
green rows**. That is the entire extent of what it can observe.

Two consequences follow directly, and neither is documented anywhere:

- It is possible to sit at the cap with **nothing running**, because
  green-terminal rows accumulate without bound.
- It is possible to have many runs executing while the counter reads
  **near zero**, because detached dispatchers have exited.

This also explains a residual nobody had accounted for: an `active_count`
of 10 against **thirteen** rows at status `active` at 01:44:50Z. The
three-row gap is rows in neither branch.

The specification says only that the Dispatcher "MUST NOT drive more than
`wip_cap` items into the `active` state at once"
(`SPECIFICATION/contracts.md` §"Per-repo WIP cap"). Read against the two
branches, that sentence describes something the implementation does not
do — not because the implementation is wrong, but because "in the `active`
state" and "counted" are different sets, and no surface distinguishes them.

## Finding 4 — the naming collision, which caused a real misdiagnosis

Two caps of ten, one configuration file apart, are different objects:

| Setting | Scope | Owner |
|---|---|---|
| `dispatcher.wip_cap` (`.livespec.jsonc`) | per-repo, ledger-level | this Orchestrator |
| `server.scheduler.max_concurrent_runs` (`~/.fabro/settings.toml`) | per-server | the Fabro daemon |

Both currently hold the value 10. The foreman reasoned from the second,
concluded hp had eight free slots, reported that to the maintainer, and
was wrong. This is a recorded cost, not a hypothetical.

## Finding 5 — `drive` cannot reach the documented cap override

`commands/_dispatcher_admission.py`'s own docstring records that
"`dispatch --item` is an operator override that passes `enforce_cap=False`".
That override is real: `commands/_dispatcher_run_commands.py:178` passes
`enforce_cap=False`.

But the sanctioned operator surface cannot reach it.
`drive.py`'s `build_dispatcher_argv` emits
`dispatcher.py loop --repo … --item <ref> --json`, and the loop path passes
`enforce_cap=True` (`commands/_dispatcher_loop_command.py:186`). The argv is
pinned by an equality assertion in
`tests/…/test_drive_core.py::test_build_dispatcher_argv_uses_targeted_loop_for_selected_impl_item`,
whose name confirms the routing is intentional rather than incidental.

**Evidence grade, stated so it is not over-read: this is a test-pinned
static reading of both ends of the chain. It has NOT been executed.** The
control that would settle it: with the cap saturated, run
`drive --action impl:<id>` and expect a capacity deferral, then run
`dispatcher.py dispatch --item <same id>` and expect `ledger-admit`. It
costs one slot in whichever tenant runs it, which is why it remains
unexercised.

## What this thread does NOT own

- **A per-factory or host-wide cap.** Ratified `contracts.md` §"Host
  concurrency belongs to the Fabro scheduler" states the Orchestrator owns
  no host-level limit and "MUST NOT expose a committed configuration key
  that purports to bound host-wide dispatch concurrency", and that a repo
  topping out below host capacity "is intended, not a defect to be
  corrected by re-adding a host-level key". The client-side host cap was
  deliberately deleted (`bd-ib-vmve`, closed; the decision record is
  `plan/archive/retire-host-dispatch-cap/handoff.md`). Re-proposing it
  requires a propose-change retiring that clause, and this thread does not.
- **Disk headroom, host garbage collection, or dispatch preflight on free
  space.** Owned by `bd-ib-bdcmok` / `plan/factory-host-storage-reclamation`,
  opened 2026-08-22. Its `.4` is the spec-change-tier headroom preflight.
- **Raising any cap value.** `bd-ib-3ler` (acceptance) already raised the
  committed per-repo cap from 5 to 10 across all fourteen governed repos on
  2026-08-20; `bd-ib-7cit` (backlog) owns raising the shipped default and is
  correctly marked spec-change tier.

## Prior art consulted

Scanned with `bd list --status all --limit 0 --json` over all 672 items of
this tenant, closed included:

- `bd-ib-vmve` / `.1` / `.2` (closed) — retired the client-side host cap.
- `bd-ib-3ler` (acceptance) — raised the committed cap 5 to 10.
- `bd-ib-7cit` (backlog) — raise the shipped default; spec-change tier.
- `bd-ib-aabn` (backlog) — the loop-versus-`dispatch --item` asymmetry as a
  SPEC-documentation gap, with a 2026-07-30 maintainer ruling that **the
  code is correct**. It does not cover Finding 5, which is that `drive`
  cannot reach the override at all.
- `bd-ib-vfsg` (backlog, P1) — the green-outcome bookkeeping race that
  regresses ledger status, six measured instances. Read against Branch 2,
  each occurrence manufactures a permanently counted row; its acceptance
  criteria do not mention that consequence.
- `bd-ib-pme57n` (closed) — stopped counting dead claims against the cap;
  the ancestor of today's Branch 1.
- `bd-ib-rnlks6` (pending-approval, `livespec-overseer` tenant) — blocked
  Fabro runs holding SCHEDULER slots. A neighbouring mechanism at the
  Fabro layer, not this counter.

`plan/valve-advertisement-mismatch` was evaluated as a possible owner for
Finding 5 and rejected: its defect is an advertiser and an enforcer
diverging on the approve predicate, with a mandated fix of binding both to
one shared predicate. Finding 5 is dispatch-argv routing. Different root
cause, different fix; cross-referenced only.

## Provenance

Findings 1, 2, 4 and 5 were measured by the `fabro-factory-underutilization`
session. Finding 3 was contributed by `livespec-overseer-foreman` and
verified against source here. The 02:10:54Z admission control was run by
`livespec-overseer-foreman` in its own tenant.

One correction is recorded deliberately, because the wrong version
travelled in a peer message before it was caught: this session initially
claimed that an epic parked at `active` consumes a WIP slot. **That is
false.** An epic that was never dispatched has no live lock and no journal
history, so `_claim_still_counts(history=None)` returns `False` at its
first line and the row falls through to the abandoned-record branch
uncounted. The claim was withdrawn.

## ADDENDUM, 2026-08-22 evening — three findings have been overtaken

This note is item 1 of the read-first chain in every handoff on this thread, which
makes it the highest-risk place in the plan for a claim that was true when written
and has since stopped being true. Three of its five findings are now dated. Nothing
above is deleted; read the original and then this.

### Finding 1's TITLE is one level too coarse — the body is still correct

The heading says "the counter is per-repo and ledger-derived". Measured
2026-08-22, `wip_cap` is scoped to the **CHECKOUT**, not the repository. Two
checkouts of ONE repo, read in the same second from `claimed_active_accounting`
itself against ONE ledger holding 11 rows at `active`, reported DISJOINT counts:

    /data/projects/livespec-orchestrator-beads-fabro   active_count 2
    ~/.worktrees/.../control-wip-cap-enforce-asymmetry  active_count 1

Both counting inputs resolve from the `--repo` path — the dispatch-lock directory,
and `<repo>/tmp/fabro-dispatch-journal.jsonl`. A second checkout starts with an
empty lock directory and its own journal, so N checkouts admit up to N x `wip_cap`.

WHY THE ORIGINAL FINDING IS NOT WRONG, which matters for how much to distrust it.
Finding 1 was answering "is this counter host-wide?", and its answer — no, it never
calls `fabro`, never contacts a factory, never learns of another repository — is
correct and its control settles that question. What its control COULD NOT have
detected is the checkout axis, because all three of its readings were taken from
ONE checkout; a single-vantage control cannot see a per-vantage split. So the
finding is right about what it tested, and its title overstates the scope by one
level. "Per-repo" reads as a guarantee about the repository, and it is not one.

Recorded on `bd-ib-snyquw.5` and in BOTH pending proposal files, because the
proposal's locality clause ("this repository's own ledger rows, its dispatch locks,
and its own journal") inherits the same ambiguity and would ratify it.

### Finding 2 is SUPERSEDED by PR #1718 — green rows no longer count

"Branch 2 counts success, forever" was true when written and is now false.
`claimed_active_accounting` computes
`active_count = len(live_lock_active_ids) + len(journal_unreadable_active_ids)`:
green-terminal rows are still IDENTIFIED and reported, but no longer COUNTED. The
remedy chosen was RECLAIM, and it is fail-closed — a row whose journal cannot be
READ lands in `journal_unreadable_active_ids` and IS counted, so an unreadable
journal makes the predicate count MORE, never fewer.

The sibling note `uncounted-active-rows-measured-2026-08-22.md` already carries a
#1718 addendum. This note did not, and this note is the one the read-first chain
sends people to first — which is exactly how a superseded claim keeps being
re-derived.

### Finding 5 has been EXECUTED, and its remedy has SHIPPED

Finding 5 states its own evidence grade carefully: "a test-pinned static reading …
It has NOT been executed." That is no longer the case. The control it specifies was
run on 2026-08-22, using a cheaper design than the one it describes — cap forced to
`0` in a throwaway worktree's uncommitted `.livespec.jsonc`, so saturation did not
have to be waited for:

    drive --action impl:<id>            -> stage "capacity-deferred"
                                           active_count=0 wip_cap=0 free_slots=0
    dispatcher.py dispatch --item <id>  -> stage "ledger-admit", then "dispatch-id"

Same item, same repo path, same cap, 45 seconds apart. CONFIRMED. Leg 1 cost
nothing (a deferral claims nothing); leg 2 cost the one real dispatch the control
always had to budget.

The finding's framing has also been CORRECTED by that work: the override is not
unreachable, it is UNDISCOVERABLE. `dispatcher.py dispatch --item` reaches it, and
AGENTS.md already names that command as the preferred operator dispatch route. Only
`drive` cannot express it.

REMEDY SHIPPED as `bd-ib-snyquw.3`, PR #1754 (c279c108). Direction chosen: keep
`drive` cap-enforcing — no bypass flag — because `drive --action impl:` is what the
DRAIN surfaces hand out (`_needs_attention_work_items.py:69`, `prose/plan.md:231`),
so a flag there would sit on the unattended side of the line the 2026-07-30
`bd-ib-aabn` ruling draws. Instead the capacity deferral now names the override with
the item id interpolated, and the `admit_and_select` docstring states which surfaces
reach it. Verified end-to-end against the shipped build, not from the diff.
