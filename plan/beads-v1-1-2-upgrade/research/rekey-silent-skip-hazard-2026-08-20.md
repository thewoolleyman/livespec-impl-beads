# The aux row-id re-key can silently skip a table and still report success

Measured 2026-08-20 by reading `internal/storage/schema/aux_row_id_backfill.go`,
`internal/storage/rowid/rowid.go` and migration `0049` at upstream tag
`v1.2.2`, plus `0049` as it exists at `v1.0.5`. Companion to
[`ignored-migrations-are-not-inert-2026-08-20.md`](./ignored-migrations-are-not-inert-2026-08-20.md),
which established *that* the re-key runs on our upgrade path. This note is
about *how it can fail*.

Nothing was installed, no binary was run, and no tenant was touched.

## First, the good news: the derivation is sound

The companion note listed "I did not read `internal/storage/rowid`" as an
explicit gap, taking the determinism claim from code comments. That gap is now
closed, and the claim holds — the construction is better than the comment
suggests:

```go
func New(table string, ordinal int, digest string) string {
    return uuid.NewSHA1(Namespace, []byte(table+sep+strconv.Itoa(ordinal)+sep+digest)).String()
}
```

- `Namespace` is a hardcoded constant UUID, documented as fixed forever.
- `New` is a pure function of `(table, ordinal, digest)` — no clock, no
  randomness, no clone-local state.
- `Digest` is SHA-256 over a **prefix code**: `n` for NULL, `v<len>:<bytes>`
  otherwise. The length prefix makes the encoding injective, so no two distinct
  field sequences collide even with arbitrary bytes in values, and NULL is
  distinct from the empty string. A naive concatenation would collide here; this
  does not.

Two consequences worth carrying, because they bear on the rollback boundary:

1. **The re-key is reproducible.** Restore from backup, re-migrate, and you get
   byte-identical ids. The rewrite is not a coin flip, so a restore-and-retry is
   a deterministic do-over rather than a new outcome.
2. **It is idempotent**, with a sentinel written before the first `UPDATE` so a
   crash mid-rewrite resumes rather than recording the completion marker over
   partially re-keyed rows.

So the mechanism is well built. The hazard is not in the derivation.

## The hazard: a skip path that logs, records, and returns success

`rekeyAuxRowIDs` loops over the four tables. When a table fails with the
`dolthub/dolt#11131` schema-encoding-drift signature, it does **not** abort:

```go
if isSchemaEncodingDriftErr(err) {
    skipped = append(skipped, t.name)
    // log, not the TTY-gated progress writer: a piped or CI caller
    // discards that writer, and these three lines are the only
    // notice that a table's ids stayed divergent.
    log.Printf("schema migration: aux row id re-key skipped %q — ...", t.name, err)
    continue
}
```

It then records a drift marker and logs two more lines, one of which states the
consequence plainly:

> `schema migration: %d table(s) kept their old row ids: %s — merges with other
> clones of this database may duplicate those rows`

and `MigrateUp` **completes successfully**.

The decision to degrade rather than abort is deliberate and, on its own terms,
correct: the code comment explains that aborting made the database *unopenable*
by any re-key-aware binary, because the migration re-attempts on open and the
panic recurred on every start. Given that choice, skipping loudly is the right
call.

**The problem is what "loudly" means.** By upstream's own admission, three
`log.Printf` lines "are the only notice". There is no error, no non-zero exit,
no JSON field, and nothing in any table a subsequent query could read back to
ask "did the re-key actually cover all four tables?" — the drift record exists
in the database, but nothing in our tooling reads it.

For this epic that lands in a specific place: **an attended operator who pipes,
redirects, or captures `bd` output in a way that drops the log stream gets a
clean exit code over a partially converged database.** That is the exact
silent-failure shape this repo cares about, arriving through a dependency
rather than through our own code.

## The specific reason to think this is not hypothetical

`isSchemaEncodingDriftErr` describes the trigger as "a TEXT/LONGTEXT column
whose on-disk storage-encoding tag was re-derived without rewriting rows".

Migration **`0049_longtext_large_content_columns`** — which ships in **v1.0.5**,
so **our tenants have already run it** — does exactly that shape of operation,
on one of the four re-keyed tables:

```sql
ALTER TABLE issues MODIFY COLUMN description LONGTEXT NOT NULL, ...
```

and, per its own header comment, on `comments.text`:

> `issues/wisps: description, design, acceptance_criteria, notes, close_reason`
> `comments: text`

`comments` is one of the four tables `rekeyAuxRowIDs` rewrites. So our tenants
have already applied a `TEXT` → `LONGTEXT` `MODIFY COLUMN` to a column of a
table the upgrade will later try to re-key.

**State this as a hypothesis, not a finding.** What is established is that the
operation shapes match: `0049` performs a `MODIFY COLUMN` storage-type change
on `comments.text`, and the drift signature is about a `TEXT`/`LONGTEXT`
column's storage-encoding tag being re-derived without rewriting rows. What is
**not** established is that `0049` actually induces the drift on the Dolt
version our server runs, or that any tenant currently carries it — that depends
on Dolt internals I did not read and on live state I deliberately did not probe.

It is, however, precisely the kind of thing an attended rehearsal exists to find
out, and it is cheap to check once there.

## Recommendations for the attended rehearsal (`bd-ib-ao3j`)

1. **Capture the log stream, and treat it as evidence rather than noise.** The
   only notice of a partial re-key is three `log.Printf` lines. A rehearsal that
   discards stderr cannot detect the failure mode at all.
2. **Add a receipt field for re-key completeness.** Something equivalent to
   `aux_rekey_tables_skipped: []` with a `const: []`-style assertion, so a
   partial re-key fails the receipt instead of passing silently. Today no
   receipt in `rehearsal-package/schemas/` has any field that could express it.
3. **Probe for `#11131` drift on `comments` before the real cutover**, since
   `0049` is already applied everywhere and `comments` is both a re-key target
   and the table this epic's own plan timeline lives in.
4. **Read the drift record after migrating**, not just the migration's exit
   code. The database knows which tables were skipped; nothing currently asks.

## Relationship to other threads

The log-only reporting is an instance of the silent-failure-surface class this
repo tracks in a separate live plan thread. That thread belongs to another
session; this note does not touch it or its items, and files nothing there. It
is recorded here because the instance is inside this epic's upgrade path and is
actionable through `bd-ib-ao3j`'s scope.

## What this note does not establish

- That `0049` induces `dolt#11131` drift in practice. Shape match only.
- That any live tenant currently carries drift. Not probed; the shared server
  was not touched.
- The behaviour of `rekeyAuxRowTable` itself, which performs the per-table
  `UPDATE`. I read its caller's error handling, not its body, so how it
  interacts with foreign keys or indexes during the rewrite is unexamined.
- Whether our `bd` invocation paths would in fact drop the log stream. That is
  a question about our own wrappers, answerable locally, and worth answering
  before the attended window.
