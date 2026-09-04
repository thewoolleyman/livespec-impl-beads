# Five of the six `bd` verbs the rehearsal plan invokes do not exist

**Date:** 2026-08-22
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Item:** `bd-ib-ao3j` (the attended rehearsal run)
**Status:** the O4 command plan STILL cannot execute as written — but four of
the five findings below have since been resolved or routed. See the status
update immediately after this header before acting on anything in this note.
**Nothing was installed.** Both release binaries were fetched to a scratch
directory, checksum-verified against the pins this thread already recorded, and
invoked only with `--help`. No tenant was contacted; no host path was written;
`/usr/local/bin` was not touched.

## STATUS UPDATE, 2026-08-22 (added in place, after this note's findings were acted on)

**Read this before the verb table below.** The table records what was true when
this note was written. Four of its five findings have since been resolved or
have a measured route; the note's headline conclusion survives on the fifth
alone. Amended in place rather than superseded, per this thread's practice of
annotating a note where a reader will actually see it.

| Finding | State now | Carrier |
|---|---|---|
| `inventory <projection>` — **176 calls, 16 invocations, 5 stages** | **RESOLVED.** `capture-inventory.sh` was rewritten onto the real command surface and no longer invokes the verb at all. | `bd-ib-2591`, PR #1750 (merged 2026-08-22) |
| `fixture produce` | **ROUTED.** A measured four-step route exists on v1.0.5: configure `status.custom`, import as JSONL with native statuses only, transition with `update --status`, then add edges and comments separately. | `rehearsal-fixture-route-2026-08-22.md` |
| `sync push` / `sync fetch` | **ROUTED.** `CALL DOLT_PUSH(...)` and `DOLT_FETCH` work in server mode; projection 11 is SERVED on real divergence. | `sync-leg-divergence-2026-08-22.md` |
| `remote add` | **ROUTED.** `DOLT_REMOTE('add', …)` and `dolt_remote_branches` measured working in the same probe. | `sync-leg-divergence-2026-08-22.md` |
| `schema create-golden` | **STILL OUTSTANDING.** The verb does not exist and the command plan still invokes it, at `command-plans/beads112-rehearsal.command-plan.json` lines 216 and 226. | — |

**So the Status line above remains literally true, and it is now true because of
one verb rather than five.** That distinction matters for scheduling: the
attended window's largest command-surface obstacle by an order of magnitude —
176 calls — is gone, and what remains is a single golden-schema step.

Two things this update deliberately does NOT claim. A route being *measured* is
not the same as the command plan being *rewritten* to use it: the plan JSON still
names the non-existent verbs for `fixture produce`, `sync`, and `remote add`, so
executing it as written still fails on those lines even though a working route is
now known for each. And `remote add`'s route touches `dolt_remote` against a real
remote, which is `bd-ib-092q` — parked by design pending its own authorization.

*Verified 2026-08-22 by re-reading the wrapper and the command plan rather than
inferring from the merge: `capture-inventory.sh`'s six remaining occurrences of
the string `inventory` are HALT messages, an env category label, a filename glob
and a receipt schema name — zero invocations; and the command plan's one
`"inventory"` occurrence is a category name in a list, not a verb.*

## Why this note exists

