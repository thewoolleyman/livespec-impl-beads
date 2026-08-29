# Cutover plan: executing the v1.0.5 → v1.2.2 upgrade (PLAN ONLY — not authorized to run)

**Date:** 2026-08-29
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Epic:** `bd-ib-3kolea`

This synthesizes the epic's qualification work into a concrete, ordered cutover
procedure so the maintainer can review and authorize it. **It executes nothing.**
The cutover is host-mutating against the live shared multi-tenant server with the
v1.2.1 schema-v65 landmine live; it is deferred pending explicit authorization
and its own implementation children.

## Preconditions (must ALL hold before cutover starts)

1. **`bd-ib-3kolea.2` (FINAL GATE) passed** — sandbox-test the targeted release
   against the livespec API surface. Maintainer-directed to run last; a failure
   blocks the cutover. Nothing below proceeds until this is green.
2. **Qualification discharged** — done: `bd-ib-3kolea.4` closed (retarget to
   v1.2.2 decided; provenance verified; migrations 0050–0053 confirmed as the
   only crossed span; v1.2.2 same-code-as-v1.1.2 proven behaviourally by the
   2026-08-29 isolated-server migration-delta run — the migration is
   byte-identical across binaries including the four `rekeyAuxRowIDs` tables).
3. **Backup currency** — `bd-ib-3kolea.1` (backup-layer preflight) closed;
   re-verify immediately before cutover, because tenants are live.

## The two hard constraints, from AGENTS.md and the rekey research

- **NEVER install v1.2.0 or v1.2.1.** Running the v1.2.1 binary even once
  migrates a shared tenant from schema v53 to v65, stranding every v1.1.2/v1.2.2
  client. v1.2.1 is still downloadable (marked prerelease, not withdrawn). The
  target is **v1.2.2** only; verify every fetched artifact against the recorded
  pins (tarball `8140098a…321e8`, binary `54fc0e05…1e0e`, version `6c124203e`)
  as a hard abort arm.
- **Upgrade EVERY clone and host binary before recovering anything.** A single
  leftover old/hazard binary that later touches a tenant silently re-migrates it.
  Enumerate every consumer first (this repo and the sibling clones; the guard
  delegate `/usr/local/bin/bd-real` behind the `/usr/local/bin/bd` lifecycle
  guard; `LIVESPEC_BD_PATH` if set).

## The rekey hazard, and why the preflight is per-tenant and point-in-time

The v1.2.x migration runs `rekeyAuxRowIDs`, which rewrites the CHAR(36) primary
keys of `events`, `comments`, `issue_snapshots`, `compaction_snapshots`. On
dolthub/dolt#11131 storage drift it SKIPS a table, logs three lines, and exits 0
— and our client discards that stderr on a zero exit, so a partial re-key passes
silently (`rekey-silent-skip-hazard-2026-08-20.md`). `preflight-probe.sh` is the
control: per tenant it reads `MAX(version)` (anything ≥65 is the landmine, live),
forces a decode of exactly the `auxRekeyTables` columns to surface any
"invalid hash length", and counts the rows the re-key would rewrite. It is
READ-ONLY and must be re-run immediately before the migration on each tenant,
because the reading is point-in-time on a live store.

## Ordered procedure (to be split into implementation children)

1. **Freeze / announce.** Coordinate a window; the shared server has ~14 tenants
   and several concurrent sessions. A mid-cutover write by an un-upgraded client
   is the failure mode.
2. **Fetch + verify v1.2.2** once; stage the verified binary.
3. **Per-tenant preflight** (`preflight-probe.sh`) across every tenant on the
   shared server; abort the whole cutover if any tenant reads schema ≠ expected
   baseline or shows rekey drift.
4. **Upgrade every binary** — the guard delegate and every clone's resolved `bd`
   — to v1.2.2, by absolute path, verifying the pin after each. Never `bd init`
   in a checkout/worktree.
5. **Migrate the shared server tenants** with the single designated v1.2.2
   migrator. Capture and CHECK stderr (do not trust exit 0); confirm each tenant
   reaches v53 and that `rekeyAuxRowIDs` rewrote every non-empty target table
   (the migration-delta run's method — per-table row-set hashes — is the check).
6. **Verify** the family API surface post-migration on each tenant (the
   `bd-ib-3kolea.3` harness, when it exists, or the discharged behavioural
   evidence in the interim).
7. **Record** the cutover receipt (per-tenant before/after schema + rekey
   verification) durably on the epic.

## Rollback — the one genuinely open question

The migration-delta run proved the FORWARD path is clean and identical across
binaries. It did NOT establish that a v1.0.5 binary can open a v53-migrated
store — that is `bd-ib-3kolea.3`'s matrix rollback cell (v1.0.5 binary / v1.1.2+
schema), still unbuilt, and `qualification.md`'s copy-and-edit-`.local_version`
technique is explicitly NOT a real rollback proof. **So plan the cutover as
forward-only with backups as the recovery path, not binary downgrade**, unless
the rollback cell is built and proves downgrade-open first. This is the single
most important thing for the maintainer to weigh before authorizing.

## What this phase needs from the maintainer

- Authorization to mutate the shared server and every host/clone binary.
- A ruling on rollback posture (forward-only + backups, vs. block cutover until
  `bd-ib-3kolea.3`'s rollback cell proves downgrade-open).
- The window, given fleet concurrency.

Only then should implementation children be filed (they are NOT filed here; this
is the scope, not the admission).
