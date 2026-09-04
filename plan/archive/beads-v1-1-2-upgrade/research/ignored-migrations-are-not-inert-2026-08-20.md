# The `ignored/` migrations are NOT inert, and one of them rewrites primary keys

Measured 2026-08-20 against upstream `gastownhall/beads` at tags `v1.0.5` and
`v1.2.2`. This note closes an open question the epic timeline explicitly left
open, and it corrects the reading that was provisionally attached to it.

## What was open

The 2026-08-20T10:16:27Z entry on `bd-ib-3kolea` established that the
v1.0.5 → v1.2.2 upgrade adds seven migration files: four in the active set
(`0050`–`0053`) and three under a directory literally named
`migrations/ignored/`. That entry was careful to flag its own limit:

> Three of the seven additions sit under a directory literally named
> `ignored/`. The name strongly suggests exclusion from the migration runner
> … but I did NOT read the migration loader, so treat those three as
> UNEXAMINED rather than confirmed-inert.

It also said where to start if the attended rehearsal ever saw a migration
outside `0050`–`0053` being applied. That is this note.

The caution was correct and the suggested reading was wrong.

## The correction: `ignored` means `dolt_ignore`, not "not run"

`internal/storage/schema/schema.go` at `v1.2.2` embeds **two** migration
sources and runs **both**:

```go
//go:embed migrations/*.up.sql
var upMigrations embed.FS

//go:embed migrations/ignored/*.up.sql
var upIgnoredMigrations embed.FS

var (
    mainSource    = migrationSource{files: upMigrations,        dir: "migrations",         cursorTable: "schema_migrations"}
    ignoredSource = migrationSource{files: upIgnoredMigrations, dir: "migrations/ignored", cursorTable: "ignored_schema_migrations"}
)
```

`MigrateUp` calls `ignoredSource.migrate(ctx, db, 0)` unconditionally in the
same pass as the main source, immediately after registering its cursor table
in `dolt_ignore`:

```go
db.ExecContext(ctx, "REPLACE INTO dolt_ignore VALUES ('ignored_schema_migrations', true)")
...
appliedIgnored, ignoredColumnAdded, err := ignoredSource.migrate(ctx, db, 0)
```

So the directory name refers to **Dolt version control**: the tables this
source touches are `dolt_ignore`'d, i.e. excluded from commits and never
merged between clones. It does **not** mean the files are skipped. They run.

The second-order consequence matters for how this epic reasons about version
numbers: because the ignored source keeps its **own** cursor table
(`ignored_schema_migrations`), these migrations do **not** advance the main
schema version. The epic's statement that `0050`–`0053` land at schema **v53**
remains exactly correct — it is a statement about the main cursor. The ignored
source is a parallel track that the main version number does not describe.

## The delta on our span, measured

Both trees were read with the git **tree** API, which self-reports truncation;
both returned `truncated: false`, so these absences are real evidence rather
than a paging artifact. (This is the instrument the 10:16:27Z entry's method
warning prescribes, after the GitHub **compare** API capped at
`total_files: 300` and produced a false absence.)

| Source | v1.0.5 | v1.2.2 | Added | Removed |
|---|---|---|---|---|
| main (`migrations/*.up.sql`) | 49 (max `0049`) | 53 (max `0053`) | `0050`, `0051`, `0052`, `0053` | none |
| ignored (`migrations/ignored/*.up.sql`) | 8 (`0001`–`0008`) | 11 (`0001`–`0011`) | `0009`, `0010`, `0011` | none |

This reconciles the earlier count of "57 up-migrations at v1.0.5 and 64 at
v1.2.2" exactly: 49 + 8 = 57 and 53 + 11 = 64. That earlier figure counted
both sources together. Two independent measurements, same delta.

**Our tenants' main schema version before the upgrade is therefore 49.** That
number is load-bearing below.

## What the three added ignored migrations do

**`0009_aux_row_id_rekey_marker`** — the file body is literally `SELECT 1;`.
The marker itself changes nothing. **What it gates does.** While version 9 is
pending, `MigrateUp` runs the Go function `rekeyAuxRowIDs`, which **rewrites
the `CHAR(36)` primary keys** of four synced tables to deterministic
content-derived values:

