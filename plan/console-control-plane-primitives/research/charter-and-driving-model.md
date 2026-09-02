# console-control-plane-primitives — charter and driving model

The orchestrator's execution plan for the control-plane primitives the
console consumes. Created 2026-09-02 on the maintainer's ruling after the
console plan `retire-overseer-and-redesign-control-plane-around-console`
(console epic `livespec-console-beads-fabro-pzbdbo`) found its entire
orchestrator dependency chain unfiled or undriven. Charter D7 of that plan
says the orchestrator gets its own execution plans, referenced from the
console; this is that plan.

## Driving model (binding)

- **The maintainer drives this plan's items in orchestrator sessions.** The
  console plan references this plan by `plan_ref:
  livespec-orchestrator-beads-fabro/console-control-plane-primitives` and
  advises it; a console session never executes, dispatches, or works around
  an item here. The console holds until b1–b3 land and consumes them.
- **Every item here has a console proxy** (`BLOCKED-ON
  livespec-orchestrator-beads-fabro/<id>`) in the console tenant, which
  closes only when the item here closes. That proxy is how the console's
  hold is enforced by the dispatcher rather than remembered by a session.
- **Handing a path means naming the item on the console epic**, not filing
  it here and moving on.

## The primitives (from the console program board, in unblocking order)

- **b1 — D6 contract.** `plan_slug` required and unique per tenant;
  `associated_work_item_id` at each plan-dir root; the doctor rules
  (presence, uniqueness, bidirectional consistency, closed-epic/live-dir
  errors, completeness-evidence gate on close, comment-rate warning);
  typed `next_action: {kind: impl | spec-op | human | none, ref, text}` on
  every open epic with a plan dir. One orchestrator propose-change plus the
  one-shot migration writing `associated_work_item_id` from each existing
  epic's `plan_slug`. Cheapest item on the path and the sorting rule for
  everything else.
- **b2 — `context` loader + `discuss-work-item`.** The deterministic loader
  that assembles an item's full context (epic, comments, children,
  dependency edges, typed next action, linked research directory, linked
  spec clauses) and the interactive skill over it that stands by — answers,
  drafts research, records rulings as scope events, drives only when told.
  Replaces the plan operation the console plan session runs on.
- **b3 — interview questions in `needs-attention` + answer route.** Fabro
  interview questions (permission / user-input / interview) published as an
  orchestrator attention kind with a typed answer route. The picker-kill;
  the first thing the console renders.
- **b4 — workflow variants** (`pluggable-factory-workflow-configs`,
  `bd-ib-yqpdrt`): revise / gap-capture with interview consent, then panel /
  review. Needs a re-scope and fresh children before it can be central.
- **b5 — valve policy on attention items; `accounts`** (caam generalized,
  event-driven off rate-limit signals); re-dispatch on `transient_infra`;
  starvation → dispatch cadence.

## Survivors homed here

The fabro/dispatcher defects the console has been working around instead
of consuming a fix for:

- `bd-ib-ott6` — v092 projected prepare steps render as nothing on pinned
  fabro v0.254.0; `contract_prepare_parameters` has no consumer. The
  console's literal prepare-step values are the workaround this retires.
- `bd-ib-6pzg` — the post-merge janitor bootstrap runs with cwd = primary
  and never provisions the worktree pack into the janitor checkout. The
  console's hand-installed pack is the workaround this retires.
- `bd-ib-bb41` (`fabro-fork-control-plane-gaps`, `.1`–`.6`) — referenced,
  not moved: its own epic. The console re-fork stands in for these until
  they land and the fork converges (D3).

## Exit criterion

This plan is done when the console consumes b1–b3 through the injected CLI
with no console-side substitute remaining, every console proxy for an item
here is closed, and the console's own next slice is driven through the new
path (the console charter's exit gate 6).
