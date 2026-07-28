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
| `bd-ib-imzx24` | **CLOSED** | Adopted, dispatched: PR #1076, merge `26f2b1b`. Admission-heuristic override. |
| `bd-ib-p16s` | **`backlog`** | **Premise REFUTED** — retitled and withdrawn from `ready`. See below. |
| `bd-ib-wmqsn7` | **`backlog`** | The epic. Slice A is done; **slice B remains** and is cross-repo. |
| `bd-ib-bic7hb`, `bd-ib-w4h4` | — **NOT OURS** | Both tracked by `plan/dispatch-claim-liveness/`. |

**Next action (maintainer), and it is a ruling, not a task:** slice B changes
`check-master-ci-green` in **`livespec-dev-tooling`**, and it rests on the vantage
policy question already routed to you on `livespec-dev-tooling-gam8` (2026-07-25).
Slice A has now landed, which was the ordering precondition — so slice B is
unblocked the moment you rule. Nothing in THIS repo is waiting on anything.

**The premise of that ruling has now been VERIFIED end to end, and it carries one
caveat that was not previously named.** Because four of six defect claims this thread
handled today did not survive contact with the evidence, the recommendation awaiting
your ruling was re-checked rather than left resting on its own plausibility:

- **It fires in the sandbox.** `holds_app_class_credential()` reads `GH_TOKEN` then
  `GITHUB_TOKEN` and returns True on the `ghs_` prefix. This repo's
  `render_run_config_overlay` projects exactly that — "a GITHUB_TOKEN freshly minted
  from the App installation-token provider … projected under GITHUB_TOKEN, not
  GH_TOKEN". Not merely inferred from docstrings on both sides: the same predicate
  already governs the admin lane in production via `1e85cd1`, which resolved a
  repo-wide factory outage.
- **It does NOT fire for an operator.** The predicate reads only those two env vars —
  never `gh auth token`, the keyring, or `hosts.yml`. A user-class credential
  (`gho_`/`ghp_`), or a keyring credential with neither var set, yields False, so
  pre-push enforcement is untouched. The "every red still refuses at the operator's
  pre-push" claim holds.
- **CAVEAT — it would also fire in GitHub Actions**, where the ambient `GITHUB_TOKEN`
  is likewise `ghs_`. Harmless *today* only because `check-master-ci-green` is
  deliberately excluded from the CI matrix. Slice B makes that exclusion load-bearing
  in a NEW way: it would become the only thing stopping a CI run from silently
  self-classifying out of a gate. If you prefer no new coupling, the narrower form is
  to gate the classification on `ghs_` **and** the absence of `GITHUB_ACTIONS=true`.
  Either way the coupling belongs in the check's own docstring.
- A far narrower edge: an operator who exports a `ghs_` token into their own shell
  would also be classified out-of-vantage at pre-push.

**The in-repo queue for this thread's class is exhausted, and that is a checked
conclusion rather than an assumption.** Every remaining non-closed item in the
dark-factory dispatch-path class was assessed: `bd-ib-js4t57` is outward-facing
upstream fabro (fork-track, explicitly not factory-safe); `bd-ib-blk3` declares
"host-only (sysctl/policy work; never factory-dispatched)" and needs a maintainer
policy choice; `bd-ib-bic7hb` and `bd-ib-w4h4` belong to
`plan/dispatch-claim-liveness/`; `bd-ib-elvxv2` is a family docs chore, not this
class. Nothing factory-safe, unowned, and dispatchable remains here.

## `bd-ib-p16s` — premise REFUTED; do not dispatch it as written

It was sitting in `ready` and would have been picked up next. Its own description
required diagnosis from run `01KYA2MP5JYV` "before coding", and nobody had done it.
The run's evidence survives (`~/.fabro/storage/scratch/20260724-01KYA2MP…` and
`fabro events`), so it was done.

**The pr stage did not skip the arm — it armed auto-merge AND verified it.** From
the run's `prompt.completed` event: *"Auto-merge arming returned successfully. I'm
querying the PR state now to confirm `autoMergeRequest` is present… Auto-merge is
armed with rebase merge. Current `mergeStateStatus` is `BLOCKED`, so it is waiting
on GitHub-side requirements/checks."*

Forge corroboration, not just the transcript: PR #927 carries
`autoMergeRequest.enabledAt = 2026-07-24T14:03:18Z`, `enabledBy: app/livespec-pr-bot`,
`mergeMethod: REBASE` — twelve seconds before the pr stage completed — **and the PR
merged** at 15:11:49Z. It was never a PR that "could never merge".

So both fix shapes the item proposes target a non-problem. The only real residual is
that the dispatcher's merge-poll cannot distinguish "armed but blocked on red CI,
will merge when they go green" from "starved", and times out on the former. That is a
different defect, and it overlaps `bd-ib-lza6` (`acceptance`), which already shipped
the `reconcile-merged` valve — **read `lza6` before re-scoping, and do not design a
second reconciliation path beside the one that shipped.**

