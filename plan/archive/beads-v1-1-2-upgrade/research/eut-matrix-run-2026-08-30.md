# EUT harness build + matrix run (bd-ib-3kolea.3), 2026-08-30

**Thread:** `plan/beads-v1-1-2-upgrade/` · **Item:** `bd-ib-3kolea.3`
**Authorization:** maintainer, this session ("apply and start"), via the plan operation.

Builds the Enemy Unit Test harness for Beads and runs it across the
binary-and-schema matrix on an isolated server, mirroring the archived FabroPort
track. This is the durable delta artifact (Exit criteria 5) and the run record;
the ledger handoff on `bd-ib-3kolea` summarizes it (Exit criteria 6).

## The harness (Deliverable 2/3/4)

`beads-enemy-unit-tests/` at the repo root, mirroring `fabro-enemy-unit-tests/`:
- The Port is the existing 12-method `ShellBeadsClient` aimed at a candidate
  binary via `StoreConfig.bd_path` (no code change — `_build_argv` adds no
  connection flags). `conftest.py` constructs it DIRECTLY (never
  `make_beads_client`, which returns the fake) and asserts `config.fake is False`.
- `test_tier0_beads.py` (12): exactly-the-12-method surface + exclusion list, the
  four coercion contracts with non-empty fixtures, both `list` literal forms,
  `bd ready`/`bd stats` dead-vs-working, the seven lifecycle statuses + five
  `status.custom` entries + open→backlog/in_progress→active remap.
- `test_tier1_beads.py` (7): create/update/close, dep add+remove, comment
  (`text` key), two-step create normalization (never left at `open`), create
  stdout reports id, `--assignee ""` clearing, `--metadata` compared as PARSED
  structures.
- `compare.py` + `_comparison_report.py`: run tier0 twice (control vs candidate),
  read per-assertion pass/fail/skip from JUnit XML, classify the delta, render a
  Markdown artifact; exit 0 iff both legs exit 0 AND zero delta. Parameterized
  over (binary, store) by env / CLI args, incl. a per-leg database.
- `just` targets: `beads-enemy-tier0`, `beads-enemy-tier1`, `beads-enemy-compare`.

## The matrix run (all four cells)

Isolated Dolt `sql-server` 127.0.0.1:13307 (scratch data-dir, DOLT_ROOT_PATH
scratch, dummy isolated root password — NOT the family secret, so it cannot reach
any family tenant; family server on 3307 never addressed). Binaries by absolute
path, pins verified: v1.0.5 `463b7655…` (control, copied read-only from
`/usr/local/bin/bd-real`), v1.2.2 `54fc0e05…` (candidate, fetched + pin-checked).
Version-abort arm refused anything outside `{1.0.5, 1.2.2}`; v1.2.0/v1.2.1 never
fetched. v49 fixture: issues 7, events 8, comments 5.

| Cell | Binary × Schema | tier0 | tier1 | Note |
|---|---|---|---|---|
| control | v1.0.5 × v49 | 12/12 | 7/7 | schema stays v49; a red here would be a defective test |
| pre-migration | v1.2.2 × v49 | — | — | v1.2.2 migrates v49→v53 cleanly on contact |
| steady state | v1.2.2 × v53 | 12/12 | 7/7 | counts 7/8/5 preserved |
| **rollback** | **v1.0.5 × v53** | **REFUSED** | — | fail-closed (see below) |

**Delta (compare.py, tier0 control vs candidate): ZERO.** All 12 assertions
`unchanged`; both legs exit 0; 0 regressions / 0 improvements / 0 skip deltas /
0 pinned-only / 0 candidate-only. The Beads API surface livespec uses behaves
identically across v1.0.5 → v1.2.2. Control cells are green, so the new-version
verdict is admissible (Exit criteria 3).

**Rekey proven, not assumed:** events row-hash `a9802e16`(v49)→`8076e1d9`(v53),
comments `ef5c17e3`→`33095b48` — the CHAR(36) primary keys were rewritten; issues
unchanged; all counts identical. Data survived the migration intact.

## Rollback cell — the cutover's load-bearing verdict

**Binary downgrade is NOT a rollback path (CLOSED, proven).** v1.0.5 `bd list`
against a v53 store refuses: `schema version mismatch: database is at v53, binary
knows up to v49 (4 migrations ahead)`. Fail-closed — no silent read, no data
corruption. (An escape hatch `BD_IGNORE_SCHEMA_SKEW=1` exists but is not a
sanctioned rollback.)

Side finding: v1.0.5 `migrate status` on the v53 store WROTE the tracked
version-string metadata backward (`1.2.2 → 1.0.5`) — old-binary contact is a
WRITE, not read-only. It did NOT change `schema_migrations` (authoritative cursor
stayed v53) or the data (hashes unchanged), and v1.2.2 keeps operating the store
normally. This reinforces the AGENTS.md constraint: a leftover old binary that
touches a migrated tenant writes to it, so upgrade every clone.

**Consequence for the cutover:** plan it forward-only with backups as the
recovery path, NOT binary downgrade. This resolves the open question in
`cutover-plan-2026-08-29.md` — now proven rather than hypothesized.

## Two harness instrument fixes (corrections, not weakened assertions)

Both were the instrument reading the wrong key; the behaviour under test was
present. Exit criterion 7 forbids weakening an assertion to pass — these correct
the reader:
1. `_has_blocks_edge`: raw `bd show --json` inlines each dependency as the FULL
   target record plus a `dependency_type` field — the target id is `id` (NOT
   `depends_on_id`, the package projection's key) and the edge kind is
   `dependency_type` (NOT `type`). Verified live against both binaries.
2. `compare.py`: added a per-leg `--pinned-database`/`--candidate-database` so the
   two legs (different isolated databases) each pass the tenant-match check.

## Isolated-run guard compliance

Never v1.2.0/1.2.1 (version-abort arm, did not fire); checksums verified before
invocation; scratch data-dir with no `.beads`/`.git` at or above it; the family
password absent from the environment (a dummy isolated password was used, which
cannot authenticate to a family tenant); family endpoint 3307 never addressed;
fresh scratch databases (the migrated store is a byte-identical clone of the v49
fixture, never a tenant copy); `/usr/local/bin` untouched (binaries by absolute
path); teardown by PID (never `pkill -f`), port and scratch confirmed absent.
