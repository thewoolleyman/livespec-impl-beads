# 002 - Correction: bd-ib-y4mb (driver-dispatch) is KEEP, not SUPERSEDED-BY-TRANSPORT

Written 2026-09-06 by the same session that produced note 001, about one
hour after that note landed. This note is a correction to one row of the
verdict table and to item 2 of "Things the console plan must react to".

## The verdict as published

Note 001 sorted `bd-ib-y4mb` ("Implement driver-dispatch:<id>") as
SUPERSEDED-BY-TRANSPORT, reasoning that a harness-driver run outside fabro is
the second execution substrate decision D3 retracts, and asked for an
orchestrator propose-change retiring the verb from contracts.md.

## Why that was wrong

Re-reading the ratified clause (contracts.md, "driver-dispatch:<id>") against
decision D4 of the console plan:

- The clause defines a JOURNALED DOOR valid only on `ready` items whose
  `factory_safety` is non-null, the exact set the admission valve already
  refuses and host-routes. It journals the actor and a driver-session
  reference, moves `ready` to `active`, and the driver session parks its
  result at `acceptance` for the normal accept valve.
- D4 names the thin non-dispatchable set: maintainer infra acts, the
  interactive context session, and the broken-factory fallback, "a human plus
  LLM session driving worktree to PR by hand". The third of those IS a driver
  session in the clause's sense.
- D3's retraction list is a `jobs run` runner, a four-driver `sessions`
  layer, a `dispose` primitive, and a `supervise` daemon: automated
  substrates that would compete with fabro. A ledger door that records a
  human-driven host-only pass competes with nothing; it is the bookkeeping
  D4's path needs so a host-only item can move through the same states as a
  factory item.

So `driver-dispatch` is the D4 door, not a D3 substrate. The published
verdict conflated "driver" (a harness session doing host-only work) with the
retired overseer driver layer.

## Corrected disposition

- `bd-ib-y4mb`: KEEP. The maintainer's 2026-07-28 ruling to implement it
  stands; it is factory-safe and remains the only spec-blessed forward door for
  host-only-refused ready items.
- No propose-change is filed.
- Counts after correction: KEEP 177, SUPERSEDED-BY-TRANSPORT 7 (the other
  five verdict counts are unchanged).
- Recorded on the item as a comment and on the console anchor
  `livespec-console-beads-fabro-pzbdbo` as a correction comment, so the
  original audience of the summary sees the retraction.
