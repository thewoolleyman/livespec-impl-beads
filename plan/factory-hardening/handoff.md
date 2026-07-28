# Handoff — factory-hardening

## What this thread is

Reliability hardening of the **dark-factory dispatch path** — the two failure
modes that each cost a real dispatch cycle during the `codex-credential-broker`
track (epic `bd-ib-rck`, CLOSED) and were filed as out-of-scope follow-ups.

## ▶ CURRENT STATE + NEXT ACTION (read this first)

**Status, end of 2026-07-28: nothing is blocked, nothing is in flight, and the
only remaining owned work is slice B, which is not this repo's code.**

| Item | Status now | Disposition |
|---|---|---|
| `bd-ib-bwgko4` | **CLOSED** | Superseded — its fix shipped 2026-07-24 as `bd-ib-qq7f` / PR #905. |
| `bd-ib-wefw` | **CLOSED** | Slice A. Built and shipped through the factory: PR #1064, merge `2ae4b2b`. |
| `bd-ib-eha3wh` | **CLOSED** | Adopted, dispatched: PR #1063, merge `b510433`. Read the caveat below. |
| `bd-ib-wmqsn7` | **`backlog`** | The epic. Slice A is done; **slice B remains** and is cross-repo. |
| `bd-ib-bic7hb` | `ready` — **NOT OURS** | Owned by `plan/dispatch-claim-liveness/` since 2026-07-26. |

**Next action (maintainer), and it is a ruling, not a task:** slice B changes
`check-master-ci-green` in **`livespec-dev-tooling`**, and it rests on the vantage
policy question already routed to you on `livespec-dev-tooling-gam8` (2026-07-25).
Slice A has now landed, which was the ordering precondition — so slice B is
unblocked the moment you rule. Nothing in THIS repo is waiting on anything.

## Slice A shipped — what actually landed, and how it was verified

`bd-ib-wefw`, dispatched through the factory (fabro run `01KYKEKWAY1D`, ~44 min,
$0.72 API-equivalent), merged as PR #1064 / `2ae4b2b`:

- `_dispatcher_master_ci_preflight.py` (new, 256 lines)
- `_dispatcher_run_checks.py` (+12) — wired into `dispatch_preamble` immediately
  after the source-checkout refusal, journalling before it writes stderr and
  returning `_EXIT_PRECONDITION_ERROR`
- `test_dispatcher_master_ci_preflight.py` (new, 337 lines, 20 tests)

Full Red→Green trailers present; the Red captured 19 failing tests.

**It reads the `ci-green` job's conclusion, not the run's rolled-up conclusion** —
the correction forced by live evidence during the dispatch (see below). Pending
run → proceed; red `ci-green` → refuse; `ci-green` missing, pending, unrecognized,
or unfetchable → refuse as *unprovable*; `gh` absent or uncredentialed → proceed;
credentialed call failing → refuse. There is no env var, flag, or lever anywhere
in the module.

**The verifier was demonstrated to fail, not assumed to.** In a throwaway
worktree the exact defect was injected — classify from `run["conclusion"]`
instead of the `ci-green` job — and the suite went from 20 passed to **14 failed**,
including `test_run_rollup_failure_proceeds_when_ci_green_succeeded` and
`test_lever_env_cannot_make_red_master_pass`. The worktree was then discarded.
A live smoke run of the merged `master_ci_preflight_refusal()` against real repo
state returns PROCEED on a green master.

**Which red does this still refuse?** Any failure in `check-python`,
`check-doctor-static`, `check-metadata`, `e2e-cli`, or `acceptance` — the five
jobs `ci-green` declares in its `needs`. It refuses strictly more than the naive
design in two places: an unrecognized `ci-green` conclusion refuses (the
in-sandbox gate treats that as non-blocking), and a missing `ci-green` job
refuses rather than proceeding.

## Caveat on `bd-ib-eha3wh` — it was already fixed before it was filed

