# The sync leg: projection 11 is SERVED with real divergence, not the degenerate case

**Date:** 2026-08-22
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Item:** `bd-ib-ao3j` (the projections)
**Authorization:** foreman seat, local-only ruling; six standing conditions plus
the three fetch additions. Compliance at the end. Still **NOT** authorization to
run `bd-ib-ao3j`.

## What was missing

`route-proof-2026-08-22.md` recorded `remotes.json` as UNPROVEN.
`rig-blindness-mechanism-2026-08-22.md` then proved the file-remote leg —
`DOLT_PUSH` succeeded and `dolt_remote_branches` reported
`remotes/o4origin/main` at the same hash as local `main`.

**That result was the degenerate case by construction.** A single database that
pushes and immediately reads back its own cached ref *cannot* diverge, so the
comparison the projection exists to perform had nothing to find. Equality there
was guaranteed, not measured — the same "instrument that cannot return the other
answer" shape this thread keeps hitting.

This note supplies the missing measurement: two databases on one isolated server,
deliberately diverged, zero egress.

## Why local-only is better experimental design, not merely more cautious

The foreman's ruling carried an argument stronger than the one I had offered. I
had reasoned from egress. The better reason:

> A real DoltHub or GitHub remote does not merely add egress — **it confounds the
> probe.** You would be measuring divergence semantics and credential/network
> behaviour in one run, with no way to attribute a failure to either.

The local leg answers projection 11's actual question — can a cached remote head
diverge from local, and what does `schema_migrations` read through a cached ref.
Credentials, network failure and partial fetch are a *different* question and are
split into their own item, where an outward-facing action against a third-party
service also gets authorization on its own grounds rather than riding in on a
probe approval.

## The measurement

Both divergence directions, on `bd 1.2.2 (6c124203e)` against an isolated Dolt
`sql-server` at `127.0.0.1:13307`.

**Baseline — push parity, i.e. this morning's degenerate case, reproduced first
so the later difference is attributable:**

| | value |
|---|---|
| `local_head` | `nqq4st6k…ov10` |
| `cached_head` | `nqq4st6k…ov10` |

**Direction 1 — database `o4a`, local AHEAD of cached** (two further rows written
and committed, deliberately not pushed):

| | value |
|---|---|
| `local_head` | `ap5huamb…81fup` |
| `cached_head` | `nqq4st6k…ov10` |
| `in_sync` | **0** |
| `COUNT(*) FROM issues` | **5** |
| `COUNT(*) FROM issues AS OF 'remotes/o4origin/main'` | **3** |

**Direction 2 — database `o4b`, local BEHIND/unrelated to cached** (independent
history, then `DOLT_FETCH` without merge):

| | value |
|---|---|
| `b_local_head` | `9bj4ft9n…5rj3` |
| `b_cached_head` | `nqq4st6k…ov10` |
| `b_local_issues` | **1** |
| `b_cached_issues` | **3** |

So `DOLT_PUSH`, `DOLT_FETCH`, `DOLT_REMOTE('add', …)`, `dolt_remote_branches` and
`AS OF '<remote ref>'` all work, and the local-vs-cached comparison that is the
whole purpose of `remotes.json` returns a real, attributable difference in both
directions.

### `schema_migrations` through the cached ref

The projection specifies both "local `schema_migrations` rows" and "cached-ref
`schema_migrations` rows". Measured:

| | rows | max version |
|---|---|---|
| local | 53 | 53 |
| `AS OF 'remotes/o4origin/main'` | 53 | 53 |

**They are equal, and equality here is EXPECTED** — the same binary wrote both
commits and no migration ran between them. Reported as an observation, not as a
result.

What licenses reading that equality as real rather than as a broken read is that
**the identical `AS OF` mechanism returned 5 vs 3 on the issues count minutes
earlier.** The path demonstrably discriminates; it simply had nothing to
discriminate here. This is the same epistemics as the isolation diff below, and
the reason it matters is that a migration-crossing capture — exactly what the
rehearsal performs — *is* the case where these two numbers must differ, and a
reader who saw only the equality would have no way to tell a working probe from a
dead one.

### Controls

- **A nonexistent ref errors rather than reading empty:**
  `SELECT COUNT(*) FROM issues AS OF 'remotes/o4origin/no-such-branch'` →
  `Error 1105: branch not found`. So a successful cached-ref read is a real read.
- **An error is not the outcome.** `CALL DOLT_COMMIT('-Am', …)` returned
  `Error 1105: nothing to commit`, because bd's own auto-commit had already
  committed the writes. The head had nonetheless advanced, and the divergence
  measurement proves it. Reading that error as "the divergence failed" would have
  been wrong; the discriminator was measuring the head, not trusting the verb.

## Projection 11 verdict

**SERVED**, on real divergence rather than by construction. Every listed content
is reachable: `dolt_remotes` rows, `ACTIVE_BRANCH` via `active_branch()`, the
local active-branch head via `dolt_branches`, the cached
`remotes/origin/<branch>` head via `dolt_remote_branches`, local
`schema_migrations` rows, and cached-ref `schema_migrations` rows via `AS OF`.

Still not covered by this leg, and deliberately so: the migration-files sha256
manifest and the explicit absent-column markers are file-side concerns, not SQL
ones.

## Condition compliance

Standing six as before — not `bd-ib-ao3j`; version gate printed before connecting
(`1.2.2 (6c124203e)`, abort arm outside `{1.0.5, 1.1.2, 1.2.2}`, never v1.2.0 or
v1.2.1, both tarball `8140098a…321e8` and binary `54fc0e05…1e0e` re-verified
against the recorded pins before any invocation); direct before/after isolation by
me; target proven before any write; read-only against production with no host
mutation (`/usr/local/bin/bd` still `5f55fbfb…4637a3`, `LIVESPEC_BD_PATH` unset,
`bd` on `PATH` still `/usr/local/bin/bd`, repo tree clean); `uptime` first —
`25.44 / 22.23 / 23.31` on 18 cores at 10:07:57Z, stated as the current condition.

**Addition 1 — credential absent.** `printenv BEADS_DOLT_PASSWORD | wc -c`
returned **0** at run start and again before each database's first invocation.
`/var/lib/doltdb/databases` unreadable by the probe user. Nothing ran under the
family wrapper except the two deliberate tenant reads.

**Addition 2 — target proven per database, not just per binary.** Each of `o4a`
and `o4b` re-proved from its own scratch cwd immediately before its first write:
metadata asserted programmatically, and `SELECT DATABASE()` returning `o4a` /
`o4b` respectively — the connection naming itself back.

**Addition 3 — the diff, never hash equality.** 712 records before and after,
**0 added, 0 removed, 0 changed.** Reported as an observation, not the proof: an
empty diff is also what a broken check produces. What makes it meaningful is that
this same instrument fired earlier today, catching two single-comment writes among
710 records — one of them the foreman's own handoff entry.

**Teardown confirmed by absence:** server killed by PID (never `pkill -f`), 13307
clear, and a scratchpad-wide search for `bd`, `bd-1.*` and `beads_*` returns
nothing.
