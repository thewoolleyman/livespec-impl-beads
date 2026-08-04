# Handoff — guarded Beads v1.1.2 upgrade

**Thread:** `plan/beads-v1-1-2-upgrade/`  
**Ledger anchor:** epic `bd-ib-3kolea`, currently `backlog` because it needs
decomposition  
**Related existing defect:** `bd-ib-dwv`, the v1.0.5 Docker release-asset 404  
**Detailed evidence:** `research/qualification.md`

## Outcome to deliver

Upgrade the Livespec family from Beads v1.0.5 to the official stable v1.1.2
release without bypassing the lifecycle guard and without installing Beads
through mise.

The final host and container contract is:

| Path or setting | Required value |
|---|---|
| `/usr/local/bin/bd` | tracked Livespec guard wrapper |
| `/usr/local/bin/bd-real` | checksum-verified official Beads v1.1.2 executable |
| `LIVESPEC_BD_PATH` when set | `/usr/local/bin/bd` |
| Beads installation mechanism | direct, checksum-verified manual copy; never mise |
| Production migration | attended, quiesced, backed up, one designated migrator per tenant |

This is not a simple binary bump. v1.1.2 crosses migrations 0050 through 0053
and changes storage behavior. A binary rollback alone is not a database
rollback after those migrations; restoration of the pre-migration tenant
backup is the data rollback boundary.

## Current state

### Restart checkpoint — 2026-08-04 doc reconciliation awaiting review

This is the sole authoritative restart checkpoint until PR #1284 receives an
exact-head supervisor decision. It supersedes every instruction below for
resumption purposes without merging or replacing the proposed reconciliation
that remains under review.

- Supervisor accepted the `bd-ib-dwv` attended proof and its exact-once closure
  at `2026-08-04T02:32:41Z`. The worker then performed only the authorized
  doc-only reconciliation and did not rerun the proof, mutate another ledger
  item, or begin another outcome.