```go
var auxRekeyTables = []auxRekeyTable{
    {name: "events",               columns: "issue_id, event_type, actor, old_value, new_value, comment, CAST(created_at AS CHAR)"},
    {name: "comments",             columns: "issue_id, author, text, CAST(created_at AS CHAR)"},
    {name: "issue_snapshots",      columns: "issue_id, CAST(snapshot_time AS CHAR), compaction_level, original_size, compressed_size, original_content, archived_events"},
    {name: "compaction_snapshots", columns: "issue_id, compaction_level, snapshot_json, CAST(created_at AS CHAR)"},
}
```

The purpose is legitimate and upstream explains it: migration `0037`
backfilled those primary keys with per-clone-random `UUID()`s, so clones that
upgraded independently hold the same logical rows under different keys and
their merges duplicate or refuse. The rekey converges them. But it is a
**mutation of real user data**, not internal bookkeeping.

**`0010_drop_wisp_id_defaults`** — drops `DEFAULT (UUID())` from the id columns
of `wisp_events`, `wisp_comments`, `wisp_dependencies`, guarded on
`COLUMN_DEFAULT IS NOT NULL` so re-running is a no-op. These are clone-local
dolt-ignored tables. Lowest-risk of the three.

**`0011_cleanup_orphaned_child_counters`** — moves `child_counters` rows
belonging to live wisps into `wisp_child_counters`, then **`DELETE`s** rows
dangling from `issues`. Every statement is guarded on
`INFORMATION_SCHEMA.TABLES` existence checks. Upstream's stated reason is that
one legacy orphan otherwise bricks every `bd create` via Dolt constraint
validation, so this is a repair — but it is a `DELETE` against a real table.

## The load-bearing question: does the rekey fire on OUR tenants?

`rekeyAuxRowIDs` has two early-return gates:

```go
if !markerPending && !state.pending() { return false, nil }
if mainVersionBefore >= auxRowRekeyShippedMainVersion && !state.pending() { return false, nil }
```

with `auxRowRekeyMarkerVersion = 9` and `auxRowRekeyShippedMainVersion = 51`.

Evaluated for our upgrade:

- **`markerPending`** — v1.0.5 ships ignored `0001`–`0008`, so ignored version
  **9 is pending** on a tenant that has only ever run v1.0.5. → `true`, so the
  first gate does not return.
- **`mainVersionBefore >= 51`** — our tenants are at main version **49**
  (measured above: 49 main up-migrations, max `0049`). `49 >= 51` is
  **false**, so the fresh-clone skip does not fire either.

**Conclusion: the primary-key rewrite executes on our tenants during the
v1.0.5 → v1.2.2 upgrade.** It is not one of `0050`–`0053`, and it is not
visible in the main schema version at all.

Concretely, this rewrites the primary keys of every row in `comments` — which
is where this epic's own plan handoff timeline lives. The 34 entries on
`bd-ib-3kolea` are `comments` rows.

## What this means for the attended rehearsal (`bd-ib-ao3j`)

