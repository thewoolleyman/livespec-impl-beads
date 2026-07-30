# Beads v1.1.2 upgrade qualification

**Evidence date:** 2026-07-30  
**Target:** the Livespec family’s guarded Beads runtime on the host and in the
`livespec-orchestrator` image.

## Conclusion

Beads v1.1.2 is a real, stable upstream release with a currently downloadable
Linux amd64 asset. It is the correct candidate to qualify, but it is not a
feature-identical replacement for v1.0.5: it crosses four database migrations
and a large CLI/storage delta. The rollout therefore needs compatibility tests,
tenant backups, an isolated migration rehearsal, a single attended production
migrator, and explicit restore evidence.

The installation shape is not negotiable:

- `/usr/local/bin/bd` remains the tracked Livespec guard wrapper.
- `/usr/local/bin/bd-real` becomes the checksum-verified v1.1.2 executable.
- `LIVESPEC_BD_PATH`, where explicitly configured, names
  `/usr/local/bin/bd`, not `bd-real`.
- Beads is never installed or upgraded through mise.
- The orchestrator image must mirror this guarded layout instead of putting the
  raw binary at `/usr/local/bin/bd`.

## Verified release provenance

The following facts were verified directly from the official
`gastownhall/beads` GitHub release and a fresh download on 2026-07-30.

| Property | Verified value |
|---|---|
| Release | `v1.1.2`, stable, published 2026-07-26 |
| Release page | <https://github.com/gastownhall/beads/releases/tag/v1.1.2> |
| Linux amd64 asset | `beads_1.1.2_linux_amd64.tar.gz` |
| Published checksum file | <https://github.com/gastownhall/beads/releases/download/v1.1.2/checksums.txt> |
| Tarball SHA-256 | `a72d71ed374955dc9f83a0f90b54bd7b6a0016709dd1676ae2e368651ed401c2` |
| Extracted `bd` SHA-256 | `6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82` |
| Binary-reported version | `bd version 1.1.2 (20e493e56: HEAD@20e493e569c9)` |
| SPDX artifact | `beads-v1.1.2.spdx.json` on the same release |

The tarball hash is upstream-published. The extracted-binary hash is a derived
pin: it was measured only after the tarball matched the upstream checksum and
must be independently reproduced during implementation and image build.

The current host layout was also measured:

| Path | Current role and value |
|---|---|
| `/usr/local/bin/bd` | Livespec guard wrapper; contains `bd-guard-wrapper-sentinel`; SHA-256 `5f55fbfbdb872faf1e43e91e7276ed7f1f754e1611e1c84921286029224637a3` |
| `/usr/local/bin/bd-real` | Beads v1.0.5; SHA-256 `463b7655041345ce5d4bac00c3a5d465166bb30166147e11ef1c6e07df0a4486` |

Both `bd version` through the guard and `/usr/local/bin/bd-real version`
currently report v1.0.5. A successful upgrade changes only the second file’s
binary content; it must not overwrite the first file.

## Compatibility facts and open qualification work

The v1.1.2 binary still exposes the command surface currently used by this
repository: `list`, `show`, `comments`, `children`, `create`, `update`, `close`,
`dep`, `comment`, `config`, `migrate`, `export`, `bootstrap`, and `doctor`.
Its root `-C` / `--directory` selector is also present.

`bd create --help` still does not advertise `--status`. The guard’s two-step
create normalization therefore remains necessary. The upgrade must test that
the guard’s output parsing and follow-up update remain correct against v1.1.2;
the continued absence of the flag does not prove output compatibility.

The v1.1.2 source contains these migrations beyond the current pin:

| Migration | Purpose inferred from the upstream filename |
|---|---|
| `0050_dependencies_deterministic_id` | deterministic dependency identifiers |
| `0051_drop_aux_id_defaults` | removal of auxiliary-table identifier defaults |
| `0052_add_date_indexes` | date indexes |
| `0053_repair_rig_wisps` | repair for rig/wisp data |

The v1.1 release notes specifically add migration-content hashes, a remote
migration gate, dependency-key convergence, and schema-drift repair. Those are
material changes for the family’s shared Dolt tenants.

Upstream’s stable upgrade guidance requires a pre-upgrade export, one
designated migrator for a remote-backed database, and `bd bootstrap` rather
than independent migration from other clones. The family uses central Dolt SQL
server tenants rather than a simple one-clone embedded database, so the plan
must first prove how the v1.1.2 gate classifies this topology. It must not
blindly set `BD_ALLOW_REMOTE_MIGRATE=1` on production merely because that
variable appears in the generic guide.

Authoritative upstream guidance:

- <https://github.com/gastownhall/beads/releases/tag/v1.1.0>
- <https://beads.gascity.com/getting-started/upgrading>

## Existing local defect and historical decision

Ledger item `bd-ib-dwv` records the current Docker build failure: the
v1.0.5 release asset at the pinned `gastownhall/beads` URL now returns HTTP
404. The v1.1.2 upgrade resolves that symptom by selecting a live official
release and new content pins; the item should be closed as completed or
superseded only after a rebuilt guarded image passes verification.

The archived `ledger-status-conformance` plan said to stay on canonical v1.0.5
and wait for an upstream release instead of maintaining a fork. That ruling was
correct for its date. v1.1.2 is now a canonical stable release, but it still
does not supply create-time status selection, so the rationale for keeping the
guard remains current.

Historical specification snapshots and archived handoffs must retain their
then-true v1.0.5 statements. Only current authoritative source, current
specification, current runbooks, and current tests should be revised.

## Tenant and restore qualification

The live tenant registry is the output of
`scripts/lib/common.sh:list_tenant_databases backup_sql` in
`/data/projects/dolt-server`. The family membership projection is the set of
`dolt.database` values in
`/data/projects/livespec*/.beads/config.yaml`. Both populations were measured
on 2026-07-30; their intersection contained nine family tenants. The rollout
must re-run and reconcile these two populations rather than trust that dated
count.

The current Dolt-server backup implementation is:

- `scripts/backup-sync.sh --db <DB>` for a live, point-in-time S3/DynamoDB
  snapshot through `CALL DOLT_BACKUP('sync', 's3')`; and
- `scripts/backup-restore.sh --db <DB> --verify` for clean-target restoration
  through the dedicated `backup` principal.

The current restore script has only one database argument and uses it as both
the source backup path and destination database name. Some current runbook
text still suggests a `<DB>_restoretest` target, but that form points at a
different, normally nonexistent backup source. The upgrade must not rely on
that stale example. Before rehearsal, a separately reviewed `dolt-server`
specification and implementation slice must add distinct `--source-db` and
`--target-db` arguments while retaining the clean-target refusal. The source
backup can then be restored into a named scratch tenant on the live server.

This matters to the rollback claim: a fresh backup is not sufficient evidence.
The exact restore path that would recover the migrated production tenant must
have run successfully before production migration. It also does not make the
shared S3 remote an immutable cutover point: later backup syncs advance that
remote. The authoritative post-migration rollback artifact is therefore a
checksummed, root-read-only cold archive of the complete
`/var/lib/doltdb/databases/` directory, including `.doltcfg`, captured with
Dolt and all writers stopped. The plan records exact forward and recovery
commands. A `bd export --all` JSONL file is retained as supplemental
issue-interoperability evidence, not represented as a full database backup.

## Container gap

`orchestrator-image/Dockerfile` currently downloads v1.0.5 and installs the raw
binary directly as `/usr/local/bin/bd`. It sets
`LIVESPEC_BD_PATH=/usr/local/bin/bd`, so the container bypasses the lifecycle
guard entirely.

The target Docker build must:

1. download the exact v1.1.2 asset from the official release;
2. verify the upstream tarball hash before extraction;
3. verify the derived binary hash after extraction;
4. copy the real executable to `/usr/local/bin/bd-real`;
5. stage the tracked `bd-guard/` payload into the build context;
6. install `bd-guard.sh` as `/usr/local/bin/bd` and
   `bd-guard-emit.py` beside it;
7. seed or explicitly configure the container guard mode without baking any
   secret;
8. keep `LIVESPEC_BD_PATH=/usr/local/bin/bd`;
9. prove both wrapper passthrough and `bd-real` version/hash in the image; and
10. exercise the guard against v1.1.2 in the existing ephemeral Tier-1
    substrate.

Reusing `bd-guard/install.sh` inside the image build is acceptable only after
the candidate binary has already been copied to `bd-real` and a hermetic test
proves the installer preserves that layout. Installing Beads with mise is not
acceptable in any host or image step.

## Concurrent ownership boundary

The tmux session named `fix-bd` was live on 2026-07-30 in
`/data/projects/livespec`. It owns removal of mise references to Beads across
the Livespec material and is concurrently revising guarded-path fallback
guidance.

This plan does not own those edits. Its implementation must wait for the
`fix-bd` lane’s relevant PRs to merge, fetch their merge SHAs, rebase each
affected repository, and inventory the remaining v1.0.5/version/guard/image
work. Verification may assert that no Beads installation path uses mise, but
this thread must not independently edit the mise-removal paths while `fix-bd`
owns them.
