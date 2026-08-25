---
topic: detector-coverage-records
author: claude-fable-5
created_at: 2026-08-25T11:53:34Z
---

## Proposal: Tenant-backed detection coverage records, all-or-nothing completed points, and the two staleness facts

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Gives the two detection skills — `capture-impl-gaps` (spec -> impl) and `capture-spec-drift` (impl -> spec) — an OWNED operating rhythm, closing matrix section 15's quiet ownership hole (a missed drain stalls visibly within days; missed detection diverges silently for months). Detection runs record TWO distinct, attributed, TENANT-BACKED record types on a designated per-repository coverage anchor: an ATTEMPT record for every invocation, and an all-or-nothing COMPLETED-coverage record — written ONLY on a successful terminal outcome over the declared scope with every surfaced candidate durably disposed — carrying the coverage point (the ratified spec revision a gap capture ran against; the default-branch merge SHA a drift pass ran through). A non-zero exit, an interruption, an unresolved candidate, or a partial range leaves the prior completed point UNCHANGED. Two staleness facts derive from the completed points and compose into the needs-attention snapshot with handoffs naming the skill to run: gap-capture staleness (a ratified revision newer than the last completed gap coverage point) as the BACKSTOP to livespec core's revise Step 13 every-revise binding — never a second binding — and drift staleness (default-branch merges since the last completed drift point at or past the new committed `dispatcher.drift_capture_merge_threshold`, default 1, declared API-configurable). Both skills remain consent-gated attended dialogues: the mechanism is a surfaced owned TRIGGER, never a headless run. The coverage-record write is ratified as a narrowly-scoped self-bookkeeping exception to the detection surfaces' read-only ledger posture. Adds Scenarios 81-82.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the Phase 2 charge of homelab's `steady-state-loop-hardening` program: the section-15 filing bound by that program's research/007 (finding sol 2 / fable 9) and research/008 (its section-15 correction and finding sol 1), with the maintainer's 2026-08-25 rulings — gap capture bound to EVERY revise; drift capture bound to a configurable default-branch merge count, default 1. Verified against this repository's and livespec core's primary sources on 2026-08-25.

THE OWNERSHIP HOLE (matrix section 15). The detection skills are the convergence engine livespec exists for — every gap-tied work-item and every drift proposal originates in them — yet nothing names when they run or says they are overdue: after a ratification, the only carrier of "run gap capture next" has been a sentence in a session recap.

THE CORRECTED GAP-DIRECTION PREMISE (research/008, fable 2 there — binding on this filing). livespec core's revise Step 13 post-step ALREADY SHIPS the every-revise gap-capture binding: the revise operation itself invokes gap capture, and the session sees the consent dialogue through. The gap-staleness fact ratified here is that binding's BACKSTOP — it fires for the runs Step 13 cannot guarantee (a skipped, interrupted, or bypassed post-step; a stopped run is the live example homelab records) — so ONE binding exists with ONE backstop, and this filing cites livespec core's ratified v081 coordinating epic for the `--since-version` axis so a second binding is not built. The coordinated caller caution travels with it: `--since-version` scoping is CHANGED-FILE scoping, and a changed file resurfaces EVERY live clause in it — a 72-candidate result against a 4-decision diff was observed in this repository on 2026-08-25 — so the staleness handoff names the expectation, and completed-coverage is what clears the fact, never candidate-count intuitions.

A COVERAGE POINT IS COMPLETED COVERAGE, NOT AN INVOCATION (research/008 sol 1, adopted verbatim). An attempt that dies half-way must not advance the point a staleness fact clears on — otherwise an aborted run reads as coverage and detection silently stops again, one layer down. Hence the two record types, and the all-or-nothing rule: the completed point advances only on a successful terminal outcome over the declared scope with every surfaced candidate durably disposed (consented-and-filed, consented-and-handed-off, or explicitly declined on the record); non-zero exit, interruption, an unresolved candidate, or a partial range leaves the prior point unchanged and keeps the staleness fact live. The Phase-4 proof wording downstream is exactly "a complete successful pass clears; an aborted or partial pass does not", with both branches tested.

TENANT-BACKED, NOT OFF-SUBSTRATE (research/007 sol 2 / fable 9). The dispatch journal is a per-host append-only audit file; making it the authoritative convergence database would put load-bearing state outside the shared substrate every client reads. Coverage records are therefore LEDGER-held — attributed comments on a designated per-repository detection-coverage anchor item, provisioned ONCE by the operator through `capture-work-item` (consent native) with its id committed in `.livespec.jsonc` — and the journal remains an audit trail re-derivable from the tenant. Attribution composes with the sibling invoker-attribution filing: each record carries the resolved invoker.

