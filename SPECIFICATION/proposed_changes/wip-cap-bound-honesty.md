---
topic: wip-cap-bound-honesty
author: claude-opus-5
created_at: 2026-08-22T04:54:14Z
---

## Proposal: The wip_cap bound must describe counted claims, and must not read as absolute

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Replaces the false clause "the Dispatcher MUST NOT drive more than `wip_cap`
items into the `active` state at once" with an accurate statement of the bound:
`wip_cap` bounds COUNTED CLAIMS — rows holding a live local dispatch lock plus
rows whose journal could not be read — not rows at status `active`, and it binds
the automatic drain while the hand-picked `dispatch --item` operator path
sanctions an over-cap admission. Records the fail-closed direction of the
journal-unreadable term, reconciles the whole clause with §"Host concurrency
belongs to the Fabro scheduler" so it cannot be read as licensing host
observation, and adds two Gherkin scenarios. SUBSUMES `bd-ib-aabn`, with
reasons.

### Motivation

`SPECIFICATION/contracts.md` §"Per-repo WIP cap" states:

    The Dispatcher MUST NOT drive more than `wip_cap` items into the `active`
    state at once.

That sentence is knowingly false as written, in TWO independent ways. Both were
measured on 2026-08-22, and both are in the same sentence — which is why this
proposal rewrites it once rather than patching it twice.

FALSEHOOD 1 — the sentence names the wrong QUANTITY. "At status `active`" and
"counted against the cap" are different sets. Measured 2026-08-22: the
`livespec-overseer` tenant held THIRTEEN rows at status `active` while
`active_count` read 10 — a three-row gap of rows in neither counted branch. The
same asymmetry was measured again the same day in this repo's own tenant, in the
opposite direction: SIX rows at status `active` with an `active_count` of ONE,
five of them uncounted (recorded in
`plan/wip-cap-accounting-honesty/research/uncounted-active-rows-measured-2026-08-22.md`).
Nothing in the spec, the configuration, or any operator surface says the two sets
differ. Three separate sessions reasoned from the non-existent bound on
2026-08-22.

FALSEHOOD 2 — the sentence reads as ABSOLUTE, and it is not. The automatic drain
enforces the cap; the hand-picked operator path `dispatcher.py dispatch --item`
passes `enforce_cap=False` and admits over the cap by design. A consumer reading
the current clause would conclude the cap is absolute and could build a UI or an
assertion treating an over-cap targeted dispatch as a bug, when it is sanctioned
behavior. This is the gap owned by `bd-ib-aabn`, filed on the maintainer's
explicit 2026-07-30 instruction, under that day's ruling that THE CODE IS CORRECT
and the contract is incomplete.

WHAT THE COUNTER ACTUALLY COUNTS, re-verified in source immediately before
authoring (at `HEAD` = 3de4dd4a, predicate introduced by PR #1718 / f41f4578,
`commands/_dispatcher_claim_reclaim.py`):

    active_count = len(live_lock_active_ids) + len(journal_unreadable_active_ids)

So a row counts when it holds a dispatch lock whose recorded pid — the LOCAL
DISPATCHING process's own — is still alive, or when its journal could not be READ
at all. Green-terminal rows are identified and reported but DELIBERATELY NOT
counted, having been reclaimed. The journal-unreadable term is a deliberate
FAIL-CLOSED choice: an unreadable journal makes the predicate count MORE, never
fewer, so a lost journal cannot silently over-admit.

WHY THIS IS NOT A CODE-DEFECT REPORT. The implementation is defensible on both
axes and the maintainer has already ruled so on the second. What is wrong is that
the ratified sentence describes a quantity nobody enforces. The remedy is to make
the specification state what is actually bounded.

### Proposed Changes

### Why this subsumes `bd-ib-aabn`, stated first because the item requires the decision

`bd-ib-aabn` owns the second falsehood above. This proposal ABSORBS it, deliberately
rather than by default. The reason is that both defects live in the SAME SENTENCE,
and rewriting that sentence for the quantity alone would leave it freshly ratified
and still wrong about the override — a worse outcome than today, because a
just-revised clause reads as authoritative and stops being questioned. A single
correct sentence is achievable now; two sequential half-corrections are not.

