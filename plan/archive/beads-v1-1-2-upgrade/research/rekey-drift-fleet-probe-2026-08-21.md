# The re-key drift hypothesis, tested against all 14 live tenants

**Date:** 2026-08-21
**Tests:** the hypothesis left explicitly untested by
`rekey-silent-skip-hazard-2026-08-20.md`
**Result:** **FALSIFIED** — no tenant carries the drift signature today
**Read-only.** Every statement below is a `SELECT`, issued through `bd sql`
under each tenant's own credential wrapper. Nothing was written, nothing
installed, and no v1.2.x binary was run against any tenant.

## The hypothesis being tested

The 2026-08-20 hazard note established that the v1.0.5 → v1.2.2 upgrade runs
`rekeyAuxRowIDs`, which rewrites the CHAR(36) primary keys of `events`,
`comments`, `issue_snapshots` and `compaction_snapshots` — and that on
dolthub/dolt#11131 schema-encoding drift it **skips the affected table, logs
three lines, and lets `MigrateUp` exit 0**.

It then advanced a hypothesis, correctly flagged as a hypothesis:

> the drift signature concerns a TEXT/LONGTEXT column whose storage-encoding tag
> was re-derived without rewriting rows, and migration 0049 — which SHIPS IN
> v1.0.5, so our tenants have ALREADY RUN IT — does exactly that shape of MODIFY
> COLUMN, and its header names `comments.text`. `comments` is one of the four
> re-keyed tables. The shapes match; Dolt internals and live tenant state were
> NOT examined.

If true, our tenants would already be carrying the drift, and the real migration
would silently skip `comments` on live user data while reporting success.

## Leg 1 — the shape does match, exactly

`internal/storage/schema/migrations/0049_longtext_large_content_columns.up.sql`
at v1.2.2 ends with:

```sql
'ALTER TABLE comments MODIFY COLUMN text LONGTEXT NOT NULL'
```

And `auxRekeyTables` in `internal/storage/schema/aux_row_id_backfill.go` re-keys
`comments` by reading:

```go
{name: "comments", columns: "issue_id, author, text, CAST(created_at AS CHAR)"},
```

So the converted column **is** one of the columns the re-key reads. The
hypothesis was well-aimed: this is the right table and the right column.

## Leg 2 — but the drift predicate is not a column-type check

This is where the hypothesis's mechanism comes apart. The skip is not triggered
by a column's declared type; it is triggered by a **storage decode failure**,
detected by string match on the error text:

```go
func isSchemaEncodingDriftErr(err error) bool {
	if err == nil {
		return false
	}
	return strings.Contains(strings.ToLower(err.Error()), "invalid hash length")
}
```

A `MODIFY COLUMN … LONGTEXT` is therefore **not sufficient** to cause the skip.
What matters is whether any cell, as actually stored, fails to decode. "The
shapes match" was a reason to go and measure, not a finding — and measuring is
what settles it.

## Leg 3 — the measurement: zero drift, fleet-wide

For each tenant, a query forcing a decode of **exactly the columns
`auxRekeyTables` names**, copied verbatim from the v1.2.2 source:

```sql
SELECT COUNT(*), COALESCE(SUM(LENGTH(CONCAT_WS('|', <the re-key's columns>))),0)
FROM <table>;
```

`LENGTH(CONCAT_WS(...))` forces every selected cell to be materialised, so a
cell Dolt cannot decode raises rather than being optimised away.

**All 14 live server tenants returned clean. Not one produced `invalid hash
length`.**

| Tenant | `events` | `comments` |
|---|---:|---:|
| livespec-overseer | 5,758 | 1,850 |
| livespec-orchestrator-beads-fabro | 5,152 | 748 |
| livespec | 4,459 | 876 |
| livespec-dev-tooling | 3,247 | 459 |
| livespec-console-beads-fabro | 1,947 | 384 |
| homelab | 2,085 | 124 |
| openbrain | 1,428 | 4 |
| dolt-server | 544 | 15 |
| livespec-runtime | 468 | 13 |
| livespec-driver-claude | 378 | 54 |
| livespec-orchestrator-git-jsonl | 252 | 15 |
| livespec-driver-pi | 205 | 44 |
| livespec-driver-codex | 238 | 4 |
| resume | 161 | 4 |
| **total** | **26,322** | **4,594** |

**Scope, stated because an absence claim requires it.** The population is every
`.beads/config.yaml` under `/data/projects` declaring `mode: server` — 14
tenants, matching the count AGENTS.md records. The eleven family tenants were
probed through `with-livespec-env.sh`; the three **independent** tenants
(`homelab`, `openbrain`, `resume`) refused the family wrapper with
`Error 1045 Access denied` — which is the tenant isolation working — and were
re-probed through their own `with-<project>-env.sh` wrappers. One further
directory, `homelab-05-nixrepro-tree`, has no beads database and is not a
tenant. **90.6 MB of `events` and 11.3 MB of `comments` content was decoded in
total.**

The decoder is the **Dolt server, not the client**: `dolt_version()` reports
**2.1.4**. That is what makes a v1.0.5-client probe valid evidence about what a
v1.2.2-client re-key would read — both drive the same server-side decode.

## Leg 4 — the cost, now measured rather than extrapolated

The hazard note measured `comments` on one tenant and said "the comments loop is
hundreds of statements", flagging `events` as unmeasured and largest by
construction. That is now measured, and the correction is large:

- **30,916 rows would be rewritten fleet-wide**, one `UPDATE` per row.
- **`events` is 85.1% of that** (26,322 rows) — so the table that was unmeasured
  is the one that dominates.
- **`issue_snapshots` and `compaction_snapshots` are EMPTY on all 11 family
  tenants.** Two of the four re-keyed tables are no-ops here, which shrinks the
  blast radius of the hazard by half in table terms while leaving it untouched
  in row terms.