THE CONSENT AND OPERATION-SURFACE DECISIONS, MADE EXPLICITLY (sol 2's requirement). `capture-spec-drift` is contractually read-only toward the ledger today ("reads the Ledger through the store's read API only"), and the detection surfaces create no work-items outside their consent flows. Writing a coverage record about ONE'S OWN RUN is ratified as a narrowly-scoped self-bookkeeping exception: a detection operation MAY append its attempt and completed-coverage records to the designated anchor — and may write NOTHING else: no work-item create, no disposition, no other comment. The skills themselves remain consent-gated attended dialogues; the staleness facts surface a NEED with a handoff naming the skill — never a headless run.

RUNTIME SEQUENCING (research/010 R4). The two staleness facts ride the needs-attention envelope with additive stable-ID forms under existing broad kinds; whether they need any runtime-owned change is settled against the ratified livespec-runtime attention-surface baseline (epic `livespec-runtime/livespec-runtime-mqsxsu`). The accepting revise of this proposal MUST NOT run before that baseline snapshot exists, and MUST verify the fact IDs conform to the ratified grammar (routing any needed grammar change to livespec-runtime first, per the ownership cut recorded in the sibling envelope filing).

THE SETTING'S LOCKSTEP DECLARATION (research/009 c-fable 2). `dispatcher.drift_capture_merge_threshold` is declared API-CONFIGURABLE, which deliberately triggers the console Settings-surface lockstep; the console-side row, help, docs, and completeness-test legs belong to the console repository's charge and are triggered by this declaration, exactly as that program's coordination model intends.

### Proposed Changes

Changes land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`; BCP14 throughout. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the two new `## Scenario` H2 headings, and MUST honor the runtime sequencing gate stated in the Motivation.

#### 1. `contracts.md` — new subsection `### Detection coverage records and staleness facts`, placed near the `capture-impl-gaps` / `capture-spec-drift` sections

Full text:

> ### Detection coverage records and staleness facts
>
> Detection runs are RECORDED, and their recency is COMPUTED, never remembered:
>
> - **Records.** Every invocation of `capture-impl-gaps` or `capture-spec-drift` MUST append an attributed ATTEMPT record (operation, declared scope, invoker, outcome) to the repository's designated detection-coverage anchor — a ledger item provisioned once by the operator through `capture-work-item`, its id committed in `.livespec.jsonc`. A COMPLETED-coverage record — carrying the coverage point: the ratified spec revision the gap capture ran against, or the default-branch merge SHA the drift pass ran through — MUST be appended ONLY when the run reached a successful terminal outcome over its declared scope with EVERY surfaced candidate durably disposed (consented-and-filed, consented-and-handed-off, or explicitly declined on the record). A non-zero exit, an interruption, an unresolved candidate, or a partial range MUST NOT write a completed record: the prior completed point stands, and a complete successful pass clears staleness while an aborted or partial pass does not.
> - **The self-bookkeeping exception, scoped.** Appending these two record types to the designated anchor is the ONLY ledger write the detection operations may perform outside their consent flows: no work-item create, no disposition, no edit of any other record. `capture-spec-drift`'s ledger-intent scan remains read-only; this exception covers exclusively its own run's records.
> - **Gap-capture staleness (the Step 13 BACKSTOP).** When the newest ratified spec revision is newer than the last COMPLETED gap-capture coverage point, the needs-attention snapshot MUST carry a gap-capture-staleness fact whose handoff names `capture-impl-gaps` with the stale range. This fact is the BACKSTOP to livespec core's revise Step 13 post-step — the every-revise binding, which remains the one binding — and exists for the runs Step 13 cannot guarantee: a skipped, interrupted, or bypassed post-step. It MUST NOT trigger any run itself.
> - **Drift staleness.** When the count of default-branch merges since the last COMPLETED drift coverage point is at or past the effective `dispatcher.drift_capture_merge_threshold`, the snapshot MUST carry a drift-staleness fact whose handoff names `capture-spec-drift`. Merge counting excludes nothing silently: if a class of commits is excluded, the exclusion is stated on the fact.
> - **`dispatcher.drift_capture_merge_threshold`** (committed `.livespec.jsonc`, positive integer, default **1**) — the merge-count trigger. Declared **API-configurable**: it appears in the console Settings surface per §"API-configurable completeness" (the consumer-side legs belong to the console's own specification). No per-item override — detection recency is a repository property.
> - **Consent is untouched.** Both skills remain consent-gated attended dialogues. A staleness fact is a surfaced, owned TRIGGER carrying a handoff; nothing in this section runs a detector headlessly, and no policy setting MAY do so.

#### 2. `scenarios.md` — two new scenarios

```gherkin
## Scenario 81 — Only a complete successful pass advances the coverage point

Feature: Attempt records and all-or-nothing completed coverage
  As a maintainer relying on detection recency
  I want an aborted or partial detection run to leave the coverage point unchanged
  So that a half-run can never read as coverage and silence detection again

Scenario: A complete pass writes both records and clears staleness
  Given a detection run over its declared scope whose every surfaced candidate is durably disposed
  When it reaches a successful terminal outcome
  Then an attributed attempt record and a completed-coverage record are appended to the designated anchor
  And the staleness fact derived from that coverage point clears

Scenario: An aborted or partial pass leaves the prior point standing
  Given a detection run that exits non-zero, is interrupted, or leaves a surfaced candidate undisposed
  When its records are written
  Then an attempt record is appended and no completed-coverage record is written
  And the prior completed point and the live staleness fact are unchanged

Scenario: The self-bookkeeping exception writes nothing else
  Given a detection run appending its records
  Then no work-item is created and no other ledger record is written or edited by the detection operation

## Scenario 82 — Staleness facts surface owned triggers, never headless runs

Feature: Detection recency is computed from completed coverage and surfaced with a handoff
  As an operator owning the operating rhythm
  I want overdue detection surfaced with the skill named
  So that the convergence engine is owned by a surface, not a session recap

Scenario: A ratification without a completed gap capture surfaces the backstop fact
  Given a ratified spec revision newer than the last completed gap-capture coverage point
  When needs-attention composes the snapshot
  Then a gap-capture-staleness fact appears whose handoff names capture-impl-gaps and the stale range
  And no detector is invoked by the composition

Scenario: Merges past the threshold surface the drift fact
  Given default-branch merges since the last completed drift coverage point at or past the effective threshold
  When needs-attention composes the snapshot
  Then a drift-staleness fact appears whose handoff names capture-spec-drift
  And the consent-gated dialogue remains the only way the detector runs
```
