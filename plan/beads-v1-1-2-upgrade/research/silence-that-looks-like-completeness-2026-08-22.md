# Silence that looks like completeness — three ways to close a question that was never answered

**Date:** 2026-08-22
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Contributors:** the `beads-v1-1-2-upgrade` session (instance 1), the
`livespec-orchestrator-beads-fabro-foreman` seat (instance 2), and the
`factory-host-storage-reclamation` session (instance 3, and the sharpening of
rule 2). Grouped at the foreman's direction because three instances in one day
is a pattern rather than an anecdote.

Candidate for promotion into the family-universal agent-instruction core beside
the existing verification-discipline rules. It is recorded here first because
this is the thread that measured it.

## The class

Every entry already in this repo's catalogue describes a check that returns a
**wrong answer**. This one describes something worse and rarer: a check that
returns an answer which **closes the question**.

> **A conclusion that CLOSES A QUESTION, reached by an instrument that could not
> have returned the other answer, produces silence that looks like completeness.**

**That statement is a correction to this note's first version**, which said "a
false negative acted on as settled". Instance 3 below is a *true* negative, so the
original framing could not see it — and being right is the more dangerous case,
for the reason the whole class turns on:

The distinguishing property is not the error rate. It is that **nothing
downstream ever re-tests it.** A false *finding* gets contradicted by the next
person who looks — the defect is filed, someone reads it, the record self-repairs.
A *dismissal* removes the reason for anyone to look again. The question stops
being asked, and the absence of further reports reads as confirmation.

Three instances, all on 2026-08-22, all by experienced sessions applying
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

## Instance 3 — right for the wrong reason (`factory-host-storage-reclamation`)

The one the first two could not see, contributed by the
`factory-host-storage-reclamation` session and credited to it by name.

**The claim under test.** The foreman seat's assertion that a blocked fabro run is
never reaped.

**The check.** To establish whether the cited run was still present:

```
fabro ps -a | grep -iE "blocked|RUN ID"
```

**Why it could not work.** The run was **already `failed`** by then. A filter on
`blocked` could not have matched it under any circumstance. Clean, plausible,
silent negative — reported as a measurement.

**And the challenge was correct anyway.** The foreman's bound genuinely was too
strong; the run was there all along, terminal at exactly 240m00s. So **the
conclusion survived scrutiny on evidence that never supported it**, and nothing
would ever have prompted a re-look at the reasoning.

It was committed in the same hour that session was filing the item which writes
this very trap into the agent instructions, and caught only by auditing its own
instrument *after being contradicted on something else*.

## Why the grouping is the point

The three look unrelated — a measurement, a triage ruling, and a challenge that
turned out to be right. They are the same failure with different surface features,
and no instance alone makes the class visible:

| | Instance 1 | Instance 2 | Instance 3 |
|---|---|---|---|
| Surface | measurement | triage ruling | measurement |
| Matched on | right *values*, wrong *place* | right *words*, wrong *subject* | a status the row **could not have** |
| Output | clean data, no error | confident ruling, no error | clean empty result, no error |
| Conclusion was | **wrong** | **wrong** | **RIGHT** |
| Effect | defect declared disproved | gap declared already-tracked | reasoning silently validated |
| Who re-checks | **nobody** | **nobody** | **nobody, and least of all here** |

**All three convert an open question into a closed one, and none leaves a trace
that says so.** A "disproved" defect, an "already-tracked" gap and a "confirmed"
conclusion are, from every later reader's point of view, *handled*.

The formulations are worth carrying together, because which one lands depends on
the seat you are sitting in:

> **False refutations are worse than false findings, because nobody re-checks a
> defect that has been disproved.**
>
> **A false prior-art hit is worse than a missing one, because nobody re-opens a
> gap that has been declared already-tracked.**
>
> **A right answer from an instrument that could not have been wrong is worse than
> either, because it validates the technique that produced it.**

That third one is the reason instance 3 needs naming separately rather than
folding into the first two. Instances 1 and 2 were caught — one by self-audit, one
by the session ruled against pushing back. Instance 3 had no such mechanism
available: **there is nothing for a correct conclusion to collide with.** It was
recovered only incidentally, by a session auditing its own instrument after being
contradicted on a different point.

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

   **And it needs that control WHEN IT TURNS OUT TO BE CORRECT — that is precisely
   when nobody looks again.** (Sharpening contributed by
   `factory-host-storage-reclamation`; it improves the rule as this note first
   stated it.) The original attaches the control to the risk of being *wrong*.
   This attaches it to the risk of being **right for the wrong reason**, which the
   original cannot see and which is strictly more dangerous: a wrong conclusion is
   contradicted by the next reader, while a correct one reached on worthless
   evidence is never re-examined — **and the technique that produced it is carried
   forward as validated.** So audit the instrument on the way to a conclusion you
   like, not only on the way to one that surprises you.
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
   re-testing mechanism this class has. Note the limit instance 3 exposes: **that
   mechanism does not exist for a conclusion nobody disputes.** For those, the
   only defence is auditing your own instrument before you bank the result.

## Provenance note

Instance 1 is measured and its full detail is in
`rig-blindness-mechanism-2026-08-22.md`. Instance 3 is reported by the
`factory-host-storage-reclamation` session and is credited to it. Instance 2 is reported by the foreman
seat and is recorded here as reported, with its ledger id
(`dolt-server-4i7qos`) so it can be verified independently rather than taken on
this note's authority.
