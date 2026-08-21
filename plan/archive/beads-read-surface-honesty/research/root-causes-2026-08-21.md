# Why a competent grooming pass could not read its own ledger

Measured 2026-08-21 by session `beads-problems`, reproducing every claim
against two live tenants before recording it.

## Provenance

The `livespec-dev-tooling-grooming` session completed a seven-invariant
grooming pass and closed its report with a section titled "Three
instruments that lied to me". It had not been careless: it caught all
three by cross-checking, and it recorded them on its seat anchor for the
next session. That is the behaviour this fleet's verification discipline
asks for, and it still cost most of a pass.

The question this note answers is not "what did that session get wrong".
It is **why a careful operator, following the grooming prose exactly, is
routed onto a read surface that answers wrongly without saying so** — and
why the answer to that is structural rather than a matter of care.

## Notation

- **Sanctioned read** — `list-work-items --json`, this plugin's own
  work-item projection. Trap-free, and what the prose means by "the
  machine projection that merges native and metadata fields".
- **Raw read** — a hand-composed `bd ... --json` call. Every trap below
  lives here.
- **Population** — the record set a claim was measured over. Stated for
  every number in this note, because a clean result over an unstated
  population is not evidence.
- **`omitempty`** — the Go JSON convention where a field is omitted from
  the object entirely when it holds its zero value, rather than emitted
  as `null` or `[]`.

Two tenants are cited. `livespec-dev-tooling` (523 records at time of
measurement) is where the grooming pass ran. `livespec-orch-beads-fabro`
(629 records) is this repo's own tenant, used to confirm the projection
findings.

## The seven root causes

### RC1 — `bd show --json` is strictly lossier than `bd show`, silently

`bd show <id>` prints a `COMMENTS` section with every comment body.
`bd show <id> --json` returns `comment_count` and **no `comments` key at
all**. Measured on `bd-ib-1w1h`: the plain form renders the full comment;
`--json` emits `comment_count: 1` and 15 keys, none of them `comments`.

An agent that writes a handoff comment and then reads the record back
through `--json` — the obvious verification, and the one the plan prose
asks for ("read it back before declaring it recorded") — finds no comments
and concludes **the write was lost**. It was not. This fails in the single
most alarming direction available.

`bd show --json` also returns a **one-element array**, not an object, so
the natural `payload["id"]` raises rather than returning the id.

The package already knows this. The `list_comments` docstring in
`_beads_client.py` says so verbatim: "`bd show` does NOT carry comment
bodies (only `comment_count`), so comment reads need this dedicated verb."
That knowledge lives in a Python docstring, which is not a surface a
hand-driving operator reads.

### RC2 — sparse records are indistinguishable from lost data

The `--json` record is `omitempty`-sparse. Across all 523
`livespec-dev-tooling` records, 25 distinct keys appear and only 10 appear
on every record:

| Key | Present |
|---|---:|
| `id`, `title`, `status`, `priority`, `issue_type`, `created_at`, `updated_at`, `dependency_count`, `dependent_count`, `comment_count` | 523/523 |
| `description` | 522/523 |
| `owner`, `created_by` | 497/523 |
| `closed_at` | 298/523 |
| `close_reason` | 281/523 |
| `labels` | 243/523 |
| `dependencies` | 194/523 |
| `metadata` | 183/523 |
| `notes` | 155/523 |
| `parent` | 116/523 |
| `assignee` | 87/523 |
| `acceptance_criteria` | 65/523 |
| `design`, `spec_id` | 7/523 |
| `external_ref` | 4/523 |

Seeing `labels` absent on 280 of 523 records, the grooming session
concluded the listing had dropped them and fell back to the server-side
`--label` filter as authoritative.

**That conclusion was wrong, and this note corrects it.** Control, run
three ways, each designed to produce the opposite answer if the listing
were lossy:

| Label | server-side `--label` | client-side from listing | symmetric difference |
|---|---:|---:|---:|
| `intake:triaged` | 69 | 69 | **0** |
| `origin:freeform` | 201 | 201 | **0** |
| `needs-regroom` | 3 | 3 | **0** |

And the `--all` form versus the `--status all` form, compared record by
record across all 523: identical id sets, and **zero** records whose
`labels` value differs. The 280 records without the key genuinely carry no
labels.

So the defect here is not data loss — it is that **`omitempty` sparseness
and genuine omission are the same observation**, and an operator who
reaches the correct-sounding conclusion has no way to tell. The correct
reading requires knowing the encoding convention, which nothing states.

There *is* a real way to lose labels: the `--skip-labels` flag, whose own
help text reads "The labels field in output will be empty regardless of
actual labels." Nothing in the grooming path passes it. Worth knowing it
exists, because it produces exactly the failure that was mistakenly
inferred here.

### RC3 — `dependencies` is one heterogeneous array with a non-obvious key

