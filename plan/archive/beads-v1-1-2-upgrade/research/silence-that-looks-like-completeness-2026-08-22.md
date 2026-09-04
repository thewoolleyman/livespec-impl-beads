# Silence that looks like completeness — five ways to close a question that was never answered

**Date:** 2026-08-22
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Contributors:** the `beads-v1-1-2-upgrade` session (instances 1 and 4), the
`livespec-orchestrator-beads-fabro-foreman` seat (instances 2 and 5, and the
positional remedy), and the `factory-host-storage-reclamation` session
(instance 3, and the sharpening of rule 2). Grouped at the foreman's direction
because three instances in one day is a pattern rather than an anecdote; two
more landed the same day, from two of the same seats.

Candidate for promotion into the family-universal agent-instruction core beside
the existing verification-discipline rules. It is recorded here first because
this is the thread that measured it. **That promotion is the maintainer's to
make and has been raised and not yet answered** — a peer asking for an edit to
the repo's operating-rules surface is not the right authority for it, which is
why this material lives in plan research rather than in `AGENTS.md`.

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

Five instances, all on 2026-08-22, all by experienced sessions applying
otherwise-good method. The first three were grouped together and are what made
the class visible; instances 4 and 5 arrived afterwards and extend it in a
direction the first three could not show — see "The mirror direction" below.

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

## Instance 4 — the assertion made true by the thing it forbade (measured, `beads-v1-1-2-upgrade`)

The one that belongs squarely in this class rather than beside it, and the
reason it is recorded *in* this note: it closed the question the note is about.

**The claim under test.** `bd-ib-2591` rewrote the O4 inventory-capture wrapper
so that every projection enumerating work items unions `wisps` with `issues` —
the load-bearing requirement of the item, because a rewrite that ships the
identical rig-blindness with more confidence is a regression in assurance. The
question the test existed to close was **"is the union actually implemented?"**

**The check.** A beside-test asserting that every `bd sql` invocation the
wrapper emits carries both `UNION ALL` and `wisps`, roughly:

```python
all("UNION ALL" in line and "wisps" in line for line in sql_calls)
```

**The result.** Green. 30/30. Read as: the union is in every query.

**Why it was worthless.** Every query also carried a leading
`/* … UNION ALL wisps … */` comment describing what it did — and a leading
comment is precisely what makes `bd sql` return `OK, 0 rows affected` with **no
result set at all**. So the substring the assertion matched was the *comment*,
not the SQL. **The check enforcing the union was satisfied by the very thing
that made the union unreachable.** Every SQL projection captured nothing, and
the test that existed to catch exactly that reported success.

Measured against a real isolated Dolt server (v1.2.2, pinned and checksum
verified, non-family port): three independent defects each prevented every SQL
projection from being captured, and all three are invisible to a shell stub
that returns canned JSON regardless of what it was asked. The corrected test
requires a real `UNION` in the work-item queries, requires `--csv`, **forbids a
leading comment**, and requires the per-issue calls to cover the rig row.

**Why it is this class and not merely a weak test.** A weak test that fails to
catch a bug leaves the bug findable. This one **answered the question**: "is the
union implemented" came back yes, with a green suite behind it, and nothing
downstream would have asked again. The mock-only proof could not have returned
the other answer, and it was the answer everyone wanted.

## Instance 5 — the hit that was a quotation (`livespec-orchestrator-beads-fabro-foreman`)

**The claim under test.** Whether a retracted phrase — "never reaped" — had
actually been removed from `bd-ib-bdcmok.7` after that item's corrections
landed.

**The check.** Probe the item's text for the phrase. It came back **present,
once**.

**What nearly happened.** A false correction filed against a correct item, on
the count alone.

**Why the hit meant the opposite of what it looked like.** The occurrence sits
inside the author's **retraction narrative**, quoting the claim being withdrawn,
with the corrected outcome recorded beside it. The seat caught it by reading the
surrounding text rather than concluding from the count, and reported it
voluntarily.

## The mirror direction, and the remedy that transfers

Instance 5 runs the opposite way to everything above it, which is why it earns a
place rather than a footnote. Instance 3 was a probe that **could not return a
hit**, reporting no hits. Instance 5 was a probe whose **hit was a quotation**.
The same audit question, asked twice within an hour by two seats:

> **A count is not a verdict in either direction. Absence does not establish
> that a claim is gone, and presence does not establish that it is asserted.**

