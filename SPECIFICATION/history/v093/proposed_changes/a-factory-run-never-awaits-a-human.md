---
topic: a-factory-run-never-awaits-a-human
author: claude-fable-5 (session fix-fabro-blockages)
created_at: 2026-08-30T12:19:45Z
---

## Proposal: A factory run never awaits a human — the ledger is the only human gate

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

Ratify the run half of the needs-human gate, which the specification currently does not govern at all. Today §"Every needs-human escalation still reaches a human" governs the LEDGER half exhaustively (the item rests at `blocked / blocked_reason: needs-human` until a human acts through a valve) while the Fabro RUN half — the `escalate` hexagon that holds a run, its sandbox and its scheduler slot in Fabro's native `blocked` status until someone runs `fabro attach` — is governed by nothing: no clause, no scenario, no obligation on any reaper. Measured 2026-08-30 in this repository: 17 of 336 dispatches parked at that gate over nine days and 16 of the 17 work-items were subsequently closed by another route, leaving each run holding a factory slot for a question nobody could answer any more (the "moot question" sub-case corroborated three times on bd-ib-rnlks6). This proposal adds a sibling section stating that a needs-human outcome MUST terminate the run and preserve its work by reference, that the run MUST NOT enter a human-input-required state, and that the Dispatcher MUST reconcile every configured factory's non-terminal run inventory against the ledger — exporting before terminating and journaling each reconciliation — without ever changing the item's `blocked_reason` or auto-resolving any decision. It restates exit code 4 accordingly, adds one clarifying sentence to §"Host concurrency belongs to the Fabro scheduler", and binds the behaviour with four new scenarios (103–106). Plan: ledger-is-the-only-gate, epic bd-ib-n77djm, research note plan/ledger-is-the-only-gate/research/001-design-and-slice-plan.md.

### Motivation

Make it mechanically impossible for a Fabro run to sit waiting for a human. The decision lives in the ledger, the run always terminates, and the Dispatcher reconciles any run that outlives its work-item — including a run that an agent overtook by implementing the item by hand. This must hold for every consumer of the orchestrator (the Console included) and must not weaken the existing rule that the Dispatcher never auto-resolves a needs-human decision.

### Proposed Changes

## contracts.md — new section after §"Every needs-human escalation still reaches a human"

```diff
@@ contracts.md — insert immediately after the paragraph ending "(§\"Machine-path exemption — the Dispatcher\")" of §"Every needs-human escalation still reaches a human" @@
+### A factory run never awaits a human
+
+The needs-human gate has two halves, and only the ledger half is a gate.
+The item resting at `blocked / blocked_reason: needs-human` is the ONLY
+place a human decision waits. A factory run is never that place.
+
+- A needs-human outcome inside a factory run MUST terminate the run
+  non-green and MUST preserve the run's work by reference (a pushed ref
+  and/or the preserve-by-reference pointer of §"Preserve-by-reference")
+  before terminating. The run MUST NOT enter a human-input-required
+  state, and the workflow MUST NOT carry an interactive human-decision
+  node whose answer resumes the run. The human's answer — retry,
+  re-implement, or abandon — is expressed through ledger valves
+  (`resolve-blocked`, the rework path, or leaving the item blocked),
+  never by attaching to a run.
+- The Dispatcher MUST reconcile every configured factory's non-terminal
+  run inventory against the ledger. The invariant: on every factory
+  declared under `dispatcher.factories`, the set of non-terminal runs
+  equals the set of work-items that are `active` under a live dispatch
+  claim whose journaled run id is that run. Any other non-terminal run is
+  an ORPHAN — its item is not `active`, or is `active` under a different
+  journaled run id, or is absent from the ledger — and the Dispatcher
+  MUST reconcile it without a human: EXPORT its record first (write and
+  read back the preserve-by-reference pointer), THEN terminate it, and
+  journal one record per reconciliation naming the run id, the factory,
+  the run's status kind, the item and its status, the orphan reason, and
+  the termination route. The export is the precondition, not a courtesy:
+  a termination whose export was not read back MUST NOT proceed.
+- Reconciliation runs on every Dispatcher loop tick and in the dispatch
+  preamble, and MUST also be runnable standalone (a scheduled sweep) so
+  that an item closed by any route while no Dispatcher process is alive —
+  a hand landing, a hand `bd close`, another session — still releases its
+  run. A run whose item is `active` with a matching journaled run id is
+  NOT an orphan even when no Dispatcher process is watching it.
+- A run that has nonetheless parked in a human-input-required state (a
+  run created before this contract, or by a foreign workflow) whose item
+  is still live MUST NOT hold its slot indefinitely: after
+  `dispatcher.blocked_run_grace_seconds` (default `1800`) the Dispatcher
+  MUST export it and terminate it by answering its own abandon option, so
+  that Fabro's record carries the intent. The item is left exactly as it
+  was.
+- Reconciling or terminating a run MUST NOT change the item's status,
+  `blocked_reason`, or labels, and MUST NOT auto-resolve any decision.
+  §"Every needs-human escalation still reaches a human" and Scenario 36
+  hold verbatim: the decision stays in the ledger and reaches a human.
+- Every reconciliation surface (loop, preamble, standalone sweep,
+  `needs-attention`) MUST address each factory by its declared server
+  target; a read against an undeclared or default target is not a
+  reconciliation of that factory.
+
+Design record: plan `ledger-is-the-only-gate` (epic `bd-ib-n77djm`),
+`plan/ledger-is-the-only-gate/research/001-design-and-slice-plan.md`.
```

