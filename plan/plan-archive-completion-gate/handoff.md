# Plan — plan-archive-completion-gate

**Owning repo:** `livespec-orchestrator-beads-fabro`. **Ledger anchor:** epic
**`bd-ib-2vaeny`** (this repo's beads tenant). **Status: read it from the
ledger** — `/livespec-orchestrator-beads-fabro:list-work-items --json` and
`/livespec-orchestrator-beads-fabro:next`. This file stores no status and
carries no checkbox queue.

Created 2026-08-05/06 after a real incident: a `livespec-overseer` session
groomed a plan's own anchor epic via `groom`'s regroom-out disposition, which
closed the epic administratively (content moved to two new tickets, nothing
shipped), then read this repo's current `archive-on-epic-close` text
literally and archived the plan — while both replacement work-items were
still `ready`, undispatched, zero code written. Corrected same-day
(`livespec-overseer` PR #756).

## Read-first chain

1. This file.
2. `research/incident-and-root-cause.md` — the incident, the exact current
   text that allowed it, the mechanism gap, and why no mechanical check
   catches it today.

That is the whole chain.

## Scope — a tactical stopgap, not the redesign

`livespec` core has an **open, pre-ratification** thread for this same area:
`plan/planning-lane-redesign` (epic `livespec-zsn2xh`, still `backlog`, zero
children scoped). Its accepted-for-capture recommendations already include a
"Two-leg archive gate" that would have caught this exact incident. This
thread's incident is recorded there as evidence (`livespec` PR #2066).

**This thread is a narrow, tactical stopgap** — correct this repo's own
prose/spec text and ship a mechanical verifier now, ahead of that redesign,
because the defect is live risk today for every fleet repo that runs
`plan`/`groom`. Expect this work to be folded into or superseded by whatever
the redesign eventually ratifies. Do not expand this thread to cover the
ledger-held-handoff redesign, the "plan thread"→"plan" vocabulary rename, or
the adversarial-completeness-review leg — those belong to the core thread.

## Goals, each with its acceptance

| # | goal | acceptance |
|---|---|---|
| 1 | **Correct the archive-on-epic-close text** in `.claude-plugin/prose/plan.md` Step 5 and `SPECIFICATION/contracts.md` so it no longer reads as unconditional "epic closed → archive" | The corrected text states a plan archives only on genuine completion (implemented, merged, and — where a release applies — shipped and verified), never merely because an epic's ledger status transitioned to closed for any reason; the one exception (remaining work handed to named follow-up plan(s)/work-item(s)) is stated explicitly |
| 2 | **Add the missing mechanical verifier** — before/at archive, or as a standing `just check` gate, confirm the epic's descendant work-items are ALL closed with a completion-shaped resolution, not merely that the anchor epic itself is closed | A planted violation shaped exactly like this incident (archived plan, closed anchor epic, one linked descendant still open) turns the check RED, demonstrated — not asserted. Wired into `just check` so it fires on every dispatch |

## Next action

**Groom `bd-ib-2vaeny`**, then dispatch ready children through the factory
path: `/livespec-orchestrator-beads-fabro:drive --action approve:<id>`
followed by `--action impl:<id>`. Do not hand-code implementation inline in a
planning session.

**Do not archive this thread** until both goals are implemented, merged, and
confirmed working — an epic's ledger status alone is never evidence of that.
This is the exact lesson the thread itself exists to fix; do not let it repeat
here.
