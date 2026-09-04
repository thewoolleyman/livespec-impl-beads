# The fixture-production route, and a correction to the route-proof table

**Date:** 2026-08-22
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Item:** `bd-ib-ao3j`
**Authorization:** the same foreman consensus panel and the same ten binding
guards as `route-proof-2026-08-22.md`, re-read from `bd-ib-ao3j` before starting
rather than recalled. Compliance recorded at the end.
**Nothing was installed.** Two fresh scratch databases, deleted afterward; no
tenant contacted; `/usr/local/bin` verified unchanged by checksum.

## Why this note exists

`route-proof-2026-08-22.md` answered the **inventory** leg — which of the 11
projections a real command can serve. It left the other four missing verbs
untouched. This note takes the earliest of them, `fixture produce` at stage 4,
because a plan that fails at stage 4 of 17 never reaches the projections at all.

It also corrects that note.

## The correction: four SERVED verdicts are rig-blind

`route-proof-2026-08-22.md` recorded `issues`, `labels`, `status-type-counts`
and `policy-metadata` as SERVED by the `list --json` projection. **That route
does not return `rig`-typed rows.**

Measured: importing the package's own four-record fixture set produced four
stored issues, and `list --status all --limit 0 --json` returned **three**.

| Check | Result |
|---|---|
| import reported | `Imported 4 issues` |
| `list --status all --limit 0 --json` | 3 rows |
| `show o4-rig-wisp` | renders the row in full, `Type: rig`, status OPEN |
| `list --all` / `list --include-gates` | still 3 rows |
| distinct labels via the listing | 5, where the fixture declares 6 |

So the row exists and is reachable by id; only the listing surface omits it, and
the sixth label is the one on that row.

**Why this is worse than a missing row.** The rig/wisp fixture is in the package
*specifically* to exercise v1.1.2's migration 0053 — the migration this entire
upgrade is being rehearsed for. Four of the six SERVED projections are therefore
served for ordinary issues and blind to the one shape the rehearsal exists to
test.

**It is NOT a silent drop, and the distinction took a deliberate check.** Import
printing `Imported 4 issues` while the listing shows three reads exactly like a
silent data loss, and that was the first conclusion. Fetching the row by id
before believing the absence is what separated "the listing omits it" from "the
import lost it". This is the same discrimination the thread's earlier notes keep
arriving at, and the `AGENTS.md` beads-trap catalogue already warns that a
listing surface hiding rows presents as loss.

## The fixture-production route: four steps, three obstacles

`fixture produce` has no counterpart verb, but the leg is reproducible on
v1.0.5:

1. **Configure the custom status.** `config set status.custom "ready:active"` is
   accepted; `statuses` then lists `ready [active]` and `config get
   status.custom` reads it back.
2. **Import the fixtures as JSONL, with native statuses only.** `import <file>`
   upserts, requires only `title`, and accepts what `export` emits.
3. **Transition to the custom status afterward.** `update <id> --status ready`
   works; the row then reads `ready`.
4. **Create the edges and the comment separately.** The `fixtures` array holds
   only issues, while `expected_identity` requires one dependency edge, one
   parent edge and one comment. `dep add` and `comment` are already proven.

Three obstacles the rewrite must handle, each measured rather than inferred:

**(a) The import validator does not consult the custom status.** With
`status.custom` set to `ready:active` *and* `statuses` listing it, import still
fails:

```
Error: import failed: validation failed for issue o4-ready: invalid status: ready
```

Registered, visible, and still rejected on the import path. That is precisely
why step 3 exists as a separate transition instead of being folded into step 2.

**(b) The fixture file's field name is wrong for import.** `fixtures[]` uses
`type`; the canonical export/import key is `issue_type`. Established by
exporting a known row and reading its keys, not by guessing — the export keys
are `_type, comment_count, created_at, created_by, dependency_count,
dependent_count, description, id, issue_type, labels, owner, priority, status,
title, updated_at`.

**(c) There is no custom-type config key.** `config set types.custom "rig"` is
refused: `"types.custom" is not a recognized config key. Use 'custom.*' for
user-defined keys.` Import nonetheless accepts and stores `issue_type: rig`, and
the row survives — so the type itself is not the problem. Only the listing
surface is, per the correction above.

## Guard compliance

All ten honoured. Pin and version recorded before any non-help invocation (guard
entry point `5f55fbfb…4637a3`, reports `1.0.5`, on-pin, abort arm armed and not
fired); v1.2.0/v1.2.1 never fetched, installed or invoked; two **fresh** scratch
databases, outside the family credential wrapper with `BEADS_DOLT_PASSWORD`
absent, with no `.beads/` at or above them and no family endpoint in the
resolved config; binaries invoked by absolute path; the init verb never run in a
checkout or worktree; `/usr/local/bin` verified unchanged afterward; both
scratch databases deleted.

### One instrument failure of my own

A shell loop comparing three `list` variants reported **0 rows for all three**,
including the variant that had returned 3 moments earlier. Its inline parser
caught its own exception and reported the empty result as data. Re-running the
call raw — exit status, byte count and stderr captured separately — showed 1,820
bytes and 3 rows. The binary was fine; the probe was lying.

That is twice in one session that a probe of mine reported an empty result where
the truth was an error inside the probe, which is the same failure family this
package's own artifacts kept exhibiting. A parser that swallows its exception
and returns an empty collection is indistinguishable, at the call site, from a
genuine empty answer.

## What this does not settle

The `schema create-golden` leg is **untested**. A plausible reading is that it
needs no new capability — a golden schema reference is a database freshly
initialised by the target binary — but the *comparison* would then still need
the raw-SQL schema projection that blocks `schema.json`. That is a **hypothesis,
not a finding**: confirming it means re-fetching a 47MB binary, and it was
deliberately not done. Anyone who needs it settled should settle it explicitly.

The `remote add` and `sync push`/`sync fetch` legs remain unprobed, and the
raw-SQL route remains **unproven pending a server-mode probe**, exactly as
`route-proof-2026-08-22.md` left it.
