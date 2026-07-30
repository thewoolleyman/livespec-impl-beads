---
topic: retire-host-dispatch-cap
author: claude-opus-5
created_at: 2026-07-30T10:24:30Z
---

## Proposal: Retire the client-side host dispatch cap; host concurrency belongs to the Fabro scheduler

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- SPECIFICATION/spec.md

### Summary

Remove the Orchestrator's client-side host-level dispatch concurrency cap from the specification, and replace it with a positive statement that host throughput belongs to the Fabro server's own scheduler. The `contracts.md` section "Host-level dispatch concurrency cap (`host_dispatch_cap`)" is deleted in full along with its four `scenarios.md` scenarios; a new short `contracts.md` subsection "Host concurrency belongs to the Fabro scheduler" states that the Orchestrator owns no host-level ceiling and MUST NOT refuse a dispatch on host-concurrency grounds, paired with one new `scenarios.md` scenario. Every surviving cross-reference to the removed key is rewritten rather than merely unlinked: three further sites in `contracts.md` and one in `spec.md` currently describe TWO concurrency ceilings and after this change there is exactly one. `wip_cap` keeps its value (5), its per-repo scope, its `per_item_override: false` shape, and its value domain (non-negative integer, `0` = dispatch-off) entirely unchanged.

### Motivation

Maintainer directive, 2026-07-30, recorded on ledger epic `bd-ib-vmve` and its spec slice `bd-ib-vmve.1`, with the durable reasoning in `plan/retire-host-dispatch-cap/research/why-the-client-gate-goes.md`: "just kill the tech debt that duplicates `max_concurrent_runs` (poorly)."

The specified mechanism duplicates a limit the Fabro server already enforces, and does so worse in three measured ways.

1. It never reaches the factory. `host_dispatch_cap` is resolved per dispatch and consumed inside the short-lived dispatcher process; it is absent from the `fabro run` argv (only `review_fix_visit_cap` and `merge_on_review_cap_outcome` cross that boundary). It is a client-side pre-check, not a factory setting.

2. It is a PER-REPO threshold applied to a HOST-WIDE count, so it starves rather than shares. The in-flight gauge filters on run status kind only and never reads the run's source directory or repo origin, so one repo's runs refuse another repo's dispatches. Measured 2026-07-30 with one repo at 4 and the rest at 2: host-wide in-flight was 3, all three belonging to the repo capped at 4; the repo capped at 2 was REFUSED with zero runs of its own in flight. Unequal thresholds then lock the lower-capped repo out of a band it can never enter, because the higher-capped repo refills the host each time it drains. The section under deletion concedes the model in its own words: "the host is bounded at 2 only while every dispatching repo commits (or defaults to) 2" — an honor system that broke the first day the knob was used.

3. It was set BELOW the factory's real capacity, so it throttled the factory rather than protecting it: client default 2 against a scheduler limit of 5 (since raised to 10).

The spec's stated justification for the default does not hold either. The section calls 2 "the empirically verified safe level", but 2 was the level EXERCISED, never a level at which 3 was shown to fail. The originating concern was falsified by its own diagnosis leg (`bd-ib-tyxzhv`): the `bwrap` namespace `EPERM` is a host sysctl constant reproduced in a SINGLE container under every security configuration ("concurrency was temporal coincidence"), and the host-network port-collision premise was false because sandboxes already hold per-run network namespaces. No contended host resource was ever identified. Per running sandbox the measured cost is under one core and roughly 300 MiB resident; a run is dominated by network wait on model inference.

What replaces it is not new machinery. The Fabro server — a long-lived daemon that actually owns runs — already enforces `server.scheduler.max_concurrent_runs` host-scoped in its own settings, and it QUEUES rather than refuses: excess runs wait as `runnable` and a background scheduler promotes them FIFO. That has three properties the client cap lacks — it queues instead of refusing, it is FIFO across all repos so first-come genuinely means first-served, and it is enforced by the process that knows what is running.

Scope discipline, stated so this proposal cannot be read wider than it is. `wip_cap` is NOT touched: not its value (5), not its per-repo scope, not its `per_item_override: false` shape, not its enforcement asymmetry between the drain loop and a hand-picked single-item dispatch, and not its `0`-means-dispatch-off value domain. That asymmetry is intentional and is explicitly out of scope. This proposal also does NOT make the removed cap per-repo-aware, does NOT raise it, and does NOT retain a thinner host-capacity pre-check — those alternatives were considered and rejected by the maintainer on 2026-07-30, on the ground that counting only a repo's own runs would idle the machine whenever work concentrates in one repo.

