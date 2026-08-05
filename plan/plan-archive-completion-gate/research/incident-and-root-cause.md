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

## Why nothing caught it mechanically

`SPECIFICATION/contracts.md` names "`archived` matches `epic-closed`" as one
of the "five-slot conformance concerns... whose always-on enforcement is
realized by the Conformance Pattern." Checked directly for an actual verifier:

```
grep -rln "archive.on.epic.close\|epic_close\|archive_on_epic" --include="*.py" .
```

— zero hits, in this repo and in `livespec-dev-tooling`. There is no
mechanical check anywhere. The only thing that ever "enforced" this rule was
an LLM session reading the prose and (in this case) getting it wrong. This
repo's own fleet already carries two named instances of exactly this failure
shape — a rule that ran and could not fail (`check-no-workflow-edits`, wired
into neither the aggregate nor CI; `LIVESPEC_RUN_MUTATION`, a verified
no-op). This incident is a third.

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

This thread's two goals are scoped to ship ahead of that redesign as a
tactical stopgap — see the handoff's "Scope" section.
