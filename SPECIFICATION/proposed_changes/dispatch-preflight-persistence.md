---
topic: dispatch-preflight-persistence
author: claude-fable-5
created_at: 2026-08-25T11:45:17Z
---

## Proposal: Ratify the step discipline and persist a missing required integration point into the next dispatch's refusal

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Ratifies the Dispatcher's pre-dispatch preflight and post-merge step discipline for the first time — every loop-critical step has exactly three sanctioned outcomes: pass; refuse the dispatch as a precondition error naming the missing piece and its remedy (the shipped, journaled exit-3 behavior of the master-CI preflight, `bd-ib-wefw`); or proceed under an explicit config-declared waiver with a named owner. A step that can only observe its failure post-merge (the janitor) journals a first-class degraded outcome naming the missing required integration point — and, the actual residual gap the journal evidence shows: that degraded outcome MUST PERSIST into a refusal of the NEXT dispatch for the repository, clearing only when a pre-dispatch re-verification observes the integration point provided or a committed waiver covers the step. Waivers are committed configuration (`dispatcher.step_waivers`, each entry naming the step, an owner, and a reason), deliberately NOT API-configurable, and a waived failure is journaled as waived — visible, never silent. Adds Scenario 76.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the Phase 2 charge of homelab's `steady-state-loop-hardening` program: the sections-04/05 filing, RESTATED FROM JOURNAL EVIDENCE as that program's research/007 requires (finding fable 2: the matrix's premises for these two sections were contradicted by primary evidence, so the filing must aim at the actual residual gaps, not the reconstructed ones).

THE RE-MEASUREMENT, performed by this session on 2026-08-25 against the primary records (not inherited from the review):

