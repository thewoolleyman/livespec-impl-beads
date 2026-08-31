# The migration behavioural delta: v1.1.2 vs v1.2.2 on identical v49 data is EMPTY

**Date:** 2026-08-29
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Item:** `bd-ib-3kolea.4` (the retarget) — criterion 3
**Authorization:** maintainer, this session, via the `plan` operation picker
("Authorize isolated-server run"). Compliance with the thread's ten standing
isolated-run guards recorded at the end.

## What criterion 3 needed that was not yet measured

`bd-ib-3kolea.4` criterion 3 asks the "same code as v1.1.2" claim for v1.2.2 to
be verified **behaviourally** rather than accepted: "A non-empty delta
invalidates the premise." The EUT-harness route is gated (harness is
`bd-ib-3kolea.3`, backlog P0; the `compare.py` hole is `bd-ib-282r`), so the
plan thread's standing next action was an isolated-server run as the
alternative route.

Prior runs had already established the adjacent facts, and it matters to state
what they did and did NOT cover so this run is not mistaken for a repeat:

- `server-mode-sql-probe` / `rig-blindness-mechanism`: **fresh** v1.1.2 and
  v1.2.2 databases both land at schema **v53** with identical schema, and all
  SQL projections behave identically. That exercises migrations 0050–0053 on an
  EMPTY database.
- The source-level compare (on `bd-ib-3kolea.4`): v1.1.2…v1.2.2 is 7 commits,
  180 files, **zero migration files changed**.

What none of that tests is the one thing criterion 3's "same code" is really
about for an UPGRADE: applying migrations 0050–0053 to **existing v49 data**,
where `rekeyAuxRowIDs` rewrites the CHAR(36) primary keys of four tables
(`events`, `comments`, `issue_snapshots`, `compaction_snapshots`;
`rekey-drift-fleet-probe-2026-08-21.md`). A fresh-DB comparison cannot see a
data-transformation divergence because there is no data to transform. This run
supplies exactly that missing leg.

## Design — one v49 fixture, two byte-identical clones, one migrator each

1. Isolated Dolt `sql-server` at `127.0.0.1:13307`, scratch data-dir, own
   socket, user `root` (no password), started by absolute-path
   `/usr/local/bin/dolt` (2.1.4). Owned by my `ubuntu` PID, never the family
   `dolt`-user server on 3307.
2. Seed a deterministic v49 fixture in database `o4fix` via the installed
   **v1.0.5** `/usr/local/bin/bd`: 8 issues, 8 comments, labels, one
   dependency, plus updates/close/reopen. Result at v49: `issues` 8,
   **`events` 15**, **`comments` 8**, `issue_snapshots` 0,
   `compaction_snapshots` 0 (the last two are no-ops on real tenants too, per
   the rekey-drift note — the fixture matches production shape). Baseline
   captured as per-table canonical row-set hashes.
3. Stop the server; `cp -r data/o4fix` → `data/o4a` and `data/o4b`. Verified
   **byte-identical** (`diff -rq` clean, both directions). Restart.
4. Migrate `o4a` with **v1.1.2** and `o4b` with **v1.2.2**. (Note: merely
   connecting with the newer binary triggers the migration — the same
   "connecting migrates" mechanism the v1.2.1 landmine warns about — so both
   reached v53 on first contact; `bd migrate` then confirmed idempotent at
   v53, exit 0.)
5. Dump both with a **single consistent reader** (the v1.2.2 binary, which
   knows v53 and will not re-migrate an already-v53 database) so the reader
   cannot introduce a difference. Compare per-table: schema column set +
   canonical (sorted) row-set hash.

## Result — the delta is empty

Diffing the two full dumps returns exactly **one** differing line, and a
control resolves it to wall-clock:

- Every other table is identical, including all four rekey tables
  (`events` `ba60d2d8`, `comments` `115e64bb`, both empty tables), `issues`,
  `schema_migrations`, `dependencies`, `labels`, `metadata`, `config`,
  `local_metadata`, and every schema column-hash.
