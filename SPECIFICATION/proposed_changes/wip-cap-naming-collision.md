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
