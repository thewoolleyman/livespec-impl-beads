# Cutover receipt — beads v1.0.5 → v1.2.2, all 14 tenants (2026-08-31)

Executed 2026-08-31 02:35Z–03:00Z from the plan seat, maintainer attended
throughout. The runbook is the `PROPOSED PER-TENANT CUTOVER RUNBOOK` ledger
entry on `bd-ib-3kolea` (2026-08-30T12:10Z), approved by the maintainer and
executed with the two corrections recorded below. The durable receipt is the
`CUTOVER RECEIPT` ledger entry on the same epic; this note carries the same
facts in the filesystem research store plus the method detail that does not
belong in a ledger comment.

## Outcome

| Surface | Before | After |
|---|---|---|
| `/usr/local/bin/bd-real` | v1.0.5 (`6a3f515ce`, sha `463b7655…`) | **v1.2.2** (`6c124203e: HEAD@6c124203e771`, sha `54fc0e0581ce4c5487a5b242f0a4f34af1ef09cf056e164a1af63a6ec7aa1e0e`) |
| `/usr/local/bin/bd` (guard) | tracked guard, sha `5f55fbfb…` | unchanged |
| `/usr/local/bin/bd-real.v1.0.5` | — | kept; **not** a rollback for a migrated tenant |
| all 14 server-mode tenants | schema v49 | **schema v53**, rekey complete, data preserved |
| rekey rows fleet-wide | 44,119 | 44,119 |

The tarball sha `8140098a51d3b81d5548d1c5e6db1a2d9930e5d141efe2a4bff7d079c4d321e8`
matched upstream `checksums.txt` (whose own sha matched the recorded pin
`25507c2d…`), the extracted binary matched the recorded binary pin, and the
version-abort arm confirmed the binary self-reports `1.2.2` — v1.2.0 / v1.2.1
were never fetched.

## Per-tenant result

Every row passed the full verify set (see "Verify set" below). `issues`
counts are baseline = post; rekey rows are `events + comments`
(`issue_snapshots` and `compaction_snapshots` are empty on every tenant).

| # | tenant | issues | rekey rows | migration trigger / captured stderr | dolt commit (UTC) |
|---|---|---|---|---|---|
| 1 | resume (canary) | 43 | 161 + 4 | `bd migrate --dry-run` **store-open** (see correction 1); stderr clean | 02:41:37 |
| 2 | livespec-orchestrator-git-jsonl | 34 | 260 + 16 | designated `bd migrate schema`; clean | 02:44:12 |
| 3 | livespec-driver-pi | 22 | 207 + 57 | designated; clean | 02:44:23 |
| 4 | livespec-driver-codex | 35 | 302 + 13 | designated; clean | 02:44:35 |
| 5 | livespec-runtime | 74 | 524 + 57 | designated; clean | 02:44:52 |
| 6 | dolt-server | 73 | 557 + 16 | designated; clean | 02:46:45 |
| 7 | livespec-driver-claude | 68 | 526 + 85 | designated; clean | 02:47:05 |
| 8 | homelab | 73 | 741 + 493 | designated; clean | 02:47:33 |
| 9 | openbrain | 368 | 1428 + 4 | designated; clean | 02:48:07 |
| 10 | livespec-console-beads-fabro | 302 | 2784 + 820 | designated; clean | 02:49:16 |
| 11 | livespec-dev-tooling | 555 | 3377 + 613 | designated; clean | 02:50:32 |
| 12 | livespec | 781 | 4687 + 1055 | designated; clean | 02:52:35 |
| 13 | livespec-orchestrator-beads-fabro | 886 | 8005 + 1766 | **unplanned store-open by `reconcile-runs.timer` at 02:50:00Z** (correction 2); stderr not captured; verify set PASS | 02:53:01 |
| 14 | livespec-overseer | 1009 | 10731 + 4830 | designated; clean | 02:58:51 |

"Clean" means the captured stderr of the migrating `bd` call held nothing but
the auto-backup warning bd v1.0.5 and v1.2.2 both emit on every command
(`register backup remote … command denied`), and neither stream contained
`invalid hash length`, `skip`, `warn`, `error` or `fail`.

## Phase 0 evidence

- Fleet paused: `overseerd` stopped by the maintainer; the overseerd-spawned
  `foreman-*` plan sessions plus `repo-gates-and-test-integrity` and
  `test-adequacy-gates` killed by PID on maintainer instruction; one `hp` Fabro
  run and its host dispatcher loop for `overseer-tdfe.19` killed by the
  maintainer; 0 established connections to `127.0.0.1:3307`; last tenant write
  02:24:19Z.
- Backup: `dolt-backup.service` re-triggered and finished 02:35:34Z exit 0 —
  after the last tenant write, so the S3 backup covers everything.
- `preflight-probe.sh` (now `bd-guard/test/preflight-probe.sh`): PASSED, all
  14 at v49, no rekey drift, 44,119 rekey rows.
- Baselines captured 02:39Z per tenant with the v1.0.5 `bd sql` (still safe
  pre-swap): all 28 table counts; twelve fingerprints; the full
  `bd list --status all --limit 0 --json`.

## Verify set (per tenant, after its migration)

