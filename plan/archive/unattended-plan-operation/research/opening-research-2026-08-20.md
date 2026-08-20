# unattended-plan-operation — opening research note, 2026-08-20

Plan record discipline: the ledger is authoritative over this directory; plan
state, next action, and handoffs live on the ledger anchor ledger anchor `bd-ib-idgwyk`
read through the plan timeline.

## Problem

The 2026-08-20 maintainer investigation of the stalled livespec-dev-tooling
fleet (report: https://claude.ai/code/artifact/264f5d4f-6aec-4795-8431-b6adaa6a4dd6 )
found this plugin's plan operation structurally incompatible with unattended
(overseer-driven) operation:

1. `prose/plan.md` ("ask which action to take and perform one action at a
   time") raises a blocking picker on every resume — including the resume the
   overseer daemon itself triggers after a context-threshold restart — even
   when the newest handoff names exactly one next action. Measured:
   livespec-dev-tooling's rop-railway-enforcement session parked 16h on a
   picker whose option 1 was its own recorded next action.
2. Child disposition (re-parent / close) is treated by sessions as a
   maintainer call, so the archive gate (no undisposed children) becomes
   permanently maintainer-blocked for any epic with scope creep; nothing in
   the prose says the session may dispose with a rationale.
3. The human-gated floor set (spec-change slice, regroom/backlog bounce,
   human-only acceptance, drift acceptance) has no positive complement, so
   sessions over-apply it: an unratified filter inside a check was escalated
   three times as "ratification" (livespec-dev-tooling-8zv3.5) although
   removing unratified code to match spec is conformance.
4. No guard notices runaway record-authoring: one session wrote 15 handoff
   entries and ~12 research notes in a day while blocked.

## Children (filed on the anchor as ready work items)

1. Unattended resume: when the newest handoff names exactly one next action
   and the session is daemon-launched, take it; the which-action picker is
   interactive-mode only.
2. Session-performable child disposition: re-parent or close a plan child
   with a recorded rationale; spec-change-tier children still refuse.
3. Positive floor complement in SPECIFICATION: an enumerated
   not-human-gated list (conformance fixes to unratified check behavior,
   priority edits, plan-child re-parenting, error semantics inside an
   existing ratified rule, cost estimates), routed via propose-change and
   ratified via revise.
4. Handoff rate guard: warn past a per-session-day threshold of handoff
   entries / research notes.

## Route

In-session worker for prose + spec children (propose-change → revise
authorized to run autonomously per maintainer direction 2026-08-20); factory
dispatch allowed for pure code children once acceptance is set.

## Out of scope (explicit deferrals)

- Dispatcher/acceptance-machine defects already tracked (bd-ib-tfpdya,
  bd-ib-ai9a, bd-ib-veid).
- The overseer-side consumer of the unattended marker (tracked in
  livespec-overseer's foreman-autonomy-hardening plan).
