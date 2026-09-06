# factory-spend-containment — opening research note, 2026-08-22

## Why this thread exists

The maintainer holds ONE OpenAI Codex subscription and five Anthropic Claude
subscriptions (about $1,200/month). The Codex allowance was on track to exhaust
before its window reset, and the stated goal is explicit: **do not buy a second
Codex subscription.** This thread exists to hold the containment work as a
governed plan rather than the sequence of one-off fixes it started as.

Two fixes were already built and merged before this thread existed (PR #1711,
PR #1712's successor #1732). Backfilling them as spec-carried children is part
of this thread's scope, not an afterthought — see "Retroactive coverage" below.

## Notation used in this document

- **Agent-hour** — one hour of wall time inside an ACP agent turn, summed from
  the `run_turn` spans in the `fabro` Honeycomb dataset. It is a PROXY for token
  spend, not a measurement of it: there is no Codex token telemetry anywhere in
  the stack (see Gap T3).
- **Run-hour** — one hour of a Fabro run's total wall time, including time spent
  parked at a human gate doing nothing. Distinct from agent-hours: a run can
  burn run-hours at zero token cost.
- **Diagnosable failure** — a failed run whose `fabro inspect --json` payload
  contains a failure block carrying a `causes` chain. Failures terminated by the
  stall watchdog carry a category but no causes.
- **Control** — a deliberate second measurement designed to produce the OPPOSITE
  answer. A check that cannot fail is not evidence.

## Measured baseline (2026-08-22)

Fleet-wide, from the `fabro` dataset's `run_turn` spans, which carry the ACP
adapter command and therefore attribute vendor exactly.

Seven days of Codex agent-time, by workflow node:

| node | vendor | turns | agent-hours | share of Codex |
|---|---|---|---|---|
| `implement` | Codex | 369 | 69.3 | 77.8% |
| `pr` | Codex | 254 | 12.4 | 14.0% |
| `review_fix` | Codex | 46 | 6.4 | 7.1% |
| `fix` | Codex | 13 | 1.0 | 1.1% |
| **Codex total** | | **682** | **89.0** | |
| `review` | Claude | 316 | 12.9 | — |
| `disposition` | Claude | 44 | 0.9 | — |

Codex is 87% of all factory agent wall-time. The rate is rising, not flat: the
last 24 hours alone were **36.5 Codex agent-hours**, roughly 2.9x the seven-day
daily average.

Waste, two independent instruments in agreement:

- 51.2 of 89.0 Codex agent-hours (**57.5%**) sit in runs that never emitted
  `Workflow run completed` — work performed and discarded. 50.9 of those hours
  are the `implement` node; only 0.13 reached `pr`.
- `fabro ps -a` on the hp factory: 53 failed runs consuming **118.2 of 216.8
  run-hours (54.5%)**, averaging 2h14m each against 23m for successes.

The two agree within three points by different routes, which is what makes the
number usable.

## Root causes, in the order they bite

### C1 — Provider quota exhaustion is classified retryable

The single largest diagnosable cause. All 53 failed runs were inspected:

| | count |
|---|---|
| failed runs inspected | 53 |
| with a diagnosable cause chain | 13 |
| **provider usage/spend refusals** | **11** (10 Codex, 1 Anthropic) |
| codex remote-compaction 404 | 2 |
| **failure blocks classified `transient_infra`** | **17 of 17** |
| no cause block (stall-watchdog / abandon) | 40 |

The verbatim payload, run `01M0DN6CTWPF`, at `causes[1]`:

```json
{ "message": "You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage
              to purchase more credits or try again at Aug 20th, 2026 3:33 AM.",
  "codex_error_info": "usage_limit_exceeded" }
```

fabro labelled it `transient_infra`, so `will_retry=true`; it retried against an
allowance already gone, died again in 3.4s, then parked at `escalate` for four
hours. These arrive in BURSTS — three at 240m and three at 152m inside two
ID-adjacent windows — because once the window is exhausted every subsequent
dispatch marches into it. Cost: 21.1 of the 118.2 failed run-hours.

A near-miss worth not rediscovering: the fabro fork branch
`fix/classify-provider-spend-limit-not-transient` (`3b3781888`) is NOT an
ancestor of the running `8de6611` binary, and would not fix this even merged. It
matches `"you've hit your limit"`; the Codex phrase is `"hit your USAGE limit"`.
The infix defeats the substring match. The reliable discriminator is the
structured `codex_error_info == "usage_limit_exceeded"`.

### C2 — A dead implementer keeps spending

Recorded on `bd-ib-oj71` and independently corroborated: with the implementer
dead from its first turn, the workflow still cycles janitor, **four Claude Opus
review rounds**, and disposition against a branch byte-identical to
`origin/master`, plus 16 empty process-stage commits. **Codex exhaustion
therefore burns the Claude subscriptions too.** There is no circuit breaker.

### C3 — The human gate costs four hours and nobody can answer it

Every escalation is a fixed ~4h of sandbox and scheduler slot. Measured
sequence, identical across three dumped runs: implement fails -> edge to
`escalate` -> `Run blocked blocked_reason=HumanInputRequired` -> nobody answers
-> `Stall watchdog timeout node="escalate" idle_seconds=7200` -> run failed at
`wall_time_ms=14400002`.

The reported `idle_seconds=7200` does not reconcile with the 4h wall, so the
mechanism that actually enforces the ceiling is NOT established. Do not tune
`stall_timeout` before establishing which knob fires.

Critically, **no actuator at any autonomy level can answer that gate.**
`foreman_act_types.ActionId` is a closed 15-value set and none of them addresses
a live Fabro run; `grep -rn "fabro attach"` across the overseer plugin returns
zero, and every `blocked:human` path there operates on tmux pane state. The
`foreman-full-autonomy-option` plan's D6 floor (ii) keeps "no keystroking into a
structured gate outside `foreman-act`" even under full autonomy, and its D7
cross-repo ask routes `blocked_reason: needs-human` ITEMS to the foreman panel —
a ledger disposition that arrives after the run is already dead.

So the fix is not "who answers the gate". It is: stop making answering the gate
the only way to preserve the work. `bd-ib-6o6h` states it best — *"'ask a human'
and 'discard the work' are the same action whenever nobody answers."*

### C4 — The evidence needed to see any of this does not reach anyone

Three compounding gaps, each proven with a control:

- **T1.** The Dispatcher journals `fabro_failure_cause`, `_category` and
  `_signature` as **null on 17 of 17** failed fabro-run outcomes since the
  capture shipped, including one from 2026-08-22T05:40:57Z on the current
  released build. Excluded: staleness, causeless blocks (those still populate
  `category`), missing run ids, failed inspects, and the parser — the parser was
  exercised end-to-end against a real 144,492-byte payload through the
  production classes and returns the detail correctly. Filed as `bd-ib-nf39`.
- **T2.** Calibration telemetry never leaves the host. 245 `calibration` journal
  records exist; the `livespec-dispatcher` Honeycomb dataset has 52 columns and
  not one calibration field. `_driver_span_paths` tails exactly three span FILES
  and the journal is not one of them, though `emit_calibration`'s docstring
  claims it "rides the journal -> Honeycomb leg". There is no such leg. Also in
  `bd-ib-nf39`. Related: `detail`, `exit_code`, `dispatcher.stages` and
  `dispatcher.final_stage` were last written 2026-06-14.
- **T3.** There is **no Codex token telemetry at all**. `livespec.cost.*` models
  Anthropic only (`model_basis: default:claude-opus-4-8`), and `observable` is
  false on 997 of 1000 sampled `cost.report` spans. Every spend number in this
  note is a duration proxy in consequence.

## Retroactive coverage — what already shipped without spec cover

Both landed before this thread existed and are live fleet-wide, verified four
ways (release tag containment, the executing build SHA `088d313a361e` = v0.65.1,
live `run_turn` telemetry showing only pinned adapters, and a cross-repo
`livespec-overseer` dispatch carrying both pins).

- **PR #1711** — per-node Codex model tiers. Before it, the implementer adapter
  carried no `-c model=` at all: the sandbox bakes `codex-acp@0.16.0`, whose
  models-manager cannot decode the present-day catalog (`unknown variant "max"`),
  so it fell back to a static list and landed on `gpt-5.5` at `medium`. Nobody
  chose that. Now `implement`/`fix`/`review_fix` pin `gpt-5.5` at `low` and `pr`
  pins `gpt-5.4-mini` at `high`, configurable per repo via
  `dispatcher.codex_models`.
  Measured constraint: `gpt-5.6-luna`, `gpt-5.6-terra` and `gpt-5.3-codex` are
  ALL refused by the backend from this adapter (HTTP 400). The reachable tiers
  are 5.5, 5.4 and 5.4-mini until `CODEX_ACP_VERSION` is bumped.
- **PR #1732** — provider usage limits classified permanent, the root cause
  surfaced instead of the `"ACP protocol error"` wrapper (a fixed constant in
  17 of 17 measured blocks), and `FabroFailureDetail.provider_usage_limit` added
  as the typed seam an admission gate consumes.

Neither carries a specification commitment. **A ratified spec today would not
describe the factory that is running.** That is this thread's first debt.

Note the honest limit on PR #1732: it is DIAGNOSTIC, not preventive. fabro's own
classifier runs inside the sandbox and still marks the refusal transient, so the
wasted retry still happens. What changed is that the outcome names the quota.

## Prior art this thread must not re-litigate

- `bd-ib-oj71` (backlog) — the Codex usability preflight and the dead-implementer
  circuit breaker. Carries seven riders; two are satisfied by PR #1732, and one
  BINDS any preflight design: host and sandbox Codex credential state diverge by
  construction (`project_codex_auth_snapshot` replaces the refresh token with
  `CODEX_NON_ROTATABLE_REFRESH_SENTINEL`), so a host-side `auth.json` read is a
  proven-insufficient probe.
- `bd-ib-rnlks6` (pending-approval) — blocked runs hold scheduler slots, measured
  by controlled intervention. Its warning is binding: reaping on a timer converts
  a visible stall into silent data loss.
- `bd-ib-6o6h` (backlog) — an interview raised with unpushed work destroys it.
- `bd-ib-o3ui` (backlog) — 17.2% of review gates not-reached; exit criterion
  <= 5%.
- `bd-ib-3al8` (backlog) — a clean operator Abandon finalizes as `workflow_error`.
- `bd-ib-g56f` (backlog) — the sibling record of the swallowed-cause family.
- `bd-ib-cewr` (backlog) — the silent-failure-surfaces epic; `bd-ib-nf39` is
  filed as its child.

## Ordering constraint

Preserve-by-reference must land BEFORE any shortening of the gate window.
Shortening first converts a visible stall into faster loss. Similarly, do not
raise `max_retries` before the classifier is correct: more retries against a
misclassified quota refusal spends the exhausted allowance harder.

## The evidence base is perishable, and nothing in the ledger says so

Added 2026-08-22 after the opening pass, because this is the one binding fact
about this thread that lives in no work-item and would be silently destroyed by
a routine maintenance command.

Every measurement above — the 53-run failed cohort, the 13 diagnosable cause
chains, the 11 provider-limit refusals, the burst timing, and the three `fabro
dump` exports the C3 gate sequence was reconstructed from — is derived from runs
held in the **hp factory's own storage**. Nothing has copied them anywhere. They
are retained only because nothing has garbage-collected them yet.

**`fabro system prune --yes` with no filters deletes them.** Verified from the
binary's own help text on the running build: `--older-than <DURATION>` documents
itself as *"Default: 24h when no explicit filters are set"*, and `--yes` turns
the default dry run into a real delete. So the unqualified invocation is not a
narrow cleanup; it is a 24-hour retention cut across every run on the server.

Measured against hp on 2026-08-22 (`fabro ps -a --server
https://hp-xubuntu.perch-rudd.ts.net:32276 --json`, 338 runs):

| start date | runs |
|---|---|
| 2026-08-16 | 1 |
| 2026-08-17 | 35 |
| 2026-08-18 | 28 |
| 2026-08-19 | 63 |
| 2026-08-20 | 49 |
| 2026-08-21 | 102 |
| 2026-08-22 | 60 |

**278 runs started on or before 2026-08-21, of which 54 are failed** — the
cohort this thread's entire causal analysis rests on, still intact and still
entirely inside the default prune window.

Two consequences, in the order they bite:

1. **C1 through C6 become unreproducible.** Not merely un-recheckable: the
   controls that make the numbers usable — the two independent instruments
   agreeing within three points, the 11-of-13 diagnosable split, the verbatim
   `usage_limit_exceeded` payload — cannot be re-derived from anything else.
   `livespec.cost.*` models Anthropic only (gap T3), so there is no second
   record of Codex spend anywhere in the stack.
2. **`bd-ib-d0ul`'s own design would arrive broken.** C6 is
   preserve-by-reference: a blocked or dead run leaves a *pointer* to its
   checkpoint — run id, factory URL, stage artifact path, size and digest —
   rather than an inlined diff. Every pointer it writes resolves against exactly
   the storage a prune empties. Pruning the backing runs before C6 lands means
   its first act on arrival is to mint dangling references.

**Constraint: do not run `fabro system prune` on hp — filtered or not — while
this plan is live, and specifically not before C6 (`bd-ib-d0ul`) has landed.**
If storage pressure forces the issue sooner, export first: `fabro dump <run>
--server https://hp-xubuntu.perch-rudd.ts.net:32276 -o <dir>` reaches a remote
run's store and exports its stage artifacts (verified: 61 files on run
`01M0H73GQ8Y0`, 34 including a 21,949-byte `diff.patch` on another). Dump the 54
failed runs before pruning anything, and record where the export landed here.

