# Handoff — dispatch-claim-liveness

## What this thread is

A work-item admitted to `active` by a dispatch that then reaches a terminal
outcome with no defined ledger transition is left in `active` with
`assignee: fabro` **forever**, permanently consuming a WIP slot. The failure is
silent — a full cap is indistinguishable from a busy factory — and it is
monotonic: every abandonment costs a slot that never comes back.

**Ledger anchor:** the three P1 slices below. Status is READ from the ledger
(`list-work-items` / `next`), never stored here.

| slice | id | status 2026-07-26 | scope |
|---|---|---|---|
| S1 | `bd-ib-ohdu5a` | **DONE** — PR #978 merged `a869253` | Harden the dispatch lock's liveness verdict (`started_at_epoch` + `O_EXCL`) |
| — | `bd-ib-l2vglr` | **DONE** — PR #982 merged `acf061c` | The S1 regression: stale reclamation for the now-exclusive lock write |
| S2 | `bd-ib-cfgkkk` | **DONE** — PR #1006 merged `ebe7419` | Surface a stranded merged-yet-unfinished claim in needs-attention |
| S3 | `bd-ib-pme57n` | **DONE** — PR #1014 merged `5b32017`, item `closed` | Stop counting dead claims against the per-repo WIP cap |

Open items filed by this thread, none part of the epic. All `ready`.

