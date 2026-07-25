---
topic: wip-cap-zero-dispatch-off
author: claude-fable-5
created_at: 2026-07-23T04:53:40Z
---

## Proposal: wip_cap 0 is the documented dispatch-off value

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

Bless a committed `dispatcher.wip_cap` of `0` as a valid value and as the sanctioned consumer-project dispatch-off posture value. `wip_cap`'s value domain becomes a non-negative integer (`0` for `wip_cap` ONLY — the per-item-overridable integer caps stay positive); every surface that validates or reads `wip_cap` MUST accept `0`, and a read of a committed `0` MUST resolve to `0` rather than falling back to the default, so the admission valve's capacity condition (`count(active) < wip_cap`) holds for no item and the Dispatcher admits nothing; and a schema or validation change imposing a minimum above `0` on `wip_cap` MUST NOT land without a propose-change explicitly retiring the clause. One paired Gherkin scenario is added.

### Motivation

The homelab consumer project has descoped factory dispatch and committed `dispatcher.wip_cap: 0` in its `.livespec.jsonc` as its dispatch-off switch, governed by its own specification (homelab SPECIFICATION v005, `non-functional-requirements.md` §"Dispatch-off posture"), which names the committed `wip_cap` value of `0` as one of the posture's two verifiable facts and explicitly defers the value's meaning to this spec: "What the implementation orchestrator does with configuration and credentials is defined by its own specification and is not restated here." This spec is currently silent on `wip_cap`'s value domain — §"Per-repo WIP cap" states only the default and the ceiling behavior — and the shipped implementation treats `0` as out-of-domain in three places: the `.livespec.jsonc` read falls back to the default `5` on a committed `0` (`_resolve_positive_int_setting` in `.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_policy_settings.py`), the `set-config:wip_cap:0` write is refused (`wip_cap` typed `positive_integer` in `commands/_drive_config_schema.py`), and the declared API-configurable-key manifest publishes `positive_integer` for `wip_cap` (`.claude-plugin/api-configurable-keys.json`). The consumer's committed off-switch therefore silently resolves to a cap of 5 today — the exact inversion of its committed posture — and any future schema tightening (e.g. `minimum: 1`) would entrench the breakage as a documented constraint. Blessing `0` at spec level makes the off-value documented, mechanically honored, and schema-protected.

### Proposed Changes

**(a) `contracts.md` §"Per-repo WIP cap" — bless `0` and state the value domain.**

REPLACE (verbatim — the section's whole current paragraph):

```
The WIP cap is **per-repo**, sourced from this repo's `.livespec.jsonc`
(the `livespec-orchestrator-beads-fabro.dispatcher.wip_cap` key), default
**5** — NOT a single fleet-wide number. Total fleet concurrency is the
sum of the per-repo caps; a separate fleet ceiling is a later knob if
ever wanted. The Dispatcher MUST NOT drive more than `wip_cap` items into
the `active` state at once.
```

WITH (the same paragraph preserved unchanged, followed by a new value-domain paragraph):

```
The WIP cap is **per-repo**, sourced from this repo's `.livespec.jsonc`
(the `livespec-orchestrator-beads-fabro.dispatcher.wip_cap` key), default
**5** — NOT a single fleet-wide number. Total fleet concurrency is the
sum of the per-repo caps; a separate fleet ceiling is a later knob if
ever wanted. The Dispatcher MUST NOT drive more than `wip_cap` items into
the `active` state at once.

`wip_cap`'s value domain is a **non-negative integer**: `0` is a valid
committed value, and it is the sanctioned consumer-project DISPATCH-OFF
posture value. Under a `wip_cap` of `0` the admission valve's capacity
condition (`count(active) < wip_cap`, §"Admission valve (`ready →
active`)") holds for no item, so the Dispatcher admits nothing. Every
surface that validates or reads `wip_cap` MUST accept `0`: a read of a
committed `0` MUST resolve to `0` — it MUST NOT be treated as
out-of-domain and fall back to the default. `0` is valid for `wip_cap`
ONLY; the per-item-overridable integer caps (`review_fix_cap`,
`acceptance_rework_cap`, §"Dispatcher policy settings") remain positive
integers — `wip_cap` has no per-item override and no `clear` sentinel,
so no sentinel ambiguity arises. A schema or validation change that
imposes a minimum above `0` on `wip_cap` MUST NOT land without a
propose-change that explicitly retires this clause.
```

**(b) `scenarios.md` — new Gherkin scenario (behavior ⇒ scenario discipline).**

ADD a new `## Scenario 49` (49 = the next free scenario number) after Scenario 48, its Gherkin body wrapped in the standard ```gherkin fence like the sibling scenarios, modeled on Scenario 22 (the WIP-capped rank-order admission) and reusing its vocabulary:

```
## Scenario 49 — A committed wip_cap of 0 admits nothing (dispatch-off)

Feature: A per-repo wip_cap of 0 is the consumer project's dispatch-off posture
  As a consumer project that has committed a dispatch-off posture
  I want a committed wip_cap of 0 to admit nothing
  So that switching dispatch off is a committed, verifiable fact of the repo

Scenario: No admission-eligible ready item is admitted under a committed wip_cap of 0
  Given a per-repo wip_cap of 0 committed in `.livespec.jsonc`
  And an admission-eligible ready item
  When the Dispatcher runs with no active items
  Then the committed wip_cap of 0 resolves to 0 rather than falling back to the default
  And the Dispatcher admits nothing
  And the item stays `ready`
```

**(c) `tests/heading-coverage.json` co-edit (REQUIRED by the new H2).** The new `## Scenario 49` is a new H2 heading, so the same revise payload MUST add a matching `TODO`+`reason` entry to `tests/heading-coverage.json` (path spelled `../tests/heading-coverage.json` when `--spec-target` is the main `SPECIFICATION/` tree), per the revise co-edit discipline. No other edit in this proposal adds an H2, so no other heading-coverage change is needed.

**(d) Deliberately NOT touched.** `contracts.md` §"`wip_cap` — the one setting with no per-item override" keeps its text (including "Its value semantics are unchanged"): that section defers to §"Per-repo WIP cap" as the authority on `wip_cap`'s value, and this proposal amends that authority in place. Likewise the cap-override `clear`-sentinel rationale ("the integer caps are positive integers") in the `drive` human-valve-actions text is untouched — it speaks of the PER-ITEM cap-override values (`set-review-fix-cap:` / `set-acceptance-rework-cap:`), and `wip_cap` has no per-item override, so blessing `0` for `wip_cap` cannot collide with `clear`.
