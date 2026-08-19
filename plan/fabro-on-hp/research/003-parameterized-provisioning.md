# fabro-on-hp — parameterized provisioning, and a second silent config gap

**Written 2026-08-19.** This note records work done while the thread's three
maintainer gates were closed. It adds to `001`/`002` rather than correcting
them. Candidate artifacts live beside it in `003-artifacts/`.

## Why this exists

Every open child of this epic was blocked on a human step. Rather than idle,
this pass did the part of `bd-ib-l3nptz.14` that its destination decision does
**not** gate: the destination picks a directory, but the *substance* of `.14`
is parameterizing artifacts that currently hardcode one host. That is
verifiable now, against both live factories.

## What was verified against the live hosts

The configuration captured on `.14` on 2026-08-19 was re-read off hp and
confirmed **exactly** — unit, `otel.conf` drop-in, verifier fork, settings URLs,
serve mapping, `fabro 0.254.0 (8de6611)`. Treating that capture as a claim with
a timestamp rather than as fact cost one command and found two things it did
not contain.

## Finding 1 — hp runs half of vps's scheduler concurrency

Filed as **`bd-ib-l3nptz.16`** (p1, bug).

Measured on both live servers via `GET /api/v1/settings` — resolved behavior,
not file contents:

| Host | `server.scheduler.max_concurrent_runs` |
|---|---|
| vps | **10** (explicit `[server.scheduler]` in `settings.toml`) |
| hp | **5** (no `[server.scheduler]` table at all → built-in default) |

The `5` is the shipped default at the exact pinned build both hosts run:
`lib/crates/fabro-config/src/defaults.toml:44` at `8de6611`, read at that rev —
not from the working checkout, which sits on an unrelated branch, and not from
the many `max_concurrent_runs: 5` occurrences in test files, which are fixtures
and prove nothing about the default.

**This undercuts the epic's own purpose.** This plan exists because vps was
running load average 34–53 on 18 cores; PR #1474 moved all governed dispatch to
hp. So every governed dispatch now queues against 5 slots where it previously
had 10, on the machine with *more* headroom (16 cores, 30Gi). And it announces
nothing: dispatches simply queue. The symptom is "the factory is slow" — the
exact symptom this epic was opened to fix, so it invites the conclusion that
more hosts are needed rather than one setting.

It is **not** the deferred item. The scope event defers load-balancing *across*
factories; this is one host's own configured capacity, and it is a defect in
the discharge of scope carrier #4 ("Clone/adapt vps-info/services/fabro-server/
… for hp-xubuntu") — the adaptation copied the unit but not the server
settings.

**Deliberately not applied.** Scheduler concurrency on the fleet's primary
factory is an outward-facing infrastructure change and a genuine capacity
judgement, not a transcription. Same reasoning that left `.15` recommended
rather than applied.

## Finding 2 — the thread's own "correct form" for listing children is incomplete

The 09:55 timeline entry corrected id-prefix enumeration to "filter on the
`parent` field equal to the epic id." **That form is also incomplete**, and
filing `.16` proved it immediately.

The ledger has two child mechanisms:

1. An explicit `parent-child` dependency edge — populates `parent` in the
   JSON listing. `.15` has one.
2. The implicit dotted-id hierarchy — the tool honours it (it *refused* to add
   an explicit edge for `.16`: "already a child of bd-ib-l3nptz … would create
   a deadlock") but the JSON listing still reports `parent: null`.

Measured after filing `.16`: the `parent ==` filter returns **22** children and
does **not** include `.16`, which exists and is `backlog`. Neither filter is
complete alone — the prefix form catches `.16` and misses the seven non-dotted
children; the parent form does the reverse.

**The archive gate is safe**, and this was checked rather than assumed:
`undisposed_plan_child_ids` unions `client.children()` with dependency-edge
linkage, and returns all six undisposed children including `.16`. The exposure
is to humans and agents surveying by hand with the recorded form.

**Correct form: use the package primitive**
(`undisposed_plan_child_ids` / `client.children()`), not a hand-rolled
JSON-listing filter of either shape.

## What was built

One template plus a six-line per-host values file replaces the hand-edit clone
step. See `003-artifacts/README.md` for the file inventory, the five measured
per-host axes (the runbook predicted two), and why the verifier fork is
unnecessary.

The verification that matters: **rendering the single template reproduces each
host's real unit exactly**, with every difference intentional and named — for
hp, only the `.15` fix plus the `FABRO_CANONICAL_HOST` line that de-forks the
verifier; for vps against its committed unit, only the latter.

Every claim here has a negative control, because this thread has already been
bitten by checks that could not have returned the other answer:

- The shared verifier exits **0** against hp with `FABRO_CANONICAL_HOST` set
  and **1** without it.
- `check-settings.sh` passes both hosts against their own expectations, and
  flags the `.16` drift when hp is checked against vps's — so it would have
  caught this class automatically.

## What this does not do

It does not install anything. `install.sh` has never been run from this
directory, so its host guard and its supersede-the-old-drop-in step are
unexercised; landing `.14` must include one real run on hp. It does not choose
`.16`'s number: `hosts/hp-xubuntu.settings.expected` records the observed `5`,
not a chosen value. And it does not create the destination repository, which
remains the maintainer's call.