This is an ordering constraint of the same kind as the two above it, and it is
listed separately only because its trigger is a maintenance action rather than a
development one — nobody would think to check a plan before running a cleanup.

## Two observations from the C3 ratification pass, 2026-08-23

**The Codex allowance was exhausted during this thread's own first dispatch, and
that is where the headroom number finally came from.** Dispatching C6
(`bd-ib-d0ul`) produced run `01M0PYKEEC26SRSG8W16HB2NWP`, whose Dispatcher
outcome carried `fabro_failure_category: deterministic` and the provider's own
message verbatim — *"You've hit your usage limit … try again at Aug 27th, 2026
1:20 AM."* Three corrections to this note follow from it. First, the headroom
question recorded above as unmeasurable (Cloudflare on the backend endpoints, no
answer from the app-server RPC) never needed the Codex TUI: **a dispatch outcome
carries the reset instant**, which is the same seam C4 consumes. Second, **gap
T1's "null on 17 of 17" no longer holds** — both `fabro_failure_cause` and
`_category` are populated, with the root cause rather than the `ACP protocol
error` wrapper, so PR #1732's Dispatcher-side leg works and `bd-ib-nf39` should
be re-scoped rather than re-verified. Third, **deferral D1 is confirmed rather
than superseded**: `transient_infra` still appears inside the run's own inspect
payload, so fabro's in-sandbox classifier still calls a quota refusal transient,
which is why the run retried into the dead window before parking. Four blocked
runs on hp across two repositories carried the identical string and reset, so the
ceiling is on the ACCOUNT — which is why C4's exhaustion record must be keyed on
the provider and never on the factory, or it would read healthy on `vps` and
admit straight into the same dead allowance.