`bd-ib-aabn`'s own text forbids folding it into epic `bd-ib-vmve`; it says nothing
against this, and the 2026-07-30 ruling it carries (the code is correct, the
contract is incomplete) is ADOPTED here unchanged rather than re-litigated. Its
required paired scenario is carried below. On acceptance of this proposal
`bd-ib-aabn` SHOULD be closed as absorbed, citing this topic; that closure is
ledger housekeeping for its owner and is NOT performed by this proposal.

SCOPE FENCE — this proposal does NOT resolve `bd-ib-snyquw.3`. That item is that
the `enforce_cap=False` override is UNREACHABLE from `drive`, the sanctioned
operator surface. Documenting that the override EXISTS does not make it reachable,
and `.3` remains gated on its own unrun control. Do not read this as closing it.

### Amend §"Per-repo WIP cap" — replace the bound sentence

REMOVE:

> The Dispatcher MUST NOT drive more than `wip_cap` items into the `active`
> state at once.

REPLACE WITH:

`wip_cap` bounds COUNTED CLAIMS, which is NOT the same set as rows at status
`active`. A row at status `active` counts against `wip_cap` when, and only when,
either of the following holds:

1. it holds a dispatch lock whose recorded process identifier — that of the LOCAL
   dispatching process — belongs to a live process; or
2. its dispatch journal could not be READ.

A row at status `active` that satisfies neither MUST NOT be counted. In
particular, a row whose dispatch reached a green terminal outcome is reclaimed and
MUST NOT be counted, so a repository MAY hold more rows at status `active` than
`wip_cap` without any admission having exceeded the bound. Every surface that
reports capacity MUST NOT present "rows at status `active`" as if it were the
counted quantity.

Term 2 is FAIL-CLOSED BY DESIGN and MUST remain so: an unreadable journal MUST
cause the predicate to count MORE rows, never fewer, so that losing the journal
cannot silently over-admit. A change making an unreadable journal reduce the count
MUST NOT land without a propose-change explicitly retiring this clause.

The bound governs the Dispatcher's AUTOMATIC admission path — the drain, and any
targeted invocation that enforces the cap. It is NOT absolute. The hand-picked
operator path (`dispatch --item`) is a sanctioned override that admits a single
named work-item WITHOUT enforcing `wip_cap`; this is intended behavior, not a
defect, per the 2026-07-30 maintainer ruling. A consumer of this contract MUST NOT
treat an over-cap admission arising from that override as a violation of this
section, and any surface asserting cap conformance MUST scope its assertion to the
enforcing paths.

### Amend §"Host concurrency belongs to the Fabro scheduler" — reconciliation

Append:

The counted-claim definition in §"Per-repo WIP cap" is computed ENTIRELY FROM
LOCAL STATE — this repository's own ledger rows, its dispatch locks, and its own
journal. It MUST NOT be read as licensing any host observation. In particular, the
fact that a row can stop being counted while its remote Fabro run continues to
execute is a KNOWN and ACCEPTED consequence of that locality, not a defect to be
corrected by teaching the counter about remote run liveness. Correcting it would
require host observation, which this section forbids; any such change MUST NOT
land without a propose-change explicitly retiring this clause.

### Add two scenarios to `SPECIFICATION/scenarios.md`

NUMBERING NOTE for the accepting revise pass: the pending proposal
`wip-cap-naming-collision` also adds a scenario and claims `57`. The numbers below
assume it is accepted FIRST. If the acceptance order differs, the accepting revise
pass MUST renumber these to the next free integers rather than duplicating one.

```gherkin
## Scenario 58 — Rows at status active are not the counted quantity

Feature: The per-repo WIP cap bounds counted claims, not rows at status active
  As a Dispatcher
  I want uncounted active rows to leave capacity available
  So that finished-but-unadvanced bookkeeping cannot strand a repository

Scenario: A repo holding more active rows than wip_cap still admits a ready item
  Given a per-repo wip_cap of 2
  And three work-items at status `active`
  And exactly one of them holds a dispatch lock whose recorded pid is live
  And the other two reached a green terminal outcome and were reclaimed
  And every dispatch journal is readable
  When the Dispatcher evaluates admission for an admission-eligible ready item
  Then the counted claim total is 1
  And the ready item is admitted
  And no admission has exceeded the per-repo WIP cap

## Scenario 59 — The hand-picked operator override admits over the cap

Feature: The per-repo WIP cap binds the enforcing paths, not the operator override
  As an operator
  I want a hand-picked dispatch to proceed when I have named one work-item
  So that a saturated cap cannot block a deliberate single dispatch

Scenario: A targeted dispatch is admitted at the cap while an unattended drain admits nothing
  Given a per-repo wip_cap that is already met by counted claims
  And an admission-eligible ready work-item
  When an unattended drain evaluates admission
  Then no work-item is admitted
  And the refusal reports a capacity deferral
  When the operator instead dispatches that same work-item by name through the non-enforcing path
  Then that work-item is admitted
  And the admission is not reported as a violation of the per-repo WIP cap
```

