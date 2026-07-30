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
8. Never edit work owned by `fix-bd`. Rebase after its relevant merges and
   measure the remaining scope.

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
| `fix-bd` tmux session | removal of mise references to Beads and guarded-path fallback changes |
| `beads-v1-1-2-upgrade` worker | compatibility qualification, version pins, guard/image integration, migration rehearsal, current documentation, and evidence |
| `beads-v1-1-2-upgrade-supervisor` | adversarial review of this plan and later execution evidence |
| Maintainer in the attended window | production writer quiescence, direct host copy, tenant migration authorization, and rollback decision |

Before every implementation PR, fetch and rebase, then run
`git diff --name-only origin/master...<branch>` in every affected repository.
Any path already owned by another lane stays out of this thread.

## Reconciled `fix-bd` scope and unresolved path seam

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

That guarded-entrypoint and no-mise content is complete for this thread. It
MUST NOT be reimplemented, restated as new behavior, or used to justify
touching the `fix-bd` lane's paths.

There is one unresolved implementation boundary. PR #1161 changed
`.mise.toml`, `AGENTS.md`, the current `SPECIFICATION/constraints.md`,
`SPECIFICATION/contracts.md`, and `SPECIFICATION/scenarios.md`,
`tests/heading-coverage.json`, and its frozen history snapshot. The literal
path-exclusion rule above therefore conflicts with this handoff's later
requirement to update version-specific statements in some of those same
current specification paths. Until a later reviewed decision resolves that
conflict, the strict interpretation governs: every PR #1161 path is
**no-touch**, including the current specification files. The “Current contract
updates” outcome below remains required, but it does not authorize an edit to
those paths. Do not resolve the conflict opportunistically inside an
implementation slice.

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
existing clean-target refusal, and updates the stale runbook examples. That
cross-repository slice follows `dolt-server`'s own propose-change, revise,
worktree, test, PR, and rebase-merge workflow. Production migration is blocked
until the revised helper has restored a real source backup into a differently
named scratch tenant on the live server and `--verify` has passed.

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
decomposition: do not file it through the current `groom` path and do not
mutate the ledger until a later supervised instruction supplies a safe filing
procedure.

The identifiers `O1` through `O8` below mean “remaining outcome 1” through
“remaining outcome 8.” A dependency names the outcomes whose evidence must be
complete before the dependent outcome begins.

| Order | Remaining outcome | Depends on | Required result | Factory eligibility |
|---|---|---|---|---|
| O1 | Release and CLI qualification | None | Pin upstream provenance and prove the exact command, flag, and JSON surface against v1.1.2. | factory-safe |
| O2 | Guard compatibility | O1 | Run the existing hermetic guard suite against the qualified v1.1.2 binary and resolve only demonstrated incompatibilities. | factory-safe |
| O3 | Dolt restore source/target seam | None inside this repository; it is a prerequisite of O4 | In `dolt-server`, specify and implement distinct backup-source and clean scratch-target names, preserve the clean-target refusal, and correct stale examples. | factory-safe only after that repository's spec revision |
| O4 | Migration and restore rehearsal | O1, O2, O3 | Restore each relevant tenant shape into isolation, migrate once, compare the complete invariant inventory, and prove the restore boundary. | needs privileged host |
| O5 | Guarded image layout | O1, O2 | Put v1.1.2 at `bd-real`, install the tracked wrapper at `bd`, strengthen image verification, and resolve existing defect `bd-ib-dwv` with the successful guarded rebuild as evidence. | factory-safe for code; privileged host for DinD proof |
| O6 | Current contract updates | O1, O2, O4, O5 | Update only current version-specific comments, tests, runbooks, and paths permitted by the unresolved no-touch boundary; historical records remain unchanged. | factory-safe within the permitted path set |
| O7 | Attended host and tenant rollout | O3, O4, O5, O6 | Quiesce every writer, capture the rollback artifacts, directly replace `bd-real`, migrate once per tenant, and verify before restarting writers. | mutates host machinery |
| O8 | Closure and parity evidence | O7 and the acceptance evidence from O1 through O6 | Prove host/image parity, attach the complete audit trail, and close the upgrade only after `bd-ib-dwv` has been resolved by O5 rather than duplicated. | human-reviewed |

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

Therefore O3 must eventually be filed in the `dolt-server` tenant with a
native target-tenant identifier, and the eight outcomes must not be filed or
linked through the defective path. A later reviewed filing decision must name
the safe mechanism before any ledger write occurs.

Factory-safe slices should be driven through the dark factory only after they
are safely filed and admitted. The migration rehearsal and production rollout
must carry their non-factory safety reason and run attended.

## Execution sequence

### 1. Reconcile concurrent work

The relevant `fix-bd` PRs, releases, integration commits, and exact SHAs are
recorded in “Reconciled `fix-bd` scope and unresolved path seam.” Fetch and
rebase every affected repository before implementation, repeat the
current-version and current-mise search, and exclude every path owned by that
lane under the strict no-touch rule until the recorded boundary is resolved by
a later reviewed decision.

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
examples until that source/target correction has landed.

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

The unresolved PR #1161 path seam limits this instruction. Until a reviewed
later decision changes the boundary, do not edit any PR #1161 path, even when
it contains a version-specific statement. Update permitted current paths and
record blocked current-spec statements as evidence for that later decision;
do not silently treat this outcome as overriding the path-exclusion rule.

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

Do not begin implementation and do not groom or otherwise mutate the ledger.
First land this reconciliation through a reviewed plan-only PR. After it
merges, the supervisor must obtain a reviewed decision for both the safe
filing mechanism and the PR #1161 no-touch boundary. Only then may the
supervisor authorize filing O1 through O8 in their recorded dependency order.
