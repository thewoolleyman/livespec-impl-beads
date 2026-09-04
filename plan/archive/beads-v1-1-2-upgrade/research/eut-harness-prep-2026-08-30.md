# EUT harness (bd-ib-3kolea.3) prep: reversible groundwork before the attended matrix run

**Date:** 2026-08-30
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Item:** `bd-ib-3kolea.3` (Enemy Unit Test harness / BeadsPort matrix)
**Status of this note:** PREP ONLY. It mutates no host, installs no binary, runs
no `bd` matrix, and edits no ledger item. It exists so the maintainer can review
the corrected plan **before** the attended real-binary run is authorized. The
maintainer chose this "prep first, then run" path on 2026-08-30.

## Why this item is the right verification-first pick

`bd-ib-3kolea.3` builds the harness; `bd-ib-3kolea.2` (final gate) RUNS it at
cutover time. Crucially, **`3kolea.3`'s fourth matrix cell IS the cutover's one
genuinely open question** — whether a v1.0.5 binary can open a migrated store
(`cutover-plan-2026-08-29.md` line 76+). Building it is what lets the maintainer
rule on rollback posture (forward-only+backups vs. block-on-downgrade-proof).
So the verification track directly unblocks the cutover decision.

Its two shared blockers are both closed: `bd-ib-3kolea.1` (backup preflight) and
`bd-ib-8azd` (rehearsal package). It is unblocked. It is NOT factory-safe: the
live projection flags it `mutates-host-machinery` with `human-only` acceptance,
so it is an attended in-session build+run, the same class as the `3kolea.4`
isolated-server migration-delta run the maintainer authorized in-session on
2026-08-29.

## 1. Matrix retarget: v1.1.2 -> v1.2.2 (corrects the description's Deliverable 3)

The description's Deliverable-3 table still names **v1.1.2**, from before the
epic retargeted to v1.2.2 (`bd-ib-3kolea.4`, closed). The acceptance criteria
are already version-agnostic (they say "base binary against base schema",
"an older binary opens a migrated store"), which is correct and should stay so —
`3kolea.2` re-resolves the target at cutover time. Only the description table is
stale. Corrected matrix:

| Binary | Schema | What it proves |
|---|---|---|
| v1.0.5 | v49 | the control — a red here is a defective test, not a finding |
| v1.2.2 | v49 | pre-migration compatibility (new binary, old schema) |
| v1.2.2 | v53 | post-migration steady state |
| **v1.0.5** | **v53** | **the rollback path — the load-bearing open question** |

Schema facts (from `migration-behavioural-delta-2026-08-29.md`): v1.0.5 sits at
schema **v49**; migrations 0050-0053 land at **v53**; both v1.1.2 and v1.2.2
reach v53 and produce a **byte-identical** result including the four
`rekeyAuxRowIDs` tables (empty delta apart from a wall-clock timestamp). So the
retarget is safe: the old v1.1.2 rows re-label to v1.2.2 with no behavioural
change, already proven. The v1.2.1 landmine migrates v53 -> **v65**; it must
never be installed.

**Safety invariant to bake into the matrix:** the harness fetches/runs ONLY
`{v1.0.5, v1.2.2}`. Any binary version outside that set is a hard abort arm
before any DB contact. Recorded pins (from the 2026-08-29 run): v1.2.2 tarball
`8140098a...321e8`, binary `54fc0e05...1e0e`, version `6c124203e`; v1.0.5 is the
installed `/usr/local/bin/bd-real` (`463b7655...4486`), copied READ-ONLY and
hash-verified, never displacing the guard at `/usr/local/bin/bd`.

## 2. Deliverable 2 (BeadsPort) surface verification -- verify-and-close-gaps

The 12-method `BeadsClient` protocol (`_beads_client.py:87`) plus `ShellBeadsClient`
(`:184`) already IS the thin proxy the item wants, and already accepts an
arbitrary binary: `_build_argv` composes `[config.bd_path, *verb_args]` with NO
connection flags (`_beads_client.py:190-192`), and `bd_path` is a `StoreConfig`
field (`types.py:145`). So pointing the harness at a candidate binary is
construction data, not a code change. Confirmed.

**The one concrete gap, and it changes a criterion.** The Deliverable-1 usage
inventory table (`eut-usage-inventory.md:60-72`) lists **11** methods and OMITS
`remove_dependency` (`bd dep remove`). But `remove_dependency` is a real
protocol method (`_beads_client.py:149`, impl `:290`) with a live consumer at
`commands/_plan_disposition.py:99`. The source surface is **12 methods**. A
harness built from the inventory table alone would ship `bd dep remove`
uncovered. Criterion 1 currently says "exactly the inventoried BeadsClient
surface -- the eleven methods"; that count is wrong and must become **twelve**,
naming `bd dep remove` explicitly.

**No over-exposure.** All 12 methods have >=1 live consumer, so "exactly the
inventoried surface, no more" is satisfiable; nothing dilutes the gate. The
twelve: `list_issues`, `show_issue`, `list_comments`, `children`, `exists`,
`create_issue`, `update_issue`, `close_issue`, `remove_dependency`,
`add_dependency`, `add_comment`, `register_custom_statuses`.

**Unrouted call sites are all shell** (no Python bypasses the client):
- `bd-guard/bd-guard.sh` -- the leader and the strongest EUT target. It parses
  `bd create` stdout for the new id and its status-forcing follow-up is
  fail-open (Deliverable 4 assertion 3). Route it via a shell-level assertion
  against the guard's own create-normalization, not through the Python Port.
