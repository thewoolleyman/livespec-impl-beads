# Silence that looks like completeness — the false refutation and the false prior-art hit

**Date:** 2026-08-22
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Authors:** the `beads-v1-1-2-upgrade` session (instance 1) and the
`livespec-orchestrator-beads-fabro-foreman` seat (instance 2), paired at the
foreman's direction because two instances in one day is a pattern rather than an
anecdote.

Candidate for promotion into the family-universal agent-instruction core beside
the existing verification-discipline rules. It is recorded here first because
this is the thread that measured it.

## The class

Every entry already in this repo's catalogue describes a check that returns a
**wrong answer**. This one describes something worse and rarer: a check that
returns an answer which **closes the question**.

> **A false negative that is acted on as settled produces silence that looks
> like completeness.**

The distinguishing property is not the error rate. It is that **nothing
downstream ever re-tests it.** A false *finding* gets contradicted by the next
person who looks — the defect is filed, someone reads it, the record self-repairs.
A false *dismissal* removes the reason for anyone to look again. The question
stops being asked, and the absence of further reports reads as confirmation.

Two instances, both on 2026-08-22, both by experienced sessions applying
otherwise-good method.

## Instance 1 — the false refutation (measured, `beads-v1-1-2-upgrade`)

**The claim under test.** A colleague's route proof reported that
`bd list --json` is blind to `rig`-typed rows: a four-record fixture import
produced four stored issues and the listing returned three.

**The test.** Inject a `rig` row, then compare the two read surfaces.

**The result.** Both surfaces returned the row. Clean measurement, no error, exit
0. The honest reading was *"rig-blindness does not reproduce"* — a **refutation of
a colleague's real finding**, with data behind it.

**Why it was wrong.** The row was injected into `issues`. `rig` records live in
the separate `wisps` table. The test had put the row **where the blind surface
already looks**, so it could not have reproduced the reported condition — and an
instrument that cannot reproduce the condition cannot refute it either.

**The discriminator, which generalises.** The question was never *what did the
surfaces return*. It was **did my test reproduce the reported condition**. And the
tell was available *before* the measurement, in the original report itself: it
said `show <id>` retrieves a row the listing omits. A row retrievable by id but
absent from the listing **must** sit somewhere the listing does not read. That
single sentence determines where the fixture has to go, and reasoning from it
would have caught this before any data was collected.

## Instance 2 — the false prior-art hit (`livespec-orchestrator-beads-fabro-foreman`)

**The claim under test.** A colleague reported a gap in dispatch failover.

**The ruling.** Duplicate of three existing items, on the shared words
"failover" and "standby host".

**Why it was wrong.** Those three items were about database **replication**; the
reported gap was about the **build lane**. The seat's own output said "Dolt
REPLICATION" three times and it read past it.

**How it was caught.** Not by the seat. The session that had been ruled against
came back with evidence. Filed correctly as `dolt-server-4i7qos`.

## Why the pairing is the point

The two look unrelated — one is a measurement, one is a triage ruling. They are
the same failure with different surface features, and neither instance alone makes
the class visible:

| | Instance 1 | Instance 2 |
|---|---|---|
| Surface | measurement | triage ruling |
| Matched on | the right *values*, in the wrong *place* | the right *words*, about the wrong *subject* |
| Output | clean data, no error | confident ruling, no error |
| Effect | defect declared disproved | gap declared already-tracked |
| Who re-checks | **nobody** | **nobody** |

**Both convert an open question into a closed one, and neither leaves a trace that
says so.** A "disproved" defect and an "already-tracked" gap are both, from every
later reader's point of view, *handled*.

The two formulations are duals and are worth carrying together, because which one
lands depends on the seat you are sitting in:

> **False refutations are worse than false findings, because nobody re-checks a
> defect that has been disproved.**
>
> **A false prior-art hit is worse than a missing one, because nobody re-opens a
> gap that has been declared already-tracked.**

## What to do about it

The existing rules are necessary and insufficient here. "State the scope you
searched" does not help when the scope was right and the *aim* was wrong;
instance 1 searched exactly the right database. The additional questions:

1. **Before dismissing, ask what the report says that your test must satisfy.**
   Not "what does my test return" but "does my setup recreate the reported
   condition". Read the original report for a constraint your reproduction has to
   meet — instance 1's was sitting in plain sight.
2. **A dismissal needs a positive control, exactly like a finding does.** If you
   are about to conclude "does not reproduce", first make the thing reproduce
   *somehow* — by any means, even an artificial one. If you cannot produce a
   single instance of the reported behaviour, you have not refuted it; you have
   failed to build the instrument.
3. **When matching on words, verify the subject.** Shared vocabulary between two
   items is a hypothesis about sameness, not evidence of it. Name the subject of
   each and check they are the same thing.
4. **Weight the asymmetry when uncertain.** A wrongly-filed duplicate costs one
   person a few minutes. A wrongly-dismissed real gap costs however long it takes
   for the same problem to be rediscovered from scratch — if it ever is. When a
   dismissal and a filing are close to evenly balanced, **file.**
5. **Say who disagreed.** Instance 2 was recovered only because the session ruled
   against pushed back with evidence. A dismissal that draws an objection should
   be re-opened on the objection, not defended — the objector is the only
   re-testing mechanism this class has.

## Provenance note

Instance 1 is measured and its full detail is in
`rig-blindness-mechanism-2026-08-22.md`. Instance 2 is reported by the foreman
seat and is recorded here as reported, with its ledger id
(`dolt-server-4i7qos`) so it can be verified independently rather than taken on
this note's authority.
