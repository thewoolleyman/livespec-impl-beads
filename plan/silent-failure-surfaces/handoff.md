# silent-failure-surfaces

**Ledger anchor:** bd-ib-cewr

Failures and losses that do not announce themselves — found while triaging the
2026-08-18/19 Honeycomb alert set, adopted as a track on 2026-08-19 at the
maintainer's instruction.

## Notation used in this document

- **Silent failure** — the system continued and reported success (or reported
  nothing) while losing information a human or a later agent needed.
- **Control** — a deliberate second measurement designed to produce the OPPOSITE
  answer. A check that cannot fail is not evidence, so each acceptance criterion
  in this track requires one.
- **Owned here / owned there** — which tenant's ledger holds the item. Items owned
  in another repo are tracked here for coherence only; this track does not
  implement them.

## What this track is

Five defects that share no subsystem — they span the Fabro dispatch path, the
beads-backed store, and the gate runner — but share a remedy shape: **make the
loss loud at the moment it happens**, rather than reconstructible afterwards by
someone who thinks to look.

Every one of them was caught by a second signal disagreeing. Not one announced
itself. That is the pattern this repo's `CLAUDE.md` "Verification discipline"
section was written for; these are live instances rather than hypotheticals.

## Members

**Status column added 2026-08-22.** `closed` = closed with verification;
`backlog` = filed and accepted, not yet started.

| Item | Tenant | Status | What is silent |
|---|---|---|---|
| `bd-ib-9ek4` | this repo | **closed** 2026-08-22, PR #1712 | Codex remote-compaction 404 kills context-heavy implement turns; `fabro logs` shows only `ACP turn failed` while the cause sits in `checkpoint.node_outcomes.implement.failure.causes`. Classified `transient_infra` and retried, though retry can never succeed. |
| `bd-ib-h2zj` | this repo | **closed** 2026-08-22, PR #1701 | The **conformant** store path silently destroys unmodeled metadata keys. The sanctioned close wrapper erased audit provenance a raw write had just preserved. |
| `livespec-dev-tooling-mt24` | livespec-dev-tooling | backlog | The gate runner's evidence probe reads only the parallel emitter's bracketed line, so every green **serial** aggregate reports `zero check targets completed`. The discriminator between a kill and a real pass fires on every real pass. |
| `livespec-dev-tooling-h7qp` | livespec-dev-tooling | backlog | The background guard prescribes `gate-start`/`gate-wait` and a doc, none of which exist in a fresh consumer worktree. A guard whose sanctioned alternative is missing invites engineering around the guard. |
| `overseer-izh7` | livespec-overseer | **closed** 2026-08-21 | A caller passes the beads-native `--status open`; the guard correctly refuses it (exit 3). 13 blocked ops in 3 days. The trigger flaps, so a resolved alert reads as "over" when it is not. |

## How this track was found

It began as inbox triage — "research the Honeycomb alerts, archive the stale
ones." The authoritative check showed all 20 triggers across five environments
reading `triggered: false`, i.e. nothing firing. That answer was wrong in an
interesting way: one trigger's 60-minute lookback empties between flaps, so
instantaneous trigger state cannot see a recurring condition. Reading the
underlying data instead of the gauge found the live one, and following its cause
produced the rest.

The lesson worth carrying: **an instantaneous gauge cannot answer a question
about recurrence.** Ask the data, not the alert state.

## Explicitly NOT in scope

- **`bd-ib-3kolea`** — the beads v1.0.5 → v1.1.2 upgrade epic, and its children
  `bd-ib-8azd` (closed 2026-08-19) and `bd-ib-ao3j`. Maintainer-excluded from this
  track on 2026-08-19: it is its own epic with its own plan
  (`plan/beads-v1-1-2-upgrade/`) and must not be absorbed here. This track touches
  it only as provenance — `bd-ib-9ek4` was found while diagnosing why one of its
  dispatches failed.
- **`bd-ib-rxf`** — tenant auto-backup `DOLT_BACKUP` grant. Same family, but
  already filed and already being routed to the tenant owner by the
  `livespec-orchestrator-beads-fabro-foreman` session. Do not duplicate it.
- **`bd-ib-g56f`, `bd-ib-w8sj`, `bd-ib-jm4efv`, `bd-ib-kttyks`, `bd-ib-d6v1`** —
  pre-existing items in this family. This session added live evidence to them as
  ledger comments rather than re-filing. `bd-ib-g56f` in particular predicted
  `bd-ib-9ek4`'s class exactly and would have surfaced the cause had it been fixed.

## Cross-repo coordination