Dependency rows key the target as **`depends_on_id`** — not `id`, `target`,
or `to`. Every naive accessor yields `None`, and a tenant of perfectly
sound edges reads as a tenant of dangling ones.

Worse, six edge types share the one array. Measured over all 261
dependency rows in `livespec-dev-tooling`:

| Type | Rows | Blocker? |
|---|---:|---|
| `parent-child` | 116 | no |
| `blocks` | 93 | **yes** |
| `relates-to` | 26 | no |
| `discovered-from` | 23 | no |
| `related` | 2 | no |
| `duplicates` | 1 | no |

**168 of 261 rows (64%) are not blockers.** Any filter treating the array
as a blocker list is wrong for the majority of its own input, and wrong in
the direction of inventing blockers that do not exist.

### RC4 — the trap catalogue is in the wrong repo

This repo's `AGENTS.md` carries a good beads-trap catalogue: the
`--status all` requirement, the dead `bd ready`, the child-enumeration
union, the `status == ready` blocker blindness.
`livespec-dev-tooling`'s `AGENTS.md` carries **none of it** — zero
occurrences of "status all", no "Beads runtime prerequisites" section,
only a "Ledger access needs the credential wrapper" note.

The grooming pass ran in `livespec-dev-tooling`. It hit these traps in a
repo that had been told nothing about any of them, and re-derived the trap
set from scratch at its own expense.

RC7 explains why that repo was allowed to be in that state.

### RC5 — the grooming prose names an abstraction with no referent

`livespec-overseer`'s `prose/grooming.md` (435 lines) contains **no `bd`
command and no named read primitive**. It asks for "the all-records,
all-statuses, machine-readable ledger view", "the merged projection", "the
machine projection that merges native and metadata fields" — correct
abstractions, each with no stated implementation.

Runtime-neutrality is deliberate and right. But the prose also carries a
**"Measured Traps"** section — the exact place a JSON-read trap belongs —
and every trap in it is a lifecycle, status, or dispatch trap. None
concerns the shape of the record the operator must parse. So the operator
is told what to measure, told the traps that matter, and left to invent
the read.

### RC6 — the sanctioned read cannot answer two of the seven invariants

This is the deepest cause, and it is what forces the raw path.

`list-work-items --json` is **dense** — every one of 28 keys on all 629
records of this repo's tenant, no `omitempty` sparseness — and it already
solves RC3: `depends_on` carries **blocks-only**, correctly discarding
`parent-child`. Verified on `bd-ib-3kolea.2`, whose raw edge list is one
`parent-child` plus four `blocks`, and whose projected `depends_on` is
exactly those four.

But the projection **omits `parent` and omits `labels` entirely**, against
170 `parent-child` edges live in the tenant. Set against the seven
invariants the grooming pass must leave true:

| Invariant | Needs | Answerable from sanctioned read? |
|---|---|---|
| 1 · rolls up to a plan epic | `parent` | **no** |
| 2 · acceptance criteria | `acceptance_criteria` | yes |
| 3 · lifecycle statuses | `status` | yes |
| 4 · delimiter hazard | `description` | yes |
| 5 · acceptance split ↔ label | `labels` | **no** |
| 6 · cross-repo edges | `depends_on` | yes |
| 7 · routing field | — | not modelled anywhere |

Invariants 1 and 5 are **structurally unanswerable** through the
trap-free surface. The operator must go raw, and going raw is where RC1,
RC2 and RC3 live. The grooming session's headline finding — 169 of 224
open items unparented — is precisely an invariant-1 measurement, which is
why it was computed on the trapped path and then had to be rescued by
recomputation.

The cause is a modelling gap, not a serializer bug: `WorkItem`
(`livespec_runtime/work_items/types.py`) has no `parent` and no `labels`
field, and the projection is `asdict(item)`. Labels are surfaced one
boolean at a time instead — `awaits_scope_override` is documented as
"backed by the `awaits-scope-override` beads label" — so each new label
that matters needs a new field, and a label set that is merely *read*
gets no field at all.

An orchestrator-side fix exists that needs no `livespec-runtime` change:
emit `parent` and `labels` as **computed flat keys** in
`_work_item_to_dict`, exactly as `lane`, `lane_reason` and
`dispatch_factory` are already emitted without being `WorkItem` fields.

### RC7 — the obligation row that should prevent RC4 runs over 2 of 10 members

This is the enforcement-layer instance of the same defect, and it is the
one worth fixing first, because it is why RC4 was reachable at all.

livespec core's ratified `SPECIFICATION/contracts.md` §"Fleet
agent-instruction core" is unambiguous about its population:

> Every livespec-governed repo — `livespec` itself, every
> `livespec-orchestrator-*` plugin, **`livespec-dev-tooling`**,
> `livespec-runtime`, and every future sibling generated from the copier
> template … MUST carry a **fleet-universal agent-instruction core**