### Co-edit required at revise time

The accepting revise pass MUST add one `tests/heading-coverage.json` entry per new
`## Scenario` H2 in `scenarios.md`, per this repo's revise co-edit discipline. The
`test` value MAY be the literal `"TODO"` with a non-empty `reason`.

### What this proposal deliberately does NOT do

It does NOT change what is counted, does NOT propose teaching the counter about
remote run liveness, does NOT alter the `0` dispatch-off value or its
minimum-above-zero guard clause, and does NOT make the operator override reachable
from `drive`. It makes the specification describe the bound that is actually
enforced.

### Reconciliation with the sibling pending proposal (added 2026-08-22)

`wip-cap-naming-collision` is pending against the SAME section and must be
reconciled with this one at revise time. Surfaced by the post-step objective
doctor phase; recorded here because the revise pass reads these files and MAY
process them independently via `--only-topic`.

THE TENSION. That proposal mandates the label "per-repo LEDGER cap" as the
disambiguator against the Fabro scheduler's host limit. This proposal establishes
that `wip_cap` bounds COUNTED CLAIMS and explicitly NOT rows at ledger status
`active`. "Ledger cap" therefore invites exactly the reading this proposal
removes. The word "ledger" is doing SCOPE work there, not COUNTING work, but the
label does not say so.

RESOLUTION THE ACCEPTING REVISE PASS MUST MAKE. Adopt one disambiguating label
across BOTH proposals — "per-repo CLAIM cap" is recommended, preserving the scope
contrast while naming the counted quantity correctly — and let this proposal's
counted-claims definition govern what it means. Accepting either proposal WITHOUT
settling the label MUST NOT happen: a half-adopted vocabulary is worse than
today's, because both clauses would read as freshly ratified.

The two appends to §"Host concurrency belongs to the Fabro scheduler" are
complementary and both SHOULD be taken. The scenario-numbering note above still
applies.

### The locality clause does not say WHICH local state, and it matters (added 2026-08-22)

Recorded here rather than only on `bd-ib-snyquw.5` for the same reason as the
section above: the revise pass reads these files, and a rider on a ledger item is
not something a pass over `proposed_changes/` will see.

THE PROBLEM, in this proposal's own text. The append to §"Host concurrency
belongs to the Fabro scheduler" says the counted-claim definition is computed
"ENTIRELY FROM LOCAL STATE — this repository's own ledger rows, its dispatch
locks, and its own journal". "This repository's own" is ambiguous between the
TENANT and the CHECKOUT. Every other clause in the section is tenant-scoped, so a
reader resolves it to the tenant. MEASURED, IT IS THE CHECKOUT.

THE MEASUREMENT, 2026-08-22, both readings taken in the same second from
`claimed_active_accounting` itself rather than a hand-rolled predicate, against
journal COPIES so neither real journal was mutated. ONE ledger, 11 rows at status
`active`:

    /data/projects/livespec-orchestrator-beads-fabro   active_count 2
        live_lock_active_ids (bd-ib-2os2, bd-ib-62xaj3)
    ~/.worktrees/.../control-wip-cap-enforce-asymmetry  active_count 1
        live_lock_active_ids (bd-ib-y4az3g,)

DISJOINT. Neither checkout sees the other's claims. The mechanism is that both
counting inputs resolve from the `--repo` path: the dispatch-lock directory, and
`<repo>/tmp/fabro-dispatch-journal.jsonl` (`commands/_dispatcher_paths.py`). A
second checkout starts with an empty lock directory and its own journal, so every
claim held by the first is invisible to it. N checkouts of one tenant admit up to
N x `wip_cap`. Worktrees, janitor checkouts and fresh clones are all normal here,
so this is a reachable configuration and not a contrived one.

THE SEPARABILITY POINT, which is what keeps this from being a false dilemma. The
clause conflates two different things: "no HOST observation" and "per-CHECKOUT
bookkeeping". They are independent. The tenant's ledger rows are SHARED and
readable from any checkout — counting a tenant's claims across its checkouts
requires no host observation whatsoever, only bookkeeping that is not
checkout-local. Ratifying the sentence as written would fuse the two, so a later
attempt to make the count tenant-wide would appear to be barred by the
host-observation prohibition when it is not.

