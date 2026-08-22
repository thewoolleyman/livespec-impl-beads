# Server-mode raw SQL: the route works, and it converts every open projection

**Date:** 2026-08-22
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Item:** `bd-ib-ao3j` (the projections), `bd-ib-3kolea.4` (the retarget)
**Authorization:** foreman seat, 2026-08-22, six binding conditions; compliance
recorded at the end of this note. This is explicitly **NOT** an authorization to
run `bd-ib-ao3j` itself.

## The question

`route-proof-2026-08-22.md` left the rehearsal's raw-SQL route **UNPROVEN, pending
a server-mode probe**. It had measured `bd sql` refusing in *embedded* mode on both
v1.1.2 and v1.2.2 —

```
$ bd sql 'SHOW TABLES'
Error: 'bd sql' is not yet supported in embedded mode      (exit 1)
```

— and correctly declined to generalize that to server mode, which is the mode the
rehearsal's topology actually uses (`dolt.mode: server`, isolated server on a
non-family port). Four of the eleven inventory projections were blocked on that
question and a fifth was unproven.

This note answers it by starting an isolated server and measuring.

## Headline: `bd sql` WORKS in server mode

Measured 2026-08-22T09:26:34Z, `bd version 1.0.5 (6a3f515ce)`, against an isolated
Dolt `sql-server` at `127.0.0.1:13307`, database `o4probe`:

```
$ /usr/local/bin/bd sql 'SHOW TABLES'
Tables_in_o4probe
-------------------------
blocked_issues
child_counters
...
wisps
(28 rows)
```

The result-set header reads `Tables_in_o4probe` — the connection target names
itself *in the measurement*, which is the cleanest form the condition-4 proof
could take.

**So the embedded-mode refusal is mode-gated, not capability-gated.** The verb is
present and functional; the earlier probe was simply in the wrong mode to see it.

## Per-projection result, v1.0.5 server mode

Every previously-blocked row converts. Each verdict is graded on **shape**, not on
exit status — the trap the prior probe hit twice.

| # | Projection | Prior | Now | Evidence |
|---|---|---|---|---|
| 7 | `schema-migrations.json` | NOT SERVED | **SERVED** (contents) — spec defect | see below |
| 8 | `schema.json` | NOT SERVED | **SERVED**, all five contents | 329 column rows, 98 index rows, 26 PK / 15 FK / 6 UNIQUE / 2 CHECK, 15 referential constraints, 2 views |
| 9 | `branches.json` | NOT SERVED | **SERVED** | `dolt_branches` gives `name`+`hash` — exactly the `head_hash` the CLI's `branch --json` lacks |
| 10 | `table-counts.json` | NOT SERVED | **SERVED**, exact | control below |
| 11 | `remotes.json` | UNPROVEN | **SERVED**, incl. the sync leg | controls below |

### 7 — the route is fine; the *projection spec* is wrong

`schema_migrations` and `ignored_schema_migrations` are both readable and carry
real content: 49 rows spanning versions 1–49, and 8 rows spanning 1–8,
respectively. The v49 figure independently corroborates the rehearsal's
`pre-backup-v49-baseline` naming.

But the projection declares `ordered_by: ["table_name", "version"]`, and
`table_name` **does not exist on either table**. Measured against
`information_schema.columns`:

| table | columns |
|---|---|
| `schema_migrations` | `version` (int) — that is all |
| `ignored_schema_migrations` | `version` (int), `applied_at` (datetime) |

So this row is SERVED for its three `contains` items, and the residual defect
belongs to `queries/inventory.json`, not to the route. Fixing it means dropping
`table_name` from the ordering key. **This is a spec correction, not a capability
gap** — and it is the kind that would have shipped as a mysterious empty column.

### 10 — including a control I had to run twice

`information_schema.tables.TABLE_ROWS` supplies `(base_table_name, row_count)`
directly. In MySQL/InnoDB that column is an *estimate*, so agreement had to be
established rather than assumed. First control: `TABLE_ROWS` vs a real `COUNT(*)`
across all 26 base tables — **0 mismatches**.