## contracts.md — §"Dispatcher exit codes", restate `4`

```diff
@@ contracts.md §"Dispatcher exit codes" @@
-error (missing repo / workflow / item not ready). `4` — dispatch
-completed at a live human-gate blocked state with no terminal failures.
+error (missing repo / workflow / item not ready). `4` — dispatch
+completed with the work-item routed to the ledger's human gate
+(`blocked / needs-human`) and no terminal failures; the run itself has
+terminated (§"A factory run never awaits a human").
```

## contracts.md — §"Host concurrency belongs to the Fabro scheduler", one clarifying sentence

```diff
@@ contracts.md §"Host concurrency belongs to the Fabro scheduler" — append to the paragraph beginning "Consequently the Dispatcher MUST NOT refuse a dispatch on host-concurrency grounds" @@
+Reconciling an orphaned run under §"A factory run never awaits a human"
+is not a host-concurrency refusal and not a host-global gauge: it
+releases capacity the ledger already says is unowned, and it never
+refuses, defers, or counts a dispatch.
```

## scenarios.md — four new scenarios appended after Scenario 102

```gherkin
## Scenario 103 — A needs-human outcome terminates the run and routes the decision to the ledger

Feature: The ledger is the only human gate
  As a maintainer running an unattended factory
  I want a needs-human outcome to end the run and rest the item in the ledger
  So that no factory run ever holds a slot waiting for me

Scenario: A needs-human outcome inside a run
  Given a factory run whose loop cannot auto-resolve the work-item
  When the run reaches its needs-human outcome
  Then the run preserves its work by reference before terminating
  And the run terminates non-green without entering a human-input-required state
  And the Dispatcher rests the work-item at blocked with blocked_reason needs-human
  And the dispatch reports exit code 4
  And no interactive human-decision node exists in the workflow

## Scenario 104 — An item closed by any route releases its non-terminal run

Feature: Run-inventory reconciliation
  As a maintainer
  I want a run that outlives its work-item reconciled without my intervention
  So that a hand-implemented or re-dispatched item never leaves a run behind

Scenario: The item leaves active while its run is non-terminal
  Given a non-terminal run on a declared factory attributed to a work-item
  And that work-item has left active by any route, including a hand close with no Dispatcher process alive
  When reconciliation runs on the loop tick, the dispatch preamble, or the standalone sweep
  Then the Dispatcher exports the run's record and reads the export back
  And only then terminates the run
  And journals one reconciliation record naming the run id, factory, status kind, item, item status, orphan reason, and termination route
  And the work-item's status, blocked_reason, and labels are unchanged

Scenario: A live run under a matching claim is not an orphan
  Given a running run whose work-item is active and whose journaled run id is that run
  And no Dispatcher process is watching it
  When reconciliation runs
  Then the run is not terminated

Scenario: An item superseded by a newer dispatch
  Given two non-terminal runs attributed to one active work-item
  And the ledger's newest journaled run id names the second run
  When reconciliation runs
  Then the first run is reconciled with orphan reason superseded-run
  And the second run is left alone

## Scenario 105 — A parked run past its grace period is exported and abandoned, and its item is untouched

Feature: Bounded slot hold for a legacy or foreign parked run
  As a maintainer sharing a factory with other workflows
  I want a run parked in a human-input-required state to release its slot after a bounded grace period
  So that an unattended pool cannot be strangled by parked runs

Scenario: A parked run with a live item
  Given a run in a human-input-required state whose work-item is blocked with blocked_reason needs-human
  And the run has been parked longer than dispatcher.blocked_run_grace_seconds
  When reconciliation runs
  Then the Dispatcher exports the run's record and reads the export back
  And answers the run's own abandon option so the run terminates
  And the work-item remains blocked with blocked_reason needs-human
  And the reconciliation is journaled

Scenario: A parked run inside its grace period
  Given a run in a human-input-required state parked for less than dispatcher.blocked_run_grace_seconds
  When reconciliation runs
  Then the run is not terminated

## Scenario 106 — Reconciliation addresses every declared factory by its server target

Feature: Reconciliation reads the right pool
  As a maintainer dispatching to remote factories
  I want reconciliation to query each declared factory explicitly
  So that a clean empty answer from the wrong pool is never mistaken for a reconciled one

Scenario: Two declared factories, one unreachable
  Given dispatcher.factories declares two factories
  And one of them is unreachable
  When reconciliation runs
  Then each factory is queried by its declared server target
  And the unreachable factory produces a journaled reconciliation error
  And reconciliation of the reachable factory completes
```

## tests/heading-coverage.json — co-edit

Add entries for the new H2 headings `## Scenario 103 — A needs-human outcome terminates the run and routes the decision to the ledger`, `## Scenario 104 — An item closed by any route releases its non-terminal run`, `## Scenario 105 — A parked run past its grace period is exported and abandoned, and its item is untouched`, and `## Scenario 106 — Reconciliation addresses every declared factory by its server target`, each with `test: "TODO"` and reason `"bound by plan ledger-is-the-only-gate slices S2 (103-104,106) and S5/S6 (103,105)"`. No existing heading is removed or renamed.
