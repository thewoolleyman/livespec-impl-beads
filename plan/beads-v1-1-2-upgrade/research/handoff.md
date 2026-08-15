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

## Plan label key

The labels `O1` through `O8` belong to this Beads v1.1.2 upgrade plan. They
mean, respectively: release and command-line qualification (`O1`), guard
compatibility (`O2`), the distinct backup-source and clean-target restore seam
(`O3`), the isolated migration-and-restore rehearsal (`O4`), the guarded image
layout (`O5`), version-specific current-code and documentation alignment
(`O6`), the attended production cutover (`O7`), and closure with parity
evidence (`O8`). The labels `B5` and `B8` belong to the archived
`governed-repo-bootstrap` plan; they mean its attended-restore acceptance and
audit-acceptance outcomes. Later tables retain these short labels only after
this owning-plan and descriptive-outcome definition.

## Current state

### Authoritative restart checkpoint — 2026-08-11 external factory-capacity blocker

This is the sole authoritative restart checkpoint. It supersedes every lower
restart checkpoint and every earlier version of “Immediate next action.” The
O4 filing contract and recovery are complete, but the factory-safe preparation
item has not produced a Fabro run or implementation. Read the newest
append-only supervisor marker at
`/data/projects/livespec-orchestrator-beads-fabro/tmp/overseer/beads-v1-1-2-upgrade/.supervisor-state`
in full. Its latest entry leaves obligation
`wait_for_factory_oauth_capacity_bd_ib_8azd` in
`blocked-external-capacity`, held by the supervisor and handed to the
maintainer. Its only wake mechanisms are maintainer capacity remediation or a
later explicitly requested bounded `claude-cred-status` probe. A generic plan
resume does not authorize that probe, another submission, or any mutation.

Read-only remeasurement at `MEASURED_AT=2026-08-11T06:23:42Z` established:

- The clean primary checkout, fetched `origin/master`, and public forge master
  are equal at `18fd82ffa37ed68a4d13effc1d933245041e043f`.
- Factory-safe O4 preparation task `bd-ib-8azd` remains P2, `ready`,
  unassigned, and standalone with `admission:auto`, `acceptance:ai-only`,
  `intake:triaged`, `origin:beads-v1-1-2-upgrade`, zero
  `factory-safety:*` labels, zero prerequisites, and exactly one dependent.
  Attended O4 rehearsal task `bd-ib-ao3j` remains P2, `backlog`, unassigned,
  and standalone with its sole `blocks` prerequisite pointing to
  `bd-ib-8azd`. It remains manual and unauthorized.
- `fabro ps -a --json` listed 563 historical and current runs and contained
  zero match for `bd-ib-8azd`. The exact dispatch lock
  `tmp/fabro-dispatch-bd-ib-8azd.lock` is absent, and the forge has zero
  matching remote branches and zero matching open or merged pull requests.
- The three currently listed unrelated Fabro runs were preserved:
  `01KZQJFMFZXVS4TXSBYZ8TV0ZC` for `bd-ib-mrqoy2.3` and
  `01KZQGC1QXADJVZYEQ7FRW243T` for `bd-ib-mrqoy2.8` were blocked, while
  livespec-dev-tooling run `01KZ2P36KXCK4P7JFFG696Q6V1` remained runnable.
  Their state may change independently; never alter them from this plan.

No ledger, dispatch, credential, Fabro, product, fixture, server, migration,
backup, restore, cleanup, image, host, tenant, Dolt-data, secret, or rollout
mutation occurred during this reconciliation. Stop and report the external
capacity blocker. Do not probe capacity or retry until a new durable supervisor
obligation explicitly authorizes the bounded action after its wake condition.

### Restart checkpoint — 2026-08-07 O4 create-boundary correction

This historical checkpoint is retained as execution evidence. At that time,
the only action was exact-head supervisor review of the one-file plan PR
that corrects the dry-run and real-create boundary for the two-row O4 filing
contract below. This checkpoint does not authorize a ledger dry run or write,
factory dispatch, fixture write, migration, backup, restore, cleanup, image
operation, host copy, or rollout.

- A fresh fetch at `MEASURED_AT=2026-08-06T10:41:06Z` found this repository's
  clean primary checkout, `origin/master`, and public forge master equal at
  `1a993d2d54c4fc44389948a62a306a655331b80a`. The release forge still peels
  upstream Beads tag `v1.1.2` to
  `20e493e569c922d1253bdeff068c5e56c94957fb`; the official Linux AMD64 tarball
  has SHA-256
  `a72d71ed374955dc9f83a0f90b54bd7b6a0016709dd1676ae2e368651ed401c2`,
  the extracted executable has SHA-256
  `6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82`,
  and the SPDX artifact has SHA-256
  `b05ca7f525f05e50691a4329b13aa87f10bc93160fe8d4d1ca371867701b58e6`.
- Upstream tag `v1.0.5` still peels to
  `6a3f515ced18406c189c55fff789a4925bfaa35c`. Its release API and expected
  Linux AMD64 asset both return HTTP 404, so the future fixture producer must
  be built from that exact source commit with its declared Go 1.26.2 toolchain;
  the build receipt must record the source archive, toolchain, command, and
  resulting executable hashes. It must not substitute the host's private
  delegate.
- Read-only calls through the family wrapper and public guarded `bd` surveyed
  all nine committed family tenant pointers. The representative evidence
  sources are `/data/projects/livespec` for the dense lifecycle and policy
  shape (625 all-row issues, 132 issues with dependencies, 123 with comments,
  479 with metadata, and 88 distinct label values), this repository for the
  factory-policy shape (447 all-row issues, 56 with dependencies, 108 with
  comments, 233 with metadata, and 55 distinct label values), and
  `/data/projects/livespec-driver-codex` for the sparse closed-only shape (25
  closed issues, two with dependencies, three with comments, 13 with metadata,
  and seven distinct label values). These are read-only shape sources, not
  databases to copy or mutate.
- The all-row, infrastructure-inclusive survey found zero `rig` issue rows in
  every family tenant. The 0053 rig/wisp case therefore requires a deterministic
  synthetic v1.0.5 fixture derived from the tagged upstream schema and migration
  tests. The plan must not claim that a production-derived fixture covers a
  shape the read-only evidence did not observe.