1. Schema via **mysql**, not bd: `MAX(version) FROM schema_migrations` = 53.
2. All 28 table counts equal to baseline, except the three bd bookkeeping
   deltas that are the migration itself: `schema_migrations` 49→53,
   `ignored_schema_migrations` 8→11 (rows 9–11, the same delta the isolated
   rehearsal in `migration-behavioural-delta-2026-08-29.md` recorded), and
   `local_metadata` gaining bd's own version stamp.
3. Rekey completeness, two independent order-insensitive fingerprints
   (`CAST(SUM(CAST(CRC32(x) AS UNSIGNED)) AS CHAR)` and `BIT_XOR(CRC32(x))`)
   per table: the **id** fingerprint of each non-empty rekey table MOVED, and
   its **content-excluding-id** fingerprint was UNCHANGED. A silently skipped
   table (the dolt#11131 hazard in `rekey-silent-skip-hazard-2026-08-20.md`)
   would show an unmoved id fingerprint; none did.
4. `issues`, `dependencies`, `labels` content fingerprints unchanged.
5. `bd list --status all --limit 0 --json`: identical id set and identical
   per-item JSON to the v1.0.5 baseline — with list-valued fields compared as
   multisets, because the rekey rewrites dependency-row primary keys and
   v1.2.2 emits the `dependencies` array in a new order (first seen on
   `livespec-runtime`, four items; every element identical, order only).
6. `bd show <id> --json` is a one-element array; `bd comments <id> --json`
   count equals the baseline `comment_count` and every record carries `text`.
7. `preflight-probe.sh <repo>` with `EXPECTED_SCHEMA_VERSION=53` PASSED.

Final sweep: `EXPECTED_SCHEMA_VERSION=53 preflight-probe.sh` over all 14 —
PASSED, 44,119 rekey rows, identical to the pre-cutover total.

## Correction 1 — `bd migrate --dry-run` is NOT a preview

The runbook said `bd migrate --dry-run` "previews (no change)". It does not:
v1.2.2 migrates a v49 store **on open**, before the dry-run prints
`Dolt database version: 1.2.2 / ✓ Version matches`. Measured on the canary:
mysql read `MAX(version)` = 53 immediately after the dry-run, and `dolt_log`
carries `schema: apply migrations` at 02:41:37Z with the tenant SQL user as
committer. The canary was therefore migrated by the dry-run itself. The
procedure was corrected for the remaining 13: the single first contact is
`bd migrate schema 2>stderr.log`, and every pre-contact read goes through
mysql (`mysql --skip-ssl -h 127.0.0.1 -P 3307 -u <tenant-user> -D <db>`,
password from the tenant's env wrapper). Never use any `bd` verb as a
non-mutating probe against an un-migrated tenant once the binary is v1.2.2.

## Correction 2 — the quiescence list missed a root system timer

`reconcile-runs.timer` (system slice, `OnUnitActiveSec=10min`, fires at
:x0:00) runs `with-livespec-env.sh -- /usr/bin/python3 …/dispatcher.py
reconcile-runs --repo /data/projects/livespec-orchestrator-beads-fabro`. Its
02:50:00Z tick read this repo's Ledger with the freshly swapped binary and
auto-migrated the tenant (commit 02:53:01Z; the 02:40:00Z tick predated the
02:41:17Z swap and ran v1.0.5). The per-tenant driver's pre-contact mysql
check saw schema 53 at 02:52:41Z, refused to touch the tenant and STOPPED, as
designed; the full verify set then PASSED, including rekey completeness, so
the swallowed-stderr hazard did not bite.

Attribution came from the **sudo journal**: the env wrapper escalates through
`sudo`, so every wrapper invocation is logged with its `PWD` and
`_SYSTEMD_UNIT`. That journal is the right instrument for "who touched a
tenant" — a fleet-wide read of it for 02:41:17Z–03:03Z shows no other
unplanned contact on any tenant. (The 5-minute
`livespec-codex-cred-refresh.timer` also runs in this repo directory and
provably does not open the ledger: the tenant stayed v49 through its 02:42
and 02:48 ticks.)

The next fleet-pause checklist must include `systemctl list-timers --all` for
**both** the system and the user manager and stop `reconcile-runs.timer`.
Listing only user timers, and grepping the system list for backup units, is
an instrument aimed at the wrong population — the same trap the beads-trap
catalogue in `AGENTS.md` describes.

## Bookkeeping note

On tenants migrated by store-open (resume, this repo), `local_metadata` keeps
`bd_version = 1.0.5` and has no `bd_version_max` until the next bd command
stamps them. `bd migrate schema` writes both. This is bd's own bookkeeping,
not tenant data.

## Left open after this receipt

- `bd-ib-3kolea.2` human-only acceptance (FINAL GATE PASS verdict recorded
  2026-08-30, plus this receipt).
- Phase 4 image parity: `orchestrator-image/Dockerfile` `BD_VERSION=1.1.2`
  and its two shas, `orchestrator-image/README.md` lines describing v1.1.2,
  and `bd-guard/test/run-v1-1-2-candidate-tests.sh` pins are still v1.1.2 and
  must move to v1.2.2 (tarball `8140098a…321e8`, binary `54fc0e05…1e0e`).
  Factory-safe; routed as a child of the epic.