**The actionable half is positional:**

> **DISCRIMINATE BY POSITION, NOT BY PRESENCE.**

For a tmux pane, key on the **tail region**: a live picker always renders its
selection footer last, while quoted markers sit in scrollback with ordinary
output after them. The text analogue is to **read the surrounding context**,
because a quotation sits inside prose that frames it. That turns "read around
the match" from instinct into design.

**And this is why the family recurs: the false positive is produced by GOOD
BEHAVIOUR.** The sessions most likely to quote a marker, a retracted claim or a
delimiter verbatim are the **careful** ones — the ones documenting precisely
what they withdrew and why, or proving a picker resolved by naming its markers.
A naive scan punishes exactly the discipline this catalogue is asking for.

### The caveat — same family, different subject

`overseer-i6eu2k` (repo `livespec-overseer`, `pending-approval`) is the same
family **in shipped code**: the daemon reports `picker_open` TRUE for a pane
that merely quoted picker markers while describing a peer's parked state, making
a healthy session unreachable under the foreman's own no-`SendMessage`-to-a-picker
rule. It is a **defect with load-bearing consequences and a code fix with
beside-tests**.

Instance 5 and its sibling probe lapse are **ad-hoc commands run by hand, caught
before they did anything, with no code to fix**. Cite `overseer-i6eu2k` as the
family reference; **do not fold these into it.** Widening a well-scoped code
defect with something that has no code in it would be an instance of matching on
shared vocabulary across two different systems — the false-prior-art error this
note already documents as instance 2. The foreman has told the reporting session
not to fold their instance into that item, and made the same discrimination
against their own interest in the flattering version.

### A fourth independent derivation of rule 2, from a seat none of us contacted

`overseer-i6eu2k`'s authored acceptance criteria, clause 2, requires a
three-way discriminating control and singles out leg **(a)** — *a capture whose
tail IS a live picker → `picker_open` TRUE* — with the note that it "is the one
an implementer will be tempted to skip, and without it the change cannot be
distinguished from simply weakening the detector until nothing matches. A
detector that never fires reports no pickers exactly as a correct one reports no
pickers when there are none."

That is rule 2 of this note — a dismissal needs a positive control — derived
independently, on a different system, by the **grooming drain pass**, a seat
none of the contributors here contacted. Its own parenthetical says it was
written "on the general rule this pass has been recording all night".

**Four derivations from four different failures, in one day, by four seats
working separately, makes this a property of the system rather than a lesson any
one of us learned.**

## Why the grouping is the point

This section is about instances 1 to 3, which are what made the class visible;
instances 4 and 5 are placed above because the mirror direction only makes sense
once the class is stated.

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
that says so.** So does instance 4, by the same mechanism on a green test suite;
instance 5 would have converted a *settled* question back into an open one, which
is the cheaper failure and the reason it was caught. A "disproved" defect, an "already-tracked" gap and a "confirmed"
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
5. **Discriminate by position, not by presence — in both directions.** A count
   settles nothing on its own: absence does not establish that a claim is gone
   (instance 3), and presence does not establish that it is asserted
   (instance 5). Key on where the match sits — the tail region of a pane, the
   prose around a quotation — and remember that the strings most likely to trip
   a naive scan are written by the most careful sessions.
6. **A check can be satisfied by the thing it forbids.** Instance 4's assertion
   matched the comment that broke the query. Before trusting a green check, ask
   what *else* in the artifact could make it pass, and prove the check fails
   when the behaviour is removed — the same positive-control discipline as
   rule 2, applied to an assertion rather than to a dismissal.
7. **Say who disagreed.** Instance 2 was recovered only because the session ruled
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

Instance 4 is measured by this thread and its full detail is in the commit
message of the `bd-ib-2591` review fix (PR #1750) and in the corrected
`tests/test_beads_v112_rehearsal_package.py`; the three underlying `bd sql`
defects were isolated against a real isolated Dolt server.

Instance 5 is reported by the `livespec-orchestrator-beads-fabro-foreman` seat
and recorded with its ledger carrier (`bd-ib-bdcmok.7`, trap 4) so it can be
verified independently. The positional remedy, the good-behaviour observation
and the do-not-fold caveat are theirs, quoted here with attribution rather than
restated as this note's own. The fourth-derivation citation is to
`overseer-i6eu2k` in the `livespec-overseer` tenant, acceptance clause 2 leg
(a), authored by the grooming drain pass.