`livespec-dev-tooling` and `livespec-overseer` items are filed in their own
tenants and surfaced to their foremen. Each was small enough to file directly
rather than warrant its own plan — two items and one item respectively. If either
grows past a handful of items, it should get its own plan in its own repo instead
of expanding this one.

**`livespec-dev-tooling` — accepted 2026-08-19.** That repo's foreman verified
both filings independently against source (not on this session's report) and
accepted both as P1. Three corrections and additions from that review, recorded
here because they sharpen the findings:

- `mt24` — the bare `::: just <t>` form is not the only uncounted one. The
  `(skipped)` form emitted at `just-check.sh:101` is **also** invisible to the
  counter. This session's filing named only the bare form.
- `mt24` — **the two emitters mark different events, and conflating them would
  be a new bug.** The serial bare line is written when a target *starts*; the
  parallel bracketed line is written when a target *completes*. A counter that
  simply accepted both formats would count starts and completions as the same
  thing. The recorded classification is: bracketed → completed; bare with no
  later bracket → started/in-flight; `(skipped)` in *both* emitters' spellings
  (`dispatcher:273` and `just-check.sh:101`) → skipped. Neither this session nor
  that foreman had named this until a live repro forced it.
- `mt24` — scope grew from a **formatting** fix to a **liveness** fix. A serial
  gate reports zero completed for its entire run, so a healthy in-progress gate
  is indistinguishable from a dead one — which is exactly when an operator most
  needs to know. Post-fix, an in-flight run should show started-target liveness.
  The truncated-log control still stands: a genuinely dead gate must still report
  zero completed.
- `mt24` — the fix lands in **dev-tooling's counter** (accept both formats),
  because the serial emitter lives in the *consumer* repo's
  `dev-tooling/just-check.sh`. Whether the two emitters should additionally be
  unified is a follow-on that repo will raise if the counter fix proves
  insufficient. Do not treat emitter unification as part of `mt24`.
- `h7qp` — **the shipping repo reproduces the consumer failure mode itself.**
  That foreman independently hit `Justfile does not contain recipe gate-start` in
  a fresh `livespec-dev-tooling` worktree hours before this filing, until
  `just bootstrap` materialized the gitignored `worktree.just` import. So this is
  not a consumer-integration gap; it is a fresh-worktree gap everywhere,
  including where the hook is authored.

Both are queued in that tenant behind one in-flight obligation and will be
implemented via its local-inference worker route.

## Next action

**Superseded 2026-08-22.** The paragraph this section used to carry — "await
prioritization; the host still runs `codex-cli 0.147.0`" — was both stale and
aimed at the wrong artifact, and is corrected below rather than deleted, because
it is a worked instance of this track's own subject.

Both local members are **closed with verification**. The current next action is a
maintainer call on the epic's disposition: close `bd-ib-cewr` now, recording the
two `livespec-dev-tooling` members as tracked-elsewhere, or hold it open until
that tenant disposes them. The plan is deliberately **not archived** — archiving
would assert a completeness the stated member set does not have.

### The `codex-cli 0.147.0` claim was wrong, and how

No `codex` CLI participates in a dispatch at all. The compaction request comes
from `codex-core` as pinned inside `@zed-industries/codex-acp`, running in the
Fabro **sandbox** — the run spec's `acp.command` is
`npx --no-install @zed-industries/codex-acp`. Factory host `hp-xubuntu` carries
no node, npm, npx or `codex-acp` anywhere on disk; its `~/.local/bin/codex`
(0.147.0) is never invoked. The sandbox image
`ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-agent-v1.32.0` bakes
`codex-acp@0.16.0`, and **0.16.0 is the newest published version** (46 on npm,
none later) — so the upgrade direction had no target, and the reclassification
was the only available remedy. That is what shipped.

The general shape, which is this track's whole subject: three separate
measurements of "which codex version runs" were each **healthy instruments
pointed at the wrong population**, and each returned a plausible answer with no
error. The discriminator that worked every time was a **known-positive control** —
*what must this return if it is aimed correctly, and does it?*

### Instrument correction for anyone re-measuring this

`fabro inspect <run> --json` **cannot** observe a compaction failure and returns
a clean zero even on known positives: its `conclusion.failure` records only the
last, downstream failure, and its `checkpoint.node_outcomes` may hold nothing but
`start`. Probed that way, all 30 recent failed runs read negative — including the
two that are positive. Use instead:

```
fabro dump <run> --server https://hp-xubuntu.perch-rudd.ts.net:32276 -o <dir>
grep responses/compact <dir>/events.jsonl
```
