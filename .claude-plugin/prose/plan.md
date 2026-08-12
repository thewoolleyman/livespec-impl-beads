# plan

Harness-neutral driving prose for the `plan` operation, per
`SPECIFICATION/constraints.md` "Skill orchestration constraints".
This artifact is the plugin-owned LLM-facing half of the Planning Lane:
the thread create/resume dialogue, write-once research capture, the
ledger epic anchor, ledger-held handoff timeline entries, scoping
events, routed child work, and archive gates. Each per-runtime
`SKILL.md` is a thin binding that resolves the plugin root, reads this
prose in full, and maps the neutral verbs below to that runtime's tools.

`plan` is stateful and re-entered for the same topic. It decides what
should become spec, implementation, or research before those lanes are
committed to. The durable coordination record is the plan epic in the
beads ledger; filesystem artifacts hold research only.

## Pre-requisites

- The `livespec-orchestrator-beads-fabro` Python package is on the
  import path; the bundled wrappers self-bootstrap it.
- A reachable work-items store exists. A planning thread anchors exactly
  one ledger `epic`.
- `livespec` is installed for the cross-boundary `propose-change`
  operation.
- A `plan/` directory at the project root is the thread store; the
  operation creates it on first use.

## The Planning Thread Store

A live planning thread has two stores:

- Filesystem research under `plan/<topic>/research/`. Creation writes
  one initial research note and no other filesystem artifact. Further
  reasoning updates add or revise research notes deliberately.
- One write-once plan epic in the beads ledger. The epic carries the
  thread slug in its metadata and is the status anchor, handoff anchor,
  scope-event anchor, and archive lifecycle anchor.

The operation never authors `plan/<topic>/handoff.md`. Handoffs are
append-only comments on the plan epic. Each entry is one ledger comment,
attributed and timestamped, and is read through the same timeline read
path used by the package command. Existing legacy `handoff.md` files may
be read only as historical migration input; do not create or update one.

Archived threads move whole directories to `plan/archive/<topic>/`.
There is no root `research/` tree: standalone analysis lives in a plan
thread, or after closure under `plan/archive/`.

## Package Commands

The operation's testable package substrate is
`livespec_orchestrator_beads_fabro.commands.plan`:

- `create_thread(...)` creates `plan/<slug>/research/<file>` and one
  ledger epic anchor.
- `append_handoff(...)` appends one plan-epic comment.
- `read_timeline(...)` reads plan handoff and scope comments
  oldest-first.
- `record_scope_event(...)` records requirement carriers and explicit
  deferrals before implementation children are admitted.
- `archive_thread(...)` performs both archive gates and then moves the
  thread directory to `plan/archive/<slug>/`.

Use those package calls when this operation needs deterministic local
behavior. Continue to use `list-work-items`, `next`, and
`capture-work-item` for their existing public skill responsibilities.

## Flow

### Step 1 - Resolve The Invocation Mode

This operation has two entry modes:

- No argument means interactive entry. Resume an open thread or start a
  new one.
- A `<slug>` argument means strict resume. It must match an existing
  live `plan/<slug>/` exactly. If it does not, fail hard and list the
  existing live slugs. Do not create on a typo.

### Step 2 - Interactive Entry

Compose the open-thread list from both sources and present it:

1. Open planning epics from the ledger via `list-work-items --json`.
   Status is read from the ledger only; it is never copied into a
   planning artifact.
2. Live filesystem threads from direct child directories under `plan/`,
   excluding `plan/archive/`.

Ask whether to resume one listed thread or start a new thread.

To start a new thread, ask for a one- or two-sentence topic
description. Propose a canonical dash-cased slug using the same
canonicalization as `propose-change`: lowercase, replace each run of
non-`[a-z0-9]` characters with one hyphen, strip leading and trailing
hyphens, and truncate to 64 characters. Confirm the proposed slug.

On confirmation, create exactly these records:

1. One initial research note under `plan/<slug>/research/`.
2. One ledger `epic` anchor for the thread.

Do not create `handoff.md`, status files, terminal markers, local queue
files, or any other thread metadata file.

### Step 3 - Work The Thread

Within a thread, ask which action to take and perform one action at a
time:

- Update reasoning. Add or revise a research note under
  `plan/<slug>/research/`.
- Append a handoff entry. Write one plan-epic ledger comment with the
  next action, current facts, and read-first chain. Read it back through
  `read_timeline(...)` before declaring it recorded.
- Record a scoping event. Before implementation children are admitted,
  write a scope comment that names the requirement carriers and the
  explicit deferrals. Deferrals must be concrete: what is deferred, why
  it is not part of the current implementation children, and where it
  will be reconsidered.
- Route a matured piece. If it becomes spec, hand it to
  `propose-change`. If it becomes ledger work, file it through
  `capture-work-item` as a child of the plan epic after the scoping
  event exists. Planning sessions file ripe work; they do not implement
  it inline.
- Close the thread. Run the archive gates in Step 5.

### Step 4 - Handoff Timeline Requirements

A handoff entry is ready only when a fresh session can continue from the
ledger timeline without chat history:

1. The entry names exactly one next action.
2. Every path it cites exists and is committed.
3. If the next action is implementation work, it names the factory route:
   the `drive` operation (`impl:<id>`) or Dispatcher drain. Only items
   explicitly recorded as factory-ineligible may name an in-session
   implementation route.
4. It does not embed a parallel checklist or status queue. Status is
   composed from the ledger via `list-work-items` and `next`.

### Step 5 - Archive Gates

A plan thread remains live until its work is genuinely complete:
implemented, merged, and, where a release applies, shipped and verified.
Do not archive merely because the plan epic's ledger status moved to
closed; closed can also mean regroomed out, superseded, or otherwise
retired without completing the work.

The only exception is an explicit handoff at archive time: any remaining
work must be transferred to named follow-up plan(s) or work-item(s), and
the archive record must state those names exactly. Mechanical enforcement
of this corrected archive rule is tracked outside this repo in
`livespec-dev-tooling-5asgvm` and the related converse-gap item
`livespec-dev-tooling-q3emww`.

Archiving has two required legs:

1. Mechanical child disposition. Refuse archive if any child of the plan
   epic is not disposed. Undisposed means any child work-item whose
   ledger status is not closed.
2. Completeness-review evidence. Refuse archive unless an independent
   completeness-review evidence id is supplied. The review itself is a
   downstream gate; this operation records and requires the evidence
   reference, but does not spawn the reviewer.

After both gates pass, close the epic and move the whole directory:

```text
git mv plan/<topic>/ plan/archive/<topic>/
```

Leave nothing at `plan/<topic>/`: no stub, marker, forwarding note, or
empty directory. If unresolved work remains, either keep the thread live
with its epic open, or transfer every blocker to another live plan thread
or work-item before archiving.

## Important Properties

- Research is filesystem-held; handoffs are ledger-held.
- Creation writes one research note plus one epic anchor and nothing
  else.
- Status is derived from the ledger and never shadowed in files.
- Scope events cut requirements and explicit deferrals before
  implementation children are admitted.
- Archive has two gates: no undisposed children, and independent
  completeness-review evidence.
- The operation never authors `handoff.md`.

## What This Operation Does Not Do

- Does not write status or queues into planning files.
- Does not create a thread from strict `<slug>` resume mode.
- Does not implement child work inline.
- Does not spawn the downstream completeness reviewer.