That control was nearly worthless and I am recording why. Only **3 of 26** tables
were non-empty, so an estimator would have agreed for free on the other 23. Re-run
after seeding 25 issues through the real `bd create` path: `issues` reported 25
against a real `COUNT(*)` of 25, with 7 tables now non-empty. **Exact on Dolt.**

The first version of that control is precisely the "instrument that cannot return
a hit" shape this repo catalogues; it passed, and it proved nothing.

### 11 — two controls that discriminate

`SELECT * FROM dolt_remotes` returned `(0 rows)` with no error. That observation is
consistent with *both* "no remotes configured" and "this table is not really
there", so it is not yet evidence.

- **Control A — can this query fail?** `SELECT * FROM dolt_this_table_does_not_exist`
  returns `Error 1146 (HY000): table not found`. So `(0 rows)` genuinely means an
  empty existing table.
- **Control B — can it return a hit?** After
  `CALL DOLT_REMOTE('add','o4origin','file://…')`, `dolt_remotes` returns the row.

The remaining contents follow: `active_branch()` returns `main`; `dolt_branches`
gives the local head; and the **sync leg — previously unprobed entirely** —
works: `CALL DOLT_PUSH('o4origin','main')` succeeds and `dolt_remote_branches`
then reports `remotes/o4origin/main` at `vco9iii4…in4he`, identical to local
`main`. Local-vs-cached head comparison, which is the whole purpose of that
projection, is therefore available.

## What this does NOT establish — two honest gaps

**1. Everything above is v1.0.5.** The embedded-mode refusal was measured on
v1.1.2 and v1.2.2; my server-mode confirmation is on v1.0.5. The refusal text is
mode-worded (`not yet supported in embedded mode`), so server mode very likely
works on the newer binaries too — but that is an **inference, not a measurement**,
and this thread does not ship inferences as measurements. Closing it requires
fetching those two binaries, which is a separate authorization.

> **CORRECTED 2026-08-22, later the same day, by
> `rig-blindness-mechanism-2026-08-22.md`.** Gap 1 below is now MEASURED rather
> than inferred: `bd sql` works in server mode on v1.1.2 and v1.2.2 as well.
> Gap 2's *reasoning* below is WRONG and is left in place only so the error is
> legible. v1.1.2 and v1.2.2 reject `-t rig` exactly as v1.0.5 does, so the
> newer binaries did not unblock the question the way this section predicts.
> The real mechanism: `rig` records live in the separate `wisps` table, so raw
> SQL over `issues` is blind in precisely the same way `list --json` is —
> **raw SQL is not the cure.** Read the newer note before acting on this one.

**2. Rig-blindness is untested, and cannot be tested here.** `route-proof` found
four SERVED rows to be rig-blind: `list --json` omits `rig`-typed rows. Whether
raw SQL sees them is the obvious follow-on, and I could not ask it — v1.0.5
rejects the type outright:

```
$ bd create "o4 rig wisp probe" -t rig
Error: validation failed for issue : invalid issue type: rig
```

`rig`/`wisp` arrive with migration 0053, i.e. with v1.1.2. So the question is
genuinely blocked on the same binary fetch as gap 1 — not merely unattempted. Note
that the `wisps` tables *do* exist in the v49 schema, which makes "just query them"
look available; the blocker is the type validator, not the schema.

## A false lead, checked and dropped

On first connect, `bd` warned:

> `dolt_server_port` in metadata.json is deprecated (can cause cross-project data
> leakage). The port file (`.beads/dolt-server.port`) is now the primary source.

"Cross-project data leakage" on a multi-tenant server is alarming, and this repo's
`.beads/metadata.json` does carry `dolt_server_port: 3307`. **It is not a finding.**
Both this repo and the scratch client also carry `.beads/dolt-server.port`, and a
normal wrapped call in this repo emits no such warning. The warning fired in scratch
only during the window before `bd` created its own port file. Recorded because the
next reader will hit the same warning and should not re-investigate it.

## Condition compliance

The foreman attached six conditions. Each is answered by a measurement, not an
assertion.

1. **Not `bd-ib-ao3j`.** The attended migration-and-restore rehearsal was not run
   and is untouched; it remains `backlog` under manual admission.
