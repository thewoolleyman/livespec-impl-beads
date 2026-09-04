# EUT usage inventory — family-wide sweep

**Addendum to [`eut-usage-inventory.md`](eut-usage-inventory.md), closing its
scope gap 1** ("only this repository was searched"). Still Deliverable 1 of
ledger item `bd-ib-3kolea.3`. Read-only research; no mutation of any kind.

**Measured:** 2026-08-19.

**Scope searched:** the tracked trees of ten sibling repositories under
`/data/projects` — `livespec`, `livespec-runtime`, `livespec-driver-claude`,
`livespec-driver-codex`, `livespec-driver-pi`,
`livespec-console-beads-fabro`, `livespec-overseer`, `livespec-dev-tooling`,
`livespec-orchestrator-git-jsonl`, and `dolt-server` — via `git grep` over
`*.py`, `*.sh`, `*.rs`, `*.toml`, and `*.md`. Repositories outside
`/data/projects`, and any untracked working-tree state, were **not** searched.

## Headline: the programmatic surface is concentrated here, and that is good news

No sibling repository carries its own Beads client. Searching all ten for
`bd_path`, `LIVESPEC_BD_PATH`, `/usr/local/bin/bd`, `BeadsClient`, or
`make_beads_client` returns:

| Repository | Code files invoking `bd` | Prose files instructing `bd` |
|---|---:|---:|
| `livespec` | 0 | 149 |
| `livespec-runtime` | 0 | 3 |
| `livespec-driver-claude` | 0 | 2 |
| `livespec-driver-codex` | 0 | 1 |
| `livespec-driver-pi` | 0 | 0 |
| `livespec-console-beads-fabro` | 0 | 33 |
| `livespec-overseer` | 1 *(a test)* | 34 |
| `livespec-dev-tooling` | 3 *(vendored + one test)* | 19 |
| `livespec-orchestrator-git-jsonl` | 0 | 5 |
| `dolt-server` | 2 *(server admin, not ledger)* | 2 |

The only genuine hits are a wrapper-detection **test** in `livespec-overseer`,
**vendored** third-party code plus one test in `livespec-dev-tooling`, and
`dolt-server`'s server-administration scripts, which manage the SQL server
rather than consume the work-item API.

**Consequence for the harness:** the Enemy Unit Tests, scoped to this
repository's `BeadsClient` plus `bd-guard/bd-guard.sh`, cover the family's
entire *programmatic* Beads surface. The proxy does not need to be replicated
per repository. This was an open question before the sweep; it is now answered,
within the stated scope.

## The console is Rust, and does NOT read the Beads tables

`livespec-console-beads-fabro` is a Rust workspace (40 `.rs` files). It was the
most plausible candidate for a second, uncovered consumer — a non-Python client
that a schema migration could break invisibly.

It is not one. `crates/console-eventstore/src/lib.rs` issues SQL against its
**own** `events`, `commands`, and `checkpoints` tables using `?1` positional
placeholders (SQLite, not the MySQL-protocol Dolt tenant). Its `Command::new`
call sites are overwhelmingly `tmux`, not `bd`.

So the console does **not** query the Beads `issues` table directly, and
migrations 0050–0053 cannot reach it through a private SQL path. Recorded
explicitly because "the console talks to the ledger" is a reasonable assumption
that happens to be false, and acting on it would have widened this upgrade's
blast radius for no reason.

## Prose surface, family-wide

Verb occurrences across all ten repositories' tracked `*.md`:

| Verb | Count | In `BeadsClient`? |
|---|---:|---|
| `show` | 187 | yes |
| `update` | 131 | yes |
| `create` | 105 | yes |
| `ready` | 98 | **NO** |
| `list` | 98 | yes |
| `init` | 87 | **NO** |
| `close` | 47 | yes |
| `dep` | 36 | yes |
| `config` | 26 | partial — only `config set` |
| `comment` | 20 | yes |
| `comments` | 14 | yes |
| `reopen` | 10 | **NO** |
| `doctor` | 10 | **NO** |
| `bootstrap` | 7 | **NO** |
| `search` | 6 | **NO** |
| `children` | 5 | yes |
| `version` | 3 | **NO** |
| `export` | 2 | **NO** |
| `defer` | 2 | **NO** |
| `label`, `delete` | 1 each | **NO** |

Eleven verbs are instructed in prose but never called by the client. Two
deserve individual attention:

- **`bd ready` (98 occurrences) is the largest uncovered verb in the family.**
  It is the ranking read operators lean on to choose next work. The guard
  treats it as a distinct scan phase precisely because `bd ready --claim`
  writes a non-lifecycle status while a bare `bd ready` only lists. A behavior
  change here would alter what every operator sees as "next", while no
  programmatic test would notice.
- **`bd init` (87 occurrences)** is heavily documented and simultaneously
  **forbidden** in a checkout by this repo's `CLAUDE.md`, because it
  auto-commits and clobbers `.beads/`. Most occurrences are almost certainly
  prohibition or historical narrative rather than instruction. The EUTs should
  cover it only to the depth our prose actually promises, and must never run it
  against a governed checkout.

## Counting caveat

These are raw occurrence counts over tracked Markdown, including
`SPECIFICATION/history/**` snapshots, which repeat text across archived
revisions and therefore inflate absolute numbers. The counts are reliable for
**presence and relative prominence**, not as a census of distinct instructions.
`livespec`'s 149 prose files dominate the totals for this reason.

The complementary risk from the parent note still stands: verb-frequency
scanning can under-count a command mentioned once in unusual phrasing. Neither
technique alone is exhaustive, and this addendum does not claim exhaustiveness —
it claims the scope stated at the top.

## What this changes for `bd-ib-3kolea.3`

1. **Deliverable 2 stays single-repo.** No per-repo proxy is needed.
2. **Deliverable 1 is now complete** for the programmatic half, within the
   stated scope, and substantially complete for the prose half.
3. **The uncovered-verb list is the concrete prose-coverage backlog**, led by
   `bd ready`.
4. **Scope gaps 2 and 4 from the parent note remain open**: the phrasing
   sensitivity above, and runtime-only surfaces invoked inside a dispatched
   factory sandbox image.
