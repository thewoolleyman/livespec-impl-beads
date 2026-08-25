# Adversarial review of the six runtime-independent Phase 2 proposals — reviewer codex

(Commissioned 2026-08-25 by the homelab-loop-hardening-orchestrator session; run
as an independent Codex task with full repo read access; received verbatim.)

## Executive verdict

These proposals need substantial rework before revise. The most important defect is that several proposed contracts cannot coexist with the ratified lifecycle and other pending proposals: rework creates a parked-but-`active` state outside WIP, preflight declares both "exactly three outcomes" and a fourth degraded outcome, and the master-CI change leaves a ratified hard-coded-branch violation unresolved. The implementation spot-checks also found multiple load-bearing false premises.

## Findings

### 1. Blocker — The proposed three-outcome step model contains a fourth outcome and forbids behavior another pending proposal requires

Under `dispatch-preflight-persistence.md` "Dispatch preflight and post-merge step discipline", every loop-critical step allegedly has exactly three outcomes: pass, pre-dispatch refusal, or waived proceed, followed by "There is no fourth outcome." The next paragraph nevertheless requires an unwaived post-merge janitor failure to produce a "first-class degraded outcome." That is neither a pass, a pre-dispatch refusal, nor a waived proceed. The same universal rule conflicts with `factory-headroom-preflight.md` (unreadable gauge on a hand-picked dispatch warns and MUST NOT refuse, without a committed waiver) and reads broadly enough to conflict with the ratified fail-closed cost gate (hand-picked warning; fail-open skipped result for an unresolvable run id). The proposal must either add degraded/warning/skipped as explicit outcomes or narrow the rule to a named, closed step set.

### 2. Blocker — `rework:pending` creates a lifecycle state that contradicts the ratified meaning of `active`

Ratified `contracts.md` §"Work-item state semantics" defines `active` as "admitted into a WIP slot and being worked." §"Per-state operator verb vocabulary" gives `active` "observe only," while the proposal adds an operator-triggered `dispatch --item` action and refers to a `drive` move out of `active`. It also contradicts §"Dispatcher loop invocation surface", where `--item` "never bypasses" ranked dispatch eligibility and a named item lacking a free WIP slot must not dispatch; the proposal grants a marked `active` item a special targeted route with the hand-picked over-cap posture. The proposal must explicitly revise `Work-item state semantics`, the operator-verb vocabulary, and the loop invocation contract rather than leave two meanings of `active` ratified simultaneously.

### 3. Blocker — Clearing the rework marker before launch recreates the dead end on pre-merge failure

Under "Marker lifecycle", starting rework clears `rework:pending` before launch, after which any dead dispatch is claimed recoverable by "existing stranded-dispatch and reconcile-merged machinery." `reconcile-merged` is scoped to "an already-merged item"; a rework attempt that dies before creating or merging a PR cannot use that valve, and with its marker already removed it cannot be re-selected as pending rework either. The proposal's own Motivation acknowledges the sibling `bd-ib-zp3u7y` population of `active` dispatches that died before publishing, contradicting the asserted recovery.

### 4. Blocker — The master-CI proposal leaves a ratified hard-coded-branch violation in place and misstates fail-open behavior as fail-closed

The Summary and master-CI clause configure only `workflow` and `job`, but `_latest_master_ci_run` invokes `--branch master --workflow CI`. Ratified §"Self-contained plugin dispatch" ("Default-branch resolution") requires every dispatch-path stage referencing the primary branch to resolve the target default branch and "MUST NOT hardcode `master`." Scenario 77 has no default-branch control. The proposal also claims the "fail-closed posture is unchanged," but the implementation fails open when no stored credential exists, the successful run-list payload is empty, or the latest run is pending — per the function's own docstring. The proposal must state that it changes these fail-open cases, or preserve them explicitly.

### 5. Blocker — The probe discovers an escaping change only after merging it and does not define required residue identifiers or cleanup

Under "Sanctioned target path", the probe exercises merge-on-green and only THEN "MUST FAIL when the merged diff touches any path outside" `.livespec-probe/` — at that point the escaping change is already on the default branch, and neither this clause nor the failure leg requires preventing, reverting, or remediating it. The charge also requires residue assertions scoped to reserved identifiers plus a cleanup obligation; no identifier grammar or correlation-id definition exists anywhere. "The directory holds at most the latest artifact" is retention, not cleanup.

