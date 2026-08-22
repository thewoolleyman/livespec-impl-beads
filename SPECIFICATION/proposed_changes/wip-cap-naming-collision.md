---
topic: wip-cap-naming-collision
author: claude-opus-5
created_at: 2026-08-22T04:46:17Z
---

## Proposal: Capacity surfaces must name which ceiling they mean

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Requires every operator-facing surface that reports the per-repo WIP cap, or
refuses a dispatch on capacity, to identify it as the per-repo LEDGER cap and to
state that host-run concurrency is governed separately by the Fabro scheduler;
and forbids the Orchestrator from reporting or deriving capacity from the Fabro
scheduler's own limit. Explicitly rejects renaming `dispatcher.wip_cap`, recording
why, so the decision is not re-litigated. Adds Scenario 57 covering the refusal
text, and flags the `tests/heading-coverage.json` co-edit the accepting revise
pass must make.

### Motivation

`dispatcher.wip_cap` (`.livespec.jsonc`, per-repo, ledger-level, owned by this
Orchestrator) and `server.scheduler.max_concurrent_runs` (`~/.fabro/settings.toml`,
per-server, owned by the Fabro daemon) are different objects. Both are called a
"cap" in ordinary use, both currently hold the value 10, and they sit one
configuration file apart.

THE MEASURED COST, which is why this is filed rather than noted. On 2026-08-22 a
foreman session reasoned from the Fabro per-server cap, concluded the `hp` factory
had eight free slots, and reported that to the maintainer. It was wrong, and the
correction required a full source trace through `claimed_active_count` to
establish that the Orchestrator's counter never contacts a factory at all.

THE EVIDENCE THAT PROSE ALONE IS INSUFFICIENT is the strongest part of this
motivation. `contracts.md` ALREADY carries a section — §"Host concurrency belongs
to the Fabro scheduler" — whose entire purpose is to explain that these are
different objects and that the Orchestrator owns no host-level ceiling. That
section was ratified, and the confusion happened anyway. A specification that
states a distinction in prose, and is then misread by an operator acting in good
faith, has identified a surface obligation it has not yet imposed.

The confusable moment is the act of READING — reading a refusal, or reading a
config value — not the act of naming a key. That is why this proposal places the
obligation on the surfaces that report the number.

### Proposed Changes

The Orchestrator MUST keep the `dispatcher.wip_cap` key name. A rename is
explicitly REJECTED by this proposal, and the rejection is recorded here so it is
not re-litigated: renaming does not remove the confusable moment. Two ceilings of
the same value would remain one config file apart, and an operator reading
`max_concurrent_runs = 10` beside a refusal saying `ledger_wip_cap=10` still has
two tens and no discriminator. The cost, by contrast, is concrete — a coordinated
migration across every governed repo committing the key, a deprecation window, and
re-establishing the ratified `0` dispatch-off value together with its
minimum-above-zero guard clause on a new name. A future propose-change MAY revisit
this if the disambiguation below proves insufficient.

What the operator lacked on 2026-08-22 was not a better key name. It was a
statement of WHICH object the number bounds and what the OTHER ceiling is — content
a diagnostic can carry and an identifier cannot.

### Amend §"Per-repo WIP cap"

Append a new paragraph:

Every operator-facing surface that reports `wip_cap`, or that refuses a dispatch on
capacity grounds, MUST identify the value as this repo's PER-REPO LEDGER cap rather
than by the unqualified word "cap". Such a surface MUST NOT present the value in a
form readable as a host-wide or per-server ceiling. A capacity refusal MUST state
that host-run concurrency is governed separately (§"Host concurrency belongs to the
Fabro scheduler") and is NOT what the refusal reports. These requirements bind the
refusal text and any status, doctor, or attention surface that echoes the cap; they
do NOT change what is counted, which §"Per-repo WIP cap" already governs.

### Amend §"Host concurrency belongs to the Fabro scheduler"

Append a new paragraph:

The Orchestrator MUST NOT report the Fabro scheduler's
`server.scheduler.max_concurrent_runs` as its own bound, and MUST NOT derive
available capacity from it on any surface. Reading that value to reason about
this repo's admission is a category error: the two ceilings govern different
objects and coincide in value only by accident. A surface that names host capacity
at all MUST attribute it to the Fabro server and MUST NOT imply the Orchestrator
enforces it.

### Add `SPECIFICATION/scenarios.md` §"Scenario 57"

```gherkin
## Scenario 57 — A capacity refusal names which ceiling it means

Feature: Capacity surfaces distinguish the per-repo ledger cap from the Fabro scheduler's host limit
  As an operator reading a dispatch refusal
  I want the refusal to say WHICH ceiling was reached
  So that I do not reason from the host scheduler's unrelated limit

Scenario: A capacity-deferred dispatch identifies the per-repo ledger cap and disclaims the host limit
  Given a per-repo wip_cap of 10 committed in `.livespec.jsonc`
  And the Fabro server's `server.scheduler.max_concurrent_runs` is also 10
  And this repo holds 10 counted active claims
  When the Dispatcher refuses an admission-eligible ready item on capacity
  Then the refusal identifies the exceeded ceiling as this repo's per-repo ledger cap
  And the refusal does not present the value as a host-wide or per-server limit
  And the refusal states that host-run concurrency is governed separately by the Fabro scheduler
```

### Co-edit required at revise time

The revise pass that accepts this proposal MUST add a `tests/heading-coverage.json`
entry for the new `## Scenario 57 — A capacity refusal names which ceiling it means`
H2 in `scenarios.md`, per this repo's revise co-edit discipline. The `test` value
MAY be the literal `"TODO"` with a non-empty `reason`.

### What this proposal deliberately does NOT do

It does NOT alter what `wip_cap` counts, and it MUST NOT be read as re-opening the
host-level ceiling that §"Host concurrency belongs to the Fabro scheduler" refuses.
It adds a reporting obligation only.

### Reconciliation with the sibling pending proposal (added 2026-08-22)

`wip-cap-bound-honesty` is pending against the SAME section and must be
reconciled with this one at revise time. Surfaced by the post-step objective
doctor phase for this proposal; recorded here because the revise pass reads these
files and MAY process them independently via `--only-topic`.

THE TENSION, stated plainly because it is a real one. This proposal mandates the
label "per-repo LEDGER cap" as the disambiguator against the Fabro scheduler's
host limit. The sibling proposal establishes that `wip_cap` bounds COUNTED CLAIMS
and explicitly NOT rows at ledger status `active`. Read together by an operator,
"ledger cap" invites the reading "a cap on ledger rows" — which is precisely the
misconception the sibling proposal exists to remove. The word "ledger" is doing
SCOPE work here (this Orchestrator's layer, as against the Fabro daemon's), not
COUNTING work, but nothing in the label says so.

RESOLUTION THE ACCEPTING REVISE PASS MUST MAKE. Adopt one disambiguating label
across BOTH proposals. "Per-repo CLAIM cap" is the recommended choice: it carries
the same scope contrast (per-repo, as against the Fabro server's per-server
scheduler limit) while naming the counted quantity correctly. If that label is
adopted, this proposal's mandated wording and its Scenario's `Then` steps MUST be
updated to match, and the sibling's counted-claims definition governs what the
label MEANS. Accepting either proposal WITHOUT settling the label MUST NOT
happen — a half-adopted vocabulary is worse than today's, because both clauses
would then read as freshly ratified.

Both proposals also append to §"Host concurrency belongs to the Fabro scheduler".
The two additions are complementary, not contradictory — this one forbids
reporting the Fabro limit as ours, the sibling records that the counted-claim
definition is computed from local state only — and both SHOULD be taken.

### The recommended label presumes a scope that is NOT yet settled (added 2026-08-22)

A rider to the section above, recorded here because a `--only-topic` revise pass
over THIS file alone would otherwise adopt the label without knowing the question
below is open. The finding itself is on the sibling proposal
`wip-cap-bound-honesty`, under "The locality clause does not say WHICH local
state, and it matters", and on `bd-ib-snyquw.5`.

"PER-REPO claim cap" CONTAINS A SCOPE WORD, and that word is the unsettled one.
Measured 2026-08-22, `wip_cap` is scoped to the `--repo` PATH, not to the tenant:
both of the counter's inputs — the dispatch-lock directory and
`<repo>/tmp/fabro-dispatch-journal.jsonl` — resolve from that path, so two
checkouts of ONE repository, read in the same second against ONE ledger holding 11
rows at `active`, reported DISJOINT counts of 2 and 1. N checkouts admit up to
N x `wip_cap`.

So "per-repo" is doing exactly the kind of work this proposal exists to stop a
label doing: it reads as a guarantee about the repository, and today it is a
guarantee about one checkout of it. This proposal's own Motivation is that a
distinction stated in prose was misread in good faith; a label that overstates its
scope is the same failure one level up.

WHAT THIS DOES AND DOES NOT ASK. It does NOT reject "per-repo CLAIM cap", and it
does not propose an alternative label here — picking one before the scope is
settled would repeat the mistake. It asks that the accepting revise pass settle
the SCOPE question first (the sibling states the two options and recommends one),
and only then fix the label, so the chosen word is true of the bound that was
actually ratified. If the scope is settled as tenant-wide, "per-repo CLAIM cap"
is correct as recommended and nothing here changes. If it is settled as
per-checkout, the label MUST say so instead of saying "per-repo".

This does not disturb anything else in the reconciliation above: one label across
both proposals, and neither accepted without settling it, still stand.

### Renumbering hazard and the paste-ready co-edit (added 2026-08-22)

Two mechanical corrections to the instructions above, both measured against
`SPECIFICATION/scenarios.md` and `tests/heading-coverage.json` at master
2026-08-22. Neither changes what this proposal asks the specification to say.

"THE NEXT FREE INTEGERS" IS AMBIGUOUS AND ONE READING IS WRONG. The sibling
proposal's numbering note tells the accepting pass to "renumber these to the next
free integers rather than duplicating one". Measured: `scenarios.md` holds 53
scenarios numbered 1..56, and **2, 3 and 49 are RETIRED** — absent from the file
while every number around them is present. Those three are "free" by the literal
wording. They MUST NOT be reused: a retired number is referenced by history and by
prior revisions, so re-issuing one silently aliases a new behavior onto an old
citation. Renumber by appending ABOVE the current maximum (56 today), never into a
gap. Verify the maximum at revise time rather than trusting this number, since
another proposal may land first.

AS OF THIS WRITING NO RENUMBERING IS NEEDED. 57, 58 and 59 are all unused, so this
proposal's `57` and the sibling's `58`/`59` are correct exactly as drafted provided
this proposal is accepted first, as its note already assumes.

THE CO-EDIT, PASTE-READY. The required `tests/heading-coverage.json` entry for this
proposal's scenario, matching the shape of the 95 entries already in that file (note
the em dash in `heading`, U+2014, which must match the H2 byte-for-byte):

```json
{
  "heading": "## Scenario 57 — A capacity refusal names which ceiling it means",
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "test": "TODO",
  "reason": "Ratified with the wip-cap-naming-collision revision; capacity surfaces must name which ceiling they mean. Real test ID to follow."
}
```

If the label is changed when the pass settles the shared vocabulary, the scenario
title MAY change with it — in which case the `heading` value above MUST be updated
to match the H2 exactly, or the heading-coverage check will fail on a
near-miss string.