- The non-closed target-tenant survey found only upgrade anchor `bd-ib-3kolea`
  and adjacent auto-backup defect `bd-ib-rxf` in the migration/restore defect
  class. The latter confirms that tenant-user writes cannot be trusted to make
  server-native backups because that user lacks `DOLT_BACKUP`; the rehearsal
  must use a dedicated isolated backup principal and must not repair or bypass
  that grant boundary. No ledger state was changed.

The archived live helper receipt remains credited without repetition. It
restored real source `livespec-orch-beads-fabro` into differently named clean
target `livespec-orch-beads-fabro_beads112_restore`, compared the ordered branch
list and every base-table row count, and obtained the same SHA-256 before,
during, and after the restore:
`5f73c196716ee022ebe779cf366a5f897ab1e20b290d859e7c5b116076b4b3f6`.
Its reviewed cleanup returned the live tenant count to 13. The unreproducible
older digest beginning `37dfd588` remains retired. This receipt completes this
upgrade plan's distinct backup-source and clean-target restore seam (`O3`) and
the archived governed plan's attended-restore and audit-acceptance outcomes
(`B5` and `B8`); it does not complete this upgrade plan's isolated migration
and restore rehearsal (`O4`).

The residual `O4` package below is now concrete: it uses only synthetic
v1.0.5-created non-production tenants, one designated migrator, an observed
remote-gate decision, exact invariant inventories, write round trips, a frozen
single-use pre-migration backup identity, restore to the complete baseline,
and exact cleanup receipts. Version-specific current-code and documentation
alignment (`O6`) remains blocked on accepted `O4` evidence, and the attended
production cutover (`O7`) remains unauthorized.

### Restart checkpoint — 2026-08-04 O5 proof accepted and closed

This historical checkpoint is retained as execution evidence. The
older checkpoints remain below only as historical execution evidence; none of
their instructions is executable now. Do not return to PR #1221, repeat the
guarded-image proof, or begin another upgrade outcome.

- At `MEASURED_AT=2026-08-04T05:24:13Z`, after a fresh fetch, this repository's
  clean primary checkout, fetched `origin/master`, and GitHub forge master were
  equal at `73aece7ec4034ec8da0a8eb5ea1cbed97329f562`. Target-anchored reads through
  `/data/projects/1password-env-wrapper/with-livespec-env.sh -- /usr/local/bin/bd -C /data/projects/livespec-orchestrator-beads-fabro`
  confirmed plan anchor `bd-ib-3kolea` was `backlog`, unassigned, type `epic`,
  and owned by `chad@thewoolleyman.com`; `bd-ib-dwv` was `closed`, unassigned,
  with `closed_at=2026-08-04T02:32:41Z`.
- The attended guarded-image proof for existing canonical defect
  `bd-ib-dwv` ran exactly once from source
  `b9c8904b5ad41de94eb636b3e509a027e48047a0` and produced exactly one terminal
  `ALL TIER-1 CHECKS PASSED (driver=overlayfs, web-ui=HTTP 308)` receipt. The
  supervisor independently accepted the pinned tarball and `bd-real` hashes,
  wrapper/real v1.1.2 outputs, failure-fatal lifecycle assertions, inner Dolt,
  secret-value scan, HTTP probe, cleanup, unchanged host hashes, and every
  no-mutation fence.
- The accepted proof log has SHA-256
  `53eee1e2b25fb720a7ef59d5ae483af09b6cd0e32f831325c4886b4cc57db717`.
  Through the configured family wrapper and public `/usr/local/bin/bd`, the
  existing `bd-ib-dwv` item was closed exactly once at
  `2026-08-04T02:32:41Z` with that accepted proof evidence. A fresh read-back
  confirmed `closed`, unassigned, with its sole `blocks` prerequisite
  `bd-ib-1rz6` also `closed`. There was no partial write or auto-backup warning.
- O5 is terminal. The proof must not be rerun, no Docker resource may be
  recreated, and no further attended action is authorized. No successor may
  mutate the image, registry, host `/usr/local/bin`, production tenant or Dolt
  data, backup/restore state, host Fabro server, or another ledger item under
  this checkpoint.
- The immediate remaining blocker is external to this repository and is owned
  by the separate `governed-repo-bootstrap` plan: its Dolt-server
  default-branch `ci-green` evidence has not yet published. Public remeasurement
  found the Dolt-server GitHub forge master at
  `fd7d79e97ba6bdcc169a8868df0d9d73bbfc9aaa`. The only valid cross-repository
  ledger measurement is `MEASURED_AT=2026-08-04T05:03:45Z`, taken with the
  exact target anchor
  `/usr/local/bin/with-livespec-env.sh -- /usr/local/bin/bd -C /data/projects/dolt-server`.
  It explicitly verified `dolt-server-3jhclo`, its two required `blocks`
  endpoints `dolt-server-22gb7i` and `dolt-server-s4iyi4`, and canonical O3
  item `dolt-server-wgy`. The first three were `pending-approval`;
  `dolt-server-wgy` was `ready` and unassigned.
- Do not inspect or touch the separate `governed-repo-bootstrap` plan's
  supervisor, worker, markers, logs, worktrees, or branches.
- Only after the external default-branch `ci-green` evidence publishes may
  this plan independently remeasure the public Dolt-server forge and ledger
  artifacts, with every ledger read using the exact target anchor above. If
  the existing valves then pass and `dolt-server-wgy` remains canonical and
  `ready`, the only permitted next execution is the sanctioned dark-factory
  `drive` action `impl:dolt-server-wgy` from the Dolt-server repository root.
  No duplicate O3 item, cross-tenant edge, inline implementation, or other
  O1-through-O8 outcome is authorized.

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
  or unrelated process/session was touched. After supervisor acceptance,
  `bd-ib-dwv` was closed exactly once at `2026-08-04T02:32:41Z`; no other
  ledger item was mutated. The ignored runtime terminal receipt is in
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

The former single-`--db` source/target defect is closed. Dolt-server PR #46
added distinct `--source-db` and `--target-db` arguments while preserving the
clean-target refusal, and the archived governed plan later exercised that seam
on the live server. The exact archived receipt is in the newest checkpoint.
Do not reopen or dispatch the completed seam, do not repeat the attended live
restore, and do not advance the shared production S3 backup merely to create a
new receipt. The residual rehearsal below uses a separate single-use
non-production backup namespace and never points the tracked helper at the
production server, bucket, DynamoDB manifest table, or tenant registry.

The exact on-demand snapshot form for one production tenant is:

```sh
OPENV_KEEP_PRIVILEGES=1 sudo -E /usr/local/bin/with-dolt-admin-env.sh \
  /data/projects/dolt-server/scripts/with-dolt-admin-creds.sh \
  /data/projects/dolt-server/scripts/backup-sync.sh --db '<DB>'
```

The following live-server form is retained only as historical syntax for the
already-credited receipt; it is not an executable step in the residual
rehearsal:

```sh
OPENV_KEEP_PRIVILEGES=1 sudo -E /usr/local/bin/with-dolt-admin-env.sh \
  /data/projects/dolt-server/scripts/with-dolt-admin-creds.sh \
  /data/projects/dolt-server/scripts/backup-restore.sh \
  --source-db '<DB>' \
  --target-db '<DB>_beads112_restore' \
  --verify
```

The helper must reject an existing target before issuing
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
| O4 | Migration and restore rehearsal | O1, O2, O3 | Consume the archived live helper receipt without rerunning it; create the three synthetic v1.0.5 shapes on a dedicated non-production server, migrate them through 0050–0053 with one designated migrator, compare the exact invariant and round-trip inventories, and restore the frozen pre-migration backup into clean targets that match the complete baseline. | manual/backlog; exactly `factory-safety:needs-privileged-host`; preparation code may be factory-safe, but every fixture write, server action, migration, backup, restore, and cleanup remains attended |
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

After this plan-only correction has passed its review and merge valve, a new
durable filing obligation must separately authorize any remaining local outcome
among O2, O4, O5, O6, O7, and O8. Each authorized filing runs from this
repository root through the wrapper configured in `.livespec.jsonc` and
`/usr/local/bin/bd`. O1 already exists as `bd-ib-ne11`; do not file a duplicate.
A create command must omit an explicit identifier so Beads assigns a standalone
native `bd-ib` identifier. It MUST NOT pass `--parent`. Each local outcome uses
the exact `external_ref` value
`beads-v1-1-2-upgrade:O#`, with `O#` replaced by its recorded outcome number,
and its description names `bd-ib-3kolea` and that outcome as provenance. No
parent or epic linkage is created.

#### O4 two-row filing contract

The attended residual migration-and-restore rehearsal retains the exact
`external_ref` `beads-v1-1-2-upgrade:O4`. The separate factory-safe preparation
slice uses the exact plan-authorized exception
`beads-v1-1-2-upgrade:O4-preparation`. The preparation row is a slice of this
plan's O4 isolated migration-and-restore rehearsal, not a new numbered outcome.
Before any later dry run or create, the complete ledger must be collision-checked
for both exact external references and both exact titles below.

Both future rows are standalone native `bd-ib` tasks at priority 2 with stored
null `parent_id`. Beads assigns each identifier: neither create supplies an
explicit ID or `--parent`, and neither uses inheritance, `groom`,
`append_work_item`, `--force`, an epic link, or a cross-tenant link. Each future
create uses `--no-inherit-labels`.

Every dry-run and real create for these two rows must execute from the exact
repository root `/data/projects/livespec-orchestrator-beads-fabro`. The operator
must first change to that directory, then invoke the exact configured
wrapper-and-public-guard prefix with no tenant selector:

```sh
cd /data/projects/livespec-orchestrator-beads-fabro
/data/projects/1password-env-wrapper/with-livespec-env.sh -- \
  /usr/local/bin/bd create <exact-row-arguments>
```

Here `<exact-row-arguments>` means the exact title, description, external
reference, task type, priority, labels, and `--no-inherit-labels` defined below,
plus `--dry-run --json` only for a preview. It never includes `-C`,
`--directory`, `--db`, `--global`, `--repo`, or any other tenant selector, and
it never includes an explicit ID, `--parent`, or `--force`. This ban is specific
to these create commands; the exact target-anchored `-C` forms remain permitted
for read-only and dependency commands below.

A v1.0.5 `create --dry-run --json` result is native planning output, not the
stored post-create state. It must echo the exact requested title, description,
external reference, task type, priority, and labels. It is expected to report
native `status: open`, an empty ID, and may omit `parent_id` when no parent was
supplied. The preview cannot prove the eventual native identifier, normalized
Livespec lifecycle status, or stored null parent.

A later real create omits `--dry-run`; from the established target-root working
directory and without a tenant selector, it qualifies for the public guard's
post-create `backlog` normalization. The create output is not final-state proof.
Before any next ledger write, the assigned identifier must be read back either
through the same wrapper and public guard from that already-established working
directory without a selector, or through their exact read-only target anchor
`-C /data/projects/livespec-orchestrator-beads-fabro`. That
immediate read-back must prove the native `bd-ib` ID, task type, priority 2,
exact Livespec status `backlog`, stored null `parent_id`, exact external
reference, exact title, exact description, and exact labels.

The guard's post-create normalization is fail-open, so this immediate read-back
is mandatory. Any non-`backlog` status, non-null stored parent, or other field
mismatch halts before another ledger write and is reported for a separate
corrective obligation. Do not silently normalize, delete, retry, or continue.

The preparation row is defined exactly as follows:

- Title: `Prepare the synthetic isolated Beads v1.1.2 migration-and-restore rehearsal package`.
- External reference: `beads-v1-1-2-upgrade:O4-preparation`.
- Labels, with zero `factory-safety:*` labels:
  `acceptance:ai-only`, `admission:auto`, `intake:triaged`, and
  `origin:beads-v1-1-2-upgrade`.
- Description:

  > Provenance: `bd-ib-3kolea`, O4 preparation. This factory-safe slice of O4
  > owns only the factory-safe preparation already bounded by this merged
  > package: reviewed provenance and topology manifests, including public
  > upstream artifact fetch/hash and v1.0.5 fixture-producer build receipts;
  > deterministic fixture definitions; canonical inventory queries; command and
  > credential-and-anchor wrappers; receipt schemas; the version-neutral
  > identity-probe implementation and locked dependencies; and hermetic tests.
  > It does not perform the rehearsal. It forbids every server start, tenant or
  > database write, migration, backup, restore, cleanup, image action, host
  > `/usr/local/bin` mutation, production mutation or write-capable production
  > probe, secret disclosure or mutation, and Fabro or Fabro-server mutation.
  > Its only production-facing activity is the exact read-only deterministic
  > fixture-shape survey from `/data/projects/livespec`, this repository, and
  > `/data/projects/livespec-driver-codex`, run from each target root through its
  > configured wrapper and public `/usr/local/bin/bd` as applicable.

The attended row is defined exactly as follows:

- Title: `Run the attended residual isolated Beads v1.1.2 migration-and-restore rehearsal`.
- External reference: `beads-v1-1-2-upgrade:O4`.
- Labels: `acceptance:ai-only`, `admission:manual`, `intake:triaged`,
  `origin:beads-v1-1-2-upgrade`, and
  `factory-safety:needs-privileged-host`.
- Description:

  > Provenance: `bd-ib-3kolea`, O4. Consume only the reviewed and merged O4
  > preparation package. In an attended foreground window, own the isolated
  > non-production three-shape fixture, server, migration, single-use backup,
  > clean-target restore-to-complete-baseline, and cleanup proof defined by this
  > package, including its invariant, round-trip, remote, pointer, identity,
  > stop-boundary, and receipt evidence. Preserve the already-credited live
  > distinct-source and clean-target helper receipt without rerunning it. Keep
  > this item in backlog under manual admission. It forbids production tenant or
  > data mutation, host `/usr/local/bin` mutation, every image action, secret
  > disclosure or mutation, and Fabro-server mutation. Its production-facing
  > activity is limited to the read-only unchanged-state probes required by the
  > package's preflight and cleanup receipts.

Only after both native rows exist and each has passed its immediate read-back
may a later authorized writer add their same-tenant prerequisite edge. Here
`<attended-id>` means the native ID read back for the attended row, and
`<preparation-id>` means the native ID read back for the preparation row. The
only permitted direction and verification sequence is:

```sh
/data/projects/1password-env-wrapper/with-livespec-env.sh -- \
  /usr/local/bin/bd -C /data/projects/livespec-orchestrator-beads-fabro \
  dep add <attended-id> <preparation-id> --type blocks
/data/projects/1password-env-wrapper/with-livespec-env.sh -- \
  /usr/local/bin/bd -C /data/projects/livespec-orchestrator-beads-fabro \
  show <attended-id> --json
/data/projects/1password-env-wrapper/with-livespec-env.sh -- \
  /usr/local/bin/bd -C /data/projects/livespec-orchestrator-beads-fabro \
  dep cycles
```

The edge read-back must prove that the attended row depends on the preparation
row, and `bd dep cycles` must pass before any next ledger write. The attended
row must not be admitted until the preparation row and target-tenant
`dolt-server-wgy` have each been independently verified closed. Do not create a
parent, sibling, dependency, or any other cross-tenant edge to
`dolt-server-wgy`; its closure is an independently read precondition only.

This plan-only correction authorizes no ledger write or dry run. After it is
reviewed and merged, a new durable dry-run obligation must explicitly authorize
fresh reruns of both the preparation and attended previews from the exact target
root without selectors; the earlier `-C` selector-bearing preparation preview
cannot satisfy this corrected boundary.

The first measured parent dry-run created no row, but it showed that normal
parent label inheritance would add `acceptance:human-only`,
`factory-safety:mutates-host-machinery`, and `origin:freeform` to the proposed
child labels. The corrective parent-bearing `--no-inherit-labels` dry-run also
created no row, returned the five labels then requested, and serialized null
`parent_id` despite `--parent bd-ib-3kolea`. The later standalone preparation
preview also created no row and omitted `parent_id`; that omission is permitted
native planning output and does not prove the eventual stored parent. The
required real parent proof therefore cannot pass for a parent-bearing create,
which is why this cut files standalone items and requires a strict immediate
real read-back. A dry-run echoing a requested label does not prove that the
label value is valid under the WorkItem contract; that distinction caused the
factory-safety error recorded below.

Every local dry-run and create command MUST use `--no-inherit-labels`. It must
explicitly provide exactly one `admission:*` label, exactly one `acceptance:*`
label, `intake:triaged`, and the upgrade's `origin:*` label. Factory-safe work
MUST provide **zero** `factory-safety:*` labels. Genuinely attended host-only
work MUST provide exactly one allowed factory-safety reason as classified
below. Each approved creation is exactly one create command, followed
immediately by `bd show` read-back of the assigned identifier before any next
ledger write. The read-back must show the assigned native identifier, exact
Livespec status `backlog`, exact `external_ref`, stored null `parent_id`, the
description provenance, exactly one label under each of the `admission:` and
`acceptance:` singleton prefixes, the explicitly requested values, and the
expected zero-or-one `factory-safety:` cardinality. A missing, inherited,
invalid, or contradictory policy label halts the filing sequence.

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

This step consumes the archived live helper receipt and does not repeat it. The
remaining proof uses three synthetic tenants created by the verified v1.0.5
fixture producer on one dedicated non-production Dolt server. No production
tenant, production backup, live registry, family wrapper, `/var/lib/doltdb`,
`/var/backups`, port `3307`, or production credential may appear in an
executable rehearsal command.

#### Preparation and attendance boundary

Factory-safe preparation may create only reviewed fixture definitions,
inventory queries, command wrappers, receipt schemas, and hermetic tests. It
may also fetch and hash public upstream artifacts and build the v1.0.5 fixture
producer from the tagged source in a disposable build directory. This includes
the version-neutral identity-probe implementation, its locked dependencies,
and its negative statement-refusal tests; preparation never connects that probe
to a database. Factory-safe preparation must not start a server, initialize or
write a tenant, configure a remote, take or restore a backup, or clean an
execution target. Its sole permission to run Beads against a database is the
exact read-only three-repository fixture-shape survey defined in the O4 two-row
filing contract above; every other Beads database call remains attended. Those
attended actions remain host-only even though their targets are non-production.

Every attended action requires a new durable supervisor obligation after the
preparation PR is reviewed and merged. The operator must run the attended
sequence in the foreground. No factory dispatch may perform a fixture write,
migration, backup, restore, or cleanup.

#### Executable package inputs and provenance

The preparation PR must produce a manifest before any attended action. The
manifest uses `RUN_ID` for a lowercase UTC token in the form
`yyyymmddthhmmssz`, `RUN_ROOT` for a newly created directory matching
`/var/tmp/beads112-rehearsal.${RUN_ID}`, and `RECEIPT_ROOT` for a separate
owner-only evidence directory under
`/home/ubuntu/.local/state/livespec-proof-logs/beads112-${RUN_ID}`. These names
are defined here before later command templates use them. Neither directory
may exist before the run, and neither may resolve through a symlink.

The manifest must pin all of the following:

- The v1.0.5 fixture producer comes from upstream tag `v1.0.5`, peeled commit
  `6a3f515ced18406c189c55fff789a4925bfaa35c`, and the tag's declared Go 1.26.2
  toolchain. Because no official v1.0.5 release asset exists, the receipt must
  include the source archive SHA-256, toolchain version, complete build command,
  and resulting executable SHA-256. It may not use or copy the host private
  delegate.
- The candidate comes from official tag `v1.1.2`, peeled commit
  `20e493e569c922d1253bdeff068c5e56c94957fb`. Its Linux AMD64 tarball SHA-256
  must be
  `a72d71ed374955dc9f83a0f90b54bd7b6a0016709dd1676ae2e368651ed401c2`,
  its extracted executable SHA-256 must be
  `6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82`,
  its SPDX SHA-256 must be
  `b05ca7f525f05e50691a4329b13aa87f10bc93160fe8d4d1ca371867701b58e6`,
  and its version output must be
  `bd version 1.1.2 (20e493e56: HEAD@20e493e569c9)`.
- Both Beads executables live under the reviewed package root and are invoked
  directly against isolated client directories. Beads never runs through
  mise, `/usr/local/bin/bd-real`, or any private delegate. The production
  public guard remains untouched.

#### Isolated topology and three fixture shapes

The attended run uses one Dolt process bound only to `127.0.0.1:13307`, with
its socket, configuration, data directory, PID file, logs, local sync remotes,
and client directories all beneath `RUN_ROOT`. Port `13307` must be unbound
before start. The server executable and version must match the production Dolt
server build, but the process must not read the production configuration or
data directory. A dedicated single-use backup bucket prefix and DynamoDB
manifest namespace must contain `RUN_ID`, must be different from the values in
`/data/projects/dolt-server/backup.env`, and must be visible only to the
isolated server's dedicated backup principal. If a distinct non-production
backup namespace and injected secret set are unavailable, stop; never fall
back to production values.

Each shape has three databases whose exact names are recorded in the manifest:
`beads112_${RUN_ID}_${SHAPE}_source`,
`beads112_${RUN_ID}_${SHAPE}_migrated`, and
`beads112_${RUN_ID}_${SHAPE}_restored`. Here `SHAPE` is exactly one of
`dense_policy`, `sparse_closed`, or `rig_wisp`. The source is created with the
v1.0.5 fixture producer; the migrated and restored names must not exist before
their clean-target restores. The one schema-reference database is named exactly
`beads112_${RUN_ID}_golden`; it is not a fourth tenant shape.

Every database has its own client directory and its own database-scoped SQL
user; neither may be reused by another database. The manifest maps
`dense_policy`, `sparse_closed`, and `rig_wisp` to the short shape codes `dp`,
`sc`, and `rw`, and maps source, migrated, and restored to the role codes `s`,
`m`, and `r`. For each three-shape database, its exact client directory is
`RUN_ROOT/clients/${DATABASE}` and its exact SQL user is
`b112_${RUN_ID}_${SHAPE_CODE}_${ROLE_CODE}`. The golden database uses
`RUN_ROOT/clients/beads112_${RUN_ID}_golden` and SQL user
`b112_${RUN_ID}_g`. Each user has privileges only on its exact manifest database
and cannot see any other rehearsal, family, or production database. The
topology preflight rejects duplicate client-directory realpaths, duplicate SQL
users, a database or user not containing the exact `RUN_ID`, or a name outside
this mapping.

#### Client pointer, credential, and database-identity boundary

Before a Beads executable may enter any client directory, the attended operator
must create that directory's `.beads/config.yaml` manually from the reviewed
literal template below. The template is expanded once with that manifest row's
exact `DATABASE` and `SQL_USER`, ends with one newline, and has no other
`dolt.*` key:

```yaml
dolt.auto-start: false
dolt.mode: server
dolt.server-host: 127.0.0.1
dolt.server-port: 13307
dolt.server-user: <SQL_USER>
dolt.database: <DATABASE>
dolt.prefix: b112
```

The pointer must be a regular owner-only file beneath its unique client
directory. It must contain no socket key, symlink, password, production port
`3307`, family database or SQL-user name, production/family endpoint, or value
copied from a repository's `.beads` directory. Its canonical parsed bytes and
SHA-256 are recorded in the topology manifest before first use. No command may
use `bd init` to generate or repair a pointer. If a reviewed fixture or golden
schema producer needs `bd init` after the pointer exists, it may run only inside
its mapped client directory beneath `RUN_ROOT`, only after the anchor check
below passes, and must leave the pointer hash unchanged. It must never run in a
repository primary checkout or worktree.

Regenerable `.beads/metadata.json` is a separate artifact, never part of pointer
identity and never copied between clients. The manifest records it as absent or
records its reviewed schema, exact isolated database identifier, and separate
SHA-256. It may contain no endpoint, SQL user, or credential and may not
override `config.yaml`; an unexpected metadata file or changed pointer hash is
a hard stop.

The reviewed package provides one owner-only wrapper, `WITH_CLIENT`, and pins
its SHA-256. `WITH_CLIENT CLIENT_KEY COMMAND...` resolves exactly one manifest
row, obtains that row's isolated SQL-user credential from the dedicated
non-production credential source, clears every inherited Beads/Dolt credential,
and injects only the bare `BEADS_DOLT_PASSWORD` into `COMMAND`. It must not call
the family wrapper, any production wrapper, `/usr/local/bin/with-*-env.sh`, or
the production/family credential source, and it must itself be launched outside
all such wrappers. A pre-existing bare password or family/production wrapper
marker in the parent environment is a hard stop before credential lookup. The
wrapper probes the isolated credential only with
`printenv BEADS_DOLT_PASSWORD | wc -c`, records only the positive byte count,
and never prints, hashes, persists, or copies the value. A missing value, a
second credential variable, or a credential-source/user mismatch is a hard
stop.

Immediately before every fixture-producer call, remote configuration or fetch,
migration attempt, round-trip command, inventory query, golden-schema command,
and restored-database read, `WITH_CLIENT` must run the reviewed
`assert-client-anchor` helper. `assert-client-anchor` is a version-neutral,
read-only MySQL-protocol program named `ANCHOR_PROBE`; it is not a Beads or Dolt
client. It must never invoke or import `bd`, `dolt`, a `mysql` shell, a Beads or
Dolt package, or any migration, bootstrap, remote, or arbitrary-SQL command.
It has no SQL argv, stdin, environment, configuration, callback, or plugin
surface. Its implementation contains one compile-time query literal and one
execute site, so it is mechanically incapable of submitting a second or
different statement.