While fixing the fabricated receipts (PR #1703) I needed to know what
`schema create-golden --json` writes, so that the golden side of the schema
comparison could be captured and hashed. It does not write anything, because
the command does not exist.

That one question generalised badly.

## The measurement

Six `bd` verbs appear in `command-plans/beads112-rehearsal.command-plan.json`,
counting the one inside `wrappers/capture-inventory.sh`. Each was invoked
directly on each binary. **Five of the six are unknown commands on every binary
the plan uses.**

| Verb | v1.0.5 | v1.1.2 | v1.2.2 | Where the plan uses it |
|---|---|---|---|---|
| `fixture produce` | unknown | unknown | — | `source-fixture-production`; creates all three synthetic tenants |
| `sync push` / `sync fetch` | unknown | unknown | — | `source-fixture-production`, `target-side-remote-materialization` |
| `remote add` | unknown | unknown | — | `target-side-remote-materialization` |
| `inventory <projection>` | unknown | unknown | unknown | `capture-inventory.sh`, **176 calls** across 16 invocations in 5 stages |
| `schema create-golden` | unknown | unknown | unknown | `capture-v53-and-golden-schema` |
| `migrate` | **exists** | **exists** | — | `migration-gate-and-single-retry` |

`migrate` is the positive control: it is in the same table, invoked the same
way, and returns real help (`Database migration and data transformation
commands.`). The instrument therefore discriminates, so the five
`unknown command` results are findings and not an artefact of how the probe was
run.

### Grepping `--help` would NOT have been sufficient

Cobra supports `Hidden: true`, so a command absent from `--help` can still
exist and work. An absence established by grepping the help text is exactly the
"instrument that cannot return a hit" trap in `AGENTS.md`. Every row above was
established by **invoking the verb**, which is the only form of the check that
can distinguish "hidden" from "absent". (The help-text tallies agree — 109
commands in v1.0.5, 108 in v1.1.2 — but they are corroboration, not the
evidence.)

### Provenance of the two fetched binaries

| | v1.1.2 | v1.2.2 |
|---|---|---|
| tarball SHA-256 | `a72d71ed…401c2` — matches `manifests/provenance.json` | `8140098a…321e8` — matches `v1-2-2-provenance-chain-2026-08-21.md` |
| extracted binary SHA-256 | `6d767629…d9a82` — matches | `54fc0e05…7aa1e0e` — matches |
| self-reported version | `bd version 1.1.2 (20e493e56)` | `bd version 1.2.2 (6c124203e)` |

v1.0.5 was probed through the installed public guard at `/usr/local/bin/bd`.

## What this breaks

Not a periphery. `capture-inventory.sh` is the rehearsal's entire evidence
spine: it produces the per-artifact and `combined.sha256` hashes that
`compare-restored-baseline.sh` compares, at all five capture points
(`pre-backup-v49-baseline`, `after-first-gate-decision`, `post-migration-v53`,
`post-round-trip`, `post-restore-v49`). With no inventory verb there is no
baseline, no post-migration capture, and nothing to compare a restore against —
so the restore-proof the rehearsal exists to produce cannot be produced.

`fixture produce` is upstream of all of it: without it there are no synthetic
v1.0.5 tenants to migrate in the first place.

## This is a rewrite, not an impossibility

Each leg has a real counterpart on the same binaries, so the command plan can be
re-expressed rather than abandoned. Verified present on both v1.0.5 and v1.1.2:

- **The raw-SQL verb** — "Execute a raw SQL query against the underlying
  database (SQLite or Dolt)." This is the natural home for the inventory
  projections, and the design already points there: `queries/inventory.json`
  specifies each projection as `columns` + `ordered_by` (`status`,
  `issue_type`, `COUNT(*)`, an ordered `id` list, …) — **SQL column selections,
  not subcommand names**. The projections were designed as queries;
  `capture-inventory.sh` is what translated them into a verb that was never
  there.
- **The export / import verbs** — JSONL out and in; the plausible route for
  fixture production from `fixtures/deterministic-fixtures.json`.
- **The dolt verb** ("Configure and manage Dolt database settings and server
  lifecycle") and **the federation verb** ("Manage peer-to-peer federation
  between Dolt-backed beads databases") — the plausible route for the remote and
  sync legs.

Those are *plausible* routes, established by reading one line of help each. None
has been proven to cover its leg. That work is the actual remedy and is not done
here.

## Why nothing caught this

`tests/test_beads_v112_rehearsal_package.py` checks the command plan's
**shape** — that stage names are in order, that every stage has commands, that
`argv_templates` equals `commands`, that no command carries a `planned_only` or
`prose:` marker, and that certain substrings are present. Every one of those
passes on a plan whose commands do not exist, because none of them asks a
binary anything. The suite is a plan-well-formedness check, and it was read as
a plan-correctness check.

Note the shape: this is the same defect as the fabricated receipts, one level
up. There, producers published assertions they never measured. Here, a test
suite reports a command plan valid without ever establishing that its commands
are real. Both return a clean green that carries no information about the thing
a reader assumes it covers.

## Consequence for `bd-ib-ao3j`

The receipt fix (PR #1703) was the recorded precondition for moving `bd-ib-ao3j`
to ready. It is merged and it stands — the receipts had to be fixed regardless.
But it is no longer the *last* precondition. Scheduling the attended
privileged-host window before the command surface is re-expressed would spend a
maintainer-attended window on a plan that fails at `source-fixture-production`,
which is stage 4 of 17.