Adopted and dispatched in good faith on the item's own claim of a "latent factory
outage". **That claim was false, and this file previously repeated it.** Commit
`c6ae317` (2026-07-19, *"fix(ci): feed jq its large JSON payloads on stdin, not
argv"*) had already moved both genuinely-unbounded payloads to stdin — five days
before the item was filed on 2026-07-24.

The item's description was also **wrong about one of its two named sites**:
`--argjson run "$run_span"` is a single *bounded* span, not a growth site, and the
script carries a comment saying exactly that. The dispatched agent found the fix
present, correctly declined to "fix" the bounded site, and landed static
regression guards — including `test_bounded_run_span_stays_on_argv`, which pins
the *inverse* assertion and protects against a future agent acting on the bad
advice. It used `chore: cover`, not `fix:`.

Honest scope: acceptance criteria 2 (an oversized-payload regression exercise)
and 3 (byte-equivalent output) were **not** delivered; three static text
assertions over the script source were. They can genuinely fail — reverting
`run_json` to `--argjson` reddens one — but they are weaker than asked. Closing
is still right. Do not read PR #1063 as "a live E2BIG bug was fixed."

## The stale-row pattern — read this before trusting any row on this thread

**Two of the four items handled on 2026-07-28 asserted defects the repo had
already cured**, and neither was caught by reading the item, the code, or the
plan file — only by reading the *merged diff*:

- `bd-ib-bwgko4` — fixed by `bd-ib-qq7f` / PR #905 (2026-07-24), row untouched
  since 2026-07-15.
- `bd-ib-eha3wh` — fixed by `c6ae317` (2026-07-19), filed 2026-07-24 anyway.

The fix landed, nobody reconciled the open row, and the ledger kept asserting a
live defect. `bd-ib-eha3wh`'s description names **three other drifted fleet copies
of the same script** — diff each against `c6ae317` before filing or dispatching
any of them.

## Correction: the gate that was actually holding both items

Earlier revisions of this file, and the thread's supervisor charter, stated that
both items were "BLOCKED on autonomy-tiering" with `autonomy_tiered = False`.
**That was wrong, and it pointed at a remedy that could not have worked.**

Both items carried the beads label `blocked-reason:needs-human`.
`SPECIFICATION/contracts.md` §"The four maintainer touchpoints" makes these two
distinct gates on the intake Definition-of-Ready:

- *"The acceptance is autonomously verifiable with no human judgement call."*
  Failing this routes the item to **`blocked` with
  `blocked_reason: needs-human`** — the state both items were actually in.
- *"An autonomy tier is assigned — spec-change is human-gated … everything else
  is factory-dispatchable."* Failing this has **no route to `blocked` at all**.
  A spec-change routes to `/livespec:propose-change`; everything else is simply
  dispatchable.

So the gate holding both items was their **acceptance**, and in both cases for
the same reason: the acceptance named a field event nobody can summon on demand
("a dispatch whose run straddles a `.github/workflows/` change on master…",
"a transient master-CI network flake no longer stalls all factory dispatches").

The remedy the charter proposed — `set-admission:<id>:auto` — would not have
moved either item. `set_policy` in
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_drive_policy_valves.py`
writes the policy field and returns `"status unchanged"`, and
`admission_policy` is consulted only at `pending-approval`
(`_drive_valve_predicates.can_approve_item`). The valve that actually clears a
`needs-human` block is **`resolve-blocked:<id>:ready|backlog`**, which is also
the only one that clears `blocked_reason`. That is the valve used on 2026-07-28.

## `bd-ib-bwgko4` — CLOSED, superseded

The stale-workflow push-gate race is **fixed and live**. The item sat `blocked`
from 2026-07-15 and was never updated while the same defect was independently
re-filed as **`bd-ib-qq7f`** on 2026-07-23, dispatched through the factory, and
merged on 2026-07-24 as PR #905 (`231e9a48`, *"fix: refresh PR publish base
before push"*), with a paired test
`tests/integration/test_pr_stage_prompt_publish_freshness.py`. `bd-ib-qq7f`
closed 2026-07-25 with `resolution:completed`.

The merged `pr.md` now carries exactly what `bd-ib-bwgko4` asked for — a
`git fetch origin master` + `git rebase origin/master` immediately before the
push leg, with a conflicts route to the needs-human protocol — plus a bounded
one-shot retry on the exact quoted rejection signature, which `bd-ib-bwgko4` did
not ask for.

**The pin mechanic was checked, not assumed.** The charter correctly warned that
a dispatch runs the workflow from the *pinned plugin version*, not from the repo
checkout, so "merged to master" does not by itself mean "in effect". Verified
separately by scanning every `implement-work-item/prompts/pr.md` under
`~/.claude/plugins` and classifying each copy: the currently installed version
`c878ea43f8cd` **does** contain the rebase instruction. The fix is live in the
running factory.

`bd-ib-qq7f`'s AC4 — this item's acceptance — was discharged there with an
explicit scope note worth preserving: the first real publishing dispatch after
the merge (`bd-ib-pums`, run `01KY9QWV0EPPY053K0ABE6W8MY`, PR #915 merged
2026-07-24T10:15:42Z as `03c8bf35`) drove the pr stage end-to-end in production,
but no competing merge landed during the ride, so the fetch+rebase ran against
an unmoved base. The clean-publish leg is observed live; the contended-base
variant was never naturally exercised. `bd-ib-bwgko4` adds nothing beyond that.

## `bd-ib-wmqsn7` — re-scoped, now an epic in `backlog`

Retitled away from its original wording, which was itself the problem. Six
findings, each of which changes what this item is.

### 1. Its own framing is forbidden

The title said "tolerate a transient/re-runnable master CI flake". Tolerating a
red gate is precisely what `livespec/.ai/ci-gate-discipline.md` bans by absolute
maintainer directive of 2026-07-04: *"never add a lever, env var, flag,
carve-out, or any other escape mechanism that lets a commit, push, merge, or
dispatch proceed while a CI-green gate (e.g. `check-master-ci-green`) reports
red … This holds even when the gate blocks the very change that would repair the
red."* The recorded wontfix is `li-4x3a45`, upheld and **broadened** after a
`LIVESPEC_MASTER_CI_GREEN=warn` lever briefly landed in livespec-dev-tooling
PR #245 and was removed the same day (PR #249, with a regression test pinning
the env var to having no effect). The directive names the failure mode directly:
*"When you find yourself designing a lever so the fix can land, stop."*

The item has been retitled so no future agent pattern-matches on "tolerate".

### 2. The gate is not this repo's code

`check-master-ci-green` is `livespec_dev_tooling/checks/master_ci_green.py`,
consumed from the sibling library **`livespec-dev-tooling`** (pinned in
`pyproject.toml` at tag `v0.56.6`). Changing the gate is cross-repo work plus a
release and a pin bump. **This corrects an earlier claim in this file that both
items were in-repo and therefore factory-safe.** They were not.

### 3. The correct design is already decided — and it is not a weakening

The sibling ledger already holds the analysis. `livespec-dev-tooling-gam8`
(`backlog`) recovered untruncated evidence from a fabro run scratch log,
**falsified its own original premise** (the sandbox's read of master was
*correct*, not wrong), and concluded that what remains is a pure **vantage**
policy decision, routed to the maintainer 2026-07-25: should a dispatched Red
commit die on a transiently-red master, or should master-health be classified
**out-of-vantage** inside the sandbox under a `ghs_`-class dispatch credential
and owned host-side by the Dispatcher as a pre-dispatch precondition?

The precedent is shipped and reusable, not hypothetical: commit `1e85cd1`
(*"classify the admin lane out-of-vantage under a dispatch-class credential"*)
introduced `holds_app_class_credential()`, which is present and public in the
pinned `v0.56.6` at `livespec_dev_tooling/fleet/fleet_conformance.py:151`.

**Why this passes the charter's test — "name a red the new gate still refuses":**
*every* red still refuses. An operator's pre-push under a user-class credential
is completely unchanged and still fails closed on any red. What changes is only
*where* the read happens for a `ghs_`-class sandbox context, which is
structurally not that gate's vantage. Nothing is tolerated; the decision point
moves **earlier** — from seven minutes into a dispatch, killing completed
in-sandbox work, to before the dispatch starts, where it costs nothing and the
operator can see and act on it.

### 4. It is two coherent dones, split by repo — and they are ORDERED

The description's "and/or" hid the wrong seam. The real cut:

- **Slice A — this repo. ✅ SHIPPED 2026-07-28 as `bd-ib-wefw` / PR #1064.**
  A host-side pre-dispatch precondition in the Dispatcher, refusing before
  admission and before any sandbox is provisioned. Details in §"Slice A shipped"
  at the top of this file.
- **Slice B — `livespec-dev-tooling`. NOT dispatchable from this tenant. OPEN.**
  Apply the existing `holds_app_class_credential()` vantage classification to
  `master_ci_green`, then cut a release and bump this repo's pin. Gated on the
  maintainer's vantage ruling, already routed on `livespec-dev-tooling-gam8`.

**Ordering was load-bearing, and it has been satisfied: A landed first.** B alone
would have removed the sandbox-side read with nothing replacing it, which *would*
have been a weakening. With A merged, enforcement is continuous — B now merely
relocates the read to the vantage that can act on it. This mirrors the
ci-gate-discipline corollary that enforcement must not precede the rollout it
assumes, applied in reverse.

**Honest residual, to be ruled on knowingly rather than papered over:** after
A+B, a master that goes red *during* a long dispatch is no longer caught mid-run
by the sandbox. The branch is still gated by its own PR CI and by branch
protection at merge, and the silent-red-master pattern the gate exists to
prevent is still prevented at the dispatch boundary — but the "don't build on a
broken world" property narrows. That is a real if small loss.

### 5. The `ci.yml`-retry option is DEAD — it is already implemented and already insufficient

Do not re-propose it at grooming. It is not merely weak; it has been tried.

1. **`UV_HTTP_RETRIES: "5"` is already set** at workflow scope in
   `.github/workflows/ci.yml` (line ~34), and the comment above it names *this
   exact failure mode* as its reason for existing. It ran, it retried five times,
   the job still failed — *"Request failed after 5 retries"*.
2. **The flake class spans packages and hosts.** Three distinct instances inside
   24 hours: `cpython` from GitHub (2026-07-15), `hypothesis-jsonschema` from
   `files.pythonhosted.org` (2026-07-28 ~02Z), `colorama` from the same CDN
   (2026-07-28 04:00Z). Anything scoped to a package or host under-fixes by
   construction.
3. **It addresses only network reddening.** A red master hard-gates dispatches
   whatever reddened it. Observed the same night: an `export-telemetry` job dying
   on a Honeycomb OTLP stream cancel reddened the run with zero network relevance
   to `uv`. Slice A is indifferent to the cause; a network retry is not.
4. **Both reddening commits on 2026-07-28 were single markdown files under
   `plan/`.** A change with no executable content stalled the whole factory,
   twice. That is the argument for slice A in one line: the reddening commit's
   content is irrelevant to whether the factory stalls, so the remedy cannot live
   in what the commit changed.

### 6. The run-rollup trap, found live and folded into slice A

`ci-green` is the **only** context branch protection requires, and it declares
`needs: [check-python, check-doctor-static, check-metadata, e2e-cli, acceptance]`
— `export-telemetry` is **not** among them. So a telemetry job that cannot block
a merge still sets the **run's** rolled-up `conclusion` to `failure`. A gate
reading the run rollup therefore converts a non-required job's flake into a
factory-wide dispatch outage while every required check passed. This was observed
live on 2026-07-28 and is why slice A reads the `ci-green` job's conclusion. It
is not a tolerance; it is reading the correct signal instead of a strictly
broader one.

## Why `bd-ib-bic7hb` is not owned by this thread

It is a dark-factory dispatch-path reliability defect and by charter it is ours,
but it was taken by `plan/dispatch-claim-liveness/` on 2026-07-26 because it was
the sole blocker on that epic's last slice (S3, `bd-ib-pme57n`) while this thread
was dormant. The transfer is recorded in both directions. **Do not work it here.**
Its root cause is settled and half of it has shipped (PR #1008, `5846ab7`).

## Related

- Parent track (closed): `plan/archive/codex-credential-broker/handoff.md`
  (epic `bd-ib-rck`).
- Sibling thread: `plan/credential-freshness-redesign/handoff.md` — independent;
  no code dependency.
- Binding directive: `livespec/.ai/ci-gate-discipline.md`. Read it before
  designing anything on `bd-ib-wmqsn7`.