The provenance manifest pins `ANCHOR_PROBE_SHA256`, the dependency-lock
SHA-256, and the name, version, source, and SHA-256 of every dependency artifact.
The probe and dependency closure are loaded only from the reviewed package root;
every invocation re-hashes them before connecting and stops on any mismatch.
The probe opens a transaction through the pinned driver's typed read-only API,
allows exactly the one literal statement
`SELECT DATABASE(), CURRENT_USER(), @@hostname, @@port`, rolls the transaction
back, and closes the connection. It does not expose a general query executor.

The helper then:

1. resolves the client-directory realpath and proves its one-to-one manifest
   mapping;
2. hashes and parses `.beads/config.yaml` again, proves the hash and all seven
   mappings equal the manifest, and proves no socket or extra `dolt.*` key is
   present;
3. records the separate metadata presence/hash state and the wrapper hash;
4. through that exact pointer and isolated password, runs `ANCHOR_PROBE`, while
   its reviewed MySQL-protocol transport records the TCP peer; and
5. proves the returned database, authenticated manifest account, server
   hostname, port `13307`, TCP peer `127.0.0.1:13307`, and isolated server
   instance fingerprint all equal the topology manifest.

The helper writes a canonical per-command anchor receipt containing the pinned
implementation and dependency hashes, exact query text and SHA-256, read-only
transaction flag, statement count of one, start/finish timestamps, exit code,
returned identity row, TCP peer, and isolated server fingerprint without
contaminating the wrapped command's stdout or stderr. A missing/unreadable
pointer, implementation/dependency hash mismatch, metadata change, nonzero
probe exit, query or statement-count difference, database/user mismatch, peer
other than `127.0.0.1:13307`, family or production endpoint, or inability to
prove the isolated server fingerprint hard-stops before the requested command.
The operator may not retry with another `-C`, raw database flag, wrapper,
credential, or identity tool.

Hermetic tests must prove that attempts to supply a second statement, a
semicolon-appended statement, or any mutating statement such as `INSERT`,
`UPDATE`, `DELETE`, `CREATE`, `DROP`, or `CALL` are refused before a socket is
opened; argv, stdin, environment, and dependency callbacks cannot replace the
literal; and `WITH_CLIENT` does not execute its requested command after any
probe refusal. The factory-safe preparation gate records these tests passing
against the exact implementation and dependency hashes used by the manifest.

The fixtures are synthetic; read-only family data supplies only their shape
requirements:

| Shape | Read-only evidence source | Required deterministic v1.0.5 contents |
|---|---|---|
| `dense_policy` | `/data/projects/livespec` and this repository | At least one issue in every observed lifecycle status and every observed issue type; at least two logical dependency types; comments; ordinary labels; policy labels with the `acceptance:`, `admission:`, `intake:`, `origin:`, `factory-safety:`, and `blocked-reason:` prefixes; and metadata containing `acceptance_criteria`, `non_local_depends_on`, `notes`, `origin`, and `rank`. |
| `sparse_closed` | `/data/projects/livespec-driver-codex` | One closed task, no open issue, no label, no dependency, no comment, and empty snapshot tables. This preserves empty auxiliary-table coverage while still exercising close state. |
| `rig_wisp` | Tagged upstream v1.1.2 migration 0053 and its tests, because the family survey found no rig rows | One v1.0.5 wisp with `issue_type=rig`, its label, event, comment, dependency, and child counter; one durable issue whose dependency targets that rig as a wisp; and no duplicate durable rig row before migration. The fixture SQL is reviewed and hashed during factory-safe preparation, then executed only during the attended isolated run. |

The v1.0.5 producer must leave each source at schema version 49. Each shape's
manifest defines `SYNC_REMOTE_URL` as its exact run-scoped sync remote beneath
`RUN_ROOT/remotes/${SHAPE}` and `ACTIVE_BRANCH` as the source's active branch.
The v1.0.5 client configures that source remote as `origin` and pushes the v49
baseline to it. This source-side push seeds the isolated remote, but it does
not by itself establish a remote or cached remote-tracking ref on a later
`DOLT_BACKUP` restore target.

#### Exact baseline, migration, and schema inventories

The package must provide one `capture-inventory` command that runs read-only
through `WITH_CLIENT`, emits canonical UTF-8 JSON with sorted keys and rows, and
writes a SHA-256 for each artifact plus a combined SHA-256. It runs before
backup, after the first gate decision, after migration, after round trips, and
after restore. Every capture includes exactly these projections:

1. `status-type-counts.json` contains `status`, `issue_type`, and `COUNT(*)`,
   ordered by status and type.
2. `issues.json` contains every row ordered by `id`, projecting `id`, `title`,
   `description`, `design`, `acceptance_criteria`, `notes`, `status`, `priority`,
   `issue_type`, `assignee`, `owner`, `created_at`, `created_by`, `updated_at`,
   `closed_at`, `close_reason`, `external_ref`, `spec_id`, `due_at`,
   `defer_until`, and canonicalized `metadata`.
3. `dependencies.json` contains every logical edge ordered by `issue_id` and
   target, projecting `id`, `issue_id`, `depends_on_issue_id`,
   `depends_on_wisp_id`, `depends_on_external`, `type`, `created_at`,
   `created_by`, canonicalized `metadata`, and `thread_id`.
4. `comments.json` contains `id`, `issue_id`, `author`, `text`, and
   `created_at`, ordered by issue and comment ID. `labels.json` contains
   `issue_id` and `label`, ordered by both columns.
5. `policy-metadata.json` contains each issue ID, the complete canonical
   metadata object, and the sorted labels whose prefixes are `acceptance:`,
   `admission:`, `intake:`, `origin:`, `factory-safety:`, or
   `blocked-reason:`. This is the exact policy projection; label counts alone
   are not acceptable.
6. `schema-migrations.json` contains the discovered column manifest and every
   ordered row from `schema_migrations` and `ignored_schema_migrations`.
   `schema.json` contains every user-table column, index, unique constraint,
   foreign key, and view definition from `information_schema`, ordered by
   object and ordinal position. `branches.json` contains every branch name and
   head hash. `table-counts.json` contains every base-table name and row count.
7. `remotes.json` contains the ordered `dolt_remotes` rows, `ACTIVE_BRANCH`,
   the local active-branch head, the cached
   `remotes/origin/${ACTIVE_BRANCH}` head, the local and cached-ref
   `schema_migrations` rows, and the SHA-256 manifest for the tagged v1.0.5
   migration files numbered 1 through 49. An intentionally absent column is
   represented explicitly rather than omitted.
