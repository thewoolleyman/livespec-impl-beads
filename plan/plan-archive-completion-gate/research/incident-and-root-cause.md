# Incident and root cause

## What happened, 2026-08-05

A `livespec-overseer` session was resuming
`plan/supervisor-scratch-discipline/` (its handoff's own "Next action" line
read: "Groom `overseer-5jttov`, then dispatch ready children through the
factory path"). It ran this repo's `groom` operation against the plan's own
anchor epic, `overseer-5jttov`, which split the epic's content into two new
factory-tier slices and closed the original (`status: done`, `resolution:
no-longer-applicable`) — `groom`'s standard regroom-out disposition, working
exactly as specified.

The session then read the current archive rule (quoted below) and, satisfying
its literal "iff," archived the plan to `plan/archive/`. The PR merged via
`livespec-overseer`'s repo auto-merge before the maintainer caught it. **At archive time, both replacement work-items were
`status: ready`, unassigned, undispatched, with zero code written and zero
PRs open.** The plan's actual deliverables (a charter-generation rule, an
enforcement check) did not exist. Corrected same-day: `livespec-overseer` PR
#756 un-archived the plan and rewrote its status section.

## The exact text that allowed it

`.claude-plugin/prose/plan.md`, Step 5 ("Archive on epic close"):

> "A plan thread's lifecycle binds to its ledger epic: `plan/<topic>/` is
> active if and only if its epic is open, and archived to
> `plan/archive/<topic>/` if and only if the epic is closed. When the user
> closes the thread, close the epic anchor (via the ledger) AND move the
> directory... Reopening the epic unarchives it (move back)."

`SPECIFICATION/contracts.md`, same section, stronger and unconditional:

> "whatever closes the epic also archives the directory."

Neither passage distinguishes *why* the epic closed. The "When the user
closes the thread..." sentence in the prose file at least gestures at a
deliberate, human-driven closure — but the very next sentence generalizes it
into an unconditional "iff" that a mechanical reading (by an agent or, if one
existed, a verifier) cannot help but apply to ANY closed status, including one
`groom` produces as a side effect of decomposition.

## The mechanism gap

`groom`'s regroom-out disposition (`SPECIFICATION/contracts.md` and
`.claude-plugin/prose/groom.md`) closes the ORIGINAL work-item once real
local factory slices are filed — "escalate-don't-drop." This is correct and
necessary for `groom`'s normal case: an oversized or non-converging backlog
item. It becomes a hazard only because nothing anywhere recognizes the
special case where the item being groomed is ALSO a plan's own anchor epic —
`groom` has no awareness of plan threads at all, and `plan`'s archive gate has
no awareness of *why* the epic it's watching just closed.

Two independent operations, each individually correct in isolation, compose
into this defect. Neither operation's spec text or prose currently says
anything about the other.

## Why nothing caught it mechanically — CORRECTED 2026-08-06

**This section originally claimed "there is no mechanical check anywhere,"
based on a grep for the literal substrings `archive.on.epic.close` /
`epic_close` / `archive_on_epic` — zero hits. That grep was too narrow and
the claim was wrong.** A real check family exists in `livespec-dev-tooling`,
named differently than the grep anticipated: `plan_thread_anchor_declared`
(static, requires every active handoff to declare a concrete ledger anchor)
and `plan_thread_epic_parity` (ledger-aware, credential/lever-gated —
`LIVESPEC_RUN_PLAN_EPIC_PARITY` + `BEADS_DOLT_PASSWORD` both required to
arm).

`plan_thread_epic_parity`'s own remediation text, verbatim, on finding an
active thread pointing at a closed epic: *"the plan thread is complete —
archive it... an active thread pointing at a done/closed epic is the
un-archived-thread drift this check prevents."* This is the SAME conflation
this incident exposes, now found baked into shipped code, not just prose —
and it was a deliberate, documented design choice (epic
`livespec-dev-tooling-scsj5e`, closed 2026-07-18), motivated by a real prior
incident (`rop-sweep-library-checks`) where a genuinely-complete epic sat
un-archived. That motivating case is this incident's mirror image: there,
"closed" really did mean "done"; here, "closed" meant "administratively
retired via `groom`'s regroom-out, replaced by open descendants" — same
assumption, opposite ground truth.

Two things still hold from the original (wrong) claim, now corrected in
scope rather than retracted outright:

1. **This check is un-armed everywhere in the fleet today.** Checked: zero
   `LIVESPEC_RUN_PLAN_EPIC_PARITY` references in any `.github/workflows/`
   across `livespec`, `livespec-overseer`, `livespec-orchestrator-beads-fabro`;
   `livespec-dev-tooling-d1j` ("establish a standing armed home") is still
   `backlog`, unstarted. So even where the check exists, it was not actually
   running in this session's environment — the only thing that "enforced"
   this rule at the moment of the incident was an LLM reading the prose by
   hand, which is what actually happened, and got it wrong.
2. **Even fully armed, this check would not have caught this incident.**
   Its assertion direction is "active thread + closed epic → fail." In this
   incident the *thread itself* was what got archived — by the time the
   mistake existed on disk, there was no longer an *active* thread pointing
   at a closed epic to catch; the plan had already moved to `plan/archive/`,
   which is structurally outside this check's glob (a separate, independently
   found defect: `livespec-dev-tooling-q3emww`). Catching this incident's
   specific shape needs a THIRD, different check — descendant completion,
   not anchor status — filed as `livespec-dev-tooling-5asgvm`. See the
   handoff's "Correction" section for the full re-scoping this produced.

This repo's own fleet already carries other named instances of the general
failure shape — a rule that ran and could not fail (`check-no-workflow-edits`,
wired into neither the aggregate nor CI; `LIVESPEC_RUN_MUTATION`, a verified
no-op). `plan_thread_epic_parity` un-armed is another instance of the same
family; the wrong-direction remediation text is a distinct, additional
defect on top of that.

## Cross-repo relationship

`livespec` core's fleet-wide **Archive-on-epic-close** Conformance Pattern
member (`SPECIFICATION/non-functional-requirements.md`) states the same
unconditional rule at the fleet level: "a `plan/<slug>/` record is active if
and only if its ledger epic is open, and the epic itself MAY close only
through the archive gate." Core is upstream of this repo's realization
(`livespec`'s own `plan/planning-lane-redesign` maintainer-rulings.md, ruling
4). That thread is open, pre-ratification (epic `livespec-zsn2xh`, `backlog`,
zero children scoped as of this writing), and its accepted-for-capture
recommendations already include a "Two-leg archive gate: mechanical (no
undisposed children) plus an independent adversarial completeness review of
research docs against the epic's children at archive time" — which would have
caught this exact incident by construction. This incident is recorded there
as evidence (`livespec` PR #2066).

This thread's remaining goal (the prose/spec text correction only, after
re-scoping — see the handoff's "Correction" section) ships ahead of that
redesign as a tactical stopgap.
