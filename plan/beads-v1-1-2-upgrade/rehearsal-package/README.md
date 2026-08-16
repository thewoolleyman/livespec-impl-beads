# Synthetic isolated Beads v1.1.2 migration-and-restore rehearsal package

This package prepares O4 only. It records the deterministic inputs, wrappers,
queries, and receipt contracts for the later attended rehearsal. It does not run
the rehearsal and it must not be used against a production tenant for any
write-capable operation.

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
| `manifests/topology.json` | Synthetic-only rehearsal topology and the three read-only production shape sources. |
| `fixtures/deterministic-fixtures.json` | Canonical v1.0.5 fixture definitions, including the synthetic rig/wisp shape that production did not contain. |
| `queries/inventory.json` | Canonical read-only inventory commands and expected JSON output classes. |
| `schemas/*.schema.json` | Receipt schemas for artifact fetch, v1.0.5 producer build, shape survey, identity probe, and rehearsal command plans. |
| `wrappers/*.sh` | Bounded command wrappers. They default to printing planned commands and require explicit output directories for receipts. |
| `locks/dependencies.lock` | Tool and dependency lock for this preparation package. |

## Later attended use

The attended O4 rehearsal may consume these artifacts to create isolated
synthetic v1.0.5 tenants, run a single designated v1.1.2 migrator, prove restore
to the complete baseline, and record cleanup. That later step is intentionally
outside this work item.