One out-of-target co-edit is required and is named here rather than in `target_spec_files` because it lives outside `SPECIFICATION/`: `tests/heading-coverage.json` MUST be updated in the same change via the revise pass's `resulting_files[]` mechanism, because this proposal removes one `## ` heading from `scenarios.md` and adds one. Details are in the Proposed Changes body under edit (H).

### Proposed Changes

This proposal is ONE atomic change. Its edits are interdependent: accepting the
section deletion without the cross-reference rewrites would leave dangling
section references, so the edits MUST be accepted or rejected together.

Anchors below were verified against the live tree on 2026-07-30 at
`SPECIFICATION/contracts.md` (1874 lines wide at the cited region),
`SPECIFICATION/scenarios.md`, and `SPECIFICATION/spec.md`. Line numbers are
navigational only; the verbatim quoted text is the binding anchor.

The complete inventory of live-tree occurrences of `host_dispatch_cap` outside
frozen `SPECIFICATION/history/` snapshots is EIGHT sites across three files,
addressed as edits (A) through (F) below. Frozen `SPECIFICATION/history/vNNN/`
snapshots MUST NOT be edited — they are immutable records of what the spec said
at ratification time.

---

### (A) `contracts.md` §"Per-repo WIP cap" — first paragraph: rewrite the
host-ceiling cross-reference

This paragraph MUST be retained; only its host-ceiling sentence changes. Replace
verbatim:

> The WIP cap is **per-repo**, sourced from this repo's `.livespec.jsonc`
> (the `livespec-orchestrator-beads-fabro.dispatcher.wip_cap` key), default
> **5** — NOT a single fleet-wide number. Total LEDGER-level fleet concurrency is the
> sum of the per-repo caps; the host-level ceiling on concurrently
> in-flight dispatches is the separate `host_dispatch_cap` (§"Host-level
> dispatch concurrency cap (`host_dispatch_cap`)"). The Dispatcher MUST NOT drive more than `wip_cap` items into
> the `active` state at once.

with:

> The WIP cap is **per-repo**, sourced from this repo's `.livespec.jsonc`
> (the `livespec-orchestrator-beads-fabro.dispatcher.wip_cap` key), default
> **5** — NOT a single fleet-wide number. Total LEDGER-level fleet concurrency is the
> sum of the per-repo caps. The Orchestrator owns NO host-level ceiling on
> concurrently in-flight dispatches; that ceiling belongs to the Fabro
> server's own scheduler (§"Host concurrency belongs to the Fabro
> scheduler"). The Dispatcher MUST NOT drive more than `wip_cap` items into
> the `active` state at once.

### (B) `contracts.md` §"Per-repo WIP cap" — second paragraph: drop the
`host_dispatch_cap` value-domain carve-out

The `wip_cap` value-domain clause (`0` is valid, and is the sanctioned
dispatch-off posture) MUST be retained in full. Only the carve-out naming the
removed key is dropped, because a carve-out cannot name a key that no longer
exists. Replace verbatim:

> `0` is valid for `wip_cap`
> ONLY. Every other integer setting remains a POSITIVE integer — including
> `host_dispatch_cap`, which shares `wip_cap`'s no-per-item-override shape
> (§"`wip_cap` and `host_dispatch_cap` — the settings with no per-item
> override") but NOT its value domain: `host_dispatch_cap` governs a
> ceiling shared by every repo dispatching to the host, so a `0` there
> would switch dispatch off host-wide on one repo's say-so, which is not a
> single consumer's decision to make. The per-item-overridable caps
> (`review_fix_cap`, `acceptance_rework_cap`, §"Dispatcher policy
> settings") likewise remain positive integers; `wip_cap` has no per-item
> override and no `clear` sentinel, so no sentinel ambiguity arises.

with:

> `0` is valid for `wip_cap`
> ONLY. Every other integer setting remains a POSITIVE integer: the
> per-item-overridable caps (`review_fix_cap`, `acceptance_rework_cap`,
> §"Dispatcher policy settings") remain positive integers, and `wip_cap`
> has no per-item override and no `clear` sentinel, so no sentinel
> ambiguity arises.

The immediately following sentence — "A schema or validation change that
imposes a minimum above `0` on `wip_cap` MUST NOT land without a
propose-change that explicitly retires this clause." — MUST be retained
unchanged.

### (C) `contracts.md` §"Host-level dispatch concurrency cap
(`host_dispatch_cap`)" — DELETE the whole subsection, and state the replacement
positively

Delete the entire `###` subsection titled "Host-level dispatch concurrency cap
(`host_dispatch_cap`)", from its heading through the paragraph ending "…while
retiring one-at-a-time dispatch.", immediately preceding §"Post-merge acceptance
(`acceptance → done`)". Every normative clause in it goes: the committed
`dispatcher.host_dispatch_cap` key and its default of 2; the two-independent-gauge
in-flight measurement (live capacity claims plus observed host-wide Fabro runs);
the refusal contract and its remedy wording; the parked-run exclusion; the
crashed-holder claim self-heal floor and its `bd-ib-j4clfi` residual note; and
the "empirically verified safe level" rationale paragraph.

In its place, and at the same position in the document, insert:

> ### Host concurrency belongs to the Fabro scheduler
>
> The Orchestrator owns **no** host-level dispatch concurrency limit. The number
> of factory runs permitted to execute concurrently on the shared host is the
> Fabro server's own `server.scheduler.max_concurrent_runs` — host-scoped
> configuration read by the long-lived daemon that actually owns runs. The
> Orchestrator MUST NOT duplicate, re-implement, configure, or enforce that
> ceiling, and MUST NOT expose a committed configuration key that purports to
> bound host-wide dispatch concurrency.
>
> Consequently the Dispatcher MUST NOT refuse a dispatch on host-concurrency
> grounds, and MUST NOT maintain any host-global admission gauge, claim, or
> lock artifact for that purpose. A dispatch attempted while the host is
> already at the scheduler's limit MUST proceed to submission: the Fabro server
> accepts the run and holds it in its own queue, promoting waiting runs in FIFO
> order as capacity frees. Queueing at the scheduler is the sanctioned
> behavior; a client-side refusal is not.
>
> `wip_cap` (§"Per-repo WIP cap") is therefore the ONLY concurrency control the
> Orchestrator owns. It bounds this repo's `active` work-items at the Ledger
> level and MUST NOT be read as, or extended into, a host-wide bound. A single
> repo consequently tops out at its own `wip_cap` even when the host scheduler
> would permit more; the remaining host capacity is reachable when another repo
> dispatches. This is intended, not a defect to be corrected by re-adding a
> host-level key.

### (D) `contracts.md` §"Dispatcher policy settings" — the per-item-override
design record

Replace verbatim:

> records the maintainer's ruling that every setting is per-item overridable
> EXCEPT `wip_cap`. The later `host_dispatch_cap` (2026-07-24, §"Host-level
> dispatch concurrency cap (`host_dispatch_cap`)") joins `wip_cap` under that
> ruling's rationale: a concurrency ceiling is not a per-item property.

with:

> records the maintainer's ruling that every setting is per-item overridable
> EXCEPT `wip_cap`, whose rationale is that a concurrency ceiling is not a
> per-item property.

### (E) `contracts.md` §"`wip_cap` and `host_dispatch_cap` — the settings with
no per-item override" — RETAIN the subsection, rename its heading, and correct
the count

This subsection MUST be retained: `wip_cap` still has no per-item override, so
the section survives and merely stops being about two settings. Rename the
heading from

> ### `wip_cap` and `host_dispatch_cap` — the settings with no per-item override

to

> ### `wip_cap` — the one setting with no per-item override

and replace its opening verbatim:

> `dispatcher.wip_cap` (existing, default `5`, §"Per-repo WIP cap") is likewise
> an API-settable setting, surfaced under the console Settings surface, and so
> is `dispatcher.host_dispatch_cap` (default `2`, §"Host-level dispatch
> concurrency cap (`host_dispatch_cap`)"). These are the TWO settings with
> **no per-item override**: each is a concurrency ceiling (per-repo /
> host-level), so a per-item value is structurally meaningless. Its value semantics
> are unchanged.

with:

> `dispatcher.wip_cap` (existing, default `5`, §"Per-repo WIP cap") is likewise
> an API-settable setting, surfaced under the console Settings surface. It is
> the ONE setting with **no per-item override**: it is a per-repo concurrency
> ceiling, so a per-item value is structurally meaningless. Its value semantics
> are unchanged.

The trailing design-record citation in that subsection (repo
`thewoolleyman/livespec`, `plan/archive/autonomous-mode/handoff.md`) MUST be
retained unchanged — it rules on `wip_cap`'s per-item overridability and remains
accurate.

### (F) `spec.md` §"Dispatcher policy settings" — correct the ceiling count

Replace verbatim:

> DEFAULT for the repo, and (except for the two concurrency ceilings — the
> per-repo `wip_cap` and the host-level `host_dispatch_cap`) each is
> OVERRIDABLE PER WORK-ITEM by a ledger label: the per-item

with:

> DEFAULT for the repo, and (except for the per-repo concurrency ceiling
> `wip_cap`) each is OVERRIDABLE PER WORK-ITEM by a ledger label: the per-item

### (G) `scenarios.md` — delete Scenario 49 in full; add one replacement
scenario

Delete the entire `## Scenario 49 — The host dispatch cap admits up to the cap
and refuses the next with a performable remedy` block, including its heading,
its `Feature:` line ("A host-level dispatch concurrency cap governs how many
factory dispatches may run concurrently on the shared host"), and all FOUR of
its Gherkin scenarios:

1. "The dispatch that would exceed the cap is refused before any work"
2. "A dispatch below the cap is admitted alongside a live run"
3. "A parked run never counts toward the cap"
4. "A crashed dispatch's capacity claim self-heals"

Note for whoever applies this: only the first three of the four name
`dispatcher.host_dispatch_cap` in their text. A key-scoped search returns three
hits and under-reports; the unit of deletion is the `## Scenario 49` H2 block,
not the grep hits.

The vacated number 49 MUST be left as a gap; scenarios MUST NOT be renumbered.
The live file already carries gaps at 2 and 3, so gaps are the established
convention, and renumbering would churn every downstream heading plus its
`tests/heading-coverage.json` entry for no benefit. Verified 2026-07-30: no
git-tracked file outside frozen history cross-references "Scenario 49" other
than the heading itself and its heading-coverage entry.

Because edit (C) introduces normative clauses ("the Dispatcher MUST NOT refuse a
dispatch on host-concurrency grounds"), the behavior/Gherkin split requires a
paired scenario — behavioral prose with no scenario is malformed. Append, after
the current final scenario in the file:

> ## Scenario 53 — A dispatch proceeds when the host is busy; the scheduler queues it
>
> ```gherkin
> Feature: The Orchestrator performs no host-level concurrency check, so
> host throughput is governed solely by the Fabro server's scheduler.
>
> Scenario: A dispatch is not refused when other runs are already in flight
>   Given factory runs already in flight on the shared host
>   And an admission-eligible ready work-item with a free per-repo WIP slot
>   When the Dispatcher evaluates the dispatch
>   Then no host-level concurrency check is performed
>   And the dispatch is not refused on host-concurrency grounds
>   And the run is submitted to the Fabro server
>
> Scenario: A dispatch past the host's scheduler limit queues rather than failing
>   Given the shared host's Fabro server is already at its configured
>   concurrency limit
>   And an admission-eligible ready work-item with a free per-repo WIP slot
>   When the Dispatcher dispatches it
>   Then the Dispatcher does not exit with a host-capacity refusal
>   And the work-item is admitted to `active`
>   And the run waits for scheduler capacity rather than being rejected
> ```

53 is the next free number (the live file's highest is 52).

### (H) Required out-of-target co-edit — `tests/heading-coverage.json`

This repo's revise co-edit discipline requires that any pass adding, changing, or
removing a `## ` heading in a spec file update `tests/heading-coverage.json` in
the SAME change, through the revise pass's `resulting_files[]` mechanism. This
proposal changes exactly two `## ` headings, so exactly two entries are
affected:

1. REMOVE the entry whose `heading` is `"## Scenario 49 — The host dispatch cap
   admits up to the cap and refuses the next with a performable remedy"`
   (`spec_file`: `scenarios.md`).
2. ADD an entry for `"## Scenario 53 — A dispatch proceeds when the host is
   busy; the scheduler queues it"` with `spec_root`: `SPECIFICATION`,
   `spec_file`: `scenarios.md`, `test`: `"TODO"`, and a non-empty `reason`
   recording that the exercising integration-tier test lands with the
   code-deletion slice.

The heading-coverage map is keyed on H2 headings only — all 89 current entries
begin with `## `. The two `###` heading changes in `contracts.md` (edits (C) and
(E)) therefore have no entries and trigger no co-edit.

---

### Explicitly NOT changed

- `wip_cap` in every respect: default 5, per-repo scope,
  `per_item_override: false`, non-negative-integer value domain with `0` as the
  sanctioned dispatch-off posture, and the enforcement asymmetry whereby the
  drain loop honors the cap and a hand-picked single-item dispatch deliberately
  bypasses it. That asymmetry is intentional and MUST NOT be "fixed" here.
- The `## Dispatcher admission, WIP cap, and post-merge acceptance` H2 heading
  and its introductory paragraph, which never reference the host cap.
- Every `SPECIFICATION/history/vNNN/` snapshot.