- The proposed reconciliation is open as PR
  [#1284](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/1284)
  on branch `docs/beads-v1-1-2-o5-proof-reconcile`, exact head
  `bbda528d096ea28b475c2d7e66530ae3fc987826`, against base
  `154b5fd473b233b726418746fac86716091a210f`. Its sole changed path is this
  handoff. The owned worktree is
  `/home/ubuntu/.worktrees/livespec-orchestrator-beads-fabro/docs/beads-v1-1-2-o5-proof-reconcile`
  and was clean at wind-down.
- PR #1284 remains open, non-draft, and unmerged with auto-merge disabled. The
  repository bot briefly enabled auto-merge after creation; the worker caught
  and disabled it before merge eligibility. All 95 checks are now terminal:
  94 succeeded, one skipped, and none failed.
- Applicable foreground validation passed: the eight-target doc-only aggregate
  passed manually, at commit, and at push; push-time ledger conformance was
  clean; the ownership diff contained only this handoff; and a context-free
  reader passed the handoff self-sufficiency gate. The non-fatal lefthook
  synchronization warning about an existing `.old` hook file recurred, but all
  actual hooks and gates executed successfully.
- The proposed checkpoint in PR #1284 makes O5 terminal, records
  `bd-ib-dwv` closed and the accepted proof-log SHA-256
  `53eee1e2b25fb720a7ef59d5ae483af09b6cd0e32f831325c4886b4cc57db717`,
  prohibits any proof rerun or further attended action, and replaces the stale
  PR #1221 route. It records the external Dolt-server default-branch
  `ci-green` evidence as the immediate blocker and permits only a later public
  remeasurement followed by sanctioned dark-factory action
  `impl:dolt-server-wgy` if every existing valve passes.
- Resume by verifying PR #1284 still has exact head `bbda528d…`, remains
  unmerged, and has auto-merge disabled. The primary checkout,
  `origin/master`, and GitHub forge master are now equal at
  `f42aed94979f01c0d2fe7980dc00994a55543642`, the merged restart-checkpoint
  commit. Because that checkpoint advanced master beyond PR #1284's original
  base, GitHub reports the held PR's merge state as `DIRTY`. Its exact head and
  worktree are unchanged and clean. Stop for the pending exact-head supervisor
  decision; do not rebase, modify, or merge that PR, start another outcome,
  inspect the separate governed-plan runtime, or touch any other session's
  worktree or branch without new supervisor authorization.

### Restart checkpoint — 2026-08-04 attended O5 proof complete

This checkpoint supersedes the older 2026-08-04 pre-proof checkpoint and every
stale “Immediate next action” below. The authorized attended guarded-image proof
for existing item `bd-ib-dwv` completed successfully and was fully cleaned up.
Do **not** repeat the proof, close the item, or start another outcome. The next
action is fresh supervisor review of this exact proof receipt while
`bd-ib-dwv` remains `active` and unassigned.

- The proof ran exactly once in the foreground from the clean detached source
  commit `b9c8904b5ad41de94eb636b3e509a027e48047a0` with the authorized command,
  exact image tag `livespec-orchestrator:bd-ib-dwv-20260804t0132z`, container
  `livespec-orch-verify-bd-ib-dwv-20260804t0132z`, volume
  `livespec-orch-varlib-bd-ib-dwv-20260804t0132z`, and host port `32380`. It
  exited `0` with the terminal artifact
  `ALL TIER-1 CHECKS PASSED (driver=overlayfs, web-ui=HTTP 308)`.
- The complete redacted proof output is preserved outside every checkout at
  `/home/ubuntu/.local/state/livespec-proof-logs/bd-ib-dwv-20260804t0132z.log`.
  It is 158 lines and 7,851 bytes, with SHA-256
  `53eee1e2b25fb720a7ef59d5ae483af09b6cd0e32f831325c4886b4cc57db717`.
  A value-based scan for every required injected secret found no disclosure;
  values were never printed.
- The created local image ID was
  `sha256:a64973f225fbc4b10788140ef22445261a87ff798ad0da34e01723cf33254932`
  and had no repository digest. The official v1.1.2 tarball SHA-256 was
  `a72d71ed374955dc9f83a0f90b54bd7b6a0016709dd1676ae2e368651ed401c2`;
  the extracted and image `/usr/local/bin/bd-real` SHA-256 was
  `6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82`.
  The guard sentinel was present, `LIVESPEC_BD_PATH` was
  `/usr/local/bin/bd`, and both wrapper and real version output were
  `bd version 1.1.2 (20e493e56: HEAD@20e493e569c9)`.
- The Tier-1 lifecycle leg ran failure-fatally under `set -e`. A qualifying
  create read back as `backlog`. In explicit `fail` mode, prohibited
  `--status in_progress` exited `3`, produced empty stdout, warned that
  `bd update --status in_progress' is non-lifecycle; use --status active`, and
  left the item in `backlog`. The inner Docker driver was `overlayfs`; the
  ephemeral inner Dolt round trip returned `hello-dind`; the HTTP probe was
  `308`; and the installed Fabro version was `0.254.0`.
- A first read-only inspection command had an `awk` quoting error
  (`$1: unbound variable`) and therefore printed a blank hash while still
  recording versions, path, and sentinel. It did not affect the proof. The
  hash inspection was immediately corrected with a read-only direct
  `sha256sum` entrypoint and recorded the exact `bd-real` hash above.
- Cleanup was complete. The script trap removed the exact container, volume,
  and staged `fabro`, `bd-guard`, and `plugin-scripts` payloads. The sole local
  image tag and image ID were removed without a global prune. Port `32380` is
  free; every exact Docker resource is absent; the proof checkout had no
  tracked or untracked residue and was removed; and its path is no longer
  registered. Host `/usr/local/bin/bd` and `/usr/local/bin/bd-real` hashes are
  unchanged at
  `5f55fbfbdb872faf1e43e91e7276ed7f1f754e1611e1c84921286029224637a3`
  and
  `463b7655041345ce5d4bac00c3a5d465166bb30166147e11ef1c6e07df0a4486`.
- No image was pushed, no registry was mutated, and no production tenant,
  production Dolt data, backup/restore state, host Fabro server, host binary,
  or unrelated process/session was touched. `bd-ib-dwv` was not closed and no
  other ledger item was mutated. The ignored runtime terminal receipt is in
  `tmp/overseer/beads-v1-1-2-upgrade/worker-status.log` at
  `2026-08-04T02:21:04Z` with event
  `bd-ib-dwv-attended-proof-green`.
- At this checkpoint the primary checkout is clean on `master` at
  `a25f4b415d109a900d59fdb3c6d6a59e697b067c`. The proof source commit is its
  ancestor. No proof subprocess, proof worktree, feature branch, or background
  sub-agent remains.

### Restart checkpoint — 2026-08-04 attended O5 proof

Maintainer authorization now supersedes both the stale “Immediate next action”
and the older 2026-08-03 O5-code checkpoint below. Resume **only** the attended
guarded-image proof for existing item `bd-ib-dwv`; do not start another outcome,
repair code, close the item, or perform any production or host rollout work.

- The primary checkout, fetched `origin/master`, and GitHub forge master were
  clean and equal at
  `b9c8904b5ad41de94eb636b3e509a027e48047a0` when the proof preflight ran.
  PR #1221 was independently verified merged at
  `976caf9744b8a6c1159434da8f2102081935f419` on
  `2026-08-03T04:10:48Z`; that merge is an ancestor of the verified source.
- The existing attended proof `bd-ib-dwv` passed its exact read-only
  preconditions and was moved through the configured wrapper and public guard
  from `backlog` to `active` at `2026-08-04T01:45:32Z`. It remains unassigned,
  carries `factory-safety:needs-privileged-host`, and has exactly one `blocks`
  prerequisite: closed code item `bd-ib-1rz6`. Do not mutate any other ledger
  item, and do not close `bd-ib-dwv` after the proof; successful evidence must
  stop in `active` for fresh supervisor review.
- The sole proof checkout already exists as a clean detached worktree at
  `/home/ubuntu/.worktrees/livespec-orchestrator-beads-fabro/proof-bd-ib-dwv-20260804t0132z`,
  exact HEAD `b9c8904b5ad41de94eb636b3e509a027e48047a0`. Reuse only this checkout;
  do not create another proof checkout or touch any other session worktree or
  branch. It had no tracked or untracked residue when created.
- Exact collision preflight passed immediately before the ledger transition:
  image tag `livespec-orchestrator:bd-ib-dwv-20260804t0132z`, container
  `livespec-orch-verify-bd-ib-dwv-20260804t0132z`, volume
  `livespec-orch-varlib-bd-ib-dwv-20260804t0132z`, and host listener port
  `32380` were absent. The staged `orchestrator-image/fabro`,
  `orchestrator-image/bd-guard`, and `orchestrator-image/plugin-scripts`
  payloads were also absent. Recheck every exact collision before any Docker
  mutation; halt rather than deleting or reusing a collision.
- Secret probes through
  `/data/projects/1password-env-wrapper/with-livespec-env.sh` printed names and
  character counts only. Required values were present:
  `GITHUB_APP_ID=8`, `GITHUB_PRIVATE_KEY=1649`,
  `ANTHROPIC_API_KEY_LIVESPEC_E2E=109`,
  `CLAUDE_CODE_OAUTH_TOKEN=109`, and
  `HONEYCOMB_INGEST_KEY_LIVESPEC=65` characters including the probe newline.
  `GITHUB_APP_INSTALLATION_ID` and `GITHUB_API_URL` were absent; the committed
  entrypoint and README explicitly classify both as optional overrides, so
  this is not a proof precondition failure. Never print any value.
- Pre-proof host hashes were recorded without executing the private delegate:
  guard `/usr/local/bin/bd` SHA-256
  `5f55fbfbdb872faf1e43e91e7276ed7f1f754e1611e1c84921286029224637a3` and
  real `/usr/local/bin/bd-real` SHA-256
  `463b7655041345ce5d4bac00c3a5d465166bb30166147e11ef1c6e07df0a4486`.
  Recheck them after the proof to establish no host mutation.
- The proof itself **has not started**. The worker added an outer `tee` targeting
  the ignored runtime log under the primary checkout so the complete redacted
  output would survive, and the Codex PreToolUse
  `livespec_footgun_guard.py` blocked that shell command as a primary-checkout
  write before any subprocess ran. No image, container, volume, listener,
  staged payload, inner Dolt, production tenant, production Dolt data,
  `/usr/local/bin`, Fabro server, backup, restore, or secret was mutated by the
  blocked invocation. The hook explicitly said not to retry the same command,
  and the standing safety rule required the worker to halt.
- On the fresh session, verify SessionStart/hooks are healthy, fetch and repeat
  the exact forge/ledger/worktree/Docker collision preflight, then preserve the
  complete already-redacted output at a new collision-free path **outside every
  repository checkout** (for example under a dedicated
  `/home/ubuntu/.local/state/` proof-log directory) so the primary-write hook is
  not tripped. Do not reuse or overwrite a prior output path. The one authorized
  foreground proof command remains exactly:

  ```sh
  /data/projects/1password-env-wrapper/with-livespec-env.sh -- env \
    IMAGE=livespec-orchestrator:bd-ib-dwv-20260804t0132z \
    CONTAINER=livespec-orch-verify-bd-ib-dwv-20260804t0132z \
    VARLIB_VOL=livespec-orch-varlib-bd-ib-dwv-20260804t0132z \
    HOST_PUBLISH_PORT=32380 \
    bash orchestrator-image/build-and-verify.sh
  ```

  Run it once, foreground, from the detached proof checkout. Require the
  terminal `ALL TIER-1 CHECKS PASSED` artifact, not exit code alone.
- Independently record source SHA, local image ID/digest, official v1.1.2
  tarball SHA-256
  `a72d71ed374955dc9f83a0f90b54bd7b6a0016709dd1676ae2e368651ed401c2`,
  pinned `bd-real` SHA-256
  `6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82`,
  guard sentinel, wrapper and real version outputs, `LIVESPEC_BD_PATH`,
  fail-mode prohibited lifecycle exit `3` plus warning plus unchanged
  `backlog`, qualifying-create readback as `backlog`, inner Docker driver, and
  HTTP probe. The script authorizes only its local image build, privileged
  ephemeral container/volume, inner ephemeral Dolt, Tier-1 run, and read-only
  inspection—never an image push, registry write, host `/usr/local/bin`,
  production tenant/Dolt data, backup/restore, Fabro server, or unrelated
  process/session mutation.
- After green evidence, prove the script trap removed the exact container,
  volume, and three staged build-context payloads. Remove only the exact new
  image tag/ID; do not prune Docker or remove a shared/base image. Prove all
  exact resources absent, prove the detached checkout has no tracked or
  untracked residue, remove only that proof worktree with `mise exec -- git`,
  leave `bd-ib-dwv` active, append the exact terminal receipt to the ignored
  `worker-status.log`, and stop with a concise supervisor review request.

The ignored runtime log contains the authorization milestone at
`2026-08-04T01:44:56Z`. The `.overseer-state` file was set to `winding-down`
for this restart. No proof subprocess or background sub-agent remains.

### Restart checkpoint — 2026-08-03

The next worker must resume the owned O5 correction; do not infer that O5 or
the upgrade is complete.

- O1 `bd-ib-ne11` and O2 `bd-ib-bt1n` are closed. O5 code item
  `bd-ib-1rz6` remains `active`, assigned to `fabro`, with external reference
  `beads-v1-1-2-upgrade:O5`. The separate attended proof `bd-ib-dwv` remains
  `backlog` and unassigned.
- Factory run `01KZ0K8QR904AV5RGNZWRNXFMW` produced draft PR
  [#1221](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/1221).
  At this wind-down it was re-verified open and draft with auto-merge disabled
  at unchanged remote head
  `2f06d18f7b9fe5f2d8ba069d6caa8443b5d6ee34` and base
  `5ccbd4c01f5f220eac946cae449a03efd4f2daca`.
- The supervisor rejected that exact head because
  `orchestrator-image/build-and-verify.sh` made its embedded Tier-1 `bd init`,
  `bd create`, and `bd list` operations non-proving with `|| true`. O5 must
  make the ephemeral leg failure-fatal and prove both behaviors through the
  public `/usr/local/bin/bd`: an explicitly configured fail-mode prohibited
  lifecycle mutation exits `3` with the guard warning and does not change the
  item, while a qualifying create reads back as `backlog` after guard
  normalization. No image build or run is authorized.
- The owned correction worktree is
  `/home/ubuntu/.worktrees/livespec-orchestrator-beads-fabro/feat/bd-ib-1rz6`
  on local branch `feat/bd-ib-1rz6`. The branch was fetched and rebased cleanly
  onto verified primary, `origin/master`, and GitHub forge master
  `f9a91f064198ef4fc15407728d218016c5bc7024`; the remote PR branch was not
  updated. No other worktree owned this branch at creation time.
- The missing generated worktree pack that caused the prior Red hook failure
  was repaired in this owned worktree with `mise exec -- just bootstrap`.
  `mise exec -- just check-primary-checkout-commit-refuse-hook-installed` then
  passed. The bootstrap-created pack files are ignored runtime files, not
  tracked changes. Lefthook repeatedly warned that it could not rotate an
  already-existing `.old` hook file, but the canonical pre-commit and
  commit-message hooks executed successfully; no hook was bypassed.
- The ordered Tier-1 static test is committed as a genuine Red with checksum
  trailers. Its pre-rebase commit was `9d9846df85337e7c0f1990f81ba00b37b05b244c`;
  after the required rebase it is local head
  `3e8c760f70f9b7046bcf1807829294c0888f1302`. All 72 Red-mode pre-commit
  targets passed, and the commit-message hook recorded the expected focused
  pytest failure. Do not rewrite or drop this evidence casually.
- The worktree now has exactly one unstaged tracked change:
  `orchestrator-image/build-and-verify.sh`. It replaces the permissive Tier-1
  calls with the required public guarded path, failure-fatal init/config/create
  and show operations, an exact `backlog` readback, an explicit fail-mode
  prohibited update, exit `3` and warning assertions, and an unchanged-status
  readback. No Green amend or push occurred.
- The focused Python file passed (`6 passed`), but the additional static shell
  gate `bash -n orchestrator-image/build-and-verify.sh` failed with exit `2` at
  line 197. The cause is exact: the new single-quoted `jq` program, and later
  the apostrophe in the warning text, terminate the surrounding existing
  `bash -lc '…'` argument. The worker halted on that gate as required. No image
  was built, run, inspected, tagged, loaded, or pushed, and no host, ledger,
  tenant, Dolt, secret, backup, or Fabro mutation occurred.
- The next worker must first preserve the current evidence and correct the
  quoting contract through a fresh Red, because the test file bytes covered by
  commit `3e8c760` cannot change during that commit's Green amend. Restore only
  the unstaged broken shell edit to the local Red head, then make a new
  test-only Red that extracts a real quote-safe here-document body such as
  `bash -lc "$(cat <<'TIER1_BD' … TIER1_BD )"` and still requires the exact
  ordered behavioral commands and assertions. After that genuine Red commits,
  implement the here-document form in
  `orchestrator-image/build-and-verify.sh`, amend the new Red with
  `mise exec -- git commit --amend --no-edit`, and run `bash -n`, the focused
  test file, and `mise exec -- just check` in the foreground.
- Before pushing, fetch and immediately verify forge state again. The local
  branch is rebased while the remote remains at `2f06d18f…`, so update the same
  PR only with an exact-SHA `--force-with-lease` after proving the remote lease
  still matches that reviewed head. Verify
  `mise exec -- git diff --name-only origin/master...feat/bd-ib-1rz6` contains
  only `orchestrator-image/build-and-verify.sh` and
  `tests/test_orchestrator_image_dockerfile.py`. Keep PR #1221 draft with
  auto-merge disabled, append the new head and complete gate receipt to the
  ignored runtime worker log, and stop for fresh exact-head supervisor review.
  Do not merge, dispatch, mutate the ledger, or perform any image operation.

As measured on 2026-07-30:

- The host guard is correctly installed at `/usr/local/bin/bd`.
- The real host executable is v1.0.5 at `/usr/local/bin/bd-real`.
- The official v1.1.2 Linux amd64 release asset exists and its published
  tarball SHA-256 is
  `a72d71ed374955dc9f83a0f90b54bd7b6a0016709dd1676ae2e368651ed401c2`.
- The extracted binary reproducibly hashes to
  `6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82`
  and reports `bd version 1.1.2 (20e493e56: HEAD@20e493e569c9)`.
- The image Dockerfile installs a raw v1.0.5 binary at
  `/usr/local/bin/bd`; it does not carry the guard. That layout must change.
- The separate `fix-bd` lane has merged its guarded-entrypoint, no-mise, and
  guarded-path fallback work. The exact forge artifacts and the resulting
  implementation boundary are recorded below. This thread must not duplicate
  those edits.
- This repository has integrated the released `fix-bd` dependencies and the
  guarded public-entrypoint specification. The remaining work begins after
  those merges, not from their pre-merge state.

## Non-negotiable boundaries

1. Never run `mise install bd`, `mise use bd`, `mise exec -- bd`, or any
   equivalent Beads installation/execution path. Repository git commands still
   use `mise exec -- git` because that invokes this repository’s mandatory git
   hooks; that is unrelated to installing or running Beads.
2. Never copy the candidate binary onto `/usr/local/bin/bd`. That path is the
   guard.
3. Never point production tooling directly at `bd-real`; all normal calls go
   through the guard.
4. Never run `bd init` in a primary checkout or worktree.
5. Never exercise a destructive migration against a production tenant before
   both the server-native tenant restore and the whole-server cold-archive
   extraction have been rehearsed on isolated targets.
6. Never let more than one process migrate the same tenant. All dispatchers,
   direct agents, scheduled jobs, and other ledger writers must be quiesced for
   the attended cutover.
7. Never rewrite `SPECIFICATION/history/**`, archived handoffs, or changelog
   history merely to replace an old version string.
8. Never reimplement or restate behavior owned by `fix-bd`. Rebase after its
   relevant merges and measure the remaining scope. The narrow O6
   current-version fact exception recorded below permits only a reviewed,
   non-duplicative edit; it does not release that behavioral ownership fence.

## Definition of done

The epic can close only when all of the following are true and the evidence is
linked from the ledger:

- Release provenance, tarball SHA-256, extracted binary SHA-256, version
  output, and SPDX artifact have been reviewed and recorded.
- The current Livespec command/flag/JSON contract passes against v1.1.2 on an
  isolated database migrated from a v1.0.5-shaped backup.
- The complete `bd-guard` harness passes with a v1.1.2 real binary, including
  create normalization, selector exclusions, exact stream/exit preservation,
  and telemetry fail-open behavior.
- The server-native restore helper can restore a named source backup into a
  differently named scratch tenant, and a rehearsal proves its invariants.
- A stopped-server, whole-data-directory cold archive is captured, checksummed,
  and made root-read-only, and its exact recovery commands are rehearsed. This
  frozen cutover archive, not the shared advancing S3 remote or a logical
  issue export, is the post-migration rollback boundary.
- Every production family tenant is migrated once in an attended maintenance
  window, and post-migration invariants match the recorded baseline.
- `/usr/local/bin/bd` remains the guard byte-for-byte as intended, while
  `/usr/local/bin/bd-real` reports exactly v1.1.2 after a direct manual copy.
- The orchestrator image carries the same guard/real split, builds from the
  official live asset, and passes its hermetic Tier-1 verification without
  touching a production tenant.
- Host and image report the same Beads version and expected hashes.
- Current authoritative specs, code comments, tests, and runbooks name the
  qualified version and layout; historical records remain unchanged.
- A whole-workspace search, after the `fix-bd` changes merge, proves that no
  current Beads installation path uses mise. The report must state the exact
  repositories and path exclusions searched.
- `bd-ib-dwv` is resolved with the successful guarded image rebuild as
  evidence.

## Ownership and coordination

| Owner | Scope |
|---|---|
| Merged `fix-bd` lane | completed removal of mise references to Beads and guarded-path fallback changes; no live tmux session remained at the 2026-07-30 execution-valve recheck |
| `beads-v1-1-2-upgrade` worker | compatibility qualification, version pins, guard/image integration, migration rehearsal, current documentation, and evidence |
| `beads-v1-1-2-upgrade-supervisor` | adversarial review of this plan and later execution evidence |
| Maintainer in the attended window | production writer quiescence, direct host copy, tenant migration authorization, and rollback decision |

Before every implementation PR, fetch and rebase, then run
`git diff --name-only origin/master...<branch>` in every affected repository.
Any path already owned by another lane stays out of this thread.

## Reconciled `fix-bd` scope and narrow PR #1161 path exception

The following forge state was fetched and independently verified on
2026-07-30. Each merge is an ancestor of the named repository's fetched
`origin/master`; each release tag contains the corresponding implementation
merge.

| Repository and artifact | Verified merge | Discharged scope |
|---|---|---|
| `thewoolleyman/livespec` PR [#1845](https://github.com/thewoolleyman/livespec/pull/1845), released through PR [#1848](https://github.com/thewoolleyman/livespec/pull/1848) and tag `v0.21.0` | `b2543999be24f104194151e3a56bcdf50f55d819` | Removes the repository-mise Beads pin and makes the guarded entry point authoritative in core contracts and generated guidance. |
| `thewoolleyman/livespec-dev-tooling` PR [#900](https://github.com/thewoolleyman/livespec-dev-tooling/pull/900), released through PR [#901](https://github.com/thewoolleyman/livespec-dev-tooling/pull/901) and tag `v1.8.1` | `0304d81faff32440e456a6770e3a436fc29e79a5` | Makes non-empty `LIVESPEC_BD_PATH` authoritative and otherwise falls back to the guarded `bd` on `PATH`. |
| This repository, PR [#1161](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/1161), included in `v0.49.2` | `5675a12fbd53381138a2e1c3c47141e74d2c0e91` | Establishes the guarded public entry point, prohibits Beads installation through repository mise, and prohibits normal callers from invoking the private delegate. |
| This repository, PR [#1163](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/1163) | `0c215084610839a80b9311ec151fdef6939299b5` | Integrates `livespec-dev-tooling` `v1.8.1`. |
| This repository, PR [#1166](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/1166) | `74deb3a7976dafd108fcadece138fbeb3ef5d6ce` | Integrates `livespec` `v0.21.0`. |

That guarded-entrypoint and no-mise content is complete for this thread. Its
**behavioral ownership remains binding**: this upgrade MUST NOT reimplement or
restate the guarded-entrypoint, no-mise, or private-delegate contracts as new
behavior.

A fresh fetch and session check on 2026-07-30 found primary and
`origin/master` at `91fdcd77fe0bc6805744b59489d447c02eebe420`.
`tmux list-windows -a` showed the distinct
`beads-v1-1-2-upgrade` worker and
`beads-v1-1-2-upgrade-supervisor` windows in this repository and no window
whose name contained the exact `fix-bd` token. The former literal path embargo
is therefore not permanent, but its replacement is deliberately narrow.

O6 MAY surgically update a current, version-specific v1.0.5-to-v1.1.2 fact in
a current specification path changed by PR #1161 when that edit is necessary
for this upgrade. The exact diff must receive review specifically proving that
it does not duplicate or restate PR #1161's behavioral contracts. Frozen
history remains no-touch. `.mise.toml` and `AGENTS.md` also remain no-touch
unless a separate reviewed change first demonstrates a requirement; this plan
presumes none. Every current-spec heading change must update
`tests/heading-coverage.json` in lockstep.

This is a narrow current-fact exception, not a release of the `fix-bd`
ownership fence.

## Authoritative tenant and recovery surfaces

The live server is the tenant registry. Do not use the dated count in a
README as the rollout population. From `/data/projects/dolt-server`, enumerate
every live non-system database through the tracked helper and the dedicated
backup principal:

```sh
OPENV_KEEP_PRIVILEGES=1 sudo -E /usr/local/bin/with-dolt-admin-env.sh \
  /data/projects/dolt-server/scripts/with-dolt-admin-creds.sh \
  bash -lc 'cd /data/projects/dolt-server && source scripts/lib/common.sh && list_tenant_databases backup_sql'
```

Then enumerate the family’s committed tenant pointers:

```sh
rg -n '^dolt\.database:' /data/projects/livespec*/.beads/config.yaml
```

The migration population is the intersection: every database named by a
current family pointer must exist in the live registry, and no live
`livespec*` database may be omitted without a documented reason. On
2026-07-30 the intersection contained nine tenants:

```text
livespec
livespec-console-beads-fabro
livespec-dev-tooling
livespec-driver-claude
livespec-driver-codex
livespec-orch-beads-fabro
livespec-orchestrator-git-jsonl
livespec-overseer
livespec-runtime
```

Re-run both commands at cutover; this list is evidence, not a permanent
registry.

The rollback artifact covers the complete shared Dolt server, not just the
family intersection. Therefore the quiescence population is every database
returned by `list_tenant_databases backup_sql` and every process capable of
writing any of them. Before the maintenance window:

1. map every live database to its owner and current pointer by searching the
   whole workspace, including hidden `.beads` paths:

   ```sh
   rg --hidden -n --glob '.beads/config.yaml' \
     '^dolt\.database:' /data/projects /home/ubuntu/.worktrees
   ```

2. inventory current TCP clients, socket clients, running services, timers,
   containers, dispatchers, and direct agent sessions:

   ```sh
   sudo ss -H -ntp '( sport = :3307 or dport = :3307 )'
   sudo lsof -nP /var/lib/doltdb/dolt.sock
   systemctl list-units --type=service --state=running
   systemctl list-timers --all
   docker ps --no-trunc
   pgrep -a -f 'dispatcher.py|orchestrator.py|bd-guard|/bd( |$)'
   ```

3. record the exact stop command and restart mechanism for every identified
   writer, including non-family tenants; and
4. stop those writers and their restart mechanisms, then prove the server has
   no connection except the observer itself:

   ```sh
   OPENV_KEEP_PRIVILEGES=1 sudo -E /usr/local/bin/with-dolt-admin-env.sh \
     /data/projects/dolt-server/scripts/with-dolt-admin-creds.sh \
     bash -lc 'cd /data/projects/dolt-server && source scripts/lib/common.sh && backup_sql "SELECT ID, USER, HOST, DB, COMMAND, TIME FROM information_schema.processlist WHERE ID <> CONNECTION_ID() ORDER BY ID;"'
   ```

The final query must return zero rows. Repeat the connection query after Dolt
restarts and between every migration command. Any unrecognized row or any
writer whose restart mechanism has not been disabled is a hard stop. Keep
every server-wide writer quiesced until the forward rollout is accepted or the
whole-server rollback is complete; otherwise rollback could erase valid
post-snapshot writes in a non-family database.

The server-native backup and restore authority is
`/data/projects/dolt-server/SPECIFICATION/contracts.md` under “Backup
contract,” implemented by:

- `scripts/backup-sync.sh --db <DB>` for a live
  `CALL DOLT_BACKUP('sync', 's3')`; and
- `scripts/backup-restore.sh` for a clean-target
  `CALL DOLT_BACKUP('restore', ...)` plus branch and table-row evidence.

Both commands authenticate through the `backup` principal, using
`/usr/local/bin/with-dolt-admin-env.sh` and
`scripts/with-dolt-admin-creds.sh`; no secret is printed.

There is a sharp edge in the current restore helper: its single `--db` value is
both the source S3 path and target database name. Despite stale scratch-suffix
examples in some runbooks, `--db <DB>_restoretest` cannot restore the backup
for `<DB>`. Before the Beads migration rehearsal, land a separate
`dolt-server` specification and implementation slice that adds explicit
`--source-db <DB>` and `--target-db <SCRATCH_DB>` arguments, preserves the
existing clean-target refusal, updates the stale runbook examples, and proves
the behavior with hermetic tests. That cross-repository O3 slice follows
`dolt-server`'s own propose-change, revise, worktree, test, PR, and
rebase-merge workflow. O3 does not run the live restore. After O3 closes, the
attended O4 rehearsal owns the proof that the revised helper can restore a
real source backup into a differently named scratch tenant on the live server
with `--verify`. Production migration remains blocked until that O4 proof
passes.

The exact on-demand snapshot form for one production tenant is:

```sh
OPENV_KEEP_PRIVILEGES=1 sudo -E /usr/local/bin/with-dolt-admin-env.sh \
  /data/projects/dolt-server/scripts/with-dolt-admin-creds.sh \
  /data/projects/dolt-server/scripts/backup-sync.sh --db '<DB>'
```

After the source/target slice lands, the exact rehearsal form is:

```sh
OPENV_KEEP_PRIVILEGES=1 sudo -E /usr/local/bin/with-dolt-admin-env.sh \
  /data/projects/dolt-server/scripts/with-dolt-admin-creds.sh \
  /data/projects/dolt-server/scripts/backup-restore.sh \
  --source-db '<DB>' \
  --target-db '<DB>_beads112_restore' \
  --verify
```

The revised helper must reject an existing target before issuing
`DOLT_BACKUP('restore', ...)`; that refusal is a required safety check, not
something to bypass. The S3 remote is shared and `backup-sync.sh` advances it,
so a successful restore proves the disaster-recovery mechanism but does not
freeze the exact production rollback point.

## Remaining outcome decomposition

The ledger, not this document, is the status authority. This is a prose-only
decomposition, and this plan-only change performs no filing or other ledger
mutation. The corrected factory-safety valve below governs every remaining
filing and the exact repairs to the already-filed O1 and O3 only after this
change receives exact-head supervisor review, passes all required checks, and
rebase-merges.

The identifiers `O1` through `O8` below mean “remaining outcome 1” through
“remaining outcome 8.” A dependency names the outcomes whose evidence must be
complete before the dependent outcome begins.

| Order | Remaining outcome | Depends on | Required result | Factory eligibility |
|---|---|---|---|---|
| O1 | Release and CLI qualification | None | Pin upstream provenance and prove the exact command, flag, and JSON surface against v1.1.2. | factory-safe; zero `factory-safety:*` labels |
| O2 | Guard compatibility | O1 | Run the existing hermetic guard suite against the qualified v1.1.2 binary and resolve only demonstrated incompatibilities. | factory-safe; zero `factory-safety:*` labels |
| O3 | Dolt restore source/target seam | None inside this repository; it is a prerequisite of O4 | In `dolt-server`, specify and implement distinct backup-source and clean scratch-target names, preserve the clean-target refusal, add hermetic tests, and correct stale examples; do not perform the live restore in O3. | factory-safe spec/code/test slice; zero `factory-safety:*` labels |
| O4 | Migration and restore rehearsal | O1, O2, O3 | After O3 closes, prove a real source-to-differently-named-scratch restore on the live server, restore each relevant tenant shape into isolation, migrate once, compare the complete invariant inventory, and prove the restore boundary. | manual/backlog; exactly `factory-safety:needs-privileged-host`, and cannot be admitted until the supervisor verifies O3 closed in the `dolt-server` tenant |
| O5 | Guarded image layout | O1, O2 | Put v1.1.2 at `bd-real`, install the tracked wrapper at `bd`, strengthen image verification, and resolve existing defect `bd-ib-dwv` with the successful guarded rebuild as evidence. | factory-safe code has zero `factory-safety:*` labels; a separate attended privileged DinD proof carries exactly `factory-safety:needs-privileged-host` |
| O6 | Current contract updates | O1, O2, O4, O5 | Update current version-specific comments, tests, runbooks, and permitted current specification facts under the narrow PR #1161 exception; historical records remain unchanged. | factory-safe within the reviewed path boundary; zero `factory-safety:*` labels |
| O7 | Attended host and tenant rollout | O3, O4, O5, O6 | Quiesce every writer, capture the rollback artifacts, directly replace `bd-real`, migrate once per tenant, and verify before restarting writers. | attended; exactly `factory-safety:mutates-host-machinery` |
| O8 | Closure and parity evidence | O7 and the acceptance evidence from O1 through O6 | Prove host/image parity, attach the complete audit trail, and close the upgrade only after `bd-ib-dwv` has been resolved by O5 rather than duplicated. | factory-safe evidence/closure has zero `factory-safety:*` labels; human acceptance remains a separate policy |

`bd-ib-dwv` is the one direct ledger overlap. O5 resolves that existing item;
this cut MUST NOT file a duplicate image-asset defect.

Two adjacent items constrain execution but are not adopted into this epic:

- `bd-ib-yig` records that a Beads subprocess can address the wrong tenant
  when its process working directory differs from the target repository.
  Cross-repository reads and any later authorized writes must run from the
  target repository root or use the proven `-C` anchor.
- `bd-ib-rxf` records the separate, write-only auto-backup failure caused by
  the tenant SQL user's missing `DOLT_BACKUP` grant. Read-only Beads probes do
  not demonstrate that auto-backup works. This upgrade continues to use the
  dedicated backup principal and server-native backup/restore contract; it
  does not adopt the grant defect.

Four live filing defects prohibit the current cross-repository and
epic-linkage `groom` path for this cut:

- `bd-ib-a8zi` and `bd-ib-dvmh` record the invalid local-prefix identifier
  minted for a cross-repository slice and the incomplete originating
  disposition record.
- `bd-ib-kn63nm` and `bd-ib-vari3j` record that the sanctioned writer maps
  epic linkage to a rejected `blocks` edge and can leave a created-but-unlinked
  row.

### Safe filing valve

This cut MUST NOT use `groom`, `append_work_item`, a pre-minted foreign
identifier, `--force`, any parent or epic-linkage write, or any cross-tenant
dependency write.

After this plan-only change has passed its review and merge valve, any
remaining local outcome among O2, O4, O5, O6, O7, and O8 is filed from this
repository root through the wrapper configured in `.livespec.jsonc` and
`/usr/local/bin/bd`. O1 already exists as `bd-ib-ne11`; do not file a
duplicate. A create command must omit an explicit identifier so Beads assigns
a standalone native `bd-ib` identifier. It MUST NOT pass `--parent`. Each
local outcome uses the exact `external_ref` value
`beads-v1-1-2-upgrade:O#`, with `O#` replaced by its recorded outcome number,
and its description names `bd-ib-3kolea` and that outcome as provenance. No
parent or epic linkage is created.

The first measured parent dry-run created no row, but it showed that normal
parent label inheritance would add `acceptance:human-only`,
`factory-safety:mutates-host-machinery`, and `origin:freeform` to the proposed
child labels. The corrective `--no-inherit-labels` dry-run also created no row,
returned the five labels then requested, and had null `parent_id` despite
`--parent bd-ib-3kolea`. The required parent proof therefore cannot pass,
which is why this cut files standalone items. A dry-run echoing a requested
label does not prove that the label value is valid under the WorkItem
contract; that distinction caused the factory-safety error recorded below.

Every local dry-run and create command MUST use `--no-inherit-labels`. It must
explicitly provide exactly one `admission:*` label, exactly one `acceptance:*`
label, `intake:triaged`, and the upgrade's `origin:*` label. Factory-safe work
MUST provide **zero** `factory-safety:*` labels. Genuinely attended host-only
work MUST provide exactly one allowed factory-safety reason as classified
below. Each approved creation is exactly one create command, followed
immediately by `bd show` read-back of the assigned identifier before any next
ledger write. The read-back must show the assigned native identifier, the
exact `external_ref`, null `parent_id`, the description provenance, exactly
one label under each of the `admission:` and `acceptance:` singleton prefixes,
the explicitly requested values, and the expected zero-or-one
`factory-safety:` cardinality. A missing, inherited, invalid, or contradictory
policy label halts the filing sequence.

#### Authoritative factory-safety classification and measured correction

Current `SPECIFICATION/contracts.md` under “Work-item beads-issue mapping” is
authoritative:

- An absent `factory-safety:*` label reads as null and means factory-safe.
- Any non-null `factory_safety` value is intrinsically host-only and is refused
  before a Fabro sandbox launches.
- The only allowed non-null reasons are `needs-host-secrets`,
  `mutates-host-machinery`, and `needs-privileged-host`.
- `pre-flight` is not a valid factory-safety value.

Therefore O1, O2, and O3's spec/code/hermetic-test slice carry zero
`factory-safety:*` labels. A genuinely attended slice carries exactly one of
the three allowed reasons. When an outcome mixes factory-safe code with an
attended proof, split those slices rather than making the code host-only.

The single supervised O1 dispatch attempt measured the consequence of the
filing error. `bd-ib-ne11` stayed `ready` at stage `host-only-refused`; it
produced no Fabro run, branch, worktree, or PR because
`factory-safety:pre-flight` was non-null. After this correction merges, remove
exactly that erroneous label from `bd-ib-ne11` and immediately read the item
back before one supervised retry. Do not set a workflow-scope override:
workflow citation scope cannot bypass intrinsic `factory_safety`.

Same-tenant dependency edges are added only through the native CLI after both
native endpoints exist. Each prerequisite edge uses direct `bd dep add`, is
read back immediately, and must leave `bd dep cycles` passing before another
dependency write occurs.

O3 uses this anchored command prefix:

`/usr/local/bin/with-livespec-env.sh -- /usr/local/bin/bd -C /data/projects/dolt-server`

Before its one create command, the supervisor must use that exact prefix for a
read-only target-tenant probe and verify that the result came from the
`dolt-server` tenant. O3 was filed as native target-tenant item
`dolt-server-wgy`, with no foreign identifier, cross-tenant parent, or
cross-tenant dependency edge. Its external reference records
`bd-ib-3kolea` and O3 provenance. Its current description incorrectly assigns
the live real-source-to-scratch restore proof to O3, and it carries the
erroneous `factory-safety:pre-flight` label. After this correction merges,
both require exact supervised repair and immediate read-back before spec-first
O3 work begins: the description must limit O3 to the specification, code,
hermetic tests, clean-target refusal, and stale examples, and it must carry
zero `factory-safety:*` labels. The attended live restore proof belongs to O4.

Cross-repository ordering is the linkage valve. O4 remains manual and
`backlog`; it is not admitted until the supervisor reads O3 from the
`dolt-server` tenant and verifies it is `closed`. Do not emulate the defective
sibling or dependency link across tenants.

Only outcomes whose recorded prerequisites are satisfied may be filed or
admitted. O1 and O3 are the initial independent candidates. O2 can follow O1;
the remaining outcomes follow the O1-through-O8 dependency order recorded in
the table.

Factory-safe slices carry no factory-safety label and should be driven through
the dark factory only after they are safely filed and admitted. The migration
rehearsal and production rollout must each carry exactly one applicable
allowed non-null reason and run attended.

## Execution sequence

### 1. Reconcile concurrent work

The relevant `fix-bd` PRs, releases, integration commits, and exact SHAs are
recorded in “Reconciled `fix-bd` scope and narrow PR #1161 path exception.”
Fetch and rebase every affected repository before implementation, repeat the
current-version and current-mise search, and preserve the lane's behavioral
ownership fence. Any O6 edit under the narrow exception requires an exact-diff
review for non-duplication.

Do not treat an old cache or pre-merge checkout as proof. For each claimed
absence, state the repositories, refs, globs, and historical exclusions
searched.

### 2. Freeze candidate provenance

Download `checksums.txt`, the Linux amd64 tarball, and the SPDX file from the
official v1.1.2 release. Verify the tarball against the published checksum
before extraction, derive and compare the extracted-binary hash, and record
`bd version`.

The Dockerfile must pin the exact release URL, tarball checksum, and derived
binary checksum. It must fail the build on any mismatch.

### 3. Qualify the CLI and guard in isolation

Use the candidate binary from a temporary, checksum-verified path; do not
install it on the host yet. Run the repository’s full client/argv/parser tests
and `just check`.

Add a candidate-real-binary leg to the guard harness. At minimum prove:

- all normal argv reaches the real binary unchanged;
- stdout, stderr, exit code, TTY, and signal behavior remain correct;
- list/show/comments/children JSON parses into the current WorkItem model;
- create output still yields the newly created identifier in normal, silent,
  and JSON forms;
- the follow-up lifecycle normalization updates only that identifier;
- tenant selectors remain excluded from the flag-less follow-up;
- batch, event, ephemeral, dry-run, help, and future `--status` cases retain
  their intended behavior;
- guard warning/fail modes and OTLP emission remain fail-open where specified;
  and
- `bd create --help` still lacks a usable create-time status control. If this
  changes, redesign the normalizer rather than carrying a stale two-step.

### 4. Rehearse migration and restoration

First run both commands in “Authoritative tenant and recovery surfaces” and
reconcile the live registry with the committed family pointers. For each
tenant in the resulting intersection, capture counts and stable hashes or
normalized exports for:

- issues grouped by lifecycle status and issue type;
- dependency edges;
- comments;
- labels and metadata needed by the WorkItem adapter;
- intake-triage, policy, and factory-safety labels; and
- schema migration rows and their content hashes.

Create the export root once, refusing to reuse an existing cutover timestamp:

```sh
set -euo pipefail
cutover_utc='<CUTOVER_UTC>'
export_root="/var/backups/livespec-beads-v1.1.2-pre-$cutover_utc"
operator_user="$(id -un)"
operator_group="$(id -gn)"
sudo test ! -e "$export_root"
sudo install -d -o "$operator_user" -g "$operator_group" -m 0700 \
  "$export_root/exports"
```

For each tenant, create a logical `bd export --all` interoperability artifact
through the currently guarded v1.0.5 CLI from the repository that owns that
tenant:

```sh
set -euo pipefail
cutover_utc='<CUTOVER_UTC>'
export_root="/var/backups/livespec-beads-v1.1.2-pre-$cutover_utc"
repo='<REPO>'
database='<DB>'
export_path="$export_root/exports/$database.jsonl"
test ! -e "$export_path"
/data/projects/1password-env-wrapper/with-livespec-env.sh -- \
  /usr/local/bin/bd -C "$repo" export --all -o "$export_path"
jq -c . "$export_path" >/dev/null
sha256sum "$export_path"
wc -l "$export_path"
```

Record the checksum and line count. This JSONL captures issue
interoperability data; it is not a full database backup and cannot restore
schema, branches, or the complete working set.

Also run a fresh `backup-sync.sh --db <DB>` server-native sync. After the
required source/target helper slice lands, restore that source into
`<DB>_beads112_restore` on the live server with the exact command in
“Authoritative tenant and recovery surfaces.” Run the baseline inventory
against the scratch tenant, then remove it only through the reviewed
`dolt-server` cleanup path. Do not follow the stale `<DB>_restoretest`
examples until that source/target correction has landed. This is O4's
attended `needs-privileged-host` proof, not part of factory-safe O3.

Establish how v1.1.2 classifies the family’s shared SQL-server topology. Assign
one migrator for the isolated tenant, run the migration once, and record
whether the remote-migration gate requires `BD_ALLOW_REMOTE_MIGRATE=1`. Use
that escape hatch only if the observed gate requires it and the isolated proof
shows the expected migration path.

After migration, run read/write round trips for issue creation, lifecycle
update, dependency creation, comment creation, close, list, and show. Compare
the full invariant inventory. Re-run the source-to-scratch restore and prove
that the pre-migration server-native backup still returns to the baseline.
This rehearses S3 disaster recovery; the stopped-server cold snapshot in step
7 is the frozen rollback artifact for the attended cutover.

### 5. Implement the guarded container layout

The intended Dockerfile flow is:

1. download and verify the v1.1.2 tarball;
2. extract and verify the real binary;
3. `install -m 0755 /tmp/bd /usr/local/bin/bd-real`;
4. stage the repository’s tracked `bd-guard/` payload into the image build
   context;
5. install `bd-guard.sh` as `/usr/local/bin/bd` and the emitter beside it;
6. seed the non-secret guard mode intentionally;
7. keep `ENV LIVESPEC_BD_PATH=/usr/local/bin/bd`; and
8. verify the sentinel, both file hashes, wrapper passthrough version, and real
   version during the build.

`build-and-verify.sh` must cleanly stage and clean the guard payload just as it
does other build-context artifacts. Tier 1 must continue using only an
ephemeral in-container tenant. Extend it to assert:

- `/usr/local/bin/bd` contains the guard sentinel;
- `/usr/local/bin/bd-real` has the pinned binary hash;
- both version paths report v1.1.2;
- `LIVESPEC_BD_PATH` points to the wrapper;
- a prohibited lifecycle mutation is observed or blocked according to the
  configured mode; and
- a qualifying create lands in the Livespec lifecycle status expected by the
  guard.

### 6. Update current contracts

Re-run a whole-workspace search after `fix-bd` merges. Update only current
authoritative references whose truth changes, including this repository’s
current specification, runtime comments/types, client compatibility tests,
guard documentation, Dockerfile, build verification, and image README.

The narrow PR #1161 exception limits this instruction. O6 may surgically
update a current, version-specific v1.0.5-to-v1.1.2 fact in a current
specification path changed by PR #1161 only when the upgrade requires it and
the exact diff is reviewed for non-duplication. It must not reimplement or
restate guarded-entrypoint, no-mise, or private-delegate behavior. Frozen
history remains no-touch, and `.mise.toml` and `AGENTS.md` remain no-touch
absent a separate reviewed demonstrated requirement.

Historical specification snapshots, archived plans, and changelog entries
remain unchanged. A comment that describes version-specific JSON or flags may
be updated only after a behavior test proves the new statement.

If a current specification heading changes, update
`tests/heading-coverage.json` in the same revise operation.

### 7. Perform the attended production cutover

Schedule a maintenance window after every preceding slice is green. Execute
the server-wide writer census above, stop every writer and its restart
mechanism, and require the process-list query to return zero rows. Take fresh
logical exports and server-native backup syncs and record their paths, hashes,
line counts, and restore commands.

Next freeze the rollback point for the whole shared server. First prove the
backup filesystem has more than twice the measured data-directory bytes free:
the first copy is the archive and the second is the isolated extraction
rehearsal. Stop the recurring backup timer and any in-progress backup unit,
stop Dolt, and create a cold archive of the entire data directory, including
`.doltcfg`, while the server is down. This block is a single fail-closed shell;
replace `<CUTOVER_UTC>` once with the previously recorded timestamp:

```sh
set -euo pipefail
cutover_utc='<CUTOVER_UTC>'
snapshot_root="/var/backups/doltdb/beads-v1.1.2-pre-$cutover_utc"
restore_rehearsal_root="${snapshot_root}.restore-rehearsal"
data_bytes="$(sudo du -sb /var/lib/doltdb/databases | awk '{print $1}')"
backup_free_bytes="$(df -B1 --output=avail /var/backups | awk 'NR == 2 {print $1}')"
required_free_bytes="$((data_bytes * 2))"
printf 'data_bytes=%s backup_free_bytes=%s required_free_bytes=%s\n' \
  "$data_bytes" "$backup_free_bytes" "$required_free_bytes"
test "$backup_free_bytes" -gt "$required_free_bytes"
sudo test ! -e "$snapshot_root"
sudo test ! -e "$restore_rehearsal_root"
sudo systemctl stop dolt-backup.timer dolt-backup.service
sudo systemctl stop doltdb.service
sudo install -d -o root -g root -m 0700 "$snapshot_root"
sudo tar --acls --xattrs --numeric-owner --sparse -cpf \
  "$snapshot_root/databases.tar" \
  -C /var/lib/doltdb databases
sudo sha256sum "$snapshot_root/databases.tar" |
  sudo tee "$snapshot_root/databases.tar.sha256" >/dev/null
sudo sha256sum -c "$snapshot_root/databases.tar.sha256"
sudo chmod 0400 \
  "$snapshot_root/databases.tar" \
  "$snapshot_root/databases.tar.sha256"
sudo install -d -o root -g root -m 0700 "$restore_rehearsal_root"
sudo tar --acls --xattrs --numeric-owner --sparse -xpf \
  "$snapshot_root/databases.tar" \
  -C "$restore_rehearsal_root"
sudo rsync -aHAXnc --delete --numeric-ids --itemize-changes \
  /var/lib/doltdb/databases/ \
  "$restore_rehearsal_root/databases/" |
  sudo tee "$snapshot_root/restore-rehearsal.rsync-dry-run.txt" >/dev/null
sudo test ! -s "$snapshot_root/restore-rehearsal.rsync-dry-run.txt"
sudo chmod 0400 "$snapshot_root/restore-rehearsal.rsync-dry-run.txt"
sudo systemctl start doltdb.service
```

The preflight byte count, filesystem capacity, archive checksum, and successful
checksum verification must be recorded. The isolated extraction uses the same
archive and extraction flags as rollback, and the metadata-preserving `rsync`
dry run must emit an empty file. Retain both the root-owned archive and isolated
extraction until the maintenance window closes; never overwrite either. Keep
`dolt-backup.timer` stopped until the forward rollout or rollback has passed
its baseline checks. Because the cold archive contains the whole server,
post-migration rollback is a single attended, all-tenant rollback; it is not a
per-tenant selective restore.

Stage the candidate from the already verified official tarball. Preserve an
exact, hash-qualified copy of the v1.0.5 real binary:

```sh
set -euo pipefail
sudo test ! -e \
  /usr/local/bin/bd-real.v1.0.5.463b7655041345ce.bak
sudo install -o root -g root -m 0555 \
  /usr/local/bin/bd-real \
  /usr/local/bin/bd-real.v1.0.5.463b7655041345ce.bak
printf '%s  %s\n' \
  '463b7655041345ce5d4bac00c3a5d465166bb30166147e11ef1c6e07df0a4486' \
  '/usr/local/bin/bd-real.v1.0.5.463b7655041345ce.bak' |
  sudo sha256sum -c -
```

The intended host mutation is a direct manual copy to the real target, never a
mise operation:

```sh
set -euo pipefail
grep -q 'bd-guard-wrapper-sentinel' /usr/local/bin/bd
guard_sha256="$(sha256sum /usr/local/bin/bd | awk '{print $1}')"
sudo test ! -e /usr/local/bin/bd-real.new
sudo install -m 0755 /path/to/verified/bd-1.1.2 /usr/local/bin/bd-real.new
printf '%s  %s\n' \
  '6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82' \
  '/usr/local/bin/bd-real.new' |
  sudo sha256sum -c -
sudo mv /usr/local/bin/bd-real.new /usr/local/bin/bd-real
grep -q 'bd-guard-wrapper-sentinel' /usr/local/bin/bd
test "$(sha256sum /usr/local/bin/bd | awk '{print $1}')" = "$guard_sha256"
/usr/local/bin/bd-real version
/usr/local/bin/bd version
```

Before and after the move, assert that `/usr/local/bin/bd` still contains the
guard sentinel and its expected tracked bytes. Then prove:

```sh
/usr/local/bin/bd-real version
/usr/local/bin/bd version
```

With writers still stopped and the backup timer still disabled, migrate each
production tenant exactly once using the topology-specific command proven in
rehearsal. Run the invariant and round-trip checks, restart writers in a
controlled order, and watch guard, dispatcher, Dolt, and error telemetry.
Only after those checks pass, restart `dolt-backup.timer` and declare the
window complete.

### 8. Roll back only at the proven boundary

Before any schema migration, reverting the real binary to the saved v1.0.5
file is sufficient:

```sh
set -euo pipefail
printf '%s  %s\n' \
  '463b7655041345ce5d4bac00c3a5d465166bb30166147e11ef1c6e07df0a4486' \
  '/usr/local/bin/bd-real.v1.0.5.463b7655041345ce.bak' |
  sudo sha256sum -c -
sudo test ! -e /usr/local/bin/bd-real.new
sudo install -m 0755 \
  /usr/local/bin/bd-real.v1.0.5.463b7655041345ce.bak \
  /usr/local/bin/bd-real.new
sudo mv /usr/local/bin/bd-real.new /usr/local/bin/bd-real
grep -q 'bd-guard-wrapper-sentinel' /usr/local/bin/bd
/usr/local/bin/bd-real version
```

After a tenant has crossed migrations 0050 through 0053, do not point v1.0.5
at that database. Keep writers stopped and restore the complete stopped-server
snapshot and the saved v1.0.5 binary:

```sh
set -euo pipefail
cutover_utc='<CUTOVER_UTC>'
rollback_tag='<ROLLBACK_UTC>'
snapshot_root="/var/backups/doltdb/beads-v1.1.2-pre-$cutover_utc"
failed_data_dir="/var/lib/doltdb/databases.failed-$rollback_tag"
sudo test -r "$snapshot_root/databases.tar"
sudo test -r "$snapshot_root/databases.tar.sha256"
sudo test ! -e "$failed_data_dir"
sudo test ! -e /usr/local/bin/bd-real.new
sudo systemctl stop dolt-backup.timer dolt-backup.service
sudo systemctl stop doltdb.service
sudo sha256sum -c "$snapshot_root/databases.tar.sha256"
sudo mv /var/lib/doltdb/databases "$failed_data_dir"
sudo tar --acls --xattrs --numeric-owner --sparse -xpf \
  "$snapshot_root/databases.tar" \
  -C /var/lib/doltdb
sudo test -d /var/lib/doltdb/databases/.doltcfg
printf '%s  %s\n' \
  '463b7655041345ce5d4bac00c3a5d465166bb30166147e11ef1c6e07df0a4486' \
  '/usr/local/bin/bd-real.v1.0.5.463b7655041345ce.bak' |
  sudo sha256sum -c -
sudo install -m 0755 \
  /usr/local/bin/bd-real.v1.0.5.463b7655041345ce.bak \
  /usr/local/bin/bd-real.new
sudo mv /usr/local/bin/bd-real.new /usr/local/bin/bd-real
printf '%s  %s\n' \
  '463b7655041345ce5d4bac00c3a5d465166bb30166147e11ef1c6e07df0a4486' \
  '/usr/local/bin/bd-real' |
  sudo sha256sum -c -
grep -q 'bd-guard-wrapper-sentinel' /usr/local/bin/bd
sudo systemctl start doltdb.service
```

The moved `databases.failed-<UTC>` directory is deliberately retained for
forensics; this procedure deletes nothing. With writers still stopped, prove
the guard sentinel, v1.0.5 version, tenant registry, schema rows, and the full
baseline inventory. Restart writers in a controlled order and restart
`dolt-backup.timer` only after those checks pass.

The guard wrapper remains installed throughout both forward and rollback
paths. Do not use `bd-guard/rollback.sh` as part of this version rollback,
because that would remove the required guard and move `bd-real` onto `bd`.

## Validation matrix

| Layer | Required proof |
|---|---|
| Supply chain | official stable tag, live asset, upstream tarball hash, derived binary hash, version output, SPDX retained |
| Host layout | wrapper sentinel/hash unchanged; real binary hash/version changed to v1.1.2; no direct callers of `bd-real` |
| CLI adapter | complete focused tests plus `just check`; exact argv and JSON fixtures qualified against candidate |
| Guard | full hermetic harness against stub and candidate; create normalization and selector safety proven |
| Database | isolated migrate and restore; pre/post counts, edges, comments, statuses, labels, metadata, and schema hashes match expectations |
| Concurrency | all writers enumerated and stopped; one migrator per tenant; writers restarted only after checks |
| Container | pinned guarded layout; build succeeds; Tier 1 uses only ephemeral data and proves lifecycle normalization |
| Fleet | host/image version and hashes agree; current non-historical references agree; no Beads installation via mise |
| Delivery | worktree-only commits, required hooks, `git diff --name-only` ownership check, reviewed PRs, rebase merges, clean primary checkouts |

## Immediate next action

Resume only the exact-head review hold for PR #1284 at
`bbda528d096ea28b475c2d7e66530ae3fc987826`. Verify it remains open and
unmerged with auto-merge disabled and all 95 checks terminal. GitHub currently
reports `DIRTY` because the restart checkpoint advanced master beyond the
PR's original base. Wait for the supervisor's explicit rebase/merge decision.
Do not edit, rebase, or merge the PR, return to PR #1221, rerun the proof,
begin another outcome, or touch another session's state.
