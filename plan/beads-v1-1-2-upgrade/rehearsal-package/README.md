# Synthetic isolated Beads v1.1.2 migration-and-restore rehearsal package

This package prepares O4 only. It records the deterministic inputs, wrappers,
queries, and receipt contracts for the later attended rehearsal. It does not run
the rehearsal and it must not be used against a production tenant for any
write-capable operation.

## THE COMMAND PLAN IS NOT EXECUTABLE AS WRITTEN

Do not schedule the attended window against this plan yet. Measured 2026-08-22
by invoking each verb on each binary: **five of the six `bd` verbs the command
plan uses do not exist** in v1.0.5, v1.1.2, or v1.2.2 — `fixture produce`,
`sync push`/`sync fetch`, `remote add`, `inventory <projection>` (176 calls, the
rehearsal's whole evidence spine) and `schema create-golden`. Only `migrate`
exists, and it is the positive control that proves the probe discriminates.

Each leg has a real counterpart on the same binaries, so this is a rewrite of
the plan's command surface rather than a dead end. Full measurement, provenance
of the probed binaries, and the candidate routes:
`../research/rehearsal-command-surface-does-not-exist-2026-08-22.md`.

The hermetic tests pass on this plan because they check its **shape** — stage
order, argv/command agreement, absence of placeholder markers — and never ask a
binary whether a command is real.

## Boundary

Allowed now:

- Fetch public upstream Beads artifacts and verify recorded hashes.
- Build the v1.0.5 fixture producer from the public upstream source tag.
- Run the read-only fixture-shape survey from the three recorded family roots.
- Validate package receipts and command plans hermetically.

Forbidden now:

- Starting a server.
- Writing, migrating, backing up, restoring, or cleaning up a tenant or
  database.
- Mutating `/usr/local/bin`, Fabro, Fabro-server, Docker images, secrets, or
  production data.
- Using the host private `bd-real` delegate as a production command path.

The only production-facing command in this package is
`wrappers/survey-fixture-shape.sh`, which runs read-only `bd` inventory commands
from each target root through its configured wrapper and public
`/usr/local/bin/bd`.

## Inventory

| Path | Purpose |
|---|---|
| `manifests/provenance.json` | Reviewed public artifact hashes, upstream tag anchors, and fixture-producer build receipt inputs. |
| `manifests/run-manifest.contract.json` | `RUN_ID`, `RUN_ROOT`, `RECEIPT_ROOT`, immutable-receipt, and directory-preflight contracts. |
| `manifests/topology.json` | Synthetic-only rehearsal topology and the three read-only production shape sources. |
| `fixtures/deterministic-fixtures.json` | Canonical v1.0.5 fixture definitions, including the synthetic rig/wisp shape that production did not contain. |
| `queries/inventory.json` | Canonical read-only inventory commands and expected JSON output classes. |
| `command-plans/beads112-rehearsal.command-plan.json` | Concrete attended rehearsal command-plan instance, including migration gate, round trip, restore, receipt, stop, and cleanup boundaries. |
| `schemas/*.schema.json` | Receipt schemas for every receipt the command plan produces. Each assertion field is pinned `const: true`, so a producer that computes `false` is REJECTED at validation rather than reported as a pass. |
| `wrappers/*.sh` | Bounded command wrappers. They default to printing planned commands and require explicit output directories for receipts. Every assertion a wrapper publishes is computed from inputs it holds: a wrapper is handed BOTH sides of any comparison it asserts on, and the refusal gates (`preflight-backup-namespace.sh`, `stop-manifest-pid.sh`) write their receipt and then exit non-zero when a check fails. |
| `wrappers/verify-no-secret-values.sh` | Two-armed receipt secret-leak guard: a `BEADS_DOLT_PASSWORD=` assignment shape, AND the credential VALUE itself, which is how a real leak looks (a DSN, a connection string, a JSON field, a client error message). The value is read from `BEADS_DOLT_PASSWORD` in the scanner's own environment and fed to `grep -F` on stdin -- never argv, never a file. FAIL-CLOSED: an unset or empty variable, or a receipt root the scan cannot read, exits non-zero and publishes NO receipt, because a clean `secret_scan` receipt for a scan that did not happen is worse than none. |
| `wrappers/anchor-probe.py` | Hermetic version-neutral anchor-probe contract with one compile-time read-only identity statement and pre-socket refusal tests. |
| `locks/dependencies.lock` | Tool and dependency lock for this preparation package. |

## Later attended use

The attended O4 rehearsal may consume these artifacts to create isolated
synthetic v1.0.5 tenants, run a single designated v1.1.2 migrator, prove restore
to the complete baseline, and record cleanup. That later step is intentionally
outside this work item.
