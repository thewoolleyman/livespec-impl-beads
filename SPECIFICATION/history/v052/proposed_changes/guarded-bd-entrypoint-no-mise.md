---
topic: guarded-bd-entrypoint-no-mise
author: codex-gpt-5
created_at: 2026-07-30T09:14:53Z
---

## Proposal: Make the lifecycle guard the public Beads entry point

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Clarify that the pinned Beads binary is reached through the public lifecycle guard, prohibit repository-local mise Beads declarations that can shadow it, and forbid normal callers from using the guard's private delegate.

### Motivation

Obsolete host mise installs regenerated a bd shim ahead of /usr/local/bin/bd. The current specification only says not to rely on one particular stale shim and describes LIVESPEC_BD_PATH as the pinned binary path, leaving both project-local mise shadowing and direct private-delegate use insufficiently specified.

### Proposed Changes

The Beads connection contract and substrate constraints MUST define the managed bd path as the public lifecycle-guarded entry point when the guard is installed. On the reference fleet host that entry point is `/usr/local/bin/bd`; `LIVESPEC_BD_PATH`, when set, MUST name it. A repository's mise configuration MUST NOT declare or install bd because an activated tool or regenerated shim can shadow the guard. Normal plugin, ledger, and operator calls MUST NOT invoke the guard's private delegate executable. Replace the incident-specific stale-shim wording with this invariant, add a Gherkin scenario proving guarded resolution, and co-edit `tests/heading-coverage.json` for the new scenario heading.
