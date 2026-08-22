# Both gaps closed — and rig-blindness is not what any of us thought

**Date:** 2026-08-22
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Item:** `bd-ib-ao3j` (the projections), `bd-ib-3kolea.4` (the retarget)
**Authorization:** foreman seat, fetch plan approved with three additions;
compliance at the end. Still **NOT** an authorization to run `bd-ib-ao3j`.

This closes the two gaps left open by `server-mode-sql-probe-2026-08-22.md`. One
closes cleanly. The other closes by **overturning the mechanism that note and the
route proof both assumed** — including a claim I made myself yesterday.

## Gap 1 — CLOSED. `bd sql` works in server mode on all three binaries

| Binary | Version string | Server-mode `SHOW TABLES` | Fresh-database schema version |
|---|---|---|---|
| v1.0.5 (installed) | `1.0.5 (6a3f515ce)` | works — `Tables_in_o4probe` | 49 |
| v1.1.2 (fetched) | `1.1.2 (20e493e56)` | works — `Tables_in_o4v112` | **53** |
| v1.2.2 (fetched) | `1.2.2 (6c124203e)` | works — `Tables_in_o4v122` | **53** |

The embedded-mode refusal is mode-gated on every version tested. The inference
recorded yesterday is now a measurement.

Two things fall out for free. A fresh v1.1.2 database lands at **schema v53**,
independently confirming the documented 50→53 span; and v1.2.2 lands at v53 too,
corroborating upstream's "same code, higher version" claim *on the schema
specifically* — which is narrower than the claim itself and is all this measures.

All five projections re-ran green on v1.2.2. One difference worth recording:
`schema_migrations` gains a `content_hash` column at v53 (and
`ignored_schema_migrations` gains one too), but **neither table gains
`table_name` on any version**. So the row-7 spec defect is confirmed across all
three, and it is fixed in this change.

## Gap 2 — CLOSED, and the answer is the opposite of the assumed one

### What everyone believed

The route proof found `list --json` blind to a `rig`-typed row and reasoned that
raw SQL "would likely convert" those projections. My own note yesterday went
further and stated that rig/wisp "arrive with migration 0053, i.e. with v1.1.2",
implying that the newer binary would accept the type and let the question be
asked.

**Both halves are wrong.**

### What is actually true

`rig` is rejected by the create-path validator on **every** version, including the
two that carry migration 0053:

```
v1.0.5:  bd create … -t rig  ->  Error: validation failed: invalid issue type: rig
v1.1.2:  bd create … -t rig  ->  Error: validation failed: invalid issue type: rig
v1.2.2:  bd create … -t rig  ->  Error: validation failed: invalid issue type: rig
```

Each was run with a `-t task` **control immediately before it**, which succeeded
every time — so these are genuine negatives from a working instrument, not a
broken create path.

The reported blindness is real, and its mechanism is structural:

> **`rig`-typed records live in the separate `wisps` table, not in `issues`.**

`list --json` reads `issues`. So does any raw-SQL projection written the obvious
way. Reproduced on v1.1.2 with the rig row in `wisps`:

| Surface | Result |
|---|---|
| `list --status all --limit 0 --json` | 1 row — **rig row absent** |
| `bd sql 'SELECT COUNT(*) FROM issues'` | 1 — **rig row absent** |
| `bd sql 'SELECT * FROM wisps'` | the rig row |
| `bd show o4-rig-wisp` | renders it, `Type: rig` |

Identical on v1.2.2 (`list --json` 8 rows, `rig present: False`; `issues` 8,
`wisps` 1).

**So raw SQL is NOT the cure for rig-blindness.** It is blind in exactly the same
way and for exactly the same reason. The cure is to query `wisps` as well as
`issues` — a change to *what the projection selects*, not to *which surface runs
it*. Any rewrite that swaps `list --json` for `bd sql` over `issues` and calls the
rig problem solved will ship the identical blind spot with a new implementation
and more confidence.

This matters most for the four projections the route proof marked "rig-blind"
(`status-type-counts`, `issues`, `labels`, `policy-metadata`). Moving them to raw
SQL does nothing for them by itself.

### How I nearly got this wrong, recorded because the near-miss is the lesson

My first attempt injected the rig row into **`issues`**. Both surfaces then
returned it, and the honest reading of that result was *"rig-blindness does not
reproduce"* — a refutation of a colleague's finding, from a clean measurement.