### 6. Major — The rework label is not available to the Dispatcher's materialized selection model

`rework:pending` is proposed as the selection/accounting discriminator, but §"Work-item beads-issue mapping" (the authoritative field map) is not amended. In `store.py::_record_to_work_item`, raw labels are read only to derive enumerated logical fields; the returned `WorkItem` carries no raw-label or rework-pending field, and `ready_items` receives only `list[WorkItem]`. "Rides the existing labels projection" explains listing visibility but not selection/accounting/stranded-state discrimination.

### 7. Major — Journal attribution does not cover the actual journal because multiple writers bypass `JournalFile.append`

`_dispatcher_acceptance_rework.py::_append_disposition` and `_dispatcher_ledger_close.py::_append_normalization_note` both open `journal.path` directly, bypassing the append layer. Scenario 72's "every record carries" claim will fail unless direct writes are forbidden/migrated and a negative control added.

### 8. Major — The new `probe` state-changing CLI is omitted from the invoker contract it is required to satisfy

`journal-invoker-attribution.md` enumerates only `loop`, `dispatch`, `reconcile-merged`, and `drive` — omitting `probe` and its `--invoker` flag, contradicting `loop-probe.md`'s stands-alone claim.

### 9. Major — The effective-criteria source order cannot be implemented from the current materialized record

`store.py::_record_to_work_item` computes `content_fields = {**metadata, **record}` (native overwrites metadata) and stores only the single resulting value; there is no provenance and no access to an overwritten metadata value, so "native then metadata-merged" plus source reporting is not implementable against the current type.

### 10. Major — Cross-dispatch persistence lacks a stable integration-point identity or clearing record

Persistence keys refusal on journal history "naming a missing REQUIRED integration point", while waivers key on a `step` identifier — no stable step vocabulary, uniqueness rule, or verifier mapping is defined. `_merged_degraded_detail` emits free-text `detail`, not a structured id. Scenario 76 requires the refusal to clear on re-verification but no durable clearing record.

### 11. Major — Two proposals contain ungated references to sibling contracts that may be rejected independently

`temporary-setting-restore.md` normatively cites §"Effective acceptance criteria" (exists only in pending `needs-attention-verdict.md`); `loop-probe.md` depends on that primitive, `invoker_source`, and the preflight outcome discipline. These need explicit revise gates or an atomic revision set.

### 12. Major — The proposed exit-code documentation target does not exist

No ratified exit-code enumeration exists; `_dispatcher_command_common.py` defines EXIT_FAILURE=1, EXIT_PRECONDITION_ERROR=3, EXIT_BLOCKED=4. The proposal must define a new documented exit-code section.

### 13. Minor — The temporary-setting contract does not define where ownership lives

"Named owner" without deciding assignee/label/metadata/prose; prose alone is not queryable.

### 14. Minor — Several proposed scenarios are non-decisive or omit necessary controls

Scenario 69 (mere presence vs gradeable assertions); Scenario 77 ("proves or refutes" disjunction); Scenario 78 (no When; restates an omission); Scenario 68 (no unmarked-item control); Scenario 74 (no admission-eligibility setup, no cleanup test).

### 15. Observation — Two Motivation claims overstate the implementation behavior

`ready_items` also accepts `pending-approval` via projection (dead-end conclusion still holds); `_dispatcher_completion.py` has a `NO_CHANGE_NEEDED` auto-close branch, so "any verdict parks" is inexact.

## Unverified observations

None.

## What the proposals get right

Both rework entries kept aligned; no shared-vocabulary extension; the evidence rule cleanly distinguishes observed failure from absent evidence; walls at ready/pre-dispatch with capture advisory match the charge; flag>env>marked-fallback order is clear; the probe takes a pre-filed item and treats an unreadable source as failure; the CI/ci-green constants and the credentialed-call refusal are correctly identified; the ledger route for temporary settings is decided, not left open; scenario numbering is collision-free across all pending proposals (57-59, 62-63, 66-78).
