---
topic: dry-run-not-picked-reasons
author: homelab-loop-hardening-orchestrator
created_at: 2026-08-26T08:12:09Z
---

## Proposal: Dry-run reports why a ready item was not picked

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Widens the Dispatcher's `loop --dry-run` obligation from reporting only the selection to also reporting, per candidate, why each ready work-item it considered was NOT picked. Today the ratified clause requires --dry-run to "compute and report exactly the selection the same invocation would dispatch" and is silent on exclusions, so a ready item that loses to the WIP cap, to an open sibling dependency, or to an `--item` filter simply vanishes from the output with nothing distinguishing it from an item the selector never saw. This proposal adds the exclusion-reporting obligation and a scenario exercising it.

### Motivation

Deferred second slice of maintainer commission item F (2026-08-26), relayed through the homelab steady-state-loop-hardening coordinator. The commission's wording was "dry-run emits its picks as the outcome list, plus a per-candidate reason for anything ready-but-not-picked". The picks half is already ratified text and is being implemented as ledger item bd-ib-omvia6 under plan epic bd-ib-ujihbw; this half is not, and implementing it without ratification would make the code assert what the specification does not. The motivating incident is recorded on bd-ib-omvia6: a sibling session read an empty dry-run outcome list, concluded the selector was broken, and prepared a false defect report, which a third session had to unwind by reading source. Reporting the picks fixes that specific incident; reporting the exclusions is what makes the surface answer the question operators actually bring to it, which is not only "what would run" but "why is my item not running". Without it the surface still has a silent-absence failure mode: an item excluded by a cap and an item excluded because a blocker is open are indistinguishable, and both look identical to an item the ranking never returned.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"The Dispatcher", extend the `--dry-run` bullet. After the existing sentence requiring that `--dry-run` MUST compute and report exactly the selection the same invocation would dispatch, the Dispatcher MUST additionally report, for every work-item that was `ready` and considered but NOT selected, that item's identifier together with a single machine-stable exclusion reason. The reason MUST be drawn from a closed set naming at least: the WIP cap or budget being reached, an unsatisfied blocking dependency, and exclusion by an explicit `--item` filter. A ready item that was considered and not selected MUST NOT be omitted silently from the report. The exclusion report MUST accompany the selection in the same invocation's output under `--json` and on stdout, and MUST be distinguishable from the selection rather than merged into it, so a caller can tell "would be dispatched" from "was ruled out, and why". The exclusion report MUST NOT change what `--dry-run` selects, and `--dry-run` MUST remain read-only with respect to the work-item store: it MUST NOT launch a Fabro run, MUST NOT mutate the ledger, and MUST NOT write the work-item store. Journaling the exclusion report alongside the planned selection is permitted, on the same footing the existing clause grants the selection: the journal is an append-only audit record and MUST NOT be the only surface carrying the exclusions. Where an item is excluded for more than one reason, the Dispatcher MUST report the reason that actually governed the exclusion decision rather than an arbitrary member of the set, so that acting on the reported reason is sufficient to change the outcome. In `SPECIFICATION/scenarios.md`, add a `## Scenario` exercising a dry-run over a candidate set containing one selected item and at least two ready-but-excluded items with different governing reasons, asserting Given a ready set exceeding the budget with one item carrying an open blocking dependency, When `loop --dry-run --json` runs, Then the selection carries the picked identifiers and the exclusion report names each unpicked ready item exactly once with its governing reason. The scenario MUST be linked from `tests/heading-coverage.json` in the same change, per this project's co-edit discipline.