- `orchestrator-image/acceptance-live-golden-master.sh`, `build-and-verify.sh`,
  `real-work-dispatch.sh` -- direct bd calls in embedded throwaway ledgers.
- `plan/beads-v1-1-2-upgrade/rehearsal-package/wrappers/*` -- already implement
  the arbitrary-binary invocation the harness reuses.
Each must be routed or justified per criterion 1.

**Proposed exclusion list** (client never calls these; tie to a scope deferral):
`ready`, `init`, `version`, `migrate`, `doctor`, `export`, `bootstrap`,
`config get` (only `config set` is used), `reopen`, `defer`, `create-prefix`,
`search`, `label`, `delete`. Caveat: `bd ready` and `bd init` are heavy
prose-surface verbs; cover them "only to the depth prose promises" (Deliverable
4 assertion 8), and note `bd migrate`/`bd bootstrap` are exercised by the shell
rehearsal/image scripts, not the client.

## 3. House pattern to mirror (FabroPort, archived and worked)

Copy the layout of `plan/archive/fabro-enemy-unit-tests/` and the `fabro-enemy-unit-tests/`
code tree directly:
- A `beads-enemy-unit-tests/` directory at the repo root (OUTSIDE `tests/`, so
  the hermetic `just check` aggregate never needs a live server).
- `test_tier0_*.py` (reads/asserts, no mutation, no live multi-tenant server) and
  `test_tier1_*.py` (create/update/close/dep/comment against throwaway stores;
  the guard create-normalization round-trip), separated by filename and run by
  distinct `just` targets (mirror `fabro-enemy-tier0/tier1/compare` in the
  `justfile`).
- `conftest.py` with env-parameterized fixtures: a `config` fixture reading
  `BEADS_EUT_BIN` / store target from the environment, and a `port` fixture
  constructing `ShellBeadsClient` directly (never `make_beads_client`, which
  returns the fake) -- parameterization as a constructor argument, exactly the
  FabroPort mechanism (`conftest.py:18-40` there).
- `compare.py` + `_comparison_report.py`: run tier-0 twice (control binary vs
  candidate), read per-assertion pass/fail/skip from JUnit XML, classify each as
  unchanged / candidate-only / pinned-only / skip-delta / regressed / improved,
  render a Markdown delta. The verdict consults the rendered delta, not just
  pytest exit codes (a skip = a capability present in one binary, absent in the
  other). The delta artifact IS the upgrade risk assessment (Exit criterion 5).

## 4. The rollback cell -- design it honestly, do not paper it over

`qualification.md` (lines 147-166) records the copy-a-store-and-edit
`.beads/.local_version` shortcut and explicitly disclaims it: no real
v1.0.5-created tenant, so it is NOT a rollback proof. The honest rollback cell:
1. Seed a real v49 store with the **v1.0.5** binary (the migration-delta
   fixture recipe: issues/events/comments so `rekeyAuxRowIDs` has data).
2. Clone it; migrate the clone to v53 with **v1.2.2**.
3. Point the **v1.0.5** binary at the migrated (v53) clone and attempt the read
   surface. Record exactly what happens -- clean read, refusal, or corruption.
That verdict is what the cutover rollback-posture ruling needs. Until it exists,
`cutover-plan-2026-08-29.md` stands: plan cutover forward-only with backups.

## 5. Isolated-store test plan and the ten standing safety guards

Tier-1 and matrix runs use an isolated Dolt `sql-server` on `127.0.0.1:13307`
(scratch data-dir, own socket, `root`/no-password, absolute-path
`/usr/local/dolt`), never the family server on 3307, run OUTSIDE the credential
wrapper (`BEADS_DOLT_PASSWORD` 0 bytes throughout, so it cannot authenticate to
a family tenant). Enforce all ten standing guards from the 2026-08-29 run
(`migration-behavioural-delta-2026-08-29.md` lines 106-135): never v1.2.0/1.2.1
with a version-abort arm; checksums before invocation; isolation with no `.beads`
or `.git` at/above the scratch dir; outside the wrapper; no family endpoint;
fresh scratch databases (never a tenant copy); `/usr/local/bin` untouched
(absolute-path invocation; guard-entry hash unchanged before/after); per-verb
receipts; each table named individually; teardown by absence (kill by PID, never
`pkill -f`; confirm port clear and scratch deleted).

## Proposed ledger edits (NOT yet applied -- for maintainer review)

1. **Description Deliverable 3**: replace the v1.1.2 matrix rows with the v1.2.2
   matrix above; add the never-v1.2.0/1.2.1 invariant and the checksum pins.
2. **Acceptance criterion 1**: "the eleven methods" -> "the twelve methods",
   naming `bd dep remove` (`remove_dependency`) as the omitted-by-inventory verb.
3. **Deliverable 1 note / criterion 1**: record the inventory-table omission of
   `remove_dependency` as the concrete gap Deliverable 2 closes.

The version-agnostic wording of the other criteria is deliberate and stays.

## What remains gated (the attended run) and next action

The reversible prep above is complete. The attended real-binary matrix run
(build `beads-enemy-unit-tests/`, seed fixtures, run v1.0.5/v1.2.2 across the
matrix on the isolated server, record the delta) is host-mutating and needs a
maintainer go-ahead plus an attended window. NEXT ACTION: maintainer reviews
this prep and the three proposed ledger edits; on approval, apply the edits and
begin the attended build+run under the ten guards. The rollback cell's verdict
then feeds the cutover rollback-posture ruling.
