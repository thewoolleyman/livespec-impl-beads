# This plan's own work is partly invisible to its archive gate

**Date:** 2026-08-21
**Finding:** 11 items carry `origin:beads-v1-1-2-upgrade`; only 4 were linked
as children of `bd-ib-3kolea`. **Three of the seven unlinked items are still
open**, including the attended rehearsal.
**Action taken:** `bd-ib-ao3j` linked as a parent-child child (rationale
recorded on the item first). The other two are deliberately left unlinked, with
reasons.
**Also:** corrects a factual error in the 2026-08-20 wind-down handoff.

## The measurement

Using the union of BOTH linkage mechanisms — the dotted-id hierarchy and the
explicit `parent-child` edge — which is what `undisposed_plan_child_ids` uses
and what AGENTS.md requires instead of a hand-rolled `bd list` filter:

```
items labelled origin:beads-v1-1-2-upgrade : 11
epic children (union of both linkages)     : 4
undisposed children (gates archive)        : 3   [.2, .3, .4]
```

Unlinked, with status:

| Item | Status | What |
|---|---|---|
| `bd-ib-ao3j` | **backlog** | Run the attended migration-and-restore rehearsal |
| `bd-ib-1w1h` | **acceptance** | `bd ready` returns an empty set while 18 items are ready |
| `bd-ib-4456` | **acceptance** | the ledger-survey command hides all closed items |
| `bd-ib-1rz6` | closed | guarded orchestrator-image layout |
| `bd-ib-8azd` | closed | prepare the rehearsal package |
| `bd-ib-bt1n` | closed | qualify v1.1.2 through the lifecycle guard |
| `bd-ib-ne11` | closed | qualify the release/CLI/JSON/migration surface |

## Why this matters

**`bd-ib-3kolea` could have been archived with its attended rehearsal still
open and unowned.** The archive gate refuses on undisposed *children*; verified
directly, `undisposed_plan_child_ids(bd-ib-3kolea)` returned exactly
`{.2, .3, .4}` and did not include `ao3j`.

The gate is behaving exactly as specified. **The defect is the missing linkage,
not the gate** — which is what makes this the dangerous shape: every individual
component is correct, and the composition still loses work. Nothing warns,
because a plan with all its *children* disposed looks complete.

Two of the three are in `acceptance`, which AGENTS.md specifically names as
where "shipped-but-unaccepted work hides".

## What was changed, and what was not

**`bd-ib-ao3j` is now linked** as a `parent-child` child of the epic. It is core
epic scope — the epic's own description names "backup and restore rehearsal"
among the work it covers. Verified before and after:

```
BEFORE undisposed: ['bd-ib-3kolea.2', '.3', '.4']          ao3j gates archive: False
AFTER  undisposed: ['bd-ib-3kolea.2', '.3', '.4', 'ao3j']  ao3j gates archive: True
```

The only behavioural change is that archive now refuses until the rehearsal is
disposed, which is **strictly more conservative** and the correct outcome. The
rationale was written to the item *before* the mutation, mirroring
`close_plan_child` / `reparent_plan_child`'s own discipline so a failed mutation
leaves explained intent rather than a silent structural change. The edge is
reversible.

Per AGENTS.md "Decision authority", this changes where work is TRACKED, not what
the specification REQUIRES, and is therefore session-performable.

**`bd-ib-1w1h` and `bd-ib-4456` are deliberately NOT linked.** They are general
repository defects this thread happened to *discover*; `origin:` records
provenance, not parenthood. Linking them would make this epic's archive wait on
work that is not its own. They are recorded here so they are not lost, and they
need an owner independent of this epic — both sit in `acceptance`, so what they
need is an acceptance decision, not implementation.

## A correction to the 2026-08-20 handoff

That wind-down entry states:

> Nothing was applied to ao3j or .4 - both are admission:manual and this session
> held no admission.

**That is factually wrong about `ao3j`.** Its label set, measured 2026-08-21, is
`acceptance:ai-only, admission:auto, factory-safety:needs-privileged-host,
intake:triaged, origin:beads-v1-1-2-upgrade`. It carries **`admission:auto`**.

So the stated reason for parking the 2026-08-20 rehearsal-hardening
recommendations on that item did not hold. Those recommendations are still
unapplied, but that is now a **scoping judgement for whoever runs the
rehearsal**, not an admission block. Verbatim from that handoff, they were:

- widen scope to the main source `0050-0053` **plus** ignored `0009-0011` and
  the `rekeyAuxRowIDs` pass they gate
- add a **cross-boundary data comparison** (v49 data beside v53 data) — no
  existing comparison in the package performs one
- add a **re-key completeness field** to the receipts, so a partial re-key FAILS
  rather than passes
- capture the log stream as evidence
- read the drift record rather than the exit code

They have been re-recorded on `ao3j` itself, which is where the rehearsal is
tracked, rather than left only in a plan handoff a rehearsal-runner would not
necessarily read.

## Generalisation worth carrying

`origin:<plan-slug>` and plan-epic parenthood are **different relations**, and
only the second is load-bearing for the archive gate. A thread that files work
without linking it accumulates exactly this gap, silently. Two cheap checks:

1. Before archiving any plan, diff `origin:<slug>` against the union child set
   and account for every difference — either link it or state why it is not a
   child.
2. At filing time, `capture-work-item` already accepts `plan_parent_id`; using
   it is what prevents the gap in the first place. Its prose is explicit that
   plan-child linkage is a parent-child relation and **not** a `depends_on`
   edge.

This note does not propose a mechanical check; the converse-gap tracking for
archive-rule enforcement already lives outside this repo in
`livespec-dev-tooling-5asgvm` / `livespec-dev-tooling-q3emww`, and this is a
data point for it rather than a new mechanism.
