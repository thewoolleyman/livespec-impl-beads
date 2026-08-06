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
2. `research/incident-and-root-cause.md` — the incident and the exact current
   text that allowed it. **Its "no mechanical check catches this today" claim
   is corrected below — read this file's "Correction" section too before
   trusting that research note's framing.**

That is the whole chain.

## Correction, 2026-08-06: the mechanical-verifier goal moved, and the "no check exists" claim was wrong

The original epic (`bd-ib-2vaeny`, now closed/regroomed-out) claimed "there is
no mechanical verifier for this anywhere in the fleet's shared tooling
today." That was wrong — checked more thoroughly after filing. A real,
shipped, deliberately-designed check family exists in `livespec-dev-tooling`:
`plan_thread_anchor_declared` (static) and `plan_thread_epic_parity`
(ledger-aware, credential/lever-gated). `plan_thread_epic_parity`'s own
remediation text, verbatim, on an active thread pointing at a closed epic:
*"the plan thread is complete — archive it."* That is the same conflation
this thread exists to fix, now found baked into actual shipped code, not just
prose — and it was a deliberate design choice (epic
`livespec-dev-tooling-scsj5e`, closed 2026-07-18), motivated by a real prior
incident where the opposite failure happened (a genuinely-complete epic sat
un-archived). This thread's incident is the mirror image of that one.

Two consequences:

1. **The mechanical-verifier goal (originally goal 2 here) does not belong in
   this repo.** `plan_thread_epic_parity` is shared code every fleet repo
   consumes via the `livespec-dev-tooling` pin — a repo-local duplicate here
   would be redundant. That work is filed in `livespec-dev-tooling` as
   `livespec-dev-tooling-5asgvm` (ready), and is closely related to but
   distinct from `livespec-dev-tooling-q3emww` (ready, found independently
   the same day by a different thread — fixes the *converse* gap: an archived
   thread whose anchor epic is still *open*). Neither q3emww's fix nor the
   existing check would have caught this incident: this incident's anchor
   epic *was* already closed at archive time (via `groom`'s regroom-out),
   so the gap is one hop further — descendant completion, not anchor status.
2. **`bd-ib-2vaeny` was re-groomed** (regroom-out, `resolution:
   no-longer-applicable`) into a single, correctly-scoped local slice:
   `bd-ib-ycihm7` — the prose/spec text correction only, goal 1 below.

## Scope — a tactical stopgap, not the redesign

`livespec` core has an **open, pre-ratification** thread for this same area:
`plan/planning-lane-redesign` (epic `livespec-zsn2xh`, still `backlog`, zero
children scoped). Its accepted-for-capture recommendations already include a
"Two-leg archive gate" that would have caught this exact incident. This
thread's incident is recorded there as evidence (`livespec` PR #2066).

**This thread is a narrow, tactical stopgap** — correct this repo's own
prose/spec text now, ahead of that redesign, because the defect is live risk
today for every fleet repo that runs `plan`/`groom`. Expect this work to be
folded into or superseded by whatever the redesign eventually ratifies. Do
not expand this thread to cover the ledger-held-handoff redesign, the "plan
thread"→"plan" vocabulary rename, the adversarial-completeness-review leg, or
the mechanical-verifier work — those belong to the core thread or to
`livespec-dev-tooling`, not here.

## Goal, with its acceptance

| # | goal | acceptance |
|---|---|---|
| 1 | **Correct the archive-on-epic-close text** in `.claude-plugin/prose/plan.md` Step 5 and `SPECIFICATION/contracts.md` so it no longer reads as unconditional "epic closed → archive" | The corrected text states a plan archives only on genuine completion (implemented, merged, and — where a release applies — shipped and verified), never merely because an epic's ledger status transitioned to closed for any reason; the one exception (remaining work handed to named follow-up plan(s)/work-item(s)) is stated explicitly; both cite `livespec-dev-tooling-5asgvm` / `-q3emww` by id as where mechanical enforcement lives |

## Next action

Dispatch the filed, ready slice through the factory path:

```text
/livespec-orchestrator-beads-fabro:drive --action approve:bd-ib-ycihm7
/livespec-orchestrator-beads-fabro:drive --action impl:bd-ib-ycihm7
```

Do not hand-code implementation inline in a planning session.

**Do not archive this thread** until that slice is implemented, merged, and
confirmed working — an epic's ledger status alone is never evidence of that.
This is the exact lesson the thread itself exists to fix; do not let it
repeat here.