…and about what it contains: "the repository mutation protocol …, the
agent prerequisites for plugin work, the daily-commands surface, the
revise co-edit discipline, and — **for beads-backed members** — the
**beads runtime prerequisites**." It then states the enforcement
obligation outright: presence of the core and "the beads-runtime section
in beads-backed members … MUST be enforced fleet-wide by the shared
fleet-membership obligation suite … so that drift in any member is
un-mergeable".

The check exists and is correct. `livespec-dev-tooling`'s
`fleet/_rows_instructions.py::assert_agent_instruction_surface` asserts
exactly the five headings, named in `REQUIRED_AGENTS_HEADINGS`. But its
registration in `_contract_rows.py` carries
`applies_to=TEMPLATE_BORN_CLASSES`, and

```python
TEMPLATE_BORN_CLASSES = frozenset({"impl-plugin"})
```

**one of the seven classes in `REPO_CLASSES`.** The row is structurally
incapable of running against `core`, `enforcement-suite`,
`driver-plugin`, `library`, `console`, or `control-plane-tool` — that is,
against 8 of the 10 members the manifest lists.

Measured on **`origin/master`** (not the working tree) for all ten
members of `livespec/.livespec-fleet-manifest.jsonc`, counting the five
required H2 headings. Every one of the ten carries `.beads/config.yaml`,
so every one is a beads-backed member:

| Repo | Class | Core headings | Row runs? |
|---|---|---:|---|
| `livespec` | core | 5/5 | no |
| `livespec-orchestrator-beads-fabro` | impl-plugin | 5/5 | **yes** |
| `livespec-orchestrator-git-jsonl` | impl-plugin | 5/5 | **yes** |
| `livespec-driver-claude` | driver-plugin | 2/5 | no |
| `livespec-console-beads-fabro` | console | 2/5 | no |
| `livespec-dev-tooling` | enforcement-suite | **1/5** | no |
| `livespec-driver-codex` | driver-plugin | **1/5** | no |
| `livespec-driver-pi` | driver-plugin | **1/5** | no |
| `livespec-runtime` | library | **1/5** | no |
| `livespec-overseer` | control-plane-tool | **1/5** | no |

**Seven of ten governed members carry two or fewer of the five required
headings. Six of ten lack "Beads runtime prerequisites" entirely**, the
section the contract makes mandatory for beads-backed members — which all
ten are.

The row reports **PASS**, because it is green over the two members it can
see. It is the same failure as every trap above, one layer up: **a clean
result over a population narrowed below what the contract names,
presented as evidence rather than as partial coverage.** It is also the
mechanical twin of the grooming session's own invariant 7, which that
session reported honestly as *unmeasured* rather than green. Nobody
flagged this one, because a row that says PASS does not invite the
question.

The remedy has two independent halves, and the second is the durable one:

1. Widen `applies_to` to the contract's population, and let the
   consequent findings drive the backfill. Arming ahead of adoption is
   what reddened five repos in `plan/rop-railway-enforcement/`, so the
   backfill lands first and the widening arms after — the same
   ship-disarmed-then-arm sequence the row's own comment block records
   for 2026-08-20.
2. Stop letting a row's `applies_to` silently disagree with the contract
   clause it enforces. A row narrower than its clause should have to say
   so — as a recorded, reviewable exemption — rather than passing
   quietly. Absent that, the next `applies_to` set written a class too
   narrow fails exactly this way and equally silently.

## Relation to existing ledger items

- **`bd-ib-1w1h`** (`acceptance`) — the direct predecessor. Same class,
  one instance: `bd ready` returns an empty set while 18 items are ready.
  Its criterion 2 established the rule this thread follows — sibling-repo
  prose is filed as findings in the owning repo, never edited from here.
- **`bd-ib-d9gf`** (`backlog`) — `list_work_items --json` drops
  `merge_sha` / `pr_number` because a hand-enumerated allowlist overwrites
  `asdict`'s complete result. Same family as RC6 and a distinct defect:
  that one is the serializer, RC6 is the model. Its stated remedy —
  derive the emitted key set instead of hardcoding it — applies to both.
- **`bd-ib-cewr`** (`silent-failure-surfaces`) — thematically identical
  ("make the loss loud at the moment it happens") and deliberately **not**
  the home for this work. That plan's own text sets the rule: "If either
  grows past a handful of items, it should get its own plan in its own
  repo instead of expanding this one." This is six.

## What this thread does not cover

- Invariant 7's routing field. No item in either tenant carries one, and
  the grooming session correctly reported it unmeasured rather than
  green. Whether the field should exist is a grooming-contract question,
  not a read-surface one.
- The grooming pass's own blocked triage decision — roughly 19 threads
  wanted against an allowance of 2. That is a maintainer triage call and
  is unaffected by anything here.
- Changing `bd`'s own output semantics. Upstream, out of scope, and the
  `omitempty` convention is not a bug in `bd`.
