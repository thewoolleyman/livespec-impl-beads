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