8. `client-anchor.json` contains the client key, client-directory realpath,
   database and SQL user, canonical pointer SHA-256, separate metadata
   presence/SHA-256, wrapper SHA-256, `ANCHOR_PROBE` and dependency hashes,
   credential byte count, exact query hash, read-only flag, statement count,
   probe exit and identity result, TCP peer, isolated server fingerprint, and
   the immediately following command's category and sequence number. It
   contains no credential value.

The pre-migration v49 capture is the complete baseline. The post-migration
capture must show schema version 53; migration content hashes must equal the
SHA-256 of the corresponding tagged v1.1.2 migration bytes. Migration 0050 may
change dependency IDs but must preserve the logical edge set and produce the
tagged deterministic-ID result. Migration 0051 must remove ID defaults from
`events`, `comments`, `issue_snapshots`, and `compaction_snapshots` without
changing their rows. Migration 0052 must replace the old status index with
`idx_issues_status_updated_at` and add `idx_issues_defer_until`. Migration 0053
must move the synthetic rig plus its auxiliary rows into durable tables, set
the rig non-ephemeral, rewrite wisp-targeting dependencies to durable issue
targets, and remove the migrated rig rows from wisp tables. All other logical
issue, edge, comment, label, and policy-metadata bytes must match the baseline.
The migrated schema hash must also equal a fresh v1.1.2 golden schema created
inside the same isolated server; that golden database is schema reference only,
not a fourth tenant shape.

#### Single-use backup and one designated migrator

No v1.1.2 candidate process ever opens a v49 source. Before any clean-target
restore, the attended operator uses the tracked Dolt-server backup helper with
`DOLT_SOCKET`, backup principal, bucket, manifest table, region, and source
database explicitly overridden to the isolated values. Each source is synced
exactly once. No later backup sync is allowed. The backup identity receipt
records the source database, `RUN_ID`,
backup URL, bucket prefix, manifest namespace, object key, version ID, ETag and
size inventory, every branch head, the complete v49 baseline digest, start and
finish timestamps, helper commit, command digest, and exit status. Missing
object version IDs or an advancing namespace is a hard stop.

Each single-use backup is restored through the tracked helper into its clean
`_migrated` database with `--verify`. A restore is not a clone: it creates a
fresh database and syncs roots into it, so it does not establish the source's
remote configuration or cached remote-tracking branches on the target. Before
any v1.1.2 candidate process may open an `_migrated` target, the attended
package must therefore use only the verified v1.0.5 producer/client through the
`_migrated` database's exact `WITH_CLIENT` mapping to perform this target-side
sequence:

1. Read `ACTIVE_BRANCH` and the restored local head, and prove both equal the
   source's recorded v49 baseline.
2. Refuse any existing target-side remote. Configure exactly one remote named
   `origin` at the manifest's exact `SYNC_REMOTE_URL`; any other URL, name, or
   pre-existing remote is a hard stop.
3. Fetch that run-scoped `origin` with the v1.0.5 client to materialize
   `remotes/origin/${ACTIVE_BRANCH}`. This fetch may contact only the local
   remote beneath `RUN_ROOT`.
4. Capture `dolt_remotes`, the local active-branch head, the cached remote-ref
   head, local `schema_migrations`, and `schema_migrations AS OF` the cached
   remote ref. Prove both heads equal the source v49 baseline, both ordered
   migration-row sets equal the baseline, and both resolve to the same tagged
   migration-files-1-through-49 SHA-256 manifest. If the v49 schema lacks a
   `content_hash` column, the receipt records that identical local/remote
   absence alongside the tagged file hashes; it never invents a database value.
5. Run a read-only remote-presence probe again from the exact target client
   directory and write its canonical output to `remotes.json`. An unreadable
   `dolt_remotes` row, missing or unreadable cached ref, mismatched head,
   mismatched migration rows or hashes, network destination outside
   `RUN_ROOT`, or any changed baseline artifact is a hard stop before the
   candidate starts.

Only after that target-side receipt and every associated client-anchor receipt
pass does the operator record one designated migrator identity for the entire
three-shape run: human/session identity, process ID, candidate executable hash,
host, start time, and ordered database list. No second candidate process may
open a migration target until that migrator finishes and pushes the migrated
state to its isolated remote.

No v1.1.2 process may open, inspect, inventory, or otherwise connect to a v49
`_migrated` target before the separately logged `bd migrate` invocation below.
Every anchor and v49 inventory before that point uses only `ANCHOR_PROBE`, the
verified v1.0.5 producer/client, or a reviewed version-neutral read-only capture
helper. `ANCHOR_PROBE` is not the first gate or migration attempt. The first
v1.1.2 connection to each v49 target must be the designated migrator's recorded
`bd migrate`, with its exact command, start time, stdout, stderr, and exit code
already armed for capture before process start.

For each migrated target, first prove `BD_ALLOW_REMOTE_MIGRATE` and
`BD_SMART_GATE` are unset, then invoke `bd migrate` once and capture exact
stdout, stderr, and exit code through that target's `WITH_CLIENT` mapping.
`assert-client-anchor` runs again before the permitted retry as well as before
the first attempt. Capture the full inventory again immediately.
If the gate permits a smart first-mover migration, record that decision and do
not set the escape hatch. If the gate refuses with the migrate-or-adopt
decision, prove the refusal changed no inventory bytes, then the already
designated migrator may make exactly one foreground retry with
`BD_ALLOW_REMOTE_MIGRATE=1`. A gate decision of `adopt`, `fork-skew`, an
unrecognized classification, or any changed bytes after a refusal is a hard
stop; do not migrate, bootstrap, or improvise.

#### Required command round trips

After each shape reaches the accepted v53 post-migration baseline, run the
same round trip with the verified v1.1.2 candidate from that shape's isolated
client directory. `BD112` below means the manifest-pinned candidate path and
`CLIENT_KEY` and `CLIENT_DIR` mean the migrated database's manifest key and
unique client directory. `WITH_CLIENT` means the manifest-pinned isolated
credential-and-anchor wrapper. All four variables are defined in the reviewed
command package before this template is executed, so every command gets a fresh
pointer and database-identity proof.