2. **Never v1.2.0 / v1.2.1.** The binary was version-checked *before* connecting:
   `bd version 1.0.5 (6a3f515ce)`, printed at 09:24:48Z, with an abort arm for any
   version outside `{1.0.5, 1.1.2, 1.2.2}`. It did not fire. Neither hazard version
   was fetched, installed or invoked.
3. **Isolation by my own direct before/after measurement**, not by `ao3j`'s
   receipts — which this thread proved cannot fail, and which were therefore not
   relied on. See the table below.
4. **Connection target proven before any write.** `bd where` resolved to the scratch
   workspace; the scratch `config.yaml` and `metadata.json` name port `13307`,
   database `o4probe`, user `root`, asserted programmatically; `ss -ltnp` showed
   13307 owned by **my own** PID 334115 running as `ubuntu`; and `bd`'s own outputs
   named the target back to me twice — `Tables_in_o4probe`, and a refusal reading
   `dolt server at 127.0.0.1:13307`.
5. **Read-only against production; no host mutation.** `/usr/local/bin/bd` hashes
   to `5f55fbfb…4637a3` before and after, its recorded pin. No image action, no
   Fabro-server action, no secret printed (secrets probed by byte count only). One
   item worth flagging: `bd init --reinit-local` writes `AGENTS.md`, `CLAUDE.md` and
   a `.claude/settings.json` SessionStart hook. **Every one landed inside the scratch
   client directory**; `~/.claude/settings.json` has mtime 11:17:59, predating the
   init at 11:29:52, and the repo tree stayed clean. This is exactly why the standing
   rule forbids `bd init` in a checkout or worktree.
6. **`uptime` first, timestamps throughout.** At 09:21:53Z: load `15.66 / 25.30 /
   32.66` on 18 cores — i.e. falling steeply, and stated as the current condition
   rather than as the peak. Every measurement above carries its timestamp.

### The before/after isolation table

| Measurement | Before (09:24Z) | After (09:32Z) | Verdict |
|---|---|---|---|
| Family server identity | PID 3285864, user `dolt`, started Tue Jul 21 02:19:00 2026 | identical | untouched, not restarted |
| Family listener `127.0.0.1:3307` | present | present | untouched |
| Scratch listener `127.0.0.1:13307` | absent | absent (killed **by PID**, never `pkill -f`) | fully torn down |
| `/usr/local/bin/bd` sha256 | `5f55fbfb…4637a3` | `5f55fbfb…4637a3` | unchanged |
| `BEADS_DOLT_PASSWORD` in probe env | 0 bytes | 0 bytes | probe could not authenticate to the family server |
| `/var/lib/doltdb/databases` readable as probe user | no — permission denied | no | probe could not even read family data |
| Repo working tree | clean | clean | unchanged |
| Tenant content (710 records) | `4f4699ae…d957d` | `f9bd3e5e…f6e7e` | **changed — see below** |

**The tenant hash moved, and that is the most useful line in this note.** The diff
resolves to exactly two `comment_count` increments, on items belonging to neither
this plan nor this probe:

- `bd-ib-1mjt`, +1 comment at 09:27:04Z, authored by `livespec-orchestrator-beads-fabro-foreman`
- `bd-ib-bdcmok`, +1 comment at 09:29:47Z, authored by `factory-host-storage-reclamation`

Both are ordinary plan-handoff writes by other live sessions inside my window. No
record was added, removed, or otherwise altered.

The point worth carrying: **this instrument fired.** It detected two single-comment
writes among 710 records, which is what makes its silence about everything else
meaningful. That is the difference between this check and the `ao3j` receipts that
publish `*_unchanged: True` from an apparatus with no "after" parameter — and it is
why condition 3 was the condition that mattered.

## Recommended next actions

1. **Rewrite the `capture-inventory` wrapper against the proven surface** — the
   `queries` block of `queries/inventory.json` for the CLI-served rows, and
   `bd sql` in server mode for rows 7–11. No new design is needed.
2. **Correct `queries/inventory.json` row 7**: drop `table_name` from `ordered_by`.
3. **Fetch v1.1.2 and v1.2.2 and re-run this probe** to close both honest gaps
   above — the mode confirmation on the target binaries, and the rig-blindness
   question that only they can answer. Requires its own authorization.