**A defect class worth knowing about, logged and deliberately not investigated.**
The independent ratification review caught a normative clause contradicting its
own binding scenario: §"Provider spend containment" required every containment
disposition to journal the provider and the record's expiry, while the
cause-agnostic dead-implementer truncation has neither, and Scenario 61 — written
to bind that very clause — journaled only two fields. **No structural check could
have caught it**, because both artifacts are individually well-formed, every
gherkin fence balances, and the heading-coverage map is satisfied; the
contradiction lives only in the relationship between them. A test written
verbatim from Scenario 61 would have passed a journal record the contracts clause
forbids. Whether any gate covers this class is unknown and is not this thread's
question.

## Correction, 2026-08-23: the reset instant in the refusal message is false

**The section immediately above draws one conclusion that measurement
falsifies.** It is otherwise accurate and stands: the exhaustion was real, the
Dispatcher outcome did carry the provider message verbatim, gap T1's "null on 17
of 17" really is discharged, and deferral D1 really is confirmed. What is wrong is
the inference that *"a dispatch outcome carries the reset instant"* gives C4 a
usable expiry. **It does not. The instant the provider names is not the instant
the block clears, and it is wrong by orders of magnitude.**

The refusal quoted above claimed a block until `Aug 27th, 2026 1:20 AM` — roughly
95.9 hours. Measured against it, all on 2026-08-23 on the hp factory:

- Run `01M0PYKEEC26SRSG8W16HB2NWP` (this thread's C6 dispatch) started `09:18:34Z`
  and carried the refusal.
- Run `01M0PZ4PRVVK` started `09:27:58Z` — **nine minutes and twenty-four seconds
  later** — and **succeeded** at `10:04:49Z`, its Codex `implement` and `pr` nodes
  both completing.
- Run `01M0Q01QB15W` started `09:50:36Z` and succeeded at `10:20:24Z`. Its
  `inspect` payload shows `acp_adapter` on `gpt-5.5` and `pr_adapter` on
  `gpt-5.4-mini` — the same two tiers this repo pins — with `implement` burning
  1,259,235 ms of inference. **Not small-request tolerance: a full twenty-one
  minute implement.**
- A direct host probe at `10:40Z` (`codex exec` on `gpt-5.5`, default
  `CODEX_HOME`) returned normally.

**The control, because the obvious escape is that a different account served
those runs: it was the same account.** The Dispatcher projects a snapshot of the
host's single `auth.json`; its mtime is `2026-08-14T10:27:41` and unchanged, and
the `account_id` inside it is unchanged. No rotation occurred between the refusal
and the successes.

**Why this was missed, which is the part worth keeping.** The earlier pass quoted
the provider accurately and reasoned from the quote. It never asked whether any
*other* dispatch had succeeded since — and the falsifying evidence was already in
the `fabro ps` output it had been reading, because `livespec-overseer` was
dispatching Codex through this identical dispatcher and succeeding continuously
throughout the supposedly-dead window. This is AGENTS.md's wrong-population trap
one level on: the instrument was healthy and the quote was real, but the question
asked of it was *"did the provider say the window is closed"* rather than *"is the
window closed"*.

**What it changes.** C4's third acceptance criterion previously read that each
exhaustion record carries an expiry instant and the dispatcher admits normally
once it has passed — which a builder satisfies by storing the provider-named
instant. From this one observed refusal, that gate would have idled the factory
until `2026-08-27 01:20` while the provider served traffic within ten minutes,
**and it would have justified itself by quoting the provider.** `bd-ib-jtja` now
carries seven criteria: the expiry must be *derived by the dispatcher*, the
provider-named instant must never be adopted as it, and one observed refusal must
not hold admission for the multi-day interval the message asserts. The item's own
DESIGN NOTE had already floated "hold until a later dispatch succeeds" as a
conservative alternative; that is now the requirement rather than a preference.

**Do not over-read this.** The typed `provider_usage_limit` condition remains the
right input for C4, and the account-keying conclusion above is untouched — the
ceiling is still on the provider, not the factory. Only the **duration** the
message asserts is false.