- The lone difference is `ignored_schema_migrations`, whose rows 9–11 (the
  v50→53 span) carry **identical `version` and `content_hash`**
  (`3d1ee4f9…`, `59d66446…`, `0efade0e…`) under both binaries and differ only
  in the `applied_at` datetime — o4a at 05:01:42–43Z, o4b at 05:02:02Z, i.e.
  the second each migration happened to run. **Control:** re-hashing that table
  with `applied_at` normalized to a constant makes the two **identical**
  (`c66fa7f430b8b82e` both). The diff is timing, not behaviour.

That the rekey did real work is proven, not assumed: `events` moved from the
v49 baseline hash `e33b947a` to `ba60d2d8` and `comments` from `cc7b02b6` to
`115e64bb` — the CHAR(36) primary keys were rewritten — and both binaries
rewrote them to the **same** values. `issues` (not a rekey target) is unchanged
from v49 (`fd47df56`) in both.

## Conclusion for criterion 3

The behavioural delta between v1.1.2 and v1.2.2, on the actual v1.0.5→v53
upgrade path applied to real data including the `rekeyAuxRowIDs`
transformation, is **empty** apart from the wall-clock migration timestamp that
cannot be otherwise. Criterion 3's failing condition — "a non-empty delta
invalidates the premise" — did not occur. The "same code as v1.1.2" claim for
v1.2.2 is now verified behaviourally, not merely trusted at source level.

## What this does NOT establish (honest scope)

- The fixture's `issue_snapshots` / `compaction_snapshots` are empty (as they
  are on real tenants), so the rekey of those two of the four tables is not
  exercised by data here. The rekey-drift note already records those as no-ops
  on live tenants; the two populated rekey tables (`events`, `comments`) are
  the load-bearing ones and both matched.
- This is a synthetic isolated fixture, not any family tenant. It proves the
  migration CODE behaves identically across the two binaries; the live cutover
  still gets its own pre-flight (`bd-guard/test/preflight-probe.sh`) against the real tenant
  at cutover time, which remains point-in-time by design.

## Guard compliance (ten standing isolated-run guards)

1. **Never v1.2.0 / v1.2.1** — only v1.1.2 and v1.2.2 fetched; version-checked
   before any DB contact with an abort arm for anything outside
   `{1.0.5, 1.1.2, 1.2.2}` (did not fire).
2. **Checksums before invocation** — v1.1.2 tarball `a72d71ed…` / binary
   `6d767629…d9a82`; v1.2.2 tarball `8140098a…321e8` / binary
   `54fc0e05…1e0e`; all four matched the recorded pins as a hard abort arm.
   Versions `20e493e56` / `6c124203e` confirmed.
3. **Isolation** — scratch under the session scratchpad; no `.beads` or `.git`
   at or above it (scanned to `/`); not inside a git repo.
4. **Outside the credential wrapper** — `BEADS_DOLT_PASSWORD` 0 bytes at start,
   throughout, and after; `LIVESPEC_BD_PATH` unset. The probe could not have
   authenticated to a family tenant.
5. **No family endpoint** — isolated server on port 13307, own scratch
   data-dir; family server on 3307 never addressed.
6. **Fresh scratch databases** — created for this probe, never a copy of a
   tenant. The two migration targets are byte-identical clones of the
   synthetic v49 fixture.
7. **`/usr/local/bin` untouched** — binaries invoked by absolute path; guard
   entry point `/usr/local/bin/bd` hashes to `5f55fbfb…4637a3` before AND
   after (unchanged). `bd init` was run only inside the isolated scratch client
   dir, never in a checkout or worktree.
8. **Per-verb receipts** — fetch, migrate, and dump transcripts under
   `plan/beads-v1-1-2-upgrade/…/receipts` (session scratchpad copy at
   `mig-delta-receipts`).
9. **Each table named individually** — see the per-table equality table above.
10. **Teardown by absence** — isolated server killed by PID (never `pkill -f`);
    13307 clear; scratch databases and binaries deleted and confirmed absent;
    only the family `dolt`-user server (PID 3285864, started Jul 21) remains.

### One gap vs prior runs, disclosed

Prior runs computed a before/after content hash of the family tenant's ~710
records to prove non-interference positively. This run did not compute that
hash. The fail-closed proof here is structural rather than differential:
`BEADS_DOLT_PASSWORD` was absent at every instant (measured), so the probe
could not authenticate to the family server, and the guard-entry pin and family
server identity are unchanged before/after. No probe command addressed 3307.