The rehearsal is scoped, in the epic's words, "to exactly those" migrations
`0050`–`0053`. Measured against the package under
`plan/beads-v1-1-2-upgrade/rehearsal-package/`, coverage of the rekey is
**absent on all four tables** (this sentence originally read "partial and
asymmetric"; see the CORRECTION below the table):

| Rekeyed table | Captured by the inventory? | Would the rewrite be visible? |
|---|---|---|
| `comments` | yes — `comments.json`, columns include `id`, `ordered_by: [issue_id, id]` | ~~**yes, loudly**~~ **no** — see the CORRECTION below |
| `events` | no artifact | no |
| `issue_snapshots` | no artifact | no |
| `compaction_snapshots` | no artifact | no |

Scope searched: every `artifact` entry in
`rehearsal-package/queries/inventory.json` — twelve in total
(`status-type-counts`, `issues`, `dependencies`, `comments`, `labels`,
`policy-metadata`, `schema-migrations`, `schema`, `branches`, `table-counts`,
`remotes`, `client-anchor`). Only `comments` among the four rekeyed tables is
captured. `table-counts.json` records row counts per table, and a rekey
changes ids without changing row counts, so it cannot surface there either.

Two distinct consequences, pulling in opposite directions:

1. **A false-alarm hazard on `comments`.** The rewrite changes `id` for every
   pre-existing row, and `comments.json` is ordered by `issue_id, id` — so the
   row order within an issue changes too. An operator diffing before/after will
   see what looks like wholesale churn. It is expected, deterministic
   convergence. An attended operator who has not been told this may reasonably
   abort a rehearsal that is behaving correctly.
2. **A silent gap on the other three.** `events`, `issue_snapshots` and
   `compaction_snapshots` get the same class of rewrite with no artifact
   capturing it. The rehearsal cannot prove those converged, or that they
   converged *correctly*.

> **CORRECTION, same day — consequence 1 above is WRONG, and the table's
> "yes, loudly" row with it.** I inferred visibility from the fact that
> `comments.json` captures `id`, without tracing whether anything ever
> *compares* two captures across the migration boundary. Nothing does. Reading
> `command-plans/beads112-rehearsal.command-plan.json` stage by stage, the plan
> captures an inventory at `source/v49` (`capture-v49-baseline`) and another at
> `migrated/golden-compare` (`capture-v53-and-golden-schema`), and it performs
> exactly three comparisons:
>
> - `compare-golden-schema.sh`, whose input is `schema.json` — **schema only,
>   no row data**;
> - `compare-restored-baseline.sh`, comparing `source/v49` against
>   `restored/v49` — **both sides at v49**, a backup/restore fidelity check;
> - the round-trip delta, whose script (`run-round-trip.sh`) creates two issues,
>   one dependency and one comment **on the already-migrated database** — so
>   both sides of that delta are post-migration.
>
> **No comparison in the package puts v49 data beside v53 data.** So the
> `comments.id` rewrite is not surfaced at all, there is no false-alarm hazard,
> and the gap is **uniform across all four tables** rather than asymmetric. The
> corrected table row for `comments` is "captured at both points, never
> compared across the boundary → **no**".
>
> This makes the finding **stronger**, not weaker: the rehearsal cannot detect
> an incorrect, partial, or skipped re-key on *any* of the four tables, because
> it never diffs data across the migration. Recommendation 2 below should
> therefore be read as "add a cross-boundary data comparison", not merely "add
> three more artifacts".
>
> Recorded rather than silently edited, because the original error was
> reasoning from *artifact capture* to *comparison coverage* without checking
> the second step — the same "true premise, unverified conclusion" shape this
> thread's timeline already records three instances of.

The good news: the inventory **does** capture `ignored_schema_migrations` rows
(in `schema-migrations.json`, alongside `schema_migrations`), so the ignored
cursor's advance from 8 to 11 will be recorded. The package's authors clearly
knew the second source existed. And `0011`'s `DELETE` from `child_counters`
**would** show up, via `table-counts.json`.

## What this note does NOT establish

Stated so it is not over-read, in the shape this thread's own method rules
require:

- **Our tenants' actual ignored-cursor value was not read.** I inferred "8"
  from the fact that v1.0.5 ships ignored `0001`–`0008`. An authoritative read
  of `ignored_schema_migrations` on a live tenant belongs in the attended
  window; I did not touch the shared server. If any tenant is already past 9,
  the rekey has already run there and the analysis above changes for it.
- **I did not read `internal/storage/rowid`.** The claim that the derivation
  is deterministic and convergent across clones is upstream's, taken from the
  code comments, not verified.
- **I did not trace the rehearsal wrappers end to end.** Whether the
  comment-id churn would be classified as `unexpected_changes` by
  `round-trip-delta-receipt` (which requires `unexpected_changes: 0`) depends
  on when the baselines are captured relative to the migration. I read the
  receipt schemas, not the full wrapper control flow.
- **This is a source reading, not an execution.** Nothing was installed, no
  binary was run, and no tenant was touched.

## Recommendation

Widen `bd-ib-ao3j`'s rehearsal scope from "migrations `0050`–`0053`" to "the
main source `0050`–`0053` **plus** the ignored source `0009`–`0011` and the
`rekeyAuxRowIDs` pass they gate", and add `events`, `issue_snapshots` and
`compaction_snapshots` id-bearing artifacts to the inventory so the
convergence is observable on all four tables rather than one. Brief the
attended operator that a total `comments.id` rewrite is the expected outcome,
not a corruption signal.

This is a scope amendment to an item that is `admission:manual` and
maintainer-attended, so it is recorded here and on the epic timeline as a
finding rather than applied to the item.