```sh
parent_id="$("$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" create \
  "rehearsal parent" --type epic --priority 2 \
  --labels 'origin:rehearsal,intake:triaged,admission:manual' \
  --metadata '{"rank":"m","origin":"rehearsal"}' --silent)"
child_id="$("$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" create \
  "rehearsal child" --type task --priority 3 \
  --labels 'acceptance:ai-then-human,factory-safety:needs-privileged-host' \
  --metadata '{"acceptance_criteria":"round-trip","rank":"n"}' --silent)"
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" update "$child_id" --status active --type bug \
  --set-metadata origin=rehearsal-update --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" dep add "$child_id" "$parent_id" \
  --type discovered-from --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" comments add "$child_id" \
  'isolated v1.1.2 round-trip comment' --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" close "$child_id" \
  --reason 'isolated v1.1.2 round-trip complete' --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" list --all --id "$parent_id,$child_id" --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" show "$child_id" --include-comments --json
```

Every command must exit zero and its JSON must parse. The post-round-trip
inventory must differ from the accepted post-migration baseline by exactly two
issues, one lifecycle/type update followed by one close, one logical dependency,
one comment, the declared labels, and the declared metadata. Any additional
row or field change is a hard stop.

#### Restore, cleanup, receipts, and rollback boundary

After round trips, restore each unchanged single-use pre-migration backup into
its clean `_restored` database. Use the v1.0.5 fixture producer only for the
read-only restored capture, through that restored database's unique
`WITH_CLIENT` mapping, so the candidate cannot auto-migrate the proof target.
Every restored artifact, branch head, base-table count, per-artifact hash, and
combined hash must equal that shape's complete pre-migration v49 baseline. This
is the missing restore-to-complete-baseline proof. It is not a repeat of the
archived live source-to-scratch receipt and it never uses the production S3
remote.

The immutable receipt set contains the provenance manifest, topology manifest,
fixture SQL and hashes, the complete database-to-client-directory-to-SQL-user
map, every canonical pointer hash, separate metadata state/hash, isolated
wrapper hash, `ANCHOR_PROBE` implementation/dependency hashes and hermetic-test
receipt, credential presence/length probes, every per-command single-query
SQL/endpoint identity receipt, sanitized environment-variable names, ordered
command log, stdout/stderr/exit-code hashes, each `_migrated` restore target's
exact `origin` URL, active branch, local head, cached remote-ref head,
local/remote migration-row comparison and migration-file hash manifest,
designated-migrator record, gate-decision record, every inventory and hash,
backup identity, round-trip delta, restored baseline comparison, and a top-level
`SHA256SUMS`. Secret values are never written. Copy and hash this set into
`RECEIPT_ROOT` before cleanup.

Cleanup is a separate attended action after the supervisor accepts the receipt.
It may stop only the PID whose executable, start time, port, socket, and
`RUN_ROOT` match the topology manifest; delete only the run-scoped databases,
every source and target-side remote registration, every cached
`remotes/origin/${ACTIVE_BRANCH}` ref, the local remote repositories, bucket
prefix, manifest namespace, isolated database-scoped SQL users and grants,
client directories, manually created pointers, regenerable metadata, wrappers,
the run-scoped `ANCHOR_PROBE` implementation and dependency closure, and
credential handles containing the exact `RUN_ID`; and remove only `RUN_ROOT`.
It must retain `RECEIPT_ROOT`. The cleanup receipt proves the PID and port are
absent, every manifest client directory, pointer, metadata file, isolated
wrapper, identity probe/dependency artifact, SQL user/grant, target-side remote
configuration, and cached ref is absent with every other run-scoped resource,
production port `3307` still answers as it did before the run, production tenant
registry and backup configuration digests are unchanged, and every involved
checkout is clean. Any target outside the manifest or any shared-resource match
is a hard stop.

There is no in-place schema downgrade. Before migration, a failure leaves only
disposable isolated resources for attended cleanup. After migration begins,
the rehearsal rollback boundary is the frozen single-use v49 backup restored
to a clean target and proved against the complete baseline. The production
rollback boundary remains the stopped-server cold archive described in step 7;
this isolated receipt does not authorize or replace that later attended
cutover artifact.

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
| Database | every source/migrated/restored/golden client pointer and SQL/endpoint identity is anchored; isolated migrate and restore; pre/post counts, edges, comments, statuses, labels, metadata, and schema hashes match expectations |
| Concurrency | all writers enumerated and stopped; one migrator per tenant; writers restarted only after checks |
| Container | pinned guarded layout; build succeeds; Tier 1 uses only ephemeral data and proves lifecycle normalization |
| Fleet | host/image version and hashes agree; current non-historical references agree; no Beads installation via mise |
| Delivery | worktree-only commits, required hooks, `git diff --name-only` ownership check, reviewed PRs, rebase merges, clean primary checkouts |

## Immediate next action

Stop at the external factory-capacity blocker recorded in the authoritative
2026-08-11 checkpoint above. The O4 filing contract and guarded release are
complete: `bd-ib-8azd` is safely `ready` and unassigned with no target run,
lock, branch, or pull request, while attended `bd-ib-ao3j` remains manual and
`backlog` behind its sole `blocks` prerequisite.

On restart, read this handoff and the complete append-only supervisor marker at
`/data/projects/livespec-orchestrator-beads-fabro/tmp/overseer/beads-v1-1-2-upgrade/.supervisor-state`.
If the marker is missing or unreadable, stop. If its latest entry still leaves
`wait_for_factory_oauth_capacity_bd_ib_8azd` blocked and handed to the
maintainer, report that blocker and stop. Do not infer a wake from elapsed time,
the item being ready, or a generic instruction to resume the plan. Do not run
`claude-cred-status`, inspect or change credentials, submit another factory
action, or hand-build the preparation without a new durable supervisor
obligation that explicitly authorizes that exact bounded action.

If a later durable obligation authorizes a fresh submission after capacity is
restored, remeasure the item, relation, forge, complete Fabro run set, exact
dispatch lock, matching branches, and matching pull requests first. Any future
submission must use the configured environment wrapper and the distributed
`livespec-orchestrator-beads-fabro:drive` action, never a direct Dispatcher call
or manual implementation. A partial no-run claim after another refusal may be
released only through a separately authorized guarded move valve; never repair
it with a manual status or assignee edit.

Do not admit or execute `bd-ib-ao3j`, and do not perform a fixture write,
server action, migration, backup, restore, cleanup, image operation, host copy,
`/usr/local/bin` mutation, production-tenant or Dolt-data mutation, secret
action, rollout, or Fabro code/config/service/server mutation without a new
durable obligation and the attended authorization required by this package.