Two method warnings from doing this diagnosis, both recorded on the item:
`tool_time_ms=0` on the pr stage looked damning until a known-good run showed the
same (fabro does not count the ACP agent's internal tool calls); and reading the
agent reply through a truncating slice briefly made it look like the agent stopped
mid-step, when the full 1904-character reply shows it finished. **A stage reporting
`status="succeeded"` is not evidence about what the agent DID — read the reply.**

## `bd-ib-imzx24` shipped — the admission heuristic now has a working remedy

Adopted by this thread (parent epic `bd-ib-cvgjop` is CLOSED and its thread archived,
so no live thread owned it) and dispatched: PR #1076, merge `26f2b1b`, released in
0.47.1. It fixes the defect that bit this thread's own `bd-ib-wefw` earlier the same
day.

Before adopting, the defect was confirmed still live three independent ways — merged
history showed the module's last change *was* the commit that shipped the gate; the
source carried no override mechanism; and the refusal message still named
`set-admission`, which cannot clear the block. The pre-dispatch refusal check was also
run on the item itself (it does not trip its own heuristic).

What landed: a new journaled drive valve **`set-workflow-scope-override:<id>:citation-only`**,
the store mutation that records it, `is_host_only_item` honoring it, and a rewritten
refusal message that names both the valve and the negation-declaration escape.

**Ordering is the safety property, and it is guarded.** `factory_safety` is checked
FIRST, so the override can never admit an intrinsically host-only item. Demonstrated
rather than assumed: injecting the inverse order (override checked before
`factory_safety`) in a throwaway worktree turns
`test_workflow_scope_override_admits_citation_but_not_factory_safety` red — 10 passed
becomes 1 failed. The valve was also exercised live: an unknown id returns
"work-item not found" (so it parses and routes), and an out-of-allowlist value is
refused. Its test fixture uses this thread's own scope-fence line verbatim as the
citation-only case.

### Residual found after the close: the new verb has NO specification coverage

Found by post-merge verification, recorded rather than reopened. `grep -rn
"workflow-scope-override" SPECIFICATION/*.md` returns **zero hits** — the verb is
absent from §"Per-lane valid operator verb sets" and from every action-id
enumeration. That is anomalous, not conventional: `set-admission` has 6 hits in
`contracts.md`, `set-acceptance` 10, and each of the three cap verbs 3.

It matters because that vocabulary is not internal bookkeeping. `contracts.md` says
it is "OWNED here and consumed by console adopters", and
`livespec-console-beads-fabro` defers per-item verb suppression to it explicitly — so
a console cannot offer or suppress this verb while the enforcer accepts it in every
lane. An operator's only route to discovering it is the refusal message that names it.

**Not `bd-ib-imzx24`'s fault and not reopened.** Its acceptance never asked for a spec
update and the dispatched agent delivered exactly what was specified. The fix is a
spec-change, which is human-gated and routes to `/livespec:propose-change` — so it is
**surfaced to the maintainer, not filed as a factory item**, and no `SPECIFICATION/`
file was touched here.

**Contributed as evidence to `bd-ib-dohu2g`** (the `plan/valve-advertisement-mismatch/`
epic, whose class this is) — evidence only; that thread's work was not adopted,
re-scoped, or duplicated. The useful part for them is that **the direction is
inverted**: their closed instance (`bd-ib-h57nx4`, PR #1012) was *advertised but not
enforceable*; this one is *enforceable but neither advertised nor specified*. A check
written only in their direction would pass cleanly on today's tree and still miss
this, so the mechanical check they argue for **must be bidirectional**.

**And nothing mechanical would have caught it** — a repo-wide search finds no check
asserting drive-verb/spec parity. The verb shipped through a full Red→Green→Replay
dispatch with paired tests across five test files, a review node, and a green
post-merge janitor, and no gate anywhere observed that it had no spec coverage. That
is a same-day datapoint for that epic's own thesis: careful sweeps have already failed
on this class four times, so the fix has to be mechanical.

**Carry-forward for acceptance writing:** an item that adds a first-class OPERATOR
VERB should carry a spec-coverage criterion, precisely because nothing enforces it.

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

**Which copy is in effect — the pin mechanic, applied to our own work.** This is
the charter's §"honesty hazard" turned on slice A itself, and the answer has two
halves, so state it precisely rather than as "the fix is live". The Dispatcher
resolves its modules from wherever `plugin_root()` points: the repo checkout when
`dispatcher.py` is run host-direct (how dispatches actually run here, and the path
the smoke test exercised), or the installed plugin cache under `CLAUDE_PLUGIN_ROOT`
when invoked through the plugin. At the time slice A merged, the installed cache was
`c878ea43f8cd` = release **0.46.25**, thirty-four commits behind, and it did **not**
contain the preflight — verified by grepping every cached
`_dispatcher_run_checks.py`. Master and the marketplace clone were both already at
0.47.0 with the preflight present, so the cache self-heals on the next plugin
refresh. Net: slice A was in effect immediately on the host-direct path, and reaches
the plugin path on refresh. **It has since run in production** — the `bd-ib-imzx24`
dispatch proceeded past `dispatch_preamble` against a green master.

**It guards BOTH entry points, and there is no per-item hole.** `dispatch_preamble`
is called by `_dispatcher_run_commands.py` (the `dispatch` path) and by
`_dispatcher_loop_command._start_loop` (the `loop` path), so slice A covers the
unattended drain as well as a hand-picked dispatch. A concern that the `loop` path
might check once and then dispatch many items over a long window was investigated and
is **wrong about the loop's structure**: `run_loop_command` runs exactly ONE wave — it
calls `_start_loop`, picks `candidates(...)[: budget]`, dispatches that wave
concurrently, and returns. There is no outer wave loop, so the preflight is accurate
for every item at the moment the wave starts. Recorded because the concern is a
natural one to re-derive, and because nearly filing a non-existent gap in our own code
would have been this session's fifth unverified defect claim.

**Live exercise beyond this repo.** The merged preflight was pointed read-only at
three sibling checkouts: `livespec-dev-tooling` (master CI `in_progress`) → PROCEED,
which exercises the **pending** branch live rather than only in unit tests; and
`livespec-runtime` and `livespec` (completed/success) → PROCEED, which additionally
proves the `ci-green` job lookup resolves there. **The `ci-green` job name is a
fleet-wide convention, not a this-repo quirk** — confirmed present in both siblings'
latest master runs. `_CI_GREEN_JOB` is still a hardcoded name, so renaming that job in
this repo would fail-close every dispatch; that is the safe direction, but it would
present as a mysterious factory outage, so change the two together if it ever changes.

**Not yet observed live: an actual refusal.** Slice A has been seen to PROCEED in
production and against three sibling repos, and its refusal branches are covered by
unit tests plus the injected-defect demonstration above — but no red master has
occurred since it merged (the whole fleet was green when checked), so no live refusal
has been witnessed. Do not manufacture one; the next natural red will supply it.

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

**Four of the six defect claims handled on 2026-07-28 did not survive contact with
the evidence**, and none was catchable from the item, the source, or this file —
only from the *merged diff* or the failing run's own event log:

- `bd-ib-bwgko4` — fixed by `bd-ib-qq7f` / PR #905 (2026-07-24), row untouched
  since 2026-07-15.
- `bd-ib-eha3wh` — fixed by `c6ae317` (2026-07-19), filed 2026-07-24 anyway.
- **The "three other drifted fleet copies" claim** — see below. Not inherited from
  an old row: generated fresh *during this session*, by this session, out of the
  description of a row already known to be stale.
- **`bd-ib-p16s`** — asserted the pr stage failed to arm auto-merge on PR #927. It
  armed it, verified it, and the PR merged. Refuted from the run's own event log
  plus the forge; see its section above. This one was sitting in `ready`.

### The fleet copies are NOT drifted — surveyed, all safe. Do not file an item.

An earlier revision of this file instructed the reader to "diff each against
`c6ae317` before filing or dispatching any of them", and a systemic follow-up item
was recommended to the maintainer on that basis. **The survey has now been done and
the recommendation is withdrawn.** `git fetch` in every fleet clone, then read
`origin/master:.github/scripts/export-ci-telemetry.sh` from each:

**There are EIGHT copies, not four, and ALL EIGHT are safe.** Six route both
unbounded payloads on stdin; `livespec` and `livespec-overseer` use a later variant
that writes both to temp files and reads them with `--slurpfile`, keeping even the
bounded `run_span` off argv. Enumerating every `--arg`/`--argjson` variable in each
copy: no value that grows with job or step count reaches argv anywhere in the fleet.
Both shapes are correct — this is benign divergence, not drift. Do not "harmonize"
them, and do not file the systemic item.

**The method warning is worth more than the result.** The survey's first pass
reported `livespec` and `livespec-overseer` as DEFECTIVE. False positive: both carry
a *comment* quoting the forbidden form verbatim in order to forbid it, and the
matcher read the prohibition as the declaration. That is the **third** time in one
session a text-matching check confused a citation with a declaration — the
Dispatcher's workflow-edit admission heuristic did it to `bd-ib-wefw`'s scope fence
(`bd-ib-imzx24`), and then this survey did it twice. Strip comments before matching.

**And note what this cost.** The recommendation to file was written in the same
paragraph that named the hazard — "filing creates a row asserting a defect in repos
I have not read" — and was made anyway, one turn after the charter recorded
correction 5 about exactly this. Naming a hazard is not the same as clearing it. The
check that settled all eight copies took about two minutes; it should have preceded
the recommendation, not followed it.

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
