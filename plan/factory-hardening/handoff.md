# Handoff — factory-hardening

## What this thread is

Reliability hardening of the **dark-factory dispatch path** — the two failure
modes that each cost a real dispatch cycle during the `codex-credential-broker`
track (epic `bd-ib-rck`, CLOSED) and were filed as out-of-scope follow-ups.

## ▶ CURRENT STATE + NEXT ACTION (read this first)

**Status, 2026-07-28: both items are out of `blocked`. One is CLOSED as already
shipped; the other is re-scoped to an epic and awaits grooming.** Nothing is
dispatched and nothing is in flight.

| Item | Status now | Disposition |
|---|---|---|
| `bd-ib-bwgko4` | **CLOSED** | Superseded — its fix shipped 2026-07-24 as `bd-ib-qq7f` / PR #905. |
| `bd-ib-wmqsn7` | **`backlog`** | Re-scoped: it is an EPIC spanning two repos. Needs `groom`. |
| `bd-ib-bic7hb` | `ready` — **NOT OURS** | Owned by `plan/dispatch-claim-liveness/` since 2026-07-26. |

**Next action (maintainer):** run
`/livespec-orchestrator-beads-fabro:groom bd-ib-wmqsn7` and cut it into the two
ordered slices proposed in §"`bd-ib-wmqsn7` — re-scoped" below. Slice A is
in-repo and factory-dispatchable; slice B is not this repo's code.

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

Retitled away from its original wording, which was itself the problem. Four
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

- **Slice A — this repo. Factory-safe, dispatchable now, ADDS a gate.**
  A host-side pre-dispatch precondition in the Dispatcher: refuse to dispatch
  while master CI's latest run is red, naming the run id and the
  `gh run rerun --failed <id>` remedy in the refusal text. Grepping the
  Dispatcher confirms no such precondition exists today. This alone converts the
  measured cost — 7 wasted minutes, a stranded `active` claim with
  `assignee: fabro`, and an operator round-trip to diagnose — into an instant,
  legible refusal. Autonomously verifiable by unit tests over the refusal's
  classification logic, so it clears the acceptance gate that blocked the parent.
- **Slice B — `livespec-dev-tooling`. NOT dispatchable from this tenant.**
  Apply the existing `holds_app_class_credential()` vantage classification to
  `master_ci_green`, then cut a release and bump this repo's pin.

**Ordering is load-bearing: A must land before B.** B alone removes the
sandbox-side read with nothing replacing it, which *would* be a weakening.
A-then-B keeps enforcement continuous and merely relocates it to the vantage
that can act on it. This mirrors the ci-gate-discipline corollary that
enforcement must not precede the rollout it assumes, applied in reverse.

**Honest residual, to be ruled on knowingly rather than papered over:** after
A+B, a master that goes red *during* a long dispatch is no longer caught mid-run
by the sandbox. The branch is still gated by its own PR CI and by branch
protection at merge, and the silent-red-master pattern the gate exists to
prevent is still prevented at the dispatch boundary — but the "don't build on a
broken world" property narrows. That is a real if small loss.

### 5. The `ci.yml`-retry option under-fixes

Three reasons, worth stating before grooming reaches for it as the easy option:

1. **`uv` already retries.** The 2026-07-28 failure text reads *"Request failed
   after 5 retries"* — the download was retried five times and still timed out.
   A naive outer retry adds little.
2. **The flake class is broader than the description's "cpython from GitHub".**
   The 2026-07-28 occurrence was `hypothesis-jsonschema` from
   `files.pythonhosted.org` — a different package from a different host. A retry
   scoped to the cpython fetch would not have caught it.
3. **It addresses only network reddening.** A red master fail-closes dispatches
   whatever reddened it. `bd-ib-eha3wh` (`backlog`, this tenant) records a
   non-network path to the identical symptom: `export-ci-telemetry.sh` can fail
   `E2BIG` on unbounded `jq` argv, reddening master and hard-gating dispatches.
   Slice A is indifferent to the cause; a network retry is not.

## Adjacent in-repo work in this thread's class

Surfaced during the 2026-07-28 verification, not adopted — recorded so the next
session does not have to rediscover it. `bd-ib-eha3wh` (`backlog`, P2) is
in-repo, factory-safe, and produces the *same factory outage symptom* as
`bd-ib-wmqsn7` by a different cause: `.github/scripts/export-ci-telemetry.sh`
passes monotonically-growing JSON accumulators as `jq` argv arguments, so a
large-enough CI run fails `E2BIG`, reddens master's latest run, and
`check-master-ci-green` then hard-gates every dispatch. A verified ~10-line fix
precedent exists (livespec-driver-codex PR #249 moves both unbounded values onto
stdin). It is unblocked and needs no grooming.

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
