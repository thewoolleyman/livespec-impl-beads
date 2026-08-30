# 001 — Ledger is the only gate: design and slice plan

Session `fix-fabro-blockages`, 2026-08-30. Measured against the hp and vps
factories, this repo's dispatch journal, the ledger (853 items), and the
orchestrator source at the commit named in the footer.

## Trigger

`overseer-ebik5q.2`'s Fabro run `01M18YN47DFTR5QGNX6EFGWYGT` parked at the
in-loop human gate on hp at ~10:09Z after two ACP turn timeouts on the
implement node. The plan's host seat implemented the item by hand, PR #2066
merged at 11:06Z, and the item closed at 11:10Z. The run sat `blocked /
human_input_required` holding an hp scheduler slot until it was abandoned
by hand at ~164 minutes. The ledger half worked perfectly; nothing owned
the run.

## Two things named "gate"

- The DECISION gate — a truly-unresolvable outcome needs a human (or, under
  a governed repo's `full_autonomy`, its foreman panel). Lives in the ledger
  as `blocked / blocked_reason: needs-human`. Governed exhaustively by
  contracts.md §"Every needs-human escalation still reaches a human" and
  Scenario 36; written by `_dispatcher_blocked.py`; surfaced by
  `needs-attention`; cleared by `resolve-blocked`.
- The RUN PARK — the `escalate` hexagon in
  `.claude-plugin/.fabro/workflows/implement-work-item/workflow.fabro` holds a
  Fabro run (sandbox, scheduler slot, expiring tokens) in Fabro's native
  `blocked` status until a human runs `fabro attach`. No code path in the
  orchestrator ever looks at a blocked run again. Nothing in
  `SPECIFICATION/` governs it.

## Measurements

| Measurement | Value | Source |
| --- | --- | --- |
| Dispatches that parked at needs-human, this repo, 2026-08-21..08-28 | 17 of 336 `fabro-run` stages (5%) | `tmp/fabro-dispatch-journal.jsonl`, stage `needs-human-blocked` |
| ...of which the item is now `closed` | 16 of 17 (the 17th is at `acceptance`) | join against `bd list --status all --limit 0 --json` |
| Blocked runs on hp / vps at 13:50Z 2026-08-30 | 0 / 0 | `fabro ps -a --json --server <factory>`; hp 523 succeeded / 110 failed / 2 running; vps 570 / 161 / 0 |
| ebik5q.2's run now | `failed / workflow_error`, 164m54s | the Abandon signature recorded in bd-ib-3al8 |
| Independent recurrences already recorded | three corroborations on bd-ib-rnlks6, two of them the "moot question" sub-case | ledger comments 2026-08-21/22 |

Reading: nearly every park becomes a moot-question orphan, because being
overtaken (re-dispatch, hand landing) is the normal consequence of parking.
The slot leak is invisible on an idle pool and concentrates exactly when
nobody is watching (rnlks6's controlled measurement: one blocked run removed
led to one queued run admitted immediately).

## Why nothing owns the run — by file

- `_dispatcher_fabro_terminal.py:146-190` classifies the park as `blocked`
  (exit 4) by reading `fabro inspect`. Correct.
- `_dispatcher_blocked.py:35-86` writes `blocked / needs-human /
  admission:manual`. Correct. Assignee untouched; no comment.
- `_dispatcher_preserve_reference.py:57-120` writes a comment with
  `run id: <id>` and dump digests. This comment is the ONLY place the run id
  lands in the ledger; there is no metadata key.
- `_dispatcher_io_fabro_launcher.py:161` — the watch loop runs `while
  thread.is_alive()`; a park is exactly the case where the foreground `fabro
  run` returns, so watching stops forever.
- `_dispatcher_watchdog_discovery.py:84` —
  `_ACTIONABLE_STATUS_KINDS = ("runnable", "running")`; a blocked row is a
  discovery miss.
- `_dispatcher_stale_run_sweep.py:88-92` — skips `status_kind not in
  {runnable, running}` AND skips runs whose item is not found in the ledger.
  Operator-invoked only (`dispatcher.py:328,362`); nothing schedules it.
- `_dispatcher_claim_reclaim.py:116` — claim accounting is scoped to
  `status == active`, so escalating to `blocked` frees the LEDGER slot while
  the FACTORY slot stays held.
- `resolve-blocked` (`_drive_policy_valves.py:71-94`), `reconcile-merged`
  (`_dispatcher_reconcile_merged.py`), and a hand `bd close` take no
  Fabro-side action at all.
- `_fabro_port.py` exposes `run / auth_login / inspect / events / ps /
  preflight / rm` — no attach, cancel, or answer verb. Every `fabro attach`
  in the codebase is prose in a message or docstring.
- `_fabro_port_records.py:24` — the run-to-item join is a regex over the goal
  text, not a field.
- `SPECIFICATION/contracts.md` governs the ledger half (§"Every needs-human
  escalation still reaches a human" at :3571, exit code 4 at :3310-3316,
  lifecycle `blocked` at :1917) and says nothing about the run half: no
  heading, MUST, or scenario mentions `fabro attach`, `fabro rm`,
  `stale-run-sweep`, reaping, orphaned runs, or scheduler slots.

Two facts shape the remedy. Fabro's server on the pinned
`factory-integration` branch exposes `POST /runs/{id}/questions/{qid}/answer`
(`lib/crates/fabro-server/src/server/handler/runs.rs:73`) and
`POST /runs/{id}/cancel` (`handler/lifecycle.rs:25`), so a non-interactive
answer is possible. And the graph already proves the terminal-node shape:
`non_converged`, `dead_implementer` and `abandon` are dead-end script nodes
that terminate the run with a stderr sentinel the Dispatcher consumes
(`NON_CONVERGED_MARKER`).

## The invariant

At any moment, on every configured factory, the set of non-terminal Fabro
runs equals the set of ledger items that are `active` under a live dispatch
claim whose journaled run id is that run. Any other non-terminal run is an
orphan, and the Dispatcher reconciles it — exports its record, terminates
it, journals the reconciliation — without a human. Reconciling a run never
changes the item's `blocked_reason`: the decision stays in the ledger, so
Scenario 36 is untouched.

The join is `fabro ps -a --json --server <factory>` x ledger status x the
dispatch journal's run id. It does not care HOW an item left `active`,
which is what makes "an agent hand-implemented a half-done run" a covered
case rather than a hope.

## Four enforcement layers

### A — Prevent: no run ever parks (workflow.fabro)

Replace `escalate [shape=hexagon]` with a dead-end script node in the
`non_converged` mould:

```
needs_human [
    label="Needs human: terminate, preserve, route to the ledger"
    shape=parallelogram
    timeout="600s"
    script="git push --force-with-lease origin HEAD:refs/heads/needs-human/$FABRO_RUN_ID 2>&1 || echo 'LIVESPEC_NEEDS_HUMAN_PUSH_FAILED' >&2; echo 'LIVESPEC_NEEDS_HUMAN: loop cannot auto-resolve; work preserved by reference; decision routed to the ledger' >&2; exit 1"
]
implement   -> needs_human [label="Blocked", condition="outcome=failed"]
review      -> needs_human [label="needs-human", condition="<cap && not merge_on_review_cap>"]
disposition -> needs_human [label="Blocked", condition="outcome=failed", weight=100]
pr          -> needs_human [label="Blocked", condition="outcome=failed"]
// the R/I/A edges and the abandon node are deleted
```

- The three human answers map onto ledger actions that already exist:
  [R] Retry = `resolve-blocked:<id>:ready` with `rework:pending` seeded from
  the preserved branch; [I] Re-implement = `resolve-blocked:<id>:ready`;
  [A] Abandon = leave it blocked. `needs-attention` renders them as valves.
- The Dispatcher's terminal classifier learns the `LIVESPEC_NEEDS_HUMAN`
  sentinel beside `NON_CONVERGED_MARKER` and routes to the existing
  `escalate_needs_human_block`. Exit code 4 and the `blocked` outcome
  vocabulary stay; only the trigger changes from "run parked" to "run
  terminated with the needs-human sentinel".
- Cost: the in-sandbox retry-with-context is gone. Evidence says it is worth
  almost nothing — 16 of 17 parks resolved by other routes, and a >1h park
  cannot push anyway (bd-ib-6vu: a resumed sandbox holds a dead token).
  Preserve-by-reference already captures the diff via `fabro dump`; the
  branch push is the durable copy that survives a prune.
- Collateral: bd-ib-3al8 and bd-ib-bg2zz5 become moot; the console's
  `attach_command` surface goes away.
- Edits the workflow file, so the factory's `check-no-workflow-edits`
  janitor refuses it: HAND-BUILT, after the spec amendment ratifies.

### B — Reconcile: one authority over the factory's run inventory

Grow `stale-run-sweep` into `dispatcher.py reconcile-runs`. For every
configured factory (`FabroTarget(server_url=...)`, never a bare target —
bd-ib-wmuxvy):

1. List every non-terminal run (`runnable, starting, running, blocked,
   paused`). Attribute each to a work-item by journaled run id first, goal
   regex second.
2. Join with the ledger. A run is an ORPHAN when its item is not `active`,
   OR the item is `active` but its newest journaled `fabro-run` names a
   different run id, OR the item does not exist in the ledger. A run whose
   item is `active` with a matching journaled run id is NOT an orphan even
   if no dispatcher process is alive (bd-ib-tk6e's case) — the join must
   honour that.
3. For each orphan: EXPORT first (preserve-by-reference comment with dump
   digest, read back through `bd comments --json` indexing `text` — the
   maintainer's 2026-08-26 "export, then reap" ruling made mechanical), then
   TERMINATE: a blocked run gets its interview answered Abandon through the
   answer route (keeps Fabro's own intent record); any other kind gets the
   cancel route; `fabro rm --force` only as a fallback. Journal
   `orphan-run-reconciled` with run id, factory, kind, item status, reason.
4. A blocked run whose item is still live (pre-A runs, foreign workflows):
   not answered on the spot, but not allowed to hold a slot either. After
   `dispatcher.blocked_run_grace_seconds` (default 1800) it is exported and
   Abandoned; the item stays `blocked / needs-human`. D3's ordering
   constraint (preserve-by-reference before any gate-window shortening) is
   satisfied: R6 bd-ib-d0ul closed 2026-08-23, re-verified on master
   2026-08-29 per bd-ib-yhbsd4.3.

Wire it three ways: a step of every `loop` tick and the `dispatch` preamble
(`_dispatcher_run_checks.dispatch_preamble`); a systemd timer on the
dispatching host (fabro-hosts carries the unit pattern); and a read-only
`--dry-run --json` projection that `needs-attention` renders as an
"orphaned factory runs" lane. Stamp the run id and factory on the item as
top-level metadata at dispatch (`dispatch_fabro_run_id`,
`dispatch_factory`) so the join no longer depends on a goal-text regex.

### C — Couple: lifecycle writes reap

- Post-write hook in the status-write seam: any transition out of `active`
  (close, accept, resolve-blocked, move, reconcile-merged) calls
  `reconcile_runs_for_item(item_id)` against that item's factory. The sweep
  in B covers paths that bypass Python (hand `bd close`, another repo's
  session).
- Doctor / `ledger-check` invariant: "no non-terminal run for a non-active
  item" — reads the same projection and fails closed.

### D — Ratify: the spec owns the run half

New contracts section "A factory run never awaits a human", sibling to
§"Every needs-human escalation still reaches a human":

- A needs-human outcome MUST terminate the run and preserve its work by
  reference; the run MUST NOT enter a human-input-required state.
- The Dispatcher MUST reconcile every configured factory's non-terminal run
  inventory against the ledger, export before terminate, and journal each
  reconciliation naming the governing reason.
- Reconciling a run MUST NOT change the item's `blocked_reason` or
  auto-resolve any decision (Scenario 36 verbatim).
- Exit code 4 restated: "dispatch completed with the work-item routed to
  the ledger's human gate".
- §"Host concurrency belongs to the Fabro scheduler" gains one sentence:
  reconciling an orphaned run is not a host concurrency refusal.

Scenarios: (1) needs-human terminates the run and blocks the item; (2) an
item closed by any route while its run is non-terminal → run reconciled,
item untouched; (3) a blocked run past grace → exported, abandoned, item
still blocked/needs-human; (4) resolve-blocked → ready re-dispatches from
the preserved branch.

## Standing rulings, honoured

| Ruling | How |
| --- | --- |
| O3 / bd-ib-vntx65: never auto-resolve a needs-human escalation | Nothing resolves a decision; terminating a run moves the decision into the ledger. |
| rnlks6 "what must not be the fix": a timer reap destroys the record | Export is a read-back-verified precondition of every terminate; the moot case needs no timer, it is a join. |
| D3 (bd-ib-yhbsd4.3): no gate-window shortening before preserve-by-reference | R6 landed and was re-verified; the grace timer is gated on it. |
| Maintainer 2026-08-26: export, then reap | Layer B is that procedure in code, with the same read-back. |
| Overseer floor D6(ii): no keystroking into a structured gate | After A there is no structured gate; the foreman acts on ledger valves (bd-ib-8jv8). |

## Ecosystem

- livespec-console-beads-fabro hardcodes `FabroRunState::HumanGate` for any
  observed run (`crates/console-application/src/source_adapters.rs:2584-2604`)
  and hands operators an `attach` string it never runs. After A/B it should
  consume the `reconcile-runs --dry-run --json` projection and render
  `resolve-blocked` in place of `attach`. Cross-tenant ask.
- livespec-overseer: bd-ib-8jv8 becomes a pure ledger-valve question; report
  back on overseer-3h4s5w.
- livespec core: one NFR via propose-change — "an orchestrator's factory
  runs MUST never await a human; human gates are ledger states" — so every
  family member inherits the invariant.
- fabro fork (optional, later): a per-run human-gate default answer/timeout.
  Not on the critical path; everything above works against the pinned
  0.254 build.

## Slices in dependency order

| # | Slice | Tier | Depends on |
| --- | --- | --- | --- |
| S1 | Spec amendment (contracts section, 4 scenarios, exit-code-4 wording) + core NFR ask — propose-change → revise | spec-change | — |
| S2 | Reconciler core: `reconcile-runs` over all factories and all non-terminal kinds; orphan join; export-then-terminate via HTTP answer/cancel; journal record; fixes stale-run-sweep's two skip filters | impl, factory-safe | — (maintainer ruling already authorizes the moot case) |
| S3 | Run-id + factory metadata stamped at dispatch; join prefers journal/metadata over goal regex | impl, factory-safe | — |
| S4 | Wiring: loop tick + dispatch preamble + systemd timer (fabro-hosts) + needs-attention lane | impl, factory-safe (timer unit hand-landed) | S2 |
| S5 | Grace timer for live-question blocked runs, item untouched | impl, factory-safe | S1 ratified, S2 |
| S6 | Workflow: retire `escalate`/`abandon`, add `needs_human`; sentinel classifier; R/I/A → valves; rework seeded from preserved branch | impl, HAND-BUILT | S1 ratified |
| S7 | Lifecycle-write hook + doctor invariant | impl, factory-safe | S2 |
| S8 | Cross-tenant asks: console lane + valve rendering; overseer report-back; core NFR | coordination | S1, S6 |
| S9 | Dispose prior art; archive after independent completeness review | closure | all |

S2 and S3 dispatch immediately, in parallel with S1's ratification: they
harden against a defect no spec permits. S5 and S6 wait for S1 because they
change ratified behaviour. Every factory-safe slice's criteria are written
in its own merged diff's vocabulary — no scenario references in the
criteria field.

## Prior art disposed by this plan

- bd-ib-rnlks6 (pending-approval) — closed by S2 + S5.
- bd-ib-zg5ndm (active, assignee fabro, no live run on either factory) —
  superseded by S2/S4; re-parent here, release the phantom claim.
- bd-ib-3al8 (backlog) — moot after S6.
- bd-ib-6vu (backlog, fork-track) — moot after S6.
- bd-ib-bg2zz5 (closed) — rendering split retired with the gate.
- bd-ib-mirrfu (pending-approval) — folded into S3 and S6.
- bd-ib-wmuxvy (ready) — stays independent; S2 depends on its
  correct-target discipline.
- bd-ib-8jv8 (backlog) — answered by S1 + S6; report back in S8.
- bd-ib-tk6e (ready) — independent; S2 is its safety net and must not reap
  its case.

Out of scope, deliberately: the ACP turn-timeout root causes that produce
most parks (bd-ib-b5dg zero-output hang, bd-ib-f728 token TTL). Separate
plans own them; this plan makes a park harmless whatever produces it.

Source commit for the file:line references: `6bf1f483` on origin/master.