WHY THE ANSWER IS NOT OBVIOUS, stated honestly because this proposal exists to
stop the spec asserting convenient things. Per the 2026-07-30 ruling recorded on
`bd-ib-aabn`, the cap exists to bound same-repo merge/rebase contention during
unattended draining. Merge contention is a property of the TENANT — every
checkout pushes to the same `origin/master` — so a checkout-scoped bound does not
constrain the thing the cap was created to constrain. That argues for stating the
requirement tenant-scoped. BUT this proposal's governing principle is that the
spec must describe what is ACTUALLY bounded, and tenant-scoped is not what the
code does today. Choosing the requirement over the description here is in real
tension with this proposal's own thesis, and the revise pass should make that
trade deliberately rather than inherit it from an ambiguous sentence.

RESOLUTION THE ACCEPTING REVISE PASS MUST MAKE. Settle the scope explicitly —
do not accept "this repository's own" as drafted. Either:

  (a) State the bound as TENANT-scoped (all checkouts of this repository), keep
      the host-observation prohibition, and record the current checkout-scoped
      implementation as a known divergence to be filed as a defect. RECOMMENDED,
      because ratifying (b) blesses a bound that provably fails to constrain the
      contention the cap exists for; and

  (b) State the bound as CHECKOUT-scoped and say so in those words, spelling out
      the consequence — that N checkouts admit up to N x `wip_cap` — so a
      consumer cannot read a tenant-wide guarantee into it.

Whichever is chosen, the phrase "this repository's own" MUST NOT survive
unqualified, and the sentence MUST NOT be left implying that tenant-wide counting
would require host observation.

NOT IN SCOPE OF THIS NOTE, so it does not silently widen the proposal: this is a
DIFFERENT axis from the fail-open that the green-terminal reclamation closed.
That guarantee — an UNREADABLE journal counts MORE, never fewer — is intact and
must stay intact. This is a legitimately EMPTY lock directory on another path, so
the fail-closed branch never fires and the count simply starts at zero.

### Renumbering hazard and the paste-ready co-edits (added 2026-08-22)

Mechanical corrections to the NUMBERING NOTE and the co-edit instruction above,
measured against `SPECIFICATION/scenarios.md` and `tests/heading-coverage.json` at
master 2026-08-22. Neither changes what this proposal asks the specification to say.

"THE NEXT FREE INTEGERS" IS AMBIGUOUS AND ONE READING IS WRONG. The numbering note
says that if the acceptance order differs, the pass MUST "renumber these to the next
free integers rather than duplicating one". Measured: `scenarios.md` holds 53
scenarios numbered 1..56, and **2, 3 and 49 are RETIRED** — absent while every
number around them is present. Those three are "free" by the literal wording and
MUST NOT be reused: a retired number is referenced by history and by prior
revisions, so re-issuing one silently aliases a new behavior onto an old citation.
Renumber by appending ABOVE the current maximum (56 today), never into a gap.
Verify that maximum at revise time rather than trusting this number.

AS OF THIS WRITING NO RENUMBERING IS NEEDED. 57, 58 and 59 are all unused, so this
proposal's `58` and `59` are correct as drafted provided `wip-cap-naming-collision`
is accepted first, as the note above assumes.

THE CO-EDITS, PASTE-READY. Both required `tests/heading-coverage.json` entries,
matching the shape of the 95 entries already in that file (note the em dash in
`heading`, U+2014, which must match each H2 byte-for-byte):

```json
{
  "heading": "## Scenario 58 — Rows at status active are not the counted quantity",
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "test": "TODO",
  "reason": "Ratified with the wip-cap-bound-honesty revision; wip_cap bounds counted claims, not rows at status active. Real test ID to follow."
},
{
  "heading": "## Scenario 59 — The hand-picked operator override admits over the cap",
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "test": "TODO",
  "reason": "Ratified with the wip-cap-bound-honesty revision; the hand-picked dispatch --item override is sanctioned and may exceed the cap. Real test ID to follow."
}
```

If the shared label is changed when the pass settles the vocabulary, a scenario
title MAY change with it — in which case the matching `heading` value MUST be
updated too, or the heading-coverage check fails on a near-miss string.