- homelab's dispatch journal (`tmp/fabro-dispatch-journal.jsonl`, 68 rows) contains exactly ONE `master-ci-preflight` row in its entire history — `2026-08-23T05:38:43Z`, `status: failed`, `terminal: true`, detail "credentialed gh call failed". It REFUSED; it did not proceed. The matrix's "returned master-ci-unprovable on every dispatch and proceeded anyway" is false on both clauses.
- The unprovable-refuses behavior SHIPPED in this repository on 2026-07-28 (`2ae4b2be`, contained in `v0.47.0`; the refusal path in `_dispatcher_run_checks.py` journals and exits with the precondition code 3; closed item `bd-ib-wefw`). Section 05's asked-for "cannot verify then refuses" already ships for this leg.
- The journal carries TWO degraded post-merge outcomes ("merged, but the post-merge janitor DID NOT RUN: installing the commit-refuse hooks failed ... Remediate the host") at `06:01:33Z` and `08:14:16Z` — first-class outcome records naming the failure and the remedy, produced by the shipped merged-degraded path. The matrix's "leaving only journal WARN records" undersells what shipped.
- The REAL residual gap is between those two rows: the `08:06` dispatch proceeded cleanly AFTER the `06:01` degraded outcome, with the required integration point still missing — nothing persists a known-missing required integration point into a refusal of the NEXT dispatch. (The same journal's `08:14:14Z` `acceptance-ai-pass` FAIL -> `acceptance-auto-rework` row is the primary-record confirmation of the sections-01/02 evidence; those legs are already filed as `proposed_changes/needs-attention-verdict.md` and `proposed_changes/acceptance-rework-state-machine.md`.)
- None of this discipline is ratified: `SPECIFICATION/` contains zero occurrences of the master-CI preflight, the janitor bootstrap step, or any pre/post step outcome vocabulary — the shipped refusal and degraded-outcome behaviors are implementation-only.

WHAT IS DELIBERATELY DEFERRED. Composing a repeatedly-failing step into the needs-attention surface (fable 2's residual gap (c)) belongs to the needs-attention completeness filing, which this plan sequences on the livespec-runtime attention-surface baseline (research/010 R4). This proposal is one of the runtime-independent filings and touches no attention machinery.

### Proposed Changes

Changes land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`; BCP14 throughout. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the new `## Scenario 76` heading.

#### 1. `contracts.md` — new subsection `### Dispatch preflight and post-merge step discipline`, placed among the Dispatcher's operational sections

Full text:

> ### Dispatch preflight and post-merge step discipline
>
> Every loop-critical step the Dispatcher runs around a factory dispatch — the pre-dispatch preflights (source checkout, master CI) and the post-merge steps (the janitor, including its bootstrap of the governed repository's commit-refuse hooks) — has exactly THREE sanctioned outcomes:
>
> 1. **Pass**, journaled.
> 2. **Refusal**: a pre-dispatch step that fails, or cannot verify what it exists to verify, MUST refuse the dispatch as a precondition error (exit `3`), journaled, naming the missing piece and its remedy. Absence of proof is refusal, never proceed-and-hope.
> 3. **Waived proceed**: a step covered by an explicit committed waiver proceeds, and the waived failure is journaled AS waived — visible, never silent.
>
> There is no fourth outcome: a silent warn-and-proceed branch on a loop-critical step is forbidden.
>
> A step that can only OBSERVE its failure after the merge (the post-merge janitor) MUST record a first-class degraded outcome on the dispatch's outcome record, naming the missing required integration point and the remedy — and that degraded outcome PERSISTS:
>
> **Cross-dispatch persistence.** When the journal's outcome history for the repository names a missing REQUIRED integration point (a degraded post-merge outcome, e.g. the governed repository no longer providing its commit-refuse-hook bootstrap recipe), the Dispatcher MUST refuse the NEXT dispatch for that repository at the pre-dispatch gate — exit `3`, naming the missing integration point, the originating outcome record, and the remedy — until either:
>
> - a pre-dispatch RE-VERIFICATION of that specific integration point observes it provided (every required integration point named in a degraded outcome MUST have a pre-dispatch verification; for the janitor bootstrap that is the presence of the governed repository's hook-install recipe), or
> - a committed waiver covers the step.
>
> A repository that fails to provide a required integration point therefore stops the factory FOR THAT REPOSITORY, visibly, with the remedy named — it does not degrade silently on every dispatch forever. The hard refusal IS the mechanism that makes the adopter provide the missing piece.
>
> **`dispatcher.step_waivers`** (committed `.livespec.jsonc`; a list of waiver entries, each carrying `step` — the step identifier, `owner` — a named responsible party, and `reason` — non-empty prose). A waiver is scoped to its named step only. The setting is deliberately NOT API-configurable and MUST NOT be editable through the console Settings surface or any remote API: a dial that relaxes a safety refusal is committed configuration with a reviewable diff, never a remote toggle. An expired rationale is the owner's to retire; the journal records every waived proceed with the waiver's owner, so a standing waiver is visible on every use.

#### 2. `scenarios.md` — new scenario

```gherkin
## Scenario 76 — A missing required integration point stops the next dispatch, not silently every dispatch

Feature: Degraded step outcomes persist into refusals
  As a maintainer whose repository must provide the factory's integration points
  I want a known-missing integration point to refuse the next dispatch with the remedy named
  So that the factory degrades loudly once instead of silently forever

Scenario: The next dispatch is refused after a degraded janitor outcome
  Given the journal's latest outcome for the repository names a missing required integration point
  And no committed waiver covers that step
  When the next drain or dispatch --item runs for the repository
  Then the dispatch is refused at the pre-dispatch gate with the precondition exit code
  And the refusal names the missing integration point, the originating outcome record, and the remedy

Scenario: The refusal clears when re-verification observes the point provided
  Given the same journal history
  And the governed repository now provides the named integration point
  When the pre-dispatch re-verification runs
  Then it observes the integration point provided and the dispatch proceeds

Scenario: A committed waiver proceeds visibly
  Given a committed step waiver naming the step, an owner, and a reason
  When a dispatch runs and the waived step fails
  Then the dispatch proceeds
  And the waived failure is journaled as waived with the waiver's owner
```

## Proposal: Resolve the master-CI pipeline from repository declaration, keeping the fail-closed refusal

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Replaces the master-CI preflight's hard-coded pipeline identity — today the implementation resolves the default-branch pipeline by the fixed workflow display name `CI` and the fixed aggregate job name `ci-green` — with a repository-DECLARED resolution: a committed `dispatcher.master_ci` configuration key (`workflow`, `job`) whose ABSENCE defaults to the current `CI`/`ci-green` convention, so no conforming repository changes behavior, while a repository whose real pipeline carries different names becomes provable instead of permanently unprovable. The fail-closed posture is unchanged: an unresolvable pipeline — undeclared and not matching the default convention, or declared but not found — remains a journaled refusal. This finding is argued on its own merits, NOT on the homelab incident: the journal evidence shows the incident's one refusal was a failed credentialed gh call that no name-resolution change would have prevented, and the name-based lookup demonstrably resolved that repository's CI on the dispatches that mattered.

### Motivation

Same plan-thread provenance and re-measured evidence base as the previous finding (see its Motivation); this finding carries the general fix reviewer fable's finding 2 allows on its own merits — the hard-coded `--workflow CI` / `ci-green` pair verified at `_dispatcher_master_ci_preflight.py` — while explicitly disclaiming the incident as its justification.

### Proposed Changes

Changes land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`; BCP14 throughout. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the new `## Scenario 77` heading.

#### 1. `contracts.md` — extend the new §"Dispatch preflight and post-merge step discipline" (previous finding) with a master-CI resolution clause

> **Master-CI pipeline resolution.** The master-CI preflight MUST resolve the repository's default-branch pipeline from what the repository DECLARES: the committed `dispatcher.master_ci` key (`workflow` — the workflow display name or file name; `job` — the aggregate green job name). When the key is absent, the preflight MUST use the default convention (workflow `CI`, aggregate job `ci-green`) — a declared default, not a silent assumption: the refusal text for an unresolvable pipeline MUST say which resolution was attempted (declared or default) and name the key that declares it. A pipeline that cannot be resolved — undeclared and not matching the default convention, or declared but not found — remains a journaled precondition refusal; declaration changes WHAT is looked up, never WHETHER absence of proof refuses. `dispatcher.master_ci` describes the repository's CI topology, has no per-item override, and is deliberately NOT API-configurable.

#### 2. `scenarios.md` — new scenario

```gherkin
## Scenario 77 — The master-CI preflight resolves the pipeline the repository declares

Feature: Declared pipeline resolution with a fail-closed default
  As an adopter whose CI workflow is not named CI
  I want to declare my pipeline so the preflight can prove my master green
  So that a conforming repository is not permanently unprovable by naming convention

Scenario: A declared pipeline is resolved
  Given a repository whose committed dispatcher.master_ci names its workflow and aggregate job
  When the master-CI preflight runs
  Then it resolves the declared workflow and job and proves or refutes master health from them

Scenario: An undeclared repository uses the default convention
  Given a repository with no dispatcher.master_ci key and a workflow named CI with a ci-green job
  When the master-CI preflight runs
  Then it resolves the default convention unchanged

Scenario: An unresolvable pipeline still refuses
  Given a repository whose declared or default pipeline cannot be found
  When the master-CI preflight runs
  Then the dispatch is refused with the refusal naming the attempted resolution and the declaring key
```
