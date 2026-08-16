# fabro-stability -- initial research

## Problem

Multiple independent, mechanically-fixable defects in the Fabro
dispatch path have each cost real dispatch capacity when they recur.
This plan is an umbrella tracking thread for the ones NOT already
owned by another live plan, found and partly fixed during the
2026-08-16 debug-fabro investigation into "5 dispatched items never
got a Fabro run".

## Defects in scope

1. **Zombie `runnable` fabro runs outlive their work-item's closure**
   (`bd-ib-5tyn`, filed 2026-08-05, still unfixed at the time of this
   plan's creation -- this is its SECOND measured occurrence, same run
   id `01KZ2P36KXCK`, still `runnable` 13 days after its work-item
   closed). Fix is mechanical: re-check the target item's status at
   run start (not only at enqueue time) and reap `runnable` runs whose
   item is already closed, logging the reap. See `bd-ib-5tyn` for full
   acceptance criteria.

## Cross-referenced, NOT duplicated here

2. **Review-to-disposition context propagation** (`bd-ib-hote`, third
   measured occurrence 2026-08-16 on run `01M040DFPQBK` /
   `bd-gj-a7w`) already has its own live plan,
   `plan/fix-review-disposition-context` (epic `bd-ib-d2qyze`), with
   an implementation child already filed and parented there:
   `bd-ib-n94z`. Do NOT re-file or re-parent that work under
   `fabro-stability` -- it would recreate the exact duplicate-epic
   mistake found and closed as part of this same investigation
   (`bd-ib-65mycm`, closed no-longer-applicable in favor of
   `bd-ib-d2qyze`). Track it here only as a pointer.

## Already fixed, recorded for context

3. **fabro CLI argv `--server` flag ordering** (`bd-ib-1g01`) -- fixed
   and merged same day (PR #1430, `6de3a8a1`) before this plan was
   created, because it was the active blocker preventing ANY factory
   dispatch (including of this plan's own future implementation
   children) from running. No further action needed here; listed for
   the historical record of the same investigation. See the regression
   note appended to `plan/multi-factory-support/research/
  001-initial-research.md` (epic `bd-ib-hvmbxd`) for the full account,
   since that thread's own shipped code caused it.
