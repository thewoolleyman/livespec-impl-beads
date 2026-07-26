# Handoff — dispatch-claim-liveness

## What this thread is

A work-item admitted to `active` by a dispatch that then reaches a terminal
outcome with no defined ledger transition is left in `active` with
`assignee: fabro` **forever**, permanently consuming a WIP slot. The failure is
silent — a full cap is indistinguishable from a busy factory — and it is
monotonic: every abandonment costs a slot that never comes back.

**Ledger anchor:** epic **`bd-ib-waov`** (P1). Status is READ from the ledger
(`list-work-items` / `next`), never stored here.

**Supersedes `livespec-console-beads-fabro-6ma`** (P1, filed 2026-07-20 in the
CONSOLE tenant, closed as superseded + mis-filed). That item diagnosed the
symptom correctly and cited the exact admission arithmetic, but the defect is
entirely orchestrator-side, so it sat six days in a backlog whose owners could not
fix it. Beads has no cross-tenant edge; this prose IS the link, and `-6ma`'s close
reason points back to `bd-ib-waov`.

## ▶ CURRENT STATE + NEXT ACTION (read this first)

**Status: NOTHING IMPLEMENTED. Nothing is in flight.** The epic exists; it has no
children.

**The root cause below was CORRECTED on 2026-07-26** against the dispatch
journal, the merged PR, and the ledger. The thread's original diagnosis ("the
dispatcher process died mid-flight") is DISPROVEN — see §"Root cause". The open
question the previous revision told you to settle FIRST is now SETTLED with data.

**The ledger epic `bd-ib-waov` has NOT been updated to match** — its description
still carries the superseded root cause. That is deliberate; see §"Read first"
item 2. Where the two disagree, THIS FILE is current.

**Next action:** groom `bd-ib-waov` into dependency-layered slices via
`/livespec-orchestrator-beads-fabro:groom` — a read-only drafting conversation in
which the **maintainer owns every cut and every acceptance**. Do not file slices
before the groom. A prepared cut (evidence, options, recommendation, per-slice
verifiers with their injected reds) is summarized in §"Prepared slice cut".

## Root cause — a partial terminal-outcome → ledger-transition mapping

**NOT a dead process.** The previous revision of this file claimed `active` is
written before the run and cleared after it inside ONE transient dispatcher CLI
invocation, so "if that process does not survive to the second half, nothing ever
moves the item." The reproduction refutes that: the dispatcher survived the entire
dispatch — it ran, merged the PR, ran the post-merge janitor, and journaled a
terminal outcome, calibration, review-gate telemetry, and reflection. It reached
the second half. Process death is one way in, not the cause.

`_dispatcher_loop_selection.py:170-179` is the whole disposition branch, and it
holds exactly three conditional exits from `active`:

```python
if outcome.status == "green" and args.close_on_merge:   # -> acceptance
    complete_and_accept(...)
journal.append(record={"stage": "outcome", "outcome": asdict(outcome)})
escalate_needs_human_block(...)                          # -> blocked (needs-human only)
bounce_non_convergence_to_backlog(...)                   # -> backlog (2 narrow signals)
```

`is_non_convergence_outcome` (`_dispatcher_plan.py:273-275`) returns True ONLY for
`status == "stalled-no-progress"`, or `status == "failed"` AND
`NON_CONVERGED_MARKER in outcome.detail`. Its docstring states the narrowness is
deliberate: "Ordinary failures … are NOT non-convergence and must not be bounced."