The single largest tenant is `livespec-overseer` at 7,608 rows, not this repo.

## The method itself was controlled, because it was reasoning until it wasn't

Everything above rests on one assumption: that
`SUM(LENGTH(CONCAT_WS(...)))` forces every selected cell to **materialise**, so
a cell Dolt cannot decode raises instead of being optimised away. That was
stated as fact in the first draft of this note. It was **reasoning, not
measurement** — exactly the shape this repo's Verification discipline warns
about, and it sits directly under the day's central claim, so it was
subsequently controlled.

**Control 1 — the arithmetic reconciles.** On `livespec-driver-codex`
(4 comments), per-row component lengths:

| `issue_id` | `author` | `text` | `created_at` | +3 separators | row total |
|---:|---:|---:|---:|---:|---:|
| 25 | 13 | 854 | 19 | 3 | 914 |
| 25 | 13 | 954 | 19 | 3 | 1014 |
| 28 | 13 | 2619 | 19 | 3 | 2682 |
| 25 | 13 | 34 | 19 | 3 | 94 |

914 + 1014 + 2682 + 94 = **4,704**, which is exactly what the probe reported for
that tenant. So the number is the real sum of real field lengths, not an
artifact.

**Control 2 — the decisive one, because `LENGTH` alone is not proof.** A
skeptic's objection survives Control 1: for a `TEXT`/`LONGTEXT` column stored
out-of-line, a *length* might be answerable from a stored header without ever
decoding the content. So the second control uses a function that **cannot** be
answered from metadata — a content hash — and compares it across two
independent code paths:

- the **SQL path** computed `MD5(text)` for two comments;
- the **JSON path** (`bd comments --json`, through the package client, a
  different code path entirely) returned those comments' text, which was hashed
  in Python.

```
019f273b-d1c9-79a3…   len sql=854  json=854   md5 MATCH
019f3a8a-9eea-7130…   len sql=954  json=954   md5 MATCH
```

An MD5 requires reading every byte. Both hashes match across the two paths, and
both lengths agree. **The SQL path genuinely decoded the stored bytes**, so the
probe's clean result is a real decode of every cell the re-key reads — not a
metadata read that would have returned "clean" whether or not the content was
readable.

This is the difference between a probe that *would* have caught the drift and
one that merely *reported* no drift. Without Control 2 the two are
indistinguishable from the output.

## What this does and does not establish

**ESTABLISHES.** The specific hazard the hypothesis named is **absent from every
live tenant as of 2026-08-21**. Migration 0049's TEXT→LONGTEXT conversion, which
every tenant has already run, has **not** left rows that Dolt 2.1.4 cannot
decode. The silent-skip path is real in the code but has no live trigger here
today, so the attended window is not walking into a known-present fault.

**DOES NOT ESTABLISH.**

1. **This is a point-in-time reading of live databases, not a guarantee.** The
   tenants are actively written: `events` on this repo's tenant went 5,147 →
   5,152 *during the sweep*, from this session's own ledger writes. A clean read
   today says nothing about the storage state at the moment the migration runs.
2. It does not make the silent-skip acceptable. The degrade-don't-abort choice
   and the swallowed stderr (see `rekey-silent-skip-hazard-2026-08-20.md`) are
   unchanged; this only shows the trigger is not currently pulled.
3. It does not test the re-key code path itself. It reproduces the re-key's
   `SELECT` column list against the same server, which is why it is evidence —
   but no v1.2.x binary was run.

## The actionable consequence

Because the result is point-in-time, its value is not "we are safe" — it is
**that a cheap, decisive pre-flight check exists**. The probe runs in seconds
per tenant, needs no installation, and returns a hard binary answer.

**Recommendation: run this probe as a pre-flight gate inside the attended
window, immediately before the migration, and treat a non-clean result as a
stop.** That converts the hazard from an unbounded unknown discovered afterwards
in a log nobody reads into a checked precondition.

**The probe is committed as `bd-guard/test/preflight-probe.sh`** (it lived beside this note until the 2026-08-31 cutover, then moved so the plan archive would not take it) — an earlier
draft of this paragraph left the scripts in session scratch and said they were
"small enough to re-author", which is exactly how a recommended control quietly
fails to exist. It also folds in the schema-version assertion and the
`dolt_remotes` reading from `remote-migrate-gate-does-not-fire-2026-08-21.md`,
runs one query per tenant so it is fast enough to actually be run inside the
window, and fails closed: a tenant that gives no verdict exits 2 rather than
passing. Its column lists must stay in lockstep with `auxRekeyTables`, which is
why that requirement is restated in the script's own header.

This is recorded as a finding with a disposition, not as a new maintainer
question. It bears on `bd-ib-ao3j` (the attended rehearsal) and `bd-ib-3kolea.2`
(the final gate); nothing was applied to either, since both are `admission:manual`
and this session held an admission only on `bd-ib-3kolea.4`.

## Incidental finding, recorded because it touches a sibling child

Every `bd sql` invocation emits:

```
Warning: auto-backup failed: register backup remote: add backup backup_export:
Error 1105 (HY000): command denied to user '<tenant>'@'%'
```

The per-tenant SQL user's DB-scoped grant does not carry the privilege `bd`'s
auto-backup wants, so that auto-backup is failing on every call, warning on
stderr, and exiting 0 — the same swallow-on-zero-exit shape recorded in the
hazard note. This is **not** a claim that our backups are broken:
`bd-ib-3kolea.1` (backup-layer preflight) closed `resolution:completed` against
three deliberate backup layers, and this is `bd`'s own opportunistic extra.
Recorded so whoever holds that item can decide whether the warning should be
silenced or the grant widened.
