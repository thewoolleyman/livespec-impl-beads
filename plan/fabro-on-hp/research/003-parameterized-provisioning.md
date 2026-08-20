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

## Correction to Finding 1, measured the same day

Finding 1 above is left as written, because the record of what I believed
matters. Two steps of its reasoning were wrong, in opposite directions, and
the remedy it implied was unsupported. All of it was caught by measuring the
running host instead of reasoning from configured numbers.

**Measured on hp while four runs were executing:** 16 cores, 30Gi RAM, 23Gi
available. The per-run plan is *enforced*, not advisory — `workflow.toml`
sets `cpu = 4` / `memory = "8GB"` and `docker inspect` shows
`Memory=8000000000` on every live sandbox. Actual usage per container was
**245MiB–659MiB against the 7.451GiB cap (3–9%)**, about 1.7GiB across all
four. CPU was the busier axis: 403%, 161%, 102%, 2% — roughly 6.7 of 16
cores. Zero OOM kills in 24 hours.

**Error 1 — the finding reads as "match vps's 10".** At nominal reservation
that would demand 40 cores and 80GB on a 16-core / 30Gi machine. vps's 10 was
chosen for 18 cores and 94Gi. Not a defensible target on resources alone.

**Error 2 — the opposite overcorrection, which I also briefly believed.** The
same nominal arithmetic run the other way says hp at 5 slots reserves 40GB on
a 30Gi host and is *already* unsafe. Also wrong: the 8GB is a per-container
**cap, not a reservation**, nothing bounds the sum, and measured usage is
~0.5GB per run. Nominal arithmetic overstates memory risk here by more than
an order of magnitude.

**What survives.** hp's `5` is an **unchosen default**, not a decision — that
is the entire defect, and it is unchanged. The number may even be roughly
right; the finding implied it was clearly wrong, which I could not have known
without measuring.

**A defensible target, on correct evidence.** Cores divided by the per-run
`cpu = 4` gives a nominal 4 slots for hp and 4.5 for vps. vps is set to 10,
i.e. deliberately over-subscribed ~2.2x — sound and clearly intentional,
since these runs are mostly idle waiting on the model, which is exactly what
the measurements show. The same convention puts hp near 8–10. So the original
conclusion (hp should be higher) stands, but it rests on measured idleness
and a consistent over-subscription factor, **not** on the nominal-reservation
arithmetic the finding implied. CPU, not memory, is the axis to watch: five
simultaneously-busy runs would demand ~20 cores on 16.

`bd-ib-l3nptz.16` has been **downgraded p1 → p2** accordingly. It is an
unrecorded configuration decision with no measured harm, not a live hazard
like `.15` — which is a non-self-healing loop that has already killed a run.

**Method note.** Both wrong intermediate answers came from reasoning about
configured numbers rather than measuring running ones, and both were
internally consistent and confidently wrong. `docker stats` and the kernel
journal settled in one command what two rounds of arithmetic could not.

## Where these artifacts went, 2026-08-20

`003-artifacts/` no longer exists in this research store. The destination
decision recorded above as "the maintainer's call" was made on 2026-08-20 and
the artifacts moved to their real home. See `004-destination-decision.md` for
the choice, the reasoning, and what was verified across the move. Every
reference to `003-artifacts/<file>` above should now be read as
`fabro-hosts/services/fabro-server/<file>`.