A `janitor-post-merge` red (`_dispatcher_engine_janitor.py:118-129` —
`status="failed"`, detail = the janitor's stderr tail) matches none of the three
exits. The item stays `active`/`fabro` forever.

So the defect is that **`active` conflates "a run is executing" with "a dispatch
ended in a state nobody defined an exit for", and the WIP cap counts both** — with
no liveness reconcile at the gate, no bound on the claim, and no attention surface.

The admission gate counts rows and never asks whether the claim is still owned
(`_dispatcher_admission.py`):

```
active_count = sum(1 for item in items if item.status == "active")   # :88
free_slots   = max(0, resolve_wip_cap(cwd=repo) - active_count)      # :89
```

## Evidence — measured 2026-07-26 from artifacts

### The live reproduction, in THIS tenant

`bd-ib-w4h4` — P1 bug, status ACTIVE, assignee `fabro`, created
2026-07-20T03:09:54Z, last updated 2026-07-20T18:20:22Z. The **only** active item
in the tenant. Trail from `tmp/fabro-dispatch-journal.jsonl`:

| time (UTC) | stage | meaning |
|---|---|---|
| 2026-07-20T04:57:07Z | `ledger-admit` | admitted → `active`/`fabro` |
| 2026-07-20T05:29:14Z | `fabro-run` exit 0 | the run succeeded |
| 2026-07-20T05:31:52Z | `pull-primary` `Updating c8bde4a..ba9fdaf` | **the PR merged** |
| 2026-07-20T05:34:37Z | `janitor-post-merge` exit 1 | post-merge janitor red |
| 2026-07-20T05:34:37Z | `outcome` | `{stage: janitor-post-merge, status: failed, pr_number: 836, merge_sha: ba9fdaf…}` |
| 16:46, 17:53 | reconcile retries | each re-ran the janitor; each red |

Then nothing. No exit from `active`, six days and counting.

**The stranded item's own work is already shipped.** PR #836 ("fix: protect
janitor stale reclaim race") merged 2026-07-20T05:31:50Z; `ba9fdaf` is an ancestor
of `origin/master`. `git log -S` confirms `ba9fdaf` introduced BOTH guards
`bd-ib-w4h4` demands — the `fcntl.flock` reclaim mutex AND the payload re-read
(`_dispatcher_janitor_lock.py:87-94`). The stranded run is the run that fixed the
bug. That is NOT a discharged acceptance; the maintainer still owns that call.

**Do not un-strand or close `bd-ib-w4h4`.** It is the cleanest available
reproduction and the requirement-1 verifier is modeled directly on it.

### The measured leak rate

Ledger transitions recorded across this repo's whole dispatch history:

| journal stage | meaning | count |
|---|---|---|
| `ledger-admit` | driven INTO `active` | 130 records / **113 distinct items** |
| `ledger-complete` | `active` → `acceptance` | **87 distinct items** |
| `ledger-accept` | `acceptance` → `done` in-dispatch | 18 distinct items |

**26 of 113 distinct admitted items (23%) never received a `ledger-complete`** —
each driven into `active` with no automatic exit. The journal vocabulary contains
**no bounce, no needs-human-block, and no abandonment stage at all**, so nothing
records the reclaim even when it happens.

Terminal outcomes, all time — every non-green row whose item was admitted is a
candidate stranded claim:

| terminal (stage, status) | occurrences | of which admitted |
|---|---|---|
| `done`, `green` | 87 | 87 |
| **`janitor-post-merge`, `failed`** | **20** | 20 (18 distinct items) |
| `fabro-run`, `failed` | 9 | 9 |
| `host-only-refused`, `failed` | 5 | 3 |
| `run-config-overlay`, `failed` | 4 | 3 |
| `merge-poll`, `failed` | 4 | 4 |
| `admission-held`, `failed` | 1 | 1 |

`janitor-post-merge`/`failed` is the LARGEST failure terminal in the repo.
**34 distinct items** have hit some non-green terminal after admission.

### The leak strands more than a WIP slot

Two dispatch lock files are still on disk from 2026-07-24
(`tmp/fabro-dispatch-bd-ib-fe574e.lock`, `…-bd-ib-fjj7f7.lock`; both PIDs dead),
and abandoned janitor worktrees remain under
`~/.worktrees/livespec-orchestrator-beads-fabro/` — including
`janitor-bd-ib-w4h4` and `janitor-reconcile-bd-ib-w4h4`, both at `ba9fdaf`, kept
"for diagnosis" exactly as the outcome detail says. `bd-ib-fe574e` and
`bd-ib-fjj7f7` both appear in the 26-item no-`ledger-complete` list, so the lock
files, the worktrees, and the ledger all corroborate the same abandonment.

Note the irony for requirement 4: the fleet hygiene scan ALREADY detects stale
worktrees, so it sees this failure's shadow while remaining blind to the failure.

## SETTLED — "sometimes recovers" is ad-hoc human recovery, not a code path

The previous revision asked whether recovery is inconsistent or absent, and told
you to settle it FIRST. **Settled: there is NO automatic recovery.**

Every `update_work_item_status` call site in product code:

| site | writes | trigger |
|---|---|---|
| `_dispatcher_admission.py:102` | `ready` | auto-approve |
| `_dispatcher_admission.py:113` | `active` | admission |
| `_dispatcher_completion.py:111` | `acceptance` | green only |
| `_dispatcher_completion.py:188` | `backlog` | non-convergence only |
| `_dispatcher_ledger_close.py:89` | remap target | beads-native normalize (`open→backlog`, `in_progress→active`) — **never leaves `active`** |
| `_dispatcher_acceptance_rework.py:79` | `active` | rework |
| `_drive_policy_valves.py:188` | move target | **human valve** |
| `_drive_valves.py:153/167/194` | ready/done/target | **human valves** |

Nothing leaves `active` without a green run, a non-convergence signal, or a human.
Of the 18 distinct items that hit a `janitor-post-merge` red, **17 are now closed
and 1 (`bd-ib-w4h4`) is still active** — a ~94% ad-hoc recovery rate, which is
exactly the shape that hides a leak: frequent enough to look handled, lossy enough
to leak one slot at a time, monotonically.

The mechanism the previous revision suspected is confirmed and sharper:
`move_item` (`_drive_policy_valves.py:165-196`) guards ONLY the target status
(`target_status not in _MOVE_ALLOWED`, :176) and has **no source-state guard
whatsoever** — `move:<id>:ready` on an `active` item is fully allowed and lands.
Side effect worth noting: the write passes no assignee, so moving out of `active`
leaves `assignee: fabro` behind, against the documented `active ⟹ assignee`
invariant (`work_items/types.py:118`).

## Requirements — all four; the cut into slices is the maintainer's at groom

1. **Reconcile at the gate.** Before computing `active_count`, establish whether
   each `active` item's dispatch is still alive; a dead claim is journaled as an
   abandonment and moved out of `active`. **Use the per-work-item dispatch
   ownership lock, NOT the heartbeat** — see §"The signal already exists".
   Self-healing, no new lifecycle vocabulary, and it runs exactly when the answer
   matters.
2. **Surface it.** An `active` item whose dispatch is dead MUST reach
   needs-attention. Not optional polish: invisibility is why this sat six days,
   and the system's own design expects a human to run `reconcile-merged` while
   nothing ever tells them. **A fix that only reclaims slots re-hides the very
   failure it recovers from.**
3. **Bound the claim.** An `active` claim MUST NOT be able to outlive its dispatch
   without bound. **This is cheaper than "lease vs subsumed" implies** — see
   §"The signal already exists".
4. **Detect it fleet-wide.** A stale-`active` check belongs in the runtime hygiene
   scan. **This is CROSS-REPO and larger than a missing check** — see
   §"Scope boundary". Explicitly the weakest of the four: detection, not
   prevention. It exists so the class is caught in tenants whose dispatcher path
   differs — **but no such tenant exists today, and dropping this slice is the
   standing recommendation; see §"S4 SCOPE".**

**A verifier must be able to fail.** Each requirement needs a test whose injected
defect would make it red. See §"Prepared slice cut" for each slice's red.

## The signal already exists — use the dispatch lock, not the heartbeat

The previous revision pointed requirement 1 at `HeartbeatSink` / `decide_stall`
and flagged that `reconcile-merged-dispatch-lock.md` calls the heartbeat invalid
during the post-merge janitor window. **Both concerns dissolve: the right signal
is already implemented.**

`commands/_dispatcher_dispatch_lock.py` (added 2026-07-19 in `e957b35`, BEFORE
`bd-ib-w4h4` stranded):

- `dispatch_lock_path()` → `tmp/fabro-dispatch-<work-item-id>.lock` —
  **per work-item**, so the gate can ask about one specific `active` claim.
- Payload: `work_item_id`, `pid`, `started_at_epoch`, `dispatch_id` — exactly the
  four fields `reconcile-merged-dispatch-lock.md` mandates.
- `live_dispatch_lock()` → the lock only if its PID is alive, else `None`: a
  ready-made liveness predicate.
- `_dispatcher_loop.py:86-88` writes it at dispatch start and releases it via an
  `ExitStack` callback, so it spans the WHOLE dispatch **including the post-merge
  janitor window** — precisely the window the heartbeat cannot cover.

**The admission gate never asks.** The only consumer is
`_dispatcher_reconcile_merged.py:127`.

Verified 2026-07-26 by executing the real product code: `bd-ib-w4h4` has no lock
file, so `live_dispatch_lock()` returns `None` → correctly classified dead.

### Requirement 3 resolves to "wire in the stamp that already exists"

`DispatchLock` already carries `started_at_epoch` — **and never consults it.**
`_dispatcher_dispatch_lock.py:88-93` judges liveness by bare `os.kill(pid, 0)`,
with an in-code admission: "Known residual risk: this pidfile lock accepts
standard PID-reuse ambiguity."

`_dispatcher_admission_mutex.py:264-280` already solves exactly this, correctly —
`_lock_holder_matches_pid` + `_pid_start_time_mismatches` compare the recorded
`started_at_epoch` against `process_started_at_epoch(pid)` with a tolerance. The
dispatch lock can adopt that helper directly.

**Demonstrated 2026-07-26:** given a lock whose PID is alive but whose
`started_at_epoch` predates that process's real start by 24h,
`live_dispatch_lock()` answers ALIVE while
`_dispatcher_admission_mutex._lock_holder_matches_pid()`, on identical data,
answers DEAD. Requirement 3 is red against current `master` today.

## Coordination hazards — check both before designing

Re-read `SPECIFICATION/proposed_changes/` at thread start; both may have moved.

- **`reconcile-merged-dispatch-lock.md`** (TRACKED, pending, 2026-07-19) —
  load-bearing, and it **ratifies the behavior that stranded `bd-ib-w4h4`**:

  > "A red janitor, missing merged PR, wrong source lane, ambiguous merged PR, or
  > held janitor checkout lock MUST leave the item `active` and report the failed
  > guarded precondition or janitor stage."

  That is deliberate — it preserves the item for the `reconcile-merged` recovery
  valve, on the assumption a human is told to run it. Nothing tells them. This
  collides head-on with requirement 1 unless the clause is bounded by ownership-lock
  liveness — i.e. read as "leave it `active` **for the dispatch that owns it**"
  rather than "leave it `active` unconditionally, forever". Likely one added
  sentence in that pending proposal. **Maintainer ruling required.**

  Its earlier heartbeat objection does NOT block requirement 1, because the
  dispatch-scoped lock it specifies is the signal requirement 1 should read.
- **`wip-cap-zero-dispatch-off.md`** — **now TRACKED on `origin/master`** as of
  `5dd2f8d` (2026-07-25T23:39:00Z), byte-identical to the draft analyzed here. It
  is no longer volatile; sequence against it as a real pending proposal. It
  blesses `wip_cap: 0` as the sanctioned dispatch-off value and touches the same
  admission condition. One concrete constraint follows, worth honoring regardless
  of that proposal's fate: `_dispatcher_admission.py:87-91` computes `active_count`
  only inside `if enforce_cap:`, so **requirement 1's reconcile must sit OUTSIDE
  that branch and must not be gated on "we need a slot"** — otherwise a repo at
  `wip_cap: 0`, or any run with `enforce_cap` false, never reconciles and never
  surfaces a stale claim. Cheap now, expensive to retrofit.

## Prepared slice cut — RECOMMENDED: signal before reclaim

Drafted 2026-07-26, NOT filed. The maintainer owns the cut and the acceptance.

| slice | req | scope | depends on |
|---|---|---|---|
| **S1** harden dispatch-lock liveness: consult `started_at_epoch` (PID + process start time), adopting `_dispatcher_admission_mutex._pid_start_time_mismatches` | 3 | in-repo, pure, small | — |
| **S2** needs-attention lane: `active` item with no live dispatch lock, enriched from the journal terminal `outcome` record (carry `pr_number`/`merge_sha`, hand off `reconcile-merged`) | 2 | in-repo | S1 (soft) |
| **S3** reconcile at the admission gate: per `active` item, no live lock → journal an abandonment and move it out of `active`; must sit outside `if enforce_cap:` | 1 | in-repo | S1 (**required — S3 is unsound without it after a SIGKILL**), S2 |
| **S4** stale-`active` detection in the fleet hygiene scan | 4 | **cross-repo** (see §"Scope boundary") — but see §"S4 SCOPE": recommended DROPPED, as it protects zero tenants today | independent |

**The ordering is the point: S2 before S3.** Shipping the reclaim first produces a
system that silently cleans up after a failure nobody is told about — a worse
record than today's. Both existing reclamation paths
(`_stale_admission_mutex_reclaimed`, `_stale_janitor_lock_reclaimed`) reclaim
silently and journal nothing; S3 must not copy that silence.

Requirement 2 is cheaper than it looks: `_needs_attention_work_items.py` is
in-repo, and `_recorded_host_only_refusals()` ALREADY reads
`tmp/fabro-dispatch-journal.jsonl`, filters `stage == "outcome"`, matches an
`outcome.stage`, and builds an `AttentionItem` lane. The janitor-red record is the
same verified shape (`detail`, `fabro_run_id`, `merge_sha`, `pr_number`, `stage`,
`status`, `work_item_id`). S2 is a near-copy with a different stage match.
`human_valves()` today surfaces `pending-approval`, `acceptance`, and
`blocked`(needs-human) — never `active`.

Rejected: **reclaim-first (S3→S2)**, which re-hides the failure; and **one
combined slice**, which carries four requirements plus a cross-repo leg. Note the
journal's own `sizing-warn` on `bd-ib-w4h4`: "description is 4897 chars (> 1500) …
consider splitting" and "carries 5 enumerated parts".

### ⚠ S4 SCOPE — requirement 4 is speculative today; consider dropping the slice

Requirement 4's stated rationale is that it "exists so the class is caught in
tenants whose dispatcher path differs." **Verified on the forge 2026-07-26: there
is no such tenant.** Two findings, both checkable:

1. **No second dispatcher-bearing orchestrator exists.** The only other
   orchestrator in the family, `livespec-orchestrator-git-jsonl`, vendors the SAME
   `livespec_runtime/hygiene_scan.py` but has **no dispatcher at all** — no
   `_dispatcher_admission.py`, no `wip_cap`, no `status == "active"` admission
   concept anywhere under its plugin scripts. (Its only "dispatch" matches are the
   unrelated CI workflows `bump-pin-from-dispatch.yml` and
   `release-dispatch.yml`.) So requirement 4 protects zero additional tenants
   today; it is insurance against a future backend, not coverage of a live gap.
2. **The scanner is deliberately store-agnostic, and the architecture already puts
   store-derived lanes on the CONSUMER side.** Upstream, `scan_hygiene` is invoked
   only by its own CLI (`hygiene_scan_cli.py`) and its tests — it is a standalone
   git-level tool. Meanwhile `compose_needs_attention` already accepts
   `impl_next` and `human_valve_lanes`, i.e. work-item-derived inputs **supplied by
   the consumer**. That split is intentional: the fleet has more than one
   work-items backend, so a store-reading check cannot live in the shared scanner
   without first inventing a store abstraction upstream.

Put together: "add a stale-`active` check to the fleet hygiene scan" asks a
deliberately store-agnostic scanner to read a store, to protect tenants that do
not exist. The consumer-side home for exactly this check is
`_needs_attention_work_items.py` — **which is where S2 already puts it.**

Recommendation to take to the groom: **drop S4 as a slice.** Either defer it until
a second dispatcher-bearing orchestrator actually exists, or reframe it as a
recorded CONVENTION — each orchestrator surfaces its own stale-`active` lane
through its own needs-attention composition — which S2 already satisfies for this
repo. That reduces the epic from four slices to three and removes the only
cross-repo leg. **This is a scoping recommendation, not a ruling; requirement 4 is
the maintainer's to keep, defer, or drop.**

### ⚠ S2 CONSTRAINT — do not copy the precedent's staleness bug

The precedent S2 should follow carries a latent defect. In
`_needs_attention_work_items._host_only_reasons`, the second loop adds every
journal-derived id with **no status check at all**:

```python
for item_id in _recorded_host_only_refusals(project_root=project_root):
    if item_id not in reasons:
        reasons[item_id] = _RECORDED_REFUSAL_REASON
```

The journal is append-only and never pruned, so an item refused once is surfaced
forever. Measured 2026-07-26: the lane derives five items from journal history
(`bd-ib-qcnbbp`, `bd-ib-fjj7f7`, `bd-ib-lgv`, `bd-ib-tyxzhv`, `bd-ib-p3sjiy`) and
**all five are CLOSED** — the lane surfaces five stale rows today and zero live
ones.

**S2 MUST intersect journal evidence with CURRENT ledger status.** Copied
verbatim, S2 would surface all 18 items that ever hit a `janitor-post-merge` red
— 17 of them long closed — to expose the single live one. That is the same
failure this thread exists to fix, inverted: a signal buried in noise is as
invisible as no signal. The journal record supplies the EVIDENCE (`pr_number`,
`merge_sha`, the failing stage); the ledger supplies the PREDICATE
(`status == "active"`); the dispatch lock supplies the LIVENESS. All three are
required.

The staleness bug in the existing `host-only` lane is a **separate pre-existing
defect**, not part of `bd-ib-waov`. It is recorded here because S2 must not
inherit it; filing it is the maintainer's call.

### ⚠ S2 SHAPE — how to keep S2 in-repo (it is easy to make it cross-repo by accident)

S2 is only the cheap in-repo slice if it is built the RIGHT way. Two natural-looking
choices silently convert it into the same cross-repo shape as S4.

1. **Do NOT invent a new `AttentionKind`.** It is a CLOSED `Literal` in the
   VENDORED runtime (`_vendor/livespec_runtime/attention_item.py`) with exactly
   seven values: `human-valve`, `impl`, `spec`, `plan`, `hygiene`, `internal`,
   `host-only`. Adding an eighth means an upstream `livespec-runtime` change plus
   `just vendor-update livespec_runtime` — the same cross-repo path as S4, and the
   same reason S4 is recommended dropped. `validate_attention_item_id`'s prefix
   sets (`_TWO_PART_PREFIXES = {impl, plan}`,
   `_THREE_PART_PREFIXES = {host-only, valve, hygiene, spec}`) are upstream too.
   **Reuse an existing kind.**
2. **Do NOT route S2 through `human_valves()`.** `compose_needs_attention`
   hardcodes `handoff=Handoff(kind="drive", …)` for EVERY valve lane. But
   `reconcile-merged` is a `dispatcher.py` CLI subcommand, not a `drive` action-id,
   so a valve-routed lane would misdeclare its handoff and a consumer rendering it
   would try to run it as a drive action.

**The correct in-repo precedent is `host_only_items`, not `human_valves`.** It
builds its `AttentionItem` DIRECTLY with `Handoff(kind="shell", command=…)`, and
`build_attention` CONCATENATES it onto the composed list rather than passing it
through `compose_needs_attention`:

```python
compose_needs_attention(… human_valve_lanes=human_valves(…) …)
+ host_only_items(project_root=project_root, repo=repo_name, items=materialized)
```

S2 should follow that pattern exactly: build the item directly, `Handoff(kind="shell")`
carrying the `reconcile-merged` invocation, concatenated in `build_attention`. No
upstream change, no re-vendor.

**One latent trap in that pattern.** Items concatenated this way BYPASS
`_append_if_valid`, so nothing validates their id grammar — an id that violates it
is simply never caught. S2 must therefore keep its id grammar-valid by discipline:
three parts, prefixed with one of `_THREE_PART_PREFIXES`, each component non-empty
and non-numeric (`_is_stable_component`). `valve:<verb>:<work-item-id>` qualifies,
and `verb` is free text (`WorkItemHumanValveLane.verb: str`), so no upstream change
is needed to name the new verb.

### ⚠ S2 CONSTRAINT — "run `reconcile-merged`" is not always an actionable handoff

`bd-ib-w4h4`'s janitor red is **deterministic**, and `reconcile-merged` cannot
recover it. All three attempts (2026-07-20 at 05:34, 16:48, 17:56) produced a
byte-identical failure. The operative line is:

```
error: Recipe `check-coverage` failed with exit code 2
error: Recipe `check` failed with exit code 1
```

Note the `livespec_footgun_guard.py:225` / `bd-guard-emit.py:112` lines that
dominate the captured detail are `"phase": "0-warn"`, `"level": "warning"` — Phase-0
WARNings that do NOT fail the gate. The actual cause is the coverage gate failing
in a FRESH checkout of the merged ref, even though the PR's own CI was green
before merge. Do not misread the warning noise as the failure.

Consequence for S2: a lane whose handoff is bare "run `reconcile-merged --item
<id>`" sends the operator into a loop that has already failed three times. The
lane MUST carry the failing stage, the failure detail, and **how many prior
attempts produced it**, so a repeat failure escalates instead of retrying. A
recovery surface that cannot recover, offered without that context, is another
way to re-hide the failure.

(Why the coverage gate is red in a fresh checkout when pre-merge CI was green is
a SEPARATE question — plausibly systemic, given `janitor-post-merge` is this
repo's largest failure class at 20 occurrences. It is NOT part of `bd-ib-waov`;
noted so the groom does not absorb it by accident.)

### ⚠ S3 DESIGN CONSTRAINT — "no live lock" is NOT sufficient on its own

A naive S3 that reclaims every `active` item with no live dispatch lock would be
**destructive**. There is an uncovered window between the `active` write and the
lock write, and it is not small.

`_dispatcher_loop_command.py:187-231` admits a BATCH and then dispatches it
through a thread pool:

```python
admission = admit_and_select(..., enforce_cap=True)   # writes `active` for ALL admitted
with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
    futures = [pool.submit(dispatch_one, ..., item=item) for item in admission.admitted]
```

`write_dispatch_lock` is called at `dispatch_one`'s entry
(`_dispatcher_loop.py:86`), so an admitted item acquires its lock only when a
worker thread picks it up. `--parallel` **defaults to 1**
(`dispatcher.py:317`), and the admitted batch is bounded by
`min(--budget, free_slots)`. So with `--budget 3 --parallel 1`, items 2 and 3 sit
`active` with NO lock for the full duration of the dispatches ahead of them —
and this repo's journal records individual dispatches of 100+ minutes. The
window is hours, not the ~2s the `bd-ib-w4h4` trail
(`ledger-admit` 04:57:07Z → `dispatch-id` 04:57:09Z) suggests in the budget-1 case.

Note this is the OPPOSITE window from the one the previous revision feared. The
post-merge janitor window is COVERED — the lock is held across it and released by
the `ExitStack` at `dispatch_one` exit. The uncovered window is
**admission → worker-thread start**.

Cleanest resolution, and the one to take to the groom: **write the dispatch lock
at ADMISSION time**, alongside the `active` write in `_dispatcher_admission.py`,
rather than at `dispatch_one` entry — keeping the `ExitStack` release. The lock
then means "this dispatcher process owns this claim" and spans admission →
dispatch → janitor → disposition with no gap, which makes "active with no live
lock" unambiguous and makes requirements 1 and 3 both sound. Weaker fallbacks
(a grace period/TTL before reclaiming; checking whether the admitting dispatcher
process is alive at repo level) do not close the window, only narrow it.

#### Pressure-testing that resolution — four things implementation will hit

The admission-time-lock recommendation was checked against the code rather than
asserted. It holds, with these specifics worth knowing before the work starts:

1. **`dispatch_id` is NOT available at admission.** `dispatch_id = run_id()` is
   generated inside `dispatch_one` (`_dispatcher_loop.py:85`), so an
   admission-written lock carries `dispatch_id: null`. That is already legal —
   `DispatchLock.dispatch_id` is typed `str | None` and
   `_dispatch_lock_from_payload` accepts `None`. `dispatch_one` can rewrite the
   lock to fill the id in once it has one; nothing needs the id to judge liveness.
2. **The pid does not change, only the timing.** The pool is a
   `ThreadPoolExecutor`, not a process pool, so `os.getpid()` is identical at
   admission and at `dispatch_one`. Moving the write earlier changes WHEN the
   claim is stamped, not WHOSE it is.
3. **Every item written `active` does reach `dispatch_one`, so the existing
   release still covers it.** `_dispatcher_admission.py` appends to `admitted`
   only on the same path that writes `active` (:113-119); held items go to
   `refused` and never get an `active` write. The loop then does
   `pool.submit(dispatch_one, …)` for each `admission.admitted`, and the
   `ExitStack` fires on both normal return and exception. Leave the release where
   it is.
4. **A leaked lock file is HARMLESS, and that property is what makes this safe.**
   Liveness is PID-keyed, so a lock whose owner is gone reads dead and the item is
   reclaimable. Do NOT add cleanup machinery for leaked lock files — there is
   nothing to clean up correctness-wise, and cleanup would reintroduce the
   unlink-by-pathname TOCTOU class that `bd-ib-w4h4` was filed about.

**This makes the S1 → S3 dependency load-bearing, not a preference.** Consider a
loop process killed by SIGKILL: the `ExitStack` does not run, so its locks leak
with that pid recorded. If the OS later recycles that pid to an unrelated live
process, a bare `os.kill(pid, 0)` check reports the stale lock as LIVE and the
stranded item is **never** reclaimed — the exact bug this thread exists to fix,
reintroduced through the fix itself. Only S1's PID + `started_at_epoch` check
distinguishes "the original owner" from "some new process that inherited its pid".
S3 without S1 is not merely weaker; it is unsound after any SIGKILL.

### Verifiers — each with the injected defect that makes it red

| slice | test | injected defect that makes it RED |
|---|---|---|
| S1 | lock whose `pid` is live but whose `started_at_epoch` long predates that process's real start → assert DEAD | **none needed — red against current `master` today** (demonstrated above); the cheapest honest red available |
| S2 | `active` item + no live lock + journal `janitor-post-merge`/`failed` record → assert a needs-attention lane naming the item and its merged PR | drop the lane → red |
| S2 (no staleness) | an item with a `janitor-post-merge`/`failed` record in the journal that is now CLOSED → assert NO lane is emitted | key the lane off journal history alone (as the `host-only` lane does today) → the closed item is surfaced → red |
| S3 (positive) | `active` item, no lock file → run the gate → assert moved out of `active` AND an abandonment journal record written | remove the reconcile call → item stays `active` → red |
| S3 (negative) | `active` item WITH a lock written for `os.getpid()` → assert it STAYS `active` and still counts against the cap | make the reconcile ignore lock liveness → it reclaims a live run → red |
| S3 (cap-independence) | `enforce_cap` false / `wip_cap` 0 → assert the reconcile still runs | nest the reconcile inside `if enforce_cap:` → red |
| S3 (admission window) | admit a batch larger than `--parallel`, run the gate while the queued items are still awaiting a worker → assert the queued `active` items are NOT reclaimed | leave `write_dispatch_lock` at `dispatch_one` entry → the queued items have no lock → reclaimed → red |
| S3 (recycled pid) | leaked lock recording a pid now held by an unrelated LIVE process, stamped with the original owner's start time → assert the item IS reclaimed | judge liveness by bare `os.kill(pid, 0)` (i.e. ship S3 without S1) → the stale lock reads live → never reclaimed → red |

The S3 negative test is what discharges `reconcile-merged-dispatch-lock.md`'s
objection: it proves a live dispatch inside its janitor window is never reclaimed.
S3's positive test must assert BOTH the transition AND the abandonment record, or
it passes vacuously on a status the healthy path also produces.

### Questions only the maintainer can settle

1. **Spec collision.** Does `reconcile-merged-dispatch-lock.md`'s "a red janitor …
   MUST leave the item `active`" get bounded by ownership-lock liveness (one added
   sentence, keeping requirement 1 legal), or does requirement 1 narrow to
   "surface only, never auto-reclaim"?
2. **Reclaim destination.** Where does S3 send a reclaimed item? `backlog` follows
   the `bounce_non_convergence_to_backlog` precedent, but for a MERGED-yet-janitor-red
   item the PR is already shipped, so `backlog` misrepresents it; `blocked`
   (needs-human, pointing at `reconcile-merged`) may be truer.
3. **Requirement 4 scope upstream** — see below.
4. **The slice cut itself**, and each slice's acceptance criteria.

## Scope boundary

- The console (`livespec-console-beads-fabro`) is a **consumer** and owns nothing
  in this fix; its only input is `dispatcher.wip_cap`. Do not route any part of
  this into that repo.
- **Requirement 4 is CROSS-REPO.** `hygiene_scan*.py` exists in this repo ONLY as
  a vendored copy at `.claude-plugin/scripts/_vendor/livespec_runtime/`, sourced
  per `.vendor.jsonc` from `https://github.com/thewoolleyman/livespec-runtime` at
  ref `v0.13.0`; `justfile` records `just vendor-update <lib>` as "the only blessed
  mutation path per livespec/SPECIFICATION/constraints.md §Vendoring". It CANNOT
  be implemented by editing this repo — it lands upstream in `livespec-runtime`
  and is then re-vendored. It is also **larger than "no `active` check today"**:
  `scan_hygiene` is a "Git-level hygiene scanner" taking `repo_path`, not a store
  config, and its four finding families (stale worktrees, primary health, stale
  branches, stale PRs) mean it **never reads the work-items store at all**.
  Requirement 4 is therefore "give the fleet scanner work-item-store awareness",
  a scope expansion upstream — not a one-line addition.
- Core `livespec` is involved ONLY if the design elects new lifecycle vocabulary
  or a documented lease semantic. A reconcile-at-admission fix re-derives existing
  statuses and needs neither.

## Read first

1. This file, then `supervisor-handoff.md` beside it.
2. `bd-ib-waov` in the ledger — **but read it with this caveat.** As of
   2026-07-26 its description still carries the SUPERSEDED root cause ("a
   dispatcher whose process then dies … if that process does not survive to the
   second half"), still points requirement 1 at the heartbeat/`decide_stall`
   primitives, and still frames requirement 4 as in-repo. THIS FILE is the current
   record on all three. The epic was deliberately NOT rewritten from this thread:
   restating it is a ledger write on a maintainer-owned record, and the groom is
   where that restatement belongs. **Restating `bd-ib-waov`'s description is
   itself a groom deliverable.**

Product paths below are all under
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/`:

3. `commands/_dispatcher_admission.py` (`:88-89` the arithmetic, `:114` the write).
4. `commands/_dispatcher_loop_selection.py:170-179` — the three-exit disposition
   branch that IS the defect.
5. `commands/_dispatcher_plan.py:240-275` — `is_non_convergence_outcome`, whose
   deliberate narrowness leaves the janitor-red path with no exit.
6. `commands/_dispatcher_dispatch_lock.py` — the liveness signal requirement 1
   must reuse, and the unused `started_at_epoch` that answers requirement 3.
7. `commands/_dispatcher_admission_mutex.py:264-280` — the correct PID+start-time
   liveness precedent, and (`:205-229`) the TOCTOU-correct reclaim pattern.
8. `commands/_needs_attention_work_items.py` — the in-repo journal-reading
   attention-lane precedent requirement 2 should follow.
9. `SPECIFICATION/proposed_changes/` — both hazards above.
