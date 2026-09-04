# Beads v1.1.2 upgrade qualification

> **SUPERSEDED IN PART as of 2026-08-20 — read this first.** The release
> selection below is stale: **v1.2.2** (2026-08-15) is now the latest stable,
> and it is a *recovery* release that upstream describes as "the v1.1.2 code
> under a higher version number". The technical findings in this note — the
> adapter command surface, the JSON envelope shapes, and migrations 0050–0053
> landing at schema v53 — are expected to carry over unchanged, but the
> **target version named here is no longer the one to install**. There is also
> a live hazard: running the accidentally-published **v1.2.1** even once
> migrates a database to schema v65 and strands every v1.1.2/v1.2.2 client —
> fleet-wide on our shared tenants. See
> [`release-target-restatement-2026-08-20.md`](release-target-restatement-2026-08-20.md)
> and ledger item `bd-ib-3kolea.4`. Everything below remains accurate **as of
> its own evidence date** and is left unedited for that reason.

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
| SPDX artifact | `beads-v1.1.2.spdx.json` on the same release; SHA-256 `b05ca7f525f05e50691a4329b13aa87f10bc93160fe8d4d1ca371867701b58e6` |

The tarball hash is upstream-published. The extracted-binary hash is a derived
pin: it was measured only after the tarball matched the upstream checksum and
must be independently reproduced during implementation and image build.

O1 re-measured these facts in a temporary directory on 2026-07-30 with no host
installation step:

```sh
curl -fsSLO https://github.com/gastownhall/beads/releases/download/v1.1.2/checksums.txt
curl -fsSLO https://github.com/gastownhall/beads/releases/download/v1.1.2/beads_1.1.2_linux_amd64.tar.gz
curl -fsSLO https://github.com/gastownhall/beads/releases/download/v1.1.2/beads-v1.1.2.spdx.json
sha256sum -c --ignore-missing checksums.txt
tar -xzf beads_1.1.2_linux_amd64.tar.gz
sha256sum bd beads-v1.1.2.spdx.json
./bd version
```

The official v1.0.5 Linux amd64 asset and its checksum file still returned
HTTP 404 on 2026-07-30, while the upstream git tag `refs/tags/v1.0.5` still
resolved to annotated tag `fa78674f17071fd9de6d44a77e5e13b460e5fd24` and
peeled commit `6a3f515ced18406c189c55fff789a4925bfaa35c`. This preserves the
`bd-ib-dwv` diagnosis: the old release artifact cannot be used as the upgrade
source in a reproducible image build.

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

O1 executed the current adapter-facing commands through the extracted
v1.1.2 binary against an isolated embedded-Dolt repository under `/tmp`; it did
not call the host guard, did not install `bd`, and did not touch a production
tenant. The measured command contract was:

| Adapter surface | Candidate result |
|---|---|
| `bd config set status.custom ...` | accepts the current five custom lifecycle statuses in the existing CSV form. |
| `bd create --id ... --type ... --title ... --description ... --priority ... --label ... --metadata ... --json` | emits a single JSON object for the created issue; the new issue starts in native `open`, so lifecycle normalization is still required. |
| `bd create ... --silent` | emits only the created identifier. |
| `bd update <id> --status ready --assignee fabro --add-label ... --json` | emits a JSON array containing the updated issue; `status`, `assignee`, labels, and metadata are retained in the shape the current JSON adapter accepts. |
| `bd list --status all --limit 0 --json` | emits a bare JSON array of issue objects, including `dependency_count`, `dependent_count`, and `comment_count`. |
| `bd show <id> --json` | still emits a one-element JSON array, not a bare object. |
| `bd comments <id> --json` | emits a bare JSON array with comment objects containing `id`, `issue_id`, `author`, `text`, and `created_at`. |
| `bd dep add <from> <to> --type blocks` followed by `bd dep list <from> --json` | records and reports dependency type `blocks`. |
| `bd update <id> --parent <parent>` followed by `bd children <parent> --json` | records the parent-child dependency and returns child objects with `dependencies[]` and `parent`. |

The exact fixture used a throwaway prefix `q`, issue identifiers `q-a`,
`q-b`, and `q-parent`, and metadata
`{"rank":"001","policy":{"factory_safety":null}}`. The resulting JSON shapes
match the current `coerce_record_list`, `coerce_issue_record`, and
`coerce_comment_list` expectations: list-like reads are arrays; `show` remains
an array envelope; non-record array members were not observed; and lifecycle
policy data remains in the native `metadata` object.

`bd create --help` still does not advertise `--status` or `-s`. The guard's
two-step create normalization remains the current compatibility path for this
candidate. If a later Beads candidate adds a create-time status control, the
guard must be redesigned around that fact rather than carrying this O1 result
forward.

The isolated migration-shape probe copied that throwaway repository, changed
only `.beads/.local_version` from `1.1.2` to `1.0.5`, and ran the v1.1.2
candidate against the copy. `bd migrate --inspect` reported schema version
`1.1.2`, issue count `3`, and registered migrations `0`; `bd migrate schema
--json` printed `Schema already at v53` and restored `.beads/.local_version`
to `1.1.2`. A subsequent `bd migrate status` reported:

```text
Dolt database version: 1.1.2
Version matches
All metadata fields present
```

The post-probe `bd list --status all --limit 0 --json` read preserved the
three issues, lifecycle status, metadata, labels, comment count, blocking
dependency, and parent-child edge. This is sufficient O1 evidence for the
candidate CLI and metadata-version repair surface, but it is deliberately not
claimed as the full O4 production migration rehearsal: the sandbox had no
verified v1.0.5 binary, no real v1.0.5-created Dolt tenant, no remote
SQL-server topology, and no restore-from-backup proof.

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
