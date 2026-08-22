# The third population: rows at `active` that are UNCOUNTED — measured 2026-08-22

## Why this note exists

The thread's founding research note establishes that `wip_cap` counts through
exactly two branches, and records a residual it did not resolve: an
`active_count` of 10 against **thirteen** rows at status `active`, "a three-row
gap [of] rows in neither branch."

This note measures that third population directly, in this repository's own
tenant, using the instrument `bd-ib-snyquw.1` shipped hours earlier. It matters
because the gap is not a rounding error — **it was the majority of this tenant's
`active` rows at measurement time** — and because the population contains at
least one row that looks exactly like a green-terminal slot holder and is not
one.

## Notation

- **Counted / uncounted** — whether a row at status `active` contributes to
  `active_count`. As the founding note establishes, these are different sets.
- **Branch 1 / Branch 2** — live local dispatch lock / green-terminal journal
  outcome, the two `count += 1` sites.
- **Third population** — a row at status `active` in NEITHER branch. The
  counter walks past it and journals a `dispatch-claim-abandoned` record.

## The measurement

Taken 2026-08-22, this repo's tenant, via `claimed_active_accounting` — the
function PR #1706 introduced — against the dispatcher's own default journal
(`<repo>/tmp/fabro-dispatch-journal.jsonl`, confirmed as the default in
`commands/_dispatcher_paths.py:64-67`, so the instrument is aimed at the file
the Dispatcher itself reads and not at a lookalike):

| Quantity | Value |
|---|---|
| `active_count` | **1** |
| `live_lock_active_ids` (Branch 1) | `bd-ib-9ek4` |
| `green_terminal_active_ids` (Branch 2) | **empty** |
| Rows at status `active` | **6** |
| At `active` but UNCOUNTED | **5** — `bd-ib-bx7swg`, `bd-ib-w4h4`, `bd-ib-ydjf7k`, `bd-ib-zg5ndm`, `bd-ib-zp3u7y` |

So in this tenant, at this moment, **five of six rows at `active` hold no WIP
slot at all**, and the single counted slot is a live local lock. The founding
note's three-row residual is not an anomaly of the overseer tenant; it is the
ordinary case here.

## The trap this population sets, which is the point of the note

`bd-ib-bx7swg` ("Surface Dispatcher capacity-deferred dispatch results") presents
**every outward sign of a permanently-counted green-terminal row**:

- ledger status `active`, assignee `fabro`, last updated 2026-08-17;
- its work demonstrably shipped — PR #1460 merged 2026-08-16T21:56:09Z;
- no live Fabro run anywhere (checked against `hp` explicitly, per the
  wrong-server trap in `AGENTS.md`);
- six days parked.

That is the exact signature Finding 2 describes, and the reasonable inference —
which this session drew and states here so a successor does not draw it again —
is that it has been silently consuming a slot since 2026-08-16.

**It has not.** It is uncounted. The journal carries repeated
`dispatch-claim-abandoned` records for it (measured: 171 journal lines mention
the id; the tail is a long run of abandoned-claim records), which is the counter
walking past it on every pass and saying so. `_claim_still_counts` returns
`False` for it, so it falls to the abandoned branch and contributes nothing.

The discriminator is NOT any property visible on the ledger row. Status,
assignee, staleness, and even a merged pull request are all consistent with both
outcomes. Only the journal separates them — which is precisely why `.1`'s
`green_terminal_active_ids` split is the load-bearing surface and an operator's
eyeball is not.

## What this does and does not establish

**Does:** the third population is real, is measurable with the shipped
instrument, and is large. A row parked at `active` with a merged PR is
**not** evidence of slot loss.

**Does not:** it does not weaken R3. Green-terminal occupancy was measured
directly in the `livespec-overseer` tenant — two rows, 110 minutes, released by
advancing them with the admission control re-run — and that measurement stands.
This note establishes that R3's signature cannot be recognised from the ledger
alone, not that R3 is rare.

**A limit stated so it is not over-read:** this is one tenant at one moment.
The five uncounted rows are uncounted *because of their journal history in this
repo's journal file*. A different tenant, or this tenant after a journal
rotation, could classify the same-looking rows differently — the journal is the
state, and it is local, mutable, and not the ledger.

## Consequence for `bd-ib-snyquw.2`

`.2` owns the bound/surface/reclaim decision for green-terminal occupancy. Two
riders on that item already narrow it to bound-or-reclaim, `.1` having delivered
surface. This note adds a third constraint that bears directly on **reclaim**:

A reclaim remedy MUST NOT key on the signature this note falsifies. "Row at
`active` + merged PR + no live run + stale" selects all five uncounted rows here
and would reclaim slots that were never held — a no-op that reads as a fix, and
which would then be reported as having freed capacity it did not free. Any
reclaim must key on the same journal evidence the counter itself uses, or it is
measuring a different population than the one that costs dispatches.

## Overlap with `bd-ib-bx7swg`, stated because `.1` required it

`.1`'s acceptance criterion 4 required reading `bd-ib-bx7swg` first and stating
the overlap. The dispatched run recorded no such attestation (its only comment
is the dispatch-factory marker), so it is stated here on evidence:

- **PR #1460** (`bd-ib-bx7swg`) introduced the `capacity-deferred` outcome status
  and the detail line `capacity deferred: active_count=… wip_cap=… free_slots=…`.
  It made the refusal **emit at all**.
- **PR #1706** (`bd-ib-snyquw.1`) left that line byte-intact and appended
  `live_lock_active_ids=…`, `green_terminal_active_ids=…` and `advance_rows=…`.
  It made the refusal **diagnostic**.

Strictly additive; no duplicated work. The criterion's substance holds even
though its attestation was never recorded on the item.

## Provenance

Measured by session `wip-cap-accounting-honesty` on 2026-08-22, after driving
`.1`'s dispatch (run `01M0KNYSF0XB`, PR #1706). The `bd-ib-bx7swg` hypothesis
above was this session's own, formed and then falsified by the measurement; it is
written up as a trap rather than deleted because the signature is genuinely
convincing and a successor will meet it again.