It was wrong because **my test had not reproduced the reported condition.** I put
the row where the blind surface already looks. The discriminating question was not
"what do the two surfaces return" but "does my setup actually recreate what was
observed" — and the tell was that `show` retrieving a row the listing omits
requires the row to be somewhere the listing does not read.

This is the catalogued family — an instrument aimed at the wrong population,
returning a plausible answer with no error — with the sharpest variant of the
consequence: it would have produced a **false refutation** of a real finding, and
false refutations are worse than false findings because nobody re-checks a defect
that has been "disproved."

The `wisps` tables exist in the v49 schema too, which is what makes "just query
them" look available on any version and hides that the blocker was never the
schema.

## Recommended next actions

1. **The wrapper rewrite must union `wisps` with `issues`** for every projection
   that enumerates work items, and the rehearsal's fixture assertions should count
   both. This supersedes "use raw SQL" as the remedy for rig-blindness.
2. `queries/inventory.json` row 7 is fixed here — `ordered_by` drops `table_name`,
   confirmed absent on all three versions.
3. Still unprobed and still worth its own authorization: `dolt_remote`'s `sync`
   behaviour against a *real* remote, and v1.0.5's projection routes at the
   pre-migration capture point (blocked by `bd-ib-dwv`'s 404).

## Condition compliance

Version gate, isolation, target proof, read-only posture and `uptime` as before.
The three additions attached to the fetch approval:

**Addition 1 — credential absent.** Every scratch invocation ran with
`BEADS_DOLT_PASSWORD` absent: `printenv BEADS_DOLT_PASSWORD | wc -c` returned
**0**, recorded at the run start and again immediately before each binary's first
invocation. Nothing ran under `with-livespec-env.sh` except the two deliberate
tenant reads that take the before/after measurement. This is the second
independent guard: a mis-resolved config could not have authenticated against a
family tenant even if every other control had failed. The probe user also cannot
read `/var/lib/doltdb/databases` — permission denied, measured both times.

**Addition 2 — target proven per binary.** Each leg re-proved, from its own scratch
cwd and immediately before that binary's first invocation: asserted
`port 13307 / db o4v112|o4v122 / user root` programmatically, printed the binary's
own SHA-256 and version, and confirmed the credential absent at that instant. Both
binaries then named the target back in their own output (`Tables_in_o4v112`,
`Tables_in_o4v122`).

**Addition 3 — report the diff, never hash equality.** Tenant state before and
after: **711 records both times, hash `45376b6f…8946b5` unchanged, 0 added,
0 removed, 0 changed.**

That empty diff is reported as an observation, not as the proof, and the
distinction is the whole point of this addition. An empty diff is what a *broken*
check also produces. What makes this one meaningful is that **the same instrument
fired 20 minutes earlier** on the previous probe — catching two single-comment
writes among 710 records, one of them the foreman's own handoff entry — which
established that it can detect a write of the smallest size that occurs here. This
run simply had no concurrent traffic in its four-minute window.

### Fetch-specific compliance

- Fetched **only** the v1.1.2 and v1.2.2 `linux_amd64` tarballs. v1.2.0 and v1.2.1
  were never fetched, extracted or invoked.
- **Both** the tarball and the extracted-binary SHA-256 were verified against the
  recorded pins *before any invocation*, as a hard abort arm rather than a check:
  v1.1.2 `a72d71ed…401c2` / `6d767629…d9a82`; v1.2.2 `8140098a…321e8` /
  `54fc0e05…1e0e`. **All four matched exactly.** Version strings then matched the
  recorded expectations (`20e493e56`, `6c124203e`), with an abort arm for anything
  outside `{1.0.5, 1.1.2, 1.2.2}` that did not fire.
- **Nothing was installed.** Both binaries were invoked by absolute path from the
  session scratchpad. Verified after the run: `/usr/local/bin/bd` still hashes to
  `5f55fbfb…4637a3`, `LIVESPEC_BD_PATH` is unset, `bd` on `PATH` still resolves to
  `/usr/local/bin/bd`, and the repo tree is clean.
- **Teardown confirmed by absence**, not by intent: scratch server killed by PID
  (never `pkill -f`), 13307 clear, and a scratchpad-wide search for `bd`,
  `bd-1.*` and `beads_*` returns nothing.