- **`bd-ib-bic7hb`** (P2, **host-only**) — **was** the S3 blocker; **root cause is
  now SETTLED and half of it has shipped** (PR #1008, `5846ab7`). See §"THE S3
  BLOCKER — SETTLED". **Ownership is borrowed, and the loan is recorded.** By
  charter this belongs to `plan/factory-hardening/` ("reliability hardening of the
  dark-factory dispatch path"), which already holds two items of the same class
  (`bd-ib-bwgko4`, `bd-ib-wmqsn7`). We took it because it was the sole blocker on
  S3 and that thread is dormant with both its items BLOCKED on a maintainer
  autonomy-tier assignment. The transfer is written into
  `plan/factory-hardening/handoff.md`'s ledger table and into the item's own
  description, so it cannot be worked twice or dropped.
- **`bd-ib-u46hcv`** (P2, **host-only**) — the upstream `livespec-dev-tooling`
  check defect that took the factory down. **CLOSED 2026-07-27T00:22:55Z, and its
  pin hold has been lifted** — the pin ran v0.54.19 → v0.56.2 later that morning
  and both guards are gone. This thread's pin-hold obligation is DISCHARGED; do
  not re-impose it. It closed with NO recorded close reason or resolution, and the
  "a REAL dispatch must survive setup on the new pin" condition is still UNMET, so
  the next dispatch is the test — see §"The v0.54.19 pin hold". (Earlier revisions
  of this line said no plan thread owned it and that the pin-hold half was ours.
  Both were true when written and are now superseded.)
- **`bd-ib-d6op2n`** (P2, **host-only**) — the `livespec-driver-claude`
  core-resolution misfire; can misfire our own revise pass. Owned by that repo;
  filed here because beads has no cross-tenant edge, so this prose IS the link and
  it must be routed by hand. **NO plan thread owns it** — do not assume a
  successor has picked it up, and do not adopt it into this epic.
- **`bd-ib-5ymv5p`** (P2, factory-safe) — `move_item` leaves a STALE assignee.
  It bit this thread twice on `bd-ib-pme57n`: after each failed setup the recovery
  `move:bd-ib-pme57n:ready` left `assignee: fabro` on a `ready` row, which reads
  exactly like a dispatch in progress. (The item is now `closed`, so that
  particular symptom is gone; the defect is not.) Do not hand-patch a stale
  assignee — fix it here.
- **`bd-ib-hvuhxp`** (P2, factory-safe) — `CandidateSlice.priority` is dead API
  surface; DELETE the field rather than wiring it through, because `WorkItem`
  removed `priority` deliberately and `rank` is the sole ordering authority.

Shipped by this thread beyond the slices: **`bd-ib-81l0`** (PR #1000 `47c75ac`,
S2's gate — `reconcile_plan` now threads `resolve_fabro_bin`) and
**`bd-ib-2wgooj`** (PR #1003 `817aeb1` — `_MOVE_ALLOWED` no longer contains
`"active"`, discharging S3's residual). Both verified by re-executing their reds
against the merged tree.

The originating epic **`bd-ib-waov`** was CLOSED 2026-07-26T08:32:25Z by the groom
with the explicit disposition "regroomed out into replacement slices:
`bd-ib-ohdu5a`, `bd-ib-cfgkkk`, `bd-ib-pme57n`". Its description was corrected
BEFORE closing, so the closed record carries the corrected root cause and all three
maintainer rulings rather than the superseded framing.

**Supersedes `livespec-console-beads-fabro-6ma`** (P1, filed 2026-07-20 in the
CONSOLE tenant, closed as superseded + mis-filed). That item diagnosed the
symptom correctly and cited the exact admission arithmetic, but the defect is
entirely orchestrator-side, so it sat six days in a backlog whose owners could not
fix it. Beads has no cross-tenant edge; this prose IS the link, and `-6ma`'s close
reason points back to `bd-ib-waov`.

## ▶ CURRENT STATE + NEXT ACTION (read this first)

### ✅ THE EPIC IS DONE. All three slices shipped and were verified by execution.

Say that plainly too — this thread's charter cuts both ways. It was opened because a
silent failure looked like normal operation for six days, so an unearned "done" is
the same sin as an unearned "almost done". What follows is what was actually
executed, not what a green dispatcher summary reported.

**Shipped and verified** (each red demonstrated by execution BEFORE dispatch and
re-verified flipped afterwards against the merged tree):

| piece | PR / sha |
|---|---|
| S1 `bd-ib-ohdu5a` — PID + `started_at_epoch` liveness, `O_EXCL` claim | #978 / `a869253` |
| `bd-ib-l2vglr` — the S1 regression: TOCTOU-correct stale reclamation | #982 / `acf061c` |
| `bd-ib-81l0` — S2's gate: `reconcile_plan` threads `resolve_fabro_bin` | #1000 / `47c75ac` |
| `bd-ib-2wgooj` — `_MOVE_ALLOWED` drops `"active"` (v050 divergence) | #1003 / `817aeb1` |
| S2 `bd-ib-cfgkkk` — the `host-only:stranded-dispatch` attention lane | #1006 / `ebe7419` |
| `bd-ib-bic7hb` (partial) — sandbox `mise install` runs anonymously | #1008 / `5846ab7` |
| **S3 `bd-ib-pme57n` — the WIP-cap arithmetic** | **#1014 / `5b32017`** |

**S3's verification, 2026-07-26.** The headline red was captured against `5846ab7`
BEFORE the dispatch (`wip_cap` 1, one dead claim, `admitted=[]`, nothing journaled)
and re-run against the merged tree, where it flips. All EIGHT acceptance clauses were
then exercised against the real `admit_and_select` — including the three added by the
predicate amendment — and each passes with a named injected defect that would re-red
it: the dead claim releases its slot; the abandonment is journaled
(`dispatch-claim-abandoned`, reason `terminal-outcome-non-green`); the row's status is
UNTOUCHED; a live lock still consumes its slot; both rework parks (green last outcome)
still COUNT and are NOT journaled; a dispatch killed after `ledger-admit` with no
outcome since IS reclaimed (`no-outcome-since-ledger-admit`); and the reconcile still
runs at `enforce_cap` false / `wip_cap` 0. Structurally confirmed in the shipped code:
`claimed_active_count` is called OUTSIDE the `if enforce_cap:` branch
(`_dispatcher_admission.py:93`), and `write_dispatch_lock` now fires at ADMISSION time
(`:124`) as well as at `dispatch_one` entry.

**End-to-end on the real tenant, which is the proof that matters.** Against the live
ledger and a COPY of the real journal (read-only — the real journal was not written):
`bd-ib-w4h4`, the six-day stranded claim this epic was opened for, has no live lock
and a non-green terminal outcome, so `claimed_active_count` now returns **0** where the
raw `active` row count is **1**. Its status is untouched, so `reconcile-merged` still
accepts it. And S2's lane surfaces it with the right handoff, carrying the
prior-attempt count the S2 constraint demanded:

```
host-only:stranded-dispatch:bd-ib-w4h4 [high] Reconcile merged active work-item
  bd-ib-w4h4: PR #836 merged at ba9fdaf...; janitor-post-merge failed across 3
  prior attempts.
  Handoff: dispatcher.py reconcile-merged --repo <path> --item bd-ib-w4h4 --json
```

Reclaimed capacity AND a surfaced failure with an actionable handoff — the pair the
charter insisted on, since either alone re-hides the defect.

Nothing is in flight from this thread. Repo clean on `master`, no orphaned worktrees.

**`bd-ib-w4h4` remains deliberately stranded, and that is still correct.** It is the
live fixture, it is the ONLY `active` row, and it now costs no WIP slot — which is
precisely the fixed behavior. It becomes recoverable once `bd-ib-rxxx` lands; do not
un-strand or close it before then.

**Remaining open work is NOT part of this epic** — see the filed-items list above and
§"The revise pass". The epic anchor `bd-ib-waov` was already closed at groom time.

### ✅ THE S3 BLOCKER — SETTLED 2026-07-26, and the blocking half has SHIPPED

**S3 was dispatched twice on 2026-07-26 and both runs died in sandbox SETUP**, before
any agent work, leaving the item stranded `active` each time (recovered by hand both
times via `move:bd-ib-pme57n:ready`):

| run id | at | duration | failure |
|---|---|---|---|
| `01KYG0ANS08T5V1HY1A92WR67J` | 20:02:42Z | 11s | `mise install` → 403 |
| `01KYG0FDVJKEDPCRPWQ11NH6CV` | 20:05:17Z | 8s | identical |

```
Setup command failed (exit code 1): livespec-step-timer mise-install --
  sh -c 'mise trust && mise install --quiet'
mise ERROR Failed to install aqua:koalaman/shellcheck@0.11.0: HTTP status client
  error (403 Forbidden) for url
  (https://api.github.com/repos/koalaman/shellcheck/releases/tags/v0.11.0)
```

**ROOT CAUSE — the sandbox's `mise install` was spending the FACTORY'S OWN GitHub
App credit on a third-party public-repo fetch, and that credit ran out.**

`_dispatcher_credentials.py` projects an ephemeral App INSTALLATION token into the
sandbox as `GITHUB_TOKEN`. mise's aqua backend picks that variable up automatically,
so the release-metadata lookup for `koalaman/shellcheck` went out AUTHENTICATED —
charged against the App installation's single **5000/hr PRIMARY** rate-limit bucket,
the same bucket every `gh`, janitor and merge-poll call in the fleet draws on.
Captured from inside the real sandbox image at 2026-07-26T20:27:16Z:

```
HTTP 403
{"message": "API rate limit exceeded for installation ID 131208965. ..."}
x-ratelimit-limit: 5000   x-ratelimit-remaining: 0   x-ratelimit-used: 5000
x-ratelimit-resource: core
```

**In the SAME sandbox, in the SAME second, the ANONYMOUS request for that same URL
returned 200.** That one pairing is the whole proof: identical egress, identical URL,
identical instant — only the credential differs.

**BOTH candidates this thread previously recorded are REFUTED BY EXECUTION.** Neither
was merely unproven; each was tested and failed:

- **Candidate A — "an installation token is unauthorized on a third-party repo."**
  REFUTED. An App installation token returns **200** on that URL, with
  `x-accepted-github-permissions: contents=read` and a 5000/hr limit. Installation
  tokens are not denied public-repo reads.
- **Candidate B — "a GitHub SECONDARY rate limit."** REFUTED. The failure carries the
  PRIMARY limit's headers and message body, not a secondary-limit message.
- The earlier host-side reading of **59/60 anonymous remaining** was accurate and
  simply IRRELEVANT — the failing request was never anonymous, so it drew on a
  different bucket. (A container on this host does share the host's anonymous bucket:
  verified same egress IP `66.94.121.15`, same reset epoch, decrementing counter.)

**SHIPPED: PR #1008, merged `5846ab7`.** The `mise install` prepare step in
`.claude-plugin/.fabro/workflows/implement-work-item/workflow.toml` now scrubs
`GITHUB_TOKEN`, `GH_TOKEN` and `GITHUB_API_TOKEN` from that ONE command's
environment, so aqua tool resolution runs anonymously and no longer consumes factory
credit. Anonymous is the correct posture rather than a workaround: the fetch reads
public release metadata only and touches the anonymous bucket ~2-3 times per
dispatch. Verifier `tests/integration/test_workflow_mise_install_anonymous.py`,
demonstrated RED against the unscrubbed step and GREEN against the scrubbed one; the
mechanism was independently proven in the sandbox image (a deliberately bad
`GITHUB_TOKEN` makes `mise install` fail 401, `env -u GITHUB_TOKEN` in the same shell
installs `shellcheck 0.11.0` cleanly). **Hand-built, not dispatched, deliberately:**
the janitor's `check-no-workflow-edits` hard gate refuses workflow-file drift from
inside a dispatch, so a dispatched agent cannot edit `workflow.toml` at all.

**Proven live:** dispatch `01KYG2Q1028H` of `bd-ib-pme57n` cleared the mise-install
step in 2s (20:44:05Z → 20:44:07Z) and ran on into the workflow, where the two prior
runs had died at that exact step.

**STILL OPEN on `bd-ib-bic7hb`: the durable prevention.** Pre-bake `shellcheck` and
every other aqua-backed tool so setup makes NO api.github.com call at all. **Correct
the target while you are there:** it is NOT `orchestrator-image/` as the item
originally said — the dispatch sandbox pins
`ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-agent-v0.54.19`, the FAMILY
image built in `livespec-dev-tooling`. So pre-baking is a CROSS-REPO change plus a
pin bump here, gated on `bd-ib-dwv` (image un-rebuildable) AND on `bd-ib-u46hcv`
(the pin is frozen at v0.54.19; see §"The v0.54.19 pin hold").

**A SEPARATE, LARGER FINDING falls out of this and belongs to nobody yet.** The App
installation's 5000/hr bucket reaching ZERO is a fleet-level problem. While it is
empty, EVERY credentialed GitHub call the factory makes fails the same way — `gh pr
create` in the pr node, the merge poll, the janitor. The sandbox `mise install` was
merely the first consumer to surface it. Nothing here measures what burns 5000
requests/hour against installation 131208965; a sample at 20:28:24Z showed a healthy
bucket (10 used), so the burn is BURSTY rather than steady. Recorded in
`bd-ib-bic7hb` under §"SEPARATE FINDING"; it is not part of this epic.

**S3's red is already captured** in `bd-ib-pme57n`'s description — executed against
the real `admit_and_select` with `wip_cap: 1`: a dead claim consumed the only slot,
`admitted=[]`, and no abandonment was journaled. The next session does not need to
re-derive it. **S3's predicate is the AMENDED one**, not "active + no live lock" —
see §"Rework doors".

Both slices were `pending-approval` and both dispatched directly with NO approval
step — see §"Dispatching a `pending-approval` slice"; the approve valve is closed by
construction on this repo.

### The v0.54.19 pin hold — LIFTED 2026-07-27. Not ours any more; one thing is UNVERIFIED.

**Status changed while this thread was mid-session, so read the dates, not the
prose you may remember.** `bd-ib-u46hcv` was **CLOSED 2026-07-27T00:22:55Z** — with
**no recorded close reason and no resolution** — and the pin then moved off v0.54.19
in five bumps between 06:01:53Z and 09:55:22Z: `v0.55.0` (`e45527d`), `v0.55.1`
(`9e630e1`), `v0.56.0` (`15f1281`), `v0.56.1` (`b8c8121`), `v0.56.2` (`6b2e0c9`).
The sandbox image pin moved with it — `workflow.toml` now pins
`ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-agent-v0.56.2`. Both hold
guards are gone from `pin-freshness.yml` and `bump-pin-from-dispatch.yml`.

The ordering is coherent — item closed FIRST, then the bumps flowed — so this reads
as deliberate discharge by the owning item, **not** unattended drift. This thread's
pin-hold obligation is therefore DISCHARGED and is no longer ours to defend. Do not
try to re-impose the hold.

**What was held at v0.54.19 and why** (retained so a successor can judge the risk):
v0.54.20..v0.54.24 took the factory DOWN because
`primary_checkout_commit_refuse_hook_installed` asserts the presence of the
gitignored worktree pack, which cannot exist in a fresh clone — and the sandbox runs
that check as a SETUP command on a fresh clone. The gate-blindness that let it merge
green: `just check` runs on the BOOTSTRAPPED checkout, where the broken check passes.

**⚠ ONE THING IS UNVERIFIED, and it is the condition this section used to state.**
The rule was "do NOT move the pin until a REAL dispatch is proven to survive setup
on the new pin — a green `just check` is not that proof." **That proof does not
exist for v0.56.2.** The dispatch journal's last record is `2026-07-27T00:39:28Z`,
before the first bump at 06:01:53Z, so **no dispatch has run on any pin after
v0.54.19.** S3's dispatch (`01KYG2Q1028H`) is not the proof either — it ran at
`5846ab7`, where the pin was still v0.54.19 (verified by reading that commit's
`pyproject.toml`). **The next factory dispatch is the test.** If it dies in setup on
`primary_checkout_commit_refuse_hook_installed`, this is why — check the pin first
rather than re-deriving the cause.

**Evidence pointing the other way, recorded fairly.** On v0.56.2, `just check`'s
`fresh-clone-setup-gate` PASSES in a fresh worktree, and that gate exercises the four
sandbox setup steps including the offending check, reporting "every conformance setup
step passes on a fresh clone". That is materially stronger than the bootstrapped-`just
check` blindness that let v0.54.24 through — but it is still a gate, not a dispatch,
and this section's own standard says a gate is not the proof. Treat it as good reason
to expect success, not as the verification.

(Corroborating the defect class is still live somewhere: this session hit
`failure_mode: "worktree_pack_absent"` from that exact check in a fresh worktree on
v0.56.2 — it passes only after `just bootstrap` materializes the gitignored pack.
The fresh-clone gate bootstraps, which is why the gate is green.)

**A second, separate assignment is also open: a `/livespec:revise` pass over BOTH
pending proposals — `reconcile-merged-dispatch-lock.md` and
`rework-return-door-attribution.md` — belongs to this track**
(maintainer-assigned 2026-07-26, scope corrected twice the same day). No deadline.
Every pending proposal is now ours; the peer's was ratified as v050. **The pass is
BLOCKED** on a local `spec/*` branch owned by another session — see §"The revise
pass", and check the precondition at run time, never earlier.

The lock work, both halves verified by executing the real product code, not by
reading a green dispatcher summary:

- **S1 `bd-ib-ohdu5a`** — PR #978 / `a869253`. Consults `started_at_epoch`, so a
  recycled PID no longer reads as the original owner; and claims with `O_EXCL`.
- **`bd-ib-l2vglr`** — PR #982 / `acf061c`, merged 2026-07-26T10:19:41Z. S1's
  `O_EXCL` had landed WITHOUT the stale reclamation that makes exclusive claiming
  safe, so any lock leaked by a dispatch that died without its `ExitStack`
  permanently blocked re-dispatch of that work-item. `write_dispatch_lock` now
  wraps the open in `attempt(...)`, and on `FileExistsError` runs
  `_stale_dispatch_lock_reclaimed`: an `fcntl.flock` mutex on a sibling `.reclaim`
  file, the S1 PID+start-time liveness verdict, **and a re-read of the payload
  compared against the first read immediately before unlinking** — the TOCTOU
  guard `bd-ib-w4h4` was filed about. Verified 2026-07-26 against the merged tree:
  a dead-pid lock is RECLAIMED and re-stamped with the new caller's pid, while a
  lock whose holder is LIVE is still REFUSED rather than clobbered.

**The two live leaked locks need no hand removal.** `tmp/fabro-dispatch-bd-ib-fe574e.lock`
(pid 930374) and `…-bd-ib-fjj7f7.lock` (pid 580668) are still on disk with dead
pids. Verified 2026-07-26 by running the merged `write_dispatch_lock` against
COPIES of both real payloads: each is reclaimed automatically, so `bd-ib-fe574e`
and `bd-ib-fjj7f7` are dispatchable again. Leave the originals alone — they are
now inert, and they are this regression's field evidence.

**Own this honestly:** the regression traced to THIS THREAD's own brief on
`bd-ib-ohdu5a`, which told the implementer "DO NOT add cleanup for leaked lock
files — liveness is PID-keyed, so a lock whose owner is gone already reads dead."
True before `O_EXCL`, false after it. The implementer followed the brief
correctly. The lesson generalizes: a brief's standing prohibitions must be
re-checked against every scope addition made after it was written.

Dependency layering, verified on the ledger: `bd-ib-cfgkkk` 1 dep / 1 dependent;
`bd-ib-pme57n` 2 / 0. `bd-ib-l2vglr` and `bd-ib-hvuhxp` carry no edges.

**S2's `bd-ib-81l0` gate is DISCHARGED.** It shipped 2026-07-26 as PR #1000
(`47c75ac`): `reconcile_plan` now threads `resolve_fabro_bin(cwd=repo)` instead of
the bare literal, so S2's `reconcile-merged` handoff no longer exec-fails under the
credential wrapper. Verified by re-executing the red against the merged tree —
`plan.fabro_bin` is now `/home/ubuntu/.fabro/bin/fabro` and execs at exit 0, where
the bare name raised `FileNotFoundError`. (The gate could never be an edge — groom
resolves `depends_on` handles only to earlier slices in the same draft — so it
lived in `bd-ib-cfgkkk`'s description as prose.)

## ⛔ Dispatching a `pending-approval` slice — the obvious answer is WRONG

Both remaining slices sit in `pending-approval`, and the intuitive move — "run the
approve valve first" — **cannot work on this repo and would block the track
indefinitely.**

`.livespec.jsonc:93` commits `auto_approve_ready: true`, so
`effective_admission_policy` resolves to `auto`, and `_approve_item`
(`_drive_valves.py:141-152`) refuses EVERY item here with `invalid-source-state —
approve requires an effective-manual pending-approval item`. **The approve valve is
closed by construction.** Another session hit exactly this on `bd-ib-wuotqm` on
2026-07-26 and had to route around it.

**⛔ That defect is NOT OURS — `plan/valve-advertisement-mismatch/` owns it**
(opened 2026-07-26). Its `research/prior-work-and-collisions.md` carries an
"Already filed — do NOT duplicate" section and names THIS thread explicitly in its
"Other live tracks — checked, no collision" section, so the cross-check has already
been done from their side. **Do not file against it, do not fix it in passing, and
do not fold it into this epic.** For us it is a standing WORKAROUND note only: the
approve valve is closed here, so dispatch `pending-approval` items directly, per
the rest of this section.

**What actually works: dispatch it directly. No approval step, no status move.**
`ready_items` (`_dispatcher_loop_selection.py:102-120`) filters with
`is_dispatch_candidate`, which re-tests a `pending-approval` item under a READY
PROJECTION (`:138-145`). The `--item` preflight
(`_dispatcher_run_checks.requested_items_preflight_error`) checks membership in
that same set, so it passes. Admission then does both writes in ONE pass:
`_dispatcher_admission.py:102` writes `ready` on the auto-approve leg, `:114` writes
`active`.

Verified 2026-07-26 by executing the real predicates against the live tenant:

```
bd-ib-cfgkkk: status='pending-approval' depends_on=(bd-ib-ohdu5a,)
  is_dispatch_candidate                          -> True
  in ready_items set                             -> True
  requested_items_preflight_error({'bd-ib-cfgkkk'}) -> None
```

So `dispatcher.py dispatch --item bd-ib-cfgkkk` just works.

**Do NOT reach for `dispatcher.py loop` to obtain the auto-approve.** A loop pass
admits a BATCH to `active` and then dispatches under `--parallel 1`, which is
exactly the unlocked-claim window S3 exists to close — and S3 has not shipped.
Per-item `dispatch --item` writes its lock at `dispatch_one` entry, so each claim is
covered for its whole life. Per-item dispatch is the rule until S3 lands.

**`move:<id>:ready` is a working fallback if the direct path ever regresses**, and
it is CLEAN for a `pending-approval` item in a way it is not for an `active` one: the
item has never been `active`, so `assignee` is already `None` and the
`bd-ib-5ymv5p` stale-assignee side effect cannot arise. v050 retires the
move-into-`active` door, NOT move-into-`ready`, so this stays sanctioned.

**Hazard recorded on `bd-ib-4m5f`.** That item reports `next` and the Dispatcher
disagreeing on the candidate set — and the divergence is what makes the above work.
Resolving it by narrowing the Dispatcher to `next`'s stored-status-only reading
would make every `pending-approval` item undispatchable here, with no approval valve
to unblock it. Converge by teaching `next` the ready-projection rule, not by
narrowing the drain.

**Dispatch recipe that worked** (run it from the repo root, already inside the
wrapper — the dispatcher self-wraps but often cannot reach the credstore alone):

```bash
/usr/local/bin/with-livespec-env.sh -- python3 .claude-plugin/scripts/bin/dispatcher.py \
    dispatch --item <id> --repo /data/projects/livespec-orchestrator-beads-fabro
```

Verify preconditions FIRST every time: the `127.0.0.1:32276` listener's
`/proc/<pid>/exe` must resolve to `~/.fabro/bin/fabro`; `fabro --version` must be
`0.254.0 (b9b63a8)` (≥ 0.256 breaks `workflow.fabro`, exit 127 — halt); WIP
headroom. Prove container ownership by an ALL-container run-config scan, never by
name/image/position/timing — every container on this host exits 137, so 137 is
normal teardown here, never kill-proof. Establish outcomes from artifacts (merged
PR, ledger row, journal), never exit codes: both S1's and `bd-ib-l2vglr`'s
dispatchers printed a green summary, and only re-executing the reds proved either
fix was real.

**`fabro ps` need NOT be clear — do not treat a foreign run as a blocker.**
`bd-ib-sd8o` closed 2026-07-24 `resolution:completed`: `host_dispatch_cap`
(default 2, spec v047) demoted the interim host-wide dispatch mutex to a counting
cap, verified live with two concurrent green dispatches. One foreign run is
therefore normal and safe; a THIRD dispatch is what gets refused. When a foreign
run IS present, identify its owner by the dispatcher **argv chain**
(`ps -eo pid,ppid,args` → the `dispatch --item <id>` leaf and the
`CODEX_COMPANION_SESSION_ID` in its launching shell), and name the owning SESSION,
recovered from `~/.claude/projects/<slug>/<session-id>.jsonl` by grepping
`Session renamed to:`. Demonstrated 2026-07-26: while this thread dispatched
`bd-ib-l2vglr`, session **`orch-dirty`** (session
`87f62319-9bda-4b9e-80b0-d35b178bef70`) concurrently dispatched `bd-ib-cfcmse`;
both ran green.

**The root cause below was CORRECTED on 2026-07-26** against the dispatch journal,
the merged PR, and the ledger. The thread's original diagnosis ("the dispatcher
process died mid-flight") is DISPROVEN — see §"Root cause". The epic's own
description was corrected to match before it was closed, so the two no longer
disagree.

**Leave `bd-ib-w4h4` stranded.** It is S3's fixture. Do not un-strand or close it
before the verifier exists. It becomes recoverable once `bd-ib-rxxx` lands.

## ⚠ Rework doors — S3's predicate is NARROWER than "active + no live lock"

**Found 2026-07-26 by the peer supervisor `console-happy-path-mvp-supervisor`,
verified here, and APPROVED as a change to S3's already-approved acceptance
criteria. `bd-ib-pme57n`'s description now carries the amendment; this section is
the reasoning behind it.**

TWO writers set `status="active"` **without passing through admission**, so they
never hold a dispatch lock. Neither is an abandonment — each parks an item for
re-dispatch:

1. **`_drive_valves.py:189`** (`_reject_item`) — `reject:<id>:rework` on an
   `acceptance` item sets `target_status = "active"`. **NOT journaled at all.**
   `valve_success` (`_drive_valve_result.py:29`) builds a `"journal"` object
   INSIDE the drive CLI's RESPONSE payload; neither drive module nor `drive.py`
   references a `JournalFile`, and the dispatch journal holds **zero
   `human-valve-*` records** across its whole history. (A peer brief described
   this door as "journaled `human-valve-reject-rework`" — that is the response
   field, not a journal record.)
2. **`_dispatcher_acceptance_rework.py:79`** — auto-rework after a failing AI
   acceptance pass, genuinely journaled `acceptance-auto-rework`. **Reachable in
   practice:** fired 4 times across 3 distinct items (`bd-ib-vp3pwe` ×2,
   `bd-ib-1jye.4`, `bd-ib-1jye.5`).

A **third** unlocked writer exists today: the bare `move:<id>:active`, legal
because `_MOVE_ALLOWED` (`_drive_policy_valves.py:40`) contains `"active"` and
`move_item` guards only the TARGET status. It is unjournaled too. The pending
`per-state-verb-vocabulary.md` proposal removes exactly that door.

**The obvious discriminator does not work.** "Also require a terminal `outcome`
journal record" fails, because the auto-rework park writes its terminal `outcome`
AFTER the rework write and it is **green** — e.g. for `bd-ib-1jye.4`:
`{"stage": "done", "status": "green", "pr_number": 800, "detail": "merged,
post-merge janitor green"}`. An abandoned claim and a rework park both have one.

**APPROVED PREDICATE** — reclaim (exclude from `active_count`, journal the
abandonment) if and only if:

```
    item.status == "active"
AND live_dispatch_lock(item) is None
AND (the most recent terminal `outcome` for the item is non-green
     OR no `outcome` record exists since its most recent `ledger-admit`)
```

| case | last outcome | verdict |
|---|---|---|
| `bd-ib-w4h4` (janitor-post-merge red) | `failed` | RECLAIM |
| `acceptance-auto-rework` park | `green` | skip |
| `reject:<id>:rework` park | `green` (it reached `acceptance` only via a green `ledger-complete`) | skip |
| dispatch SIGKILLed mid-run | none since `ledger-admit` | RECLAIM |
| queued in an admitted batch | — holds an admission-time lock | skip before the outcome leg is reached |

The last row is why this is sound ONLY together with S3's admission-time lock
move. Without it, a queued item has neither lock nor outcome and would be
reclaimed while perfectly healthy.

**KNOWN RESIDUAL, accepted at approval — now DISCHARGED at the spec level.** A
bare `move:<id>:active` item has no lock and no outcome since its (nonexistent)
admit, so it reads as abandoned. That door was retired by v050 (`27980bb`), and
the shipped-code divergence — `_MOVE_ALLOWED` still contains `"active"` — is filed
as **`bd-ib-2wgooj`**. `bd-ib-pme57n`'s description carries the same cross-
reference. Prose link only; no dependency edge is asserted, because S3's
predicate is correct either way and merely reads a bare-moved item as abandoned
until `bd-ib-2wgooj` lands.

## The revise pass — TWO files, BOTH ours

**Maintainer-assigned 2026-07-26; scope corrected twice the same day — read the
current table, not the earlier "ONLY that file" framing this section used to
carry.** No deadline; run it when the slices make it sensible. **Do not run it
while a dispatch is in flight** — it authors spec text and cuts a `spec/*` branch,
which should not race a live janitor.

`SPECIFICATION/proposed_changes/` on `origin/master` holds exactly two files, and
**both are ours**:

| proposal | filed | this track's obligation |
|---|---|---|
| `reconcile-merged-dispatch-lock.md` | 2026-07-19 (`e957b35`) | Process it. Pending since filing, untouched by any other track. |
| `rework-return-door-attribution.md` | 2026-07-26 (PR #996, `e7c0651`) | Process it. Two separable findings; see §"Rework doors" and the v050 correction below. |

#### ⚠ Ratification ORDERING against `plan/valve-advertisement-mismatch/` — SETTLED, do not re-litigate

`rework-return-door-attribution.md` is pending against the **same
`SPECIFICATION/contracts.md` §"Door rules" block** that any amendment out of the
`valve-advertisement-mismatch` thread must also touch. That thread records the
clash as its "Live collision #2" and asks whoever files theirs to check whether
ours has landed.

**DECISION: OURS RATIFIES FIRST.** Ours is already filed and is narrow — it
corrects a single false justification sentence — so ratifying it leaves a
*corrected* paragraph for their broader amendment to build on. The reverse order
would have them amend text we are about to correct, and the correction would then
have to be re-derived against their new wording. This ordering is recorded so it
is not re-decided; it is worth relaying to that thread, but **do not edit their
files to say so** — surface it to the maintainer for relay.

The peer's `per-state-verb-vocabulary.md` is **GONE** — ratified as v050 in
`27980bb` — and `wip-cap-zero-dispatch-off.md` before it as v049 in `9941317`.
**Consequence: the all-or-nothing property now costs us nothing.** Every pending
proposal is ours, so no coordination with another track is required and no
proposal has to be carved out of the payload. Earlier revisions of this section
recorded a cross-track split; that split no longer exists.

**A revise pass is NOT all-or-nothing anyway** — an early relay said it was, and
that was retracted. The revise PROSE says process every in-flight file, but the
CLI's `--revise-json` payload defines actual scope through its `decisions[]`
array. Verified independently on the forge 2026-07-26, and the timing is
decisive:

- `SPECIFICATION/history/v049/proposed_changes/` contains ONLY
  `wip-cap-zero-dispatch-off.md` and `wip-cap-zero-dispatch-off-revision.md`.
- v049 was ratified at 2026-07-26T09:13:02Z (`9941317`).
- `per-state-verb-vocabulary.md` was added at **08:46:07Z** (`495b903`) — 27
  minutes BEFORE v049 was cut — and `reconcile-merged-dispatch-lock.md` on
  2026-07-19 (`e957b35`), seven days before.

Both therefore sat pending while v049 snapshotted and ratified a single proposal,
and neither received a `-revision.md`. A single-proposal pass is mechanically
supported and was demonstrated today.

### ⛔ The blocking precondition — check it IMMEDIATELY BEFORE the run

Step 3.5 halts on any local `refs/heads/spec/*` ahead of `origin/master`.

**This check is binding at run time, not at session start.** It was verified
EMPTY twice on 2026-07-26 and was non-empty again within the hour on both
occasions. Two demonstrations, both real:

1. `refs/heads/spec/ratify-verb-vocabulary` — the peer track's v050 pass, which
   blocked this pass for most of 2026-07-26. **RESOLVED 2026-07-26: removed on
   maintainer authorization** (branch was `30ffe29`, plus its worktree at
   `~/.worktrees/livespec-orchestrator-beads-fabro/spec-ratify-verb-vocabulary`).
   Checked to destruction first: `git diff origin/master 30ffe29 -- SPECIFICATION/`
   showed the branch carried NOTHING under `SPECIFICATION/` that master lacks —
   the whole v050 ratification is on master via PR #995 / `27980bb` — the worktree
   was clean and no process held it. It was the pre-rebase twin of a merged commit.
   `console-happy-path-mvp-supervisor` was notified after the fact.

   **CORRECTION, recorded because this thread relayed it wrong.** Earlier revisions
   of this file said the branch "is owned by session
   `console-happy-path-mvp-supervisor`; do not remove it ourselves". That
   attribution originated here, was relayed onward unverified, and was wrong: their
   pass CREATED it, but what remained was a **local ref in OUR clone with no unique
   content** — our housekeeping, not theirs. The standing
   never-touch-another-session's-worktree clause is UNCHANGED for everything else;
   the exemption here is narrow and was earned by proving the ref carried nothing.
   The general lesson is this thread's own recurring one: an ownership claim is a
   claim with a timestamp, and "another session owns it" needs the same evidence
   standard as any other assertion before it is allowed to block work.
2. This thread's OWN propose-change cut and deleted `spec/rework-return-door-attribution`
   inside a single turn. Filing a proposal is itself a way to trip the gate.

So: `git for-each-ref refs/heads/spec/` MUST be empty at the moment of the run.
An earlier-in-session verification proves nothing — **including the 2026-07-26
removal recorded above.**

**And do not run the pass while a dispatch is in flight** (already stated above,
repeated here because this is where a successor will be standing): the pass
authors spec text and cuts a `spec/*` branch, which must not race a live janitor.
On 2026-07-26 the precondition came clear WHILE S3's dispatch was running, and the
correct answer was still to wait for the dispatch, not to start the pass.

**Likely outcome for `reconcile-merged-dispatch-lock.md`: accept as written, no
amendment.** The original spec clash is recorded DISSOLVED (§"CORRECTED") — the
approved design leaves the item `active` and narrows the count, so the proposal's
"a red janitor … MUST leave the item `active`" is honored literally.

**But re-read before accepting: v050 landed AFTER that analysis and changed the
door rules around `active`.** The DISSOLVED reading was derived pre-v050. Verify
it against BOTH the proposal's current bytes and the ratified v050 text in
`SPECIFICATION/contracts.md` rather than trusting the earlier conclusion. Expect
a short pass, but do not assume one.

### A driver defect that can misfire this very pass

`bd-ib-d6op2n` (P2, `ready`, host-only): every `livespec-driver-claude` binding —
all eight, `revise` included — ships a core-resolution snippet that tests the
prose DIRECTORY (`-d "./.claude-plugin/prose"`) while its own documented rule 2
tests that operation's prose FILE. This repo HAS a `.claude-plugin/prose/` (six
orchestrator prose files, none of them spec-side), so the snippet resolves
`<core-root>` to THIS repo and the not-found guard — which re-tests the directory
— passes it through silently.

**Workaround, already used successfully:** apply the documented rule-2 condition
(test for `prose/revise.md` specifically), or resolve rule 3 directly from
`~/.claude/plugins/installed_plugins.json`. Do not trust the shipped snippet.

### The peer's proposal contradicts itself — HANDED BACK, not our blocker

**Ruling 2026-07-26: hand back for amendment; delivered.** This is recorded for
the peer's benefit and for provenance. It is **NOT a gate on our pass**, because
`per-state-verb-vocabulary.md` is out of our scope entirely. Do not wait on it and
do not edit the peer's proposal — it is a completed maintainer decision owned by
another track.

The proposal's door rule (line ~66) states:

> "`active` is entered ONLY by a journaled dispatch: **factory dispatch** … or
> **driver-dispatch**. Bare operator moves into `active` are removed from every
> lane."

Its own lane table (line ~56) simultaneously keeps `reject (rework | regroom)` as
a valid operator verb on `acceptance` — and `reject:rework` lands the item in
`active` (`_drive_valves.py:189`), which is neither a dispatch nor journaled. The
document never states where reject-rework lands. **So this is an internal
inconsistency, not merely a clash with shipped code** — the maintainer can settle
it without adjudicating behavior at all. The second contradiction is
`acceptance-auto-rework`: journaled, but not a dispatch.

The intent is clearly to kill the BARE operator move (`_MOVE_ALLOWED`), which the
rest of the proposal supports. The narrowest repair keeps that intent and makes
the text true — for example: "`active` is entered only by a journaled dispatch
(factory dispatch or driver-dispatch) **or by a rework return from `acceptance`
— the `reject:rework` valve or the Dispatcher's `acceptance-auto-rework`
disposition**. Bare operator moves into `active` are removed from every lane."
Drafted here as a concrete option for whoever amends it; the wording is theirs to
choose.

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
   abandonment and **excluded from the count**. **Use the per-work-item dispatch
   ownership lock, NOT the heartbeat** — see §"The signal already exists".
   Self-healing, no new lifecycle vocabulary, and it runs exactly when the answer
   matters. (Earlier revisions of this line said "moved out of `active`". That is
   RETRACTED — moving the item breaks the shipped `reconcile-merged` valve; see
   §"CORRECTED".)
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
answers DEAD. Requirement 3 was red against `master` until 2026-07-26 — **it is now
FIXED** by S1 (PR #978 / `a869253`), verified by re-executing the demonstration.
This section is retained as the diagnosis, not as a live defect.

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
- **`wip-cap-zero-dispatch-off.md`** — **RESOLVED: ratified as spec v049** in
  `9941317` (2026-07-26T09:13:02Z). It is no longer a pending proposal and no
  longer a coordination hazard; `wip_cap: 0` is now the documented dispatch-off
  value. Its constraint on this thread SURVIVES ratification and is now normative
  rather than speculative: `_dispatcher_admission.py:87-91` computes `active_count`
  only inside `if enforce_cap:`, so **requirement 1's reconcile must sit OUTSIDE
  that branch and must not be gated on "we need a slot"** — otherwise a repo at
  `wip_cap: 0`, or any run with `enforce_cap` false, never reconciles and never
  surfaces a stale claim. Cheap now, expensive to retrofit.

## Slice cut — APPROVED AND FILED 2026-07-26

> **This section is now HISTORY plus the filed record.** The cut below was approved
> by the maintainer as drafted and filed through
> `/livespec-orchestrator-beads-fabro:groom`. **S4 was DROPPED** (ruling 2), so the
> table's S4 row is retained only for the rationale that killed it — do not
> resurrect it. Filed ids: S1 `bd-ib-ohdu5a`, S2 `bd-ib-cfgkkk`, S3 `bd-ib-pme57n`.
> Two approved scope changes are folded into the FILED slices and are NOT reflected
> in the table rows below: **S1 also closes the write-side `O_EXCL` gap**, and
> **S3 also moves `write_dispatch_lock` to admission time**. Read the filed items
> for the authoritative scope.

Drafted 2026-07-26, NOT filed. The maintainer owns the cut and the acceptance.

| slice | req | scope | depends on |
|---|---|---|---|
| **S1** harden dispatch-lock liveness: consult `started_at_epoch` (PID + process start time), adopting `_dispatcher_admission_mutex._pid_start_time_mismatches` | 3 | in-repo, pure, small | — |
| **S2** needs-attention lane: `active` item with no live dispatch lock, enriched from the journal terminal `outcome` record (carry `pr_number`/`merge_sha`, hand off `reconcile-merged`) | 2 | in-repo | S1 (soft) |
| **S3** narrow `active_count` to claims a LIVE dispatch lock still holds, and journal the abandonment. **Do NOT move the item's status** (§"CORRECTED"); must sit outside `if enforce_cap:` | 1 | in-repo | S1 (**required — unsound without it after a SIGKILL**), S2 (**required — S3 alone deletes the only backpressure; see §"S2 MANDATORY"**) |
| **S4** stale-`active` detection in the fleet hygiene scan | 4 | **cross-repo** (see §"Scope boundary") — but see §"S4 SCOPE": recommended DROPPED, as it protects zero tenants today | independent |

**The ordering is the point: S2 before S3.** Both existing reclamation paths
(`_stale_admission_mutex_reclaimed`, `_stale_janitor_lock_reclaimed`) reclaim
silently and journal nothing; S3 must not copy that silence.

> **Refined by later research — read §"Reclaim destination" before relying on
> this paragraph.** The original argument was "shipping the reclaim first cleans
> up silently after a failure nobody is told about." That is now too strong: if
> S3 sends the item to `blocked`/`needs-human` (the recommended destination), the
> EXISTING `human_valves()` lane surfaces it with no new code. The accurate
> argument is worse for S3-alone, not better — the default lane's handoff is
> `resolve-blocked:<id>:ready`, which pushes an ALREADY-MERGED item back into the
> dispatch queue. So S3 alone does not fail to surface; it surfaces with a handoff
> that causes a second defect. The ordering holds, for a sharper reason.

Requirement 2 is cheaper than it looks — `_needs_attention_work_items.py` is
in-repo, and `_recorded_host_only_refusals()` ALREADY reads
`tmp/fabro-dispatch-journal.jsonl`, filters `stage == "outcome"`, matches an
`outcome.stage`, and builds an `AttentionItem` lane. The janitor-red record is the
same verified shape (`detail`, `fabro_run_id`, `merge_sha`, `pr_number`, `stage`,
`status`, `work_item_id`). `human_valves()` today surfaces `pending-approval`,
`acceptance`, and `blocked`(needs-human) — never `active`.

**But "near-copy" is a trap; three constraints bound it.** S2 is only cheap and
only in-repo if it (a) is built like `host_only_items` rather than routed through
`human_valves()`, and invents no new `AttentionKind` — §"S2 SHAPE"; (b) intersects
journal evidence with CURRENT ledger status rather than copying the precedent's
staleness bug — §"S2 CONSTRAINT — do not copy…"; and (c) carries an actionable
handoff with the prior-attempt count, since `reconcile-merged` cannot always
recover — §"S2 CONSTRAINT — 'run `reconcile-merged`'…". Read all three before
sizing S2.

Rejected: **reclaim-first (S3→S2)**, which ships the wrong handoff first; and
**one combined slice**, which carries four requirements (and, unless S4 is dropped
per §"S4 SCOPE", a cross-repo leg). Note the journal's own `sizing-warn` on
`bd-ib-w4h4`: "description is 4897 chars (> 1500) … consider splitting" and
"carries 5 enumerated parts".

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

(Why the gate is red in a fresh checkout when pre-merge CI was green is a SEPARATE
question — and it is **already filed twice**, as `bd-ib-rxxx` and `bd-ib-d6v1`,
both P1. `bd-ib-rxxx` was filed while dispatching `bd-ib-w4h4` and names it. It is
NOT part of `bd-ib-waov`; see §"The janitor red's ROOT CAUSE is already filed" for
the corroboration and for two discrepancies in `bd-ib-rxxx` worth the maintainer's
eye.)

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
| S1 — **DONE, both reds verified flipped** | lock whose `pid` is live but whose `started_at_epoch` long predates that process's real start → assert DEAD; and a second claim on an existing lock is refused | shipped in PR #978 |
| `bd-ib-l2vglr` — **DONE, red demonstrated before dispatch and verified flipped after** | leaked lock whose recorded pid is dead → assert `write_dispatch_lock` RECLAIMS and re-stamps with the new caller's pid; lock whose holder is LIVE → assert it still REFUSES | shipped in PR #982. Pre-dispatch red: bare `os.open(..., O_EXCL)` raised `FileExistsError` on the dead-pid lock. Injected defect that would re-red it: swallow the raise instead of reclaiming → two dispatches share one claim |
| S2 | `active` item + no live lock + journal `janitor-post-merge`/`failed` record → assert a needs-attention lane naming the item and its merged PR | drop the lane → red |
| S2 (no staleness) | an item with a `janitor-post-merge`/`failed` record in the journal that is now CLOSED → assert NO lane is emitted | key the lane off journal history alone (as the `host-only` lane does today) → the closed item is surfaced → red |
| S2 (right handoff) | a stranded merged-yet-janitor-red item → assert its handoff invokes `reconcile-merged` | emit a handoff that moves the item (e.g. `resolve-blocked:<id>:ready`) → an already-merged item is pushed back into the dispatch queue → red |
| S3 (status preserved) | reclaim a merged-yet-janitor-red item → assert its status is STILL `active` afterwards AND `reconcile-merged --item <id>` still passes its source-lane guard | move it to `blocked`/`backlog` → `reconcile-merged` refuses with "expected active item" → the item is stranded from its own recovery path → red |
| S3 (uncounted, not moved) | one `active` item with no live lock plus `wip_cap` 1 → assert an admission-eligible ready item IS admitted on the same pass | count all `active` rows (today's `_dispatcher_admission.py:88`) → `free_slots` is 0 → nothing admitted → red |
| S3 (live janitor window) | an `active` + PR-merged item whose dispatch is mid-janitor with a live lock, up to the 1h `_JANITOR_TIMEOUT_SECONDS` bound | infer death from `status == "active"` + a merged PR (the `bd-ib-ug4z` defect) → a live run's slot is reclaimed → red |
| S3 (positive) | `active` item, no lock file → run the gate → assert it is EXCLUDED from `active_count` AND an abandonment journal record is written. **Do NOT assert it was moved out of `active`** — that expectation is retracted (§"CORRECTED") | remove the reconcile call → the item is still counted and no record is written → red |
| S3 (negative) | `active` item WITH a lock written for `os.getpid()` → assert it STILL counts against the cap | make the reconcile ignore lock liveness → a live run's slot is released → red |
| S3 (cap-independence) | `enforce_cap` false / `wip_cap` 0 → assert the reconcile still runs | nest the reconcile inside `if enforce_cap:` → red |
| S3 (admission window) | admit a batch larger than `--parallel`, run the gate while the queued items are still awaiting a worker → assert the queued `active` items are NOT reclaimed | leave `write_dispatch_lock` at `dispatch_one` entry → the queued items have no lock → reclaimed → red |
| S3 (recycled pid) | leaked lock recording a pid now held by an unrelated LIVE process, stamped with the original owner's start time → assert the item IS reclaimed | judge liveness by bare `os.kill(pid, 0)` (i.e. ship S3 without S1) → the stale lock reads live → never reclaimed → red |
| S3 (auto-rework park) — **added by the 2026-07-26 amendment** | `active` item parked by `acceptance-auto-rework` (no lock; most recent terminal `outcome` is green) → assert it is STILL COUNTED against the cap and gets NO abandonment record | use the bare "active + no live lock" predicate → the item is uncounted and a FALSE abandonment is journaled → red |
| S3 (valve rework park) — **added by the 2026-07-26 amendment** | `active` item parked by `reject:<id>:rework` (no lock, no journal record of its own, most recent terminal `outcome` green) → assert likewise still counted and unjournaled | as above → red |
| S3 (killed before outcome) — **added by the 2026-07-26 amendment** | a dispatch killed after `ledger-admit` but before any `outcome` record → assert the item IS reclaimed | require an explicit non-green outcome → a SIGKILLed dispatch is never reclaimed and requirement 3 goes unsatisfied → red |

The S3 negative test is what discharges `reconcile-merged-dispatch-lock.md`'s
objection: it proves a live dispatch inside its janitor window is never reclaimed.
S3's positive test must assert BOTH the transition AND the abandonment record, or
it passes vacuously on a status the healthy path also produces.

### Draft amendment — FALLBACK ONLY; likely not needed

> **⛔ Read §"CORRECTED" first.** Under the corrected design (leave the item
> `active`, narrow the count) the pending proposal's "MUST leave the item
> `active`" is honored LITERALLY and **no spec amendment is required at all.**
> This section is retained ONLY as a fallback for the case where the maintainer
> prefers a status move despite the `reconcile-merged` source-lane guard. Do not
> read it as live guidance.

DRAFTED, NOT FILED. The spec side is the maintainer's; this exists so the
decision is a yes/no on concrete text rather than an open design question.

`reconcile-merged-dispatch-lock.md` (TRACKED, still pending on `origin/master`)
contains, at line 70 of its proposed contract block:

> "A red janitor, missing merged PR, wrong source lane, ambiguous merged PR, or
> held janitor checkout lock MUST leave the item `active` and report the failed
> guarded precondition or janitor stage."

Read literally, that forbids requirement 1. The narrowest fix is to bound the
claim by the ownership lock the SAME proposal already mandates, appending one
sentence immediately after it:

```markdown
An item left `active` by this valve remains claimed only while a live
dispatch-scoped ownership lock names it. Once no live lock owns the item the
claim is abandoned, and the Dispatcher's admission valve MUST NOT count it
against the per-repo WIP cap: it MUST journal the abandonment and move the item
out of `active` to `blocked` with `blocked_reason` `needs-human`, so the recovery
this valve exists for is surfaced for a human rather than silently held.
```

Why this shape:

- It reuses the proposal's OWN vocabulary — the "dispatch-scoped ownership lock"
  is introduced two paragraphs earlier in the same block — so it adds no new
  concept and needs no new definition.
- It preserves the clause's intent exactly. The item still stays `active` for the
  dispatch that owns it, which is what the clause is protecting; it only stops
  `active` from outliving every owner.
- It names `blocked`/`needs-human` rather than `backlog`, consistent with
  §"Reclaim destination" and with `escalate_needs_human_block`'s existing
  reasoning.
- It is additive: no existing sentence is deleted or reworded, so it does not
  disturb the rest of a proposal already under review.

**Two routes, maintainer's choice.** Either fold this into
`reconcile-merged-dispatch-lock.md` BEFORE it is revised in (cleanest — the
contract lands coherent the first time), or ratify that proposal as-is and file a
follow-on `propose-change` afterwards (lower coupling, but leaves a window where
the ratified contract forbids requirement 1). If the maintainer instead rules
that requirement 1 narrows to "surface only, never auto-reclaim", **no spec change
is needed at all** — S2 alone is legal under the clause as written, and S3 drops
out of the cut.

### ⛔ CORRECTED 2026-07-26 — do NOT move the item at all; stop COUNTING it

**This supersedes §"Reclaim destination" below, which recommended
`blocked`/`needs-human`. That recommendation was WRONG and is retracted.** It was
made without checking the shipped recovery valve.

`_dispatcher_reconcile_merged.py:110-113`:

```python
if item.status != "active":
    detail = f"ERROR: reconcile-merged expected active item {item.id}; found {item.status}\n"
    return EXIT_PRECONDITION_ERROR
```

Moving a reclaimed item OUT of `active` — to `blocked`, `backlog`, or anything
else — makes it **unrecoverable by the sanctioned valve**, which is precisely the
state `bd-ib-lza6` was filed to fix. A reclaim that strands the item from its own
recovery path is worse than the leak.

**The corrected design: leave the status alone and fix the ARITHMETIC.** Requirement
1's actual goal is "a dead claim must not hold a WIP slot", not "the row must
change status". Narrow `active_count` (`_dispatcher_admission.py:88`) to count only
`active` items that a LIVE dispatch lock still claims. Everything else follows:

- **`reconcile-merged` keeps working** — the item stays `active`, so its source-lane
  guard passes.
- **The pending proposal is satisfied LITERALLY.** "A red janitor … MUST leave the
  item `active`" is honored exactly. **So §"Draft amendment" is NOT needed** — the
  spec collision dissolves rather than requiring a ratification-tier change. Keep
  the draft only as a fallback if the maintainer prefers a status move after all.
- **Requirement 2 returns to its original shape.** The item stays `active`, so the
  `blocked`/`needs-human` valve lane does NOT fire and surfacing is NOT free. S2
  must build its own lane, exactly as §"S2 SHAPE" describes. The claim in
  §"Reclaim destination" that surfacing comes free is retracted with it.
- **It is a strictly smaller change** — one predicate in the admission arithmetic,
  no ledger write, no new lifecycle vocabulary, no spec amendment.

Requirement 3 is still satisfied: the claim is bounded in EFFECT (it stops
consuming capacity) even though the row keeps its status. "Unbounded" does not
survive as the answer.

The abandonment MUST still be journaled — dropping the ledger write does not
license dropping the record. See §"S2 CONSTRAINT" clauses; silence is the
anti-precedent.

#### The corrected design makes S2 MANDATORY, not merely first

This follows directly and is the sharpest form of this thread's thesis.

**Today the leak is self-limiting, in a perverse way.** Every stranded claim
permanently costs one slot, so at `wip_cap` 5 the fifth abandonment halts dispatch
entirely. That total stoppage IS the current forcing function — it is ugly and
slow, but it guarantees a human eventually looks. The console tenant's four-of-five
rows are exactly that pressure, one abandonment from the wall.

**Narrowing `active_count` removes that forcing function.** Under the corrected
design a stranded claim costs nothing, so the cap never fills, dispatch never
stops, and NOTHING ever compels anyone to look. The row sits `active` forever,
uncounted and unexamined.

So S3 shipped alone would not merely "re-hide" the failure — it would **delete the
only backpressure that currently surfaces it, while adding no signal in its place.**
That is strictly worse than today's behavior, not a partial improvement.

**Therefore S2 is not a sequencing preference under the corrected design; it is a
correctness precondition.** S3 MUST NOT merge before the attention lane exists. If
the maintainer wants S3 sooner, the honest options are to ship S2 first, or to ship
them as ONE slice — never S3 alone.

(This is a stronger claim than the earlier "ordering is the point" paragraph, and
it supersedes it. That paragraph argued S2-first on record-keeping grounds; this
argues it on capacity-backpressure grounds, which holds even if one considers the
record adequate.)

### ⚠ LEDGER OVERLAP — `bd-ib-waov` is NOT greenfield; four items already cover parts

Scanned 2026-07-26 across all 80 non-closed items. The groom MUST reconcile against
these before cutting slices, or it will file work that is already shipped.

| item | P | status | relationship to `bd-ib-waov` |
|---|---|---|---|
| **`bd-ib-lza6`** | 2 | **acceptance** | **The same defect, already ruled and shipped.** "Merged items strand in `active` when the dispatch process does not complete its post-run disposition." Maintainer ruled 2026-07-19: build FIX OPTION 2, the `reconcile-merged` valve (PR #797). Options 1 ("route to an acceptance-recoverable state / dedicated lane") and 3 ("make the janitor gate pre-merge") were **explicitly NOT selected.** Held from acceptance pending `bd-ib-ug4z`. |
| **`bd-ib-ug4z`** | 1 | **acceptance** | Added the liveness guard to `reconcile-merged` — this is where `_dispatcher_dispatch_lock.py` came from. |
| `bd-ib-hycf` | 1 | backlog | Largely FALSIFIED on re-check (a journal read-timing misread). Its surviving finding matters here: the **admission lock is released BEFORE the outcome event is journaled**, so a watcher keyed on lock release reads a torn state. |
| `bd-ib-81l0` | 2 | ready | `reconcile_plan` hardcodes `fabro_bin='fabro'`, so **the recovery valve exec-fails inside the credential wrapper.** |

Note on the two `acceptance` rows: `bd-ib-lza6` states it is "HELD from acceptance
pending" `bd-ib-ug4z`. `bd-ib-ug4z`'s fix has SHIPPED (`_dispatcher_dispatch_lock.py`
is on `master`) and the item now sits in `acceptance` itself, so whether lza6's hold
is discharged depends on whether "pending this fix" means merged (satisfied) or
accepted (not yet). Both have been parked since 2026-07-19. Worth the maintainer's
eye — accepting them would settle the ratified recovery path this epic's
requirement 2 is built around.

**What this leaves genuinely NEW in `bd-ib-waov`** — and the groom should scope it
to exactly this, not re-litigate the above:

1. **The WIP-cap consequence.** `bd-ib-lza6` built a recovery path; nothing has ever
   addressed the fact that a stranded claim permanently consumes a slot. That is
   this epic's core.
2. **The notification gap (requirement 2).** `bd-ib-lza6`'s design assumes a human is
   told to run `reconcile-merged`. **Nothing tells them.** Requirement 2 is precisely
   the missing half of an already-ruled design — which is a much stronger warrant
   than "surface it as polish".
3. **The liveness hardening (requirement 3).** `bd-ib-ug4z` shipped the lock but left
   `started_at_epoch` unconsulted.

Two consequences for the plan:

- **`bd-ib-81l0` is a de-facto dependency of S2.** S2's whole handoff is "run
  `reconcile-merged`", and that valve currently exec-fails under the credential
  wrapper. Surfacing a lane pointing at a broken command is not a fix.
- **The 1-hour janitor timeout is the hard bound S3 must respect.**
  `_dispatcher_engine_janitor.py:40` sets `_JANITOR_TIMEOUT_SECONDS = 3600.0`, so a
  LIVE, healthy dispatch can legitimately sit `active` + PR-merged + mid-janitor for
  a full hour. `bd-ib-ug4z` was filed because `reconcile-merged` inferred death from
  `status == "active"` + a merged PR, which is NOT unique to a dead process. **S3
  must not repeat that inference.** This is the strongest available justification for
  keying the reclaim on the live dispatch lock rather than on status, age, or a TTL.

### The janitor red's ROOT CAUSE is already filed — keep it out of `bd-ib-waov`

An earlier revision called the fresh-checkout janitor red "a SEPARATE question —
plausibly systemic" and left it there. It is separate, and it is **already filed
twice**, both P1 `backlog`:

- **`bd-ib-rxxx`** — "janitor gate is checkout-dependent: `supervisor_discipline`
  passes on master, fails in a fresh janitor checkout, stranding items."
  **Filed 2026-07-20 while dispatching `bd-ib-w4h4` and naming it explicitly.** It
  measured both sides: the primary checkout at clean `origin/master` returns rc=0
  with 8 × `"phase": "0-warn"` for `.claude/hooks/livespec_footgun_guard.py` and
  `bd-guard/bd-guard-emit.py` — the SAME two files `bd-ib-w4h4`'s janitor-red
  detail cites, with `"newly_covered": true`. Strong corroboration.
- **`bd-ib-d6v1`** — "`just check-coverage` reuses a STALE `.coverage` with no
  freshness check", so a standalone invocation reports coverage for a tree state
  unrelated to the working tree.

**Consequence for the groom: `bd-ib-waov` must NOT try to fix the janitor red.**
Its cause is owned elsewhere. `bd-ib-waov` owns the *consequence* — that a
stranded claim silently eats a WIP slot and nobody is told — which is true
regardless of why the janitor went red.

It also means **`bd-ib-w4h4` becomes recoverable once `bd-ib-rxxx` lands**, since
its janitor red would stop reproducing. That is the natural moment to un-strand it
— but not before the requirement-1 verifier exists, since it is the fixture.

#### Two discrepancies in `bd-ib-rxxx` worth the maintainer's eye

Recorded because this thread's own charter says a filed item is a claim with a
timestamp, and both were checked against the forge.

1. **`bd-ib-rxxx` says the dispatch "STRANDED that item `active` with no PR". That
   is FALSE.** PR **#836** exists, its head branch is literally
   `feat/bd-ib-w4h4`, it MERGED at 2026-07-20T05:31:50Z with merge commit
   `ba9fdaf`, and all three of `bd-ib-w4h4`'s terminal outcome records carry
   `pr_number: 836` + that merge SHA. This matters practically: a maintainer
   reading "no PR" could reasonably re-dispatch `bd-ib-w4h4`, which would try to
   rebuild an already-merged change — the exact failure `bd-ib-lza6` documents as
   a non-viable workaround.
2. **The two sources attribute the red differently.** `bd-ib-rxxx` attributes it to
   checkout-dependent `supervisor_discipline`; the captured janitor tail carries an
   explicit `error: Recipe `check-coverage` failed with exit code 2` (the
   `supervisor_discipline` lines in that same tail are `"phase": "0-warn"`,
   `"level": "warning"`, which do not fail the gate). Both readings are recorded
   here without adjudication — `bd-ib-rxxx` did a measured both-sides comparison,
   which is stronger evidence than reading a truncated stderr tail, but it does not
   explain the explicit non-zero `check-coverage` line. `bd-ib-d6v1` may reconcile
   them. **Settling this belongs to `bd-ib-rxxx`, not here.**

### Reclaim destination — SUPERSEDED, retained for the reasoning about `backlog`

Researched 2026-07-26. `backlog` is the wrong destination, and the repo already
argues so in its own words.

**`backlog` would re-dispatch already-merged work.** A `janitor-post-merge` red
means the PR IS ON MASTER (`bd-ib-w4h4` carries `pr_number: 836`,
`merge_sha: ba9fdaf…`). `backlog` leaves the item admission-eligible, so the
Dispatcher would pick it up again and try to redo work that already shipped.
`bounce_non_convergence_to_backlog` is a fine precedent for a slice that never
converged — it is the wrong precedent for a slice that converged and merged.

**The repo's own precedent says so.** `escalate_needs_human_block`'s docstring:

> "Persist that as a Dispatcher-level terminal ledger state, not as `backlog`:
> the item remains unavailable to autonomous admission until a human valve
> deliberately clears the block."

That is exactly this situation. The write seam already exists —
`update_work_item_blocked_state(path=…, item_id=…, status="blocked",
blocked_reason="needs-human", admission_policy="manual")` — and sets the
admission policy in the same call. Admission-ineligibility is guaranteed by
construction: `is_item_ready` is defined as `lane_of(...).name == "ready"`, and
`lane_of` maps a stored `blocked` to `Lane("blocked", <blocked_reason>)`.

**This partially satisfies requirement 2 for free — but NOT completely, and the
residue is the important part.** `lane_of` returns
`Lane("blocked", item.blocked_reason)`, and `human_valves()` already has:

```python
elif status == "blocked" and lane_reason == "needs-human":
    lanes.append(_valve(verb="resolve-blocked", …,
                        action_id=f"resolve-blocked:{item_id}:ready"))
```

So a reclaimed item SHOWS UP in needs-attention immediately, with no new lane
code. **But that lane's handoff is `resolve-blocked:<id>:ready` — which pushes an
already-merged item back to `ready` and straight into the dispatch queue.** The
default surfacing is therefore actively wrong for this class: it tells the
operator to do the one thing that redoes merged work.

**This SHARPENS the S2-before-S3 ordering rather than weakening it.** Shipping S3
alone would not leave the failure unsurfaced — it would surface it with a handoff
that causes a second defect. S2's real job is narrower and clearer than first
stated: not "make it visible" (the blocked lane does that) but **"give it the
right handoff"** — `reconcile-merged` carrying the failing stage, the merge
evidence, and the prior-attempt count, instead of the generic
`resolve-blocked → ready`.

### ⛔ FILING CONSTRAINT — linking slices to the epic is KNOWN-BROKEN; read before filing

The groom's output is "dependency-layered slices under `bd-ib-waov`". **The
sanctioned store writer cannot express that link**, and failing halfway is its
observed behavior — not a hypothetical.

Two filed items, both P2 and both `blocked`:

- **`bd-ib-vari3j`** — "store writer cannot express beads epic membership".
  `_store_mutations._add_dependency_edges` maps every `depends_on` entry to
  `bd dep add <item> <dep> --type blocks`, and the live backend REJECTS that when
  the target is an epic: `Error: tasks can only block other tasks, not epics`.
  `create_work_item` also calls `create_issue(parent_id=None)` hardcoded. So a
  child→epic relationship **has no valid expression through the sanctioned
  writer.**
- **`bd-ib-kn63nm`** — the same defect's consequence: because edges are added
  AFTER the item row is written, the rejection leaves a **PARTIALLY-COMPLETED
  write.** The work-item EXISTS, its declared `depends_on` does not, and the
  caller sees only a traceback. **Re-running the same filing therefore
  DUPLICATES the item.**

**What the groom must do about it:**

1. **Do NOT give a slice a `depends_on` entry pointing at `bd-ib-waov`.** It will
   traceback, and the row will already exist.
2. **Inter-slice edges are FINE.** S1→S3 and S2→S3 are task→task, and `blocks` is
   valid there. Only the child→EPIC edge fails.
3. **Record epic membership in PROSE** (in each slice's description) until
   `bd-ib-vari3j` / `bd-ib-kn63nm` land — the same "prose IS the link" device this
   thread already uses for the cross-tenant `-6ma` supersession.
4. **If any filing tracebacks, RE-READ the store before retrying.** The item is
   probably already there.

Also verified 2026-07-26: **`bd-ib-waov` currently has `dependency_count: 0`,
`dependent_count: 0`, and no children** — it is entirely unlinked, and no other
item in the ledger references it. The four overlapping items in §"LEDGER OVERLAP"
are related only by this prose. Linking them is a groom deliverable, subject to
the constraint above.

### Maintainer rulings — ALL SETTLED 2026-07-26. Do not re-ask.

1. **Spec collision — DISSOLVED.** The reclaim narrows the count and leaves status
   untouched, so the pending proposal's "a red janitor … MUST leave the item
   `active`" is honored LITERALLY. **No amendment to
   `reconcile-merged-dispatch-lock.md` is needed**; §"Draft amendment" stays
   FALLBACK ONLY.
2. **Reclaim mechanism — narrow the count, do NOT move the item.** The
   `blocked`/`needs-human` destination stays RETRACTED, because
   `_dispatcher_reconcile_merged.py:110-113` refuses any item not in `active`.
3. **Requirement 4 / S4 — DROPPED, not deferred.** Closed out of the epic entirely
   on the finding that it protects zero tenants today. The rationale is recorded in
   the closed epic's description so a successor does not resurrect it as an
   oversight. See §"S4 SCOPE".
4. **Epic scope — narrowed to the three genuinely-new pieces**, with `bd-ib-81l0`
   pulled in as S2's gate (as prose; it cannot be an edge).
5. **The cut and every acceptance criterion — APPROVED as drafted**, plus two scope
   additions approved at groom time: S1 also closes the write-side `O_EXCL` gap, and
   S3 also moves `write_dispatch_lock` to admission time.

Three further rulings, settled 2026-07-26 AFTER the groom:

6. **S3's reclaim predicate — AMENDED.** It is no longer "active + no live lock";
   it additionally requires that the item's most recent terminal `outcome` be
   non-green, or that no `outcome` exist since its most recent `ledger-admit`.
   `bd-ib-pme57n`'s description carries the amendment and three added verifiers.
   See §"Rework doors".
7. **`per-state-verb-vocabulary.md`'s self-contradiction — HAND BACK for amendment**,
   delivered 2026-07-26. It is NOT a gate on this track's revise pass, because that
   proposal is not in this track's scope. Never edit it here.
8. **The revise pass covers BOTH pending proposals, and both are ours** —
   `reconcile-merged-dispatch-lock.md` and `rework-return-door-attribution.md`.
   This ruling was corrected twice: an early relay claimed a pass is
   all-or-nothing across every in-flight proposal (retracted, and refuted by
   v049's own history); the correction then scoped us to one file, which went
   stale the moment the peer's proposal ratified as v050 and we filed our own.
   No cross-track coordination is required any more. See §"The revise pass".
9. **The v050 rework-return journaling claim is FALSE and a correction is filed.**
   `reject:rework` is journaled nowhere — the `"journal"` object lives in the
   drive CLI's response payload, and the dispatch journal holds zero
   `human-valve-*` records over 134 dispatches. Filed against OUR spec tree as
   `rework-return-door-attribution.md`. Its second finding — whether the
   unattributable door gains attribution or is removed — is deliberately left for
   ratification to settle, with the recommendation stated. See §"Rework doors".
10. **Two follow-on items filed 2026-07-26**, both `ready`, neither part of the
    epic: **`bd-ib-2wgooj`** (P2, factory-safe — `_MOVE_ALLOWED` still permits the
    bare `move:<id>:active` door that v050 retired; discharges S3's accepted
    residual) and **`bd-ib-d6op2n`** (P2, **host-only**, `factory_safety:
    mutates-host-machinery` — the `livespec-driver-claude` core-resolution
    misfire; owned by that repo, filed in this tenant because beads has no
    cross-tenant edge, so the prose IS the link and it must be routed by hand).

Two further calls settled at groom time:

- **Closing the anchor epic was accepted.** `file_approved_slices` always closes the
  target; the anchor moved to the three filed slices and this file was repointed.
- **`CandidateSlice.priority` is dead API surface** — declared on the dataclass but
  never read by `_work_item_for`, and `WorkItem` dropped `priority` entirely. The
  filed slices therefore came out at the store default P2 despite the draft passing
  `priority=1`; they were set back to P1 to match the epic. Worth its own item;
  filing that is the maintainer's call.

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
