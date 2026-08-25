---
topic: needs-attention-verdict
author: claude-fable-5
created_at: 2026-08-25T11:35:58Z
---

## Proposal: Ratify the NEEDS_ATTENTION verdict, the evidence rule, one effective-criteria primitive, and the two criteria walls

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Ratifies the full acceptance-verdict vocabulary — the third verdict `NEEDS_ATTENTION` and the shipped-but-unreachable fourth, `NO_CHANGE_NEEDED` — today implementation-only (`_dispatcher_acceptance_ai.py`; the ratified contract still says the AI pass yields "a PASS or FAIL verdict") — with an evidence rule (a verdict MUST NOT be manufactured from ABSENT evidence: observed failing evidence yields FAIL, absent/unobservable evidence yields NEEDS_ATTENTION, and PASS requires every leg observed and passing), a full per-policy disposition table (under EVERY `acceptance_policy` a NEEDS_ATTENTION verdict parks the item in `acceptance` for a human, never auto-accepts, never auto-reworks, and never consumes `acceptance_rework_cap`), and ONE public effective-acceptance-criteria primitive (native field when it yields gradeable content, else the metadata-merged read, else the description's "Exit criteria" section) used by every producer and consumer gate. Adds the two refusal walls the primitive powers — entry-to-`ready` and pre-dispatch (a new documented exit code `5`) for AI-dispositive items whose effective criteria parse to zero gradeable assertions — while capture and groom front-ends ADVISE (display the parse) and never refuse. Supersedes the `bd-ib-au4t` FAIL-on-empty stopgap in the direction `bd-ib-1dbg` endorses, and sequences implementation with the `bd-ib-tfpdya` parser repair. Adds Scenarios 69-71.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the Phase 2 charge of homelab's `steady-state-loop-hardening` program: the section-01 filing bound by that program's research/007 (findings fable 4 and sol 10 of this repository's commissioned adversarial reviews, homelab PR #1027). Every claim below was RE-VERIFIED against this repository's primary sources on 2026-08-25 before filing.

THE VERIFIED GAP. `NEEDS_ATTENTION` exists ONLY as implementation: `commands/_dispatcher_acceptance_ai.py` defines `NEEDS_ATTENTION_VERDICT` and `_verdict` returns it — but only when telemetry PASSED and the merged diff was ungradeable. `SPECIFICATION/{spec,contracts,constraints,scenarios}.md` contain zero occurrences of the verdict; the ratified §"Post-merge acceptance" clause says the AI pass yields "a PASS or FAIL verdict". The incident that motivates widening (homelab, 2026-08-23, `steady-state-loop-hardening` research/002 section 01): an item whose filed criteria parsed to ZERO checks, with telemetry unobservable from the remote factory, fell THROUGH the narrow guard (telemetry had failed, the diff was readable) to a FAIL — a judgment rendered with no evidence examined — and then into auto-rework, which for already-merged work is a no-op that burns the rework budget and lands at `blocked`/`needs-human` (the pathology `bd-ib-1dbg` measures: 147 of 230 live AI-dispositive items — 64% — carry zero gradeable criteria and are guaranteed that fate today).

WHAT THE CURRENT IMPLEMENTATION ALREADY GETS RIGHT, RATIFIED RATHER THAN CHANGED. The completion flow (`_dispatcher_completion.py`) already parks any verdict that is neither an accepting PASS, a dispositive FAIL, nor the auto-closing `NO_CHANGE_NEEDED` (ratified below): the item stays `acceptance`, the parking is journaled (`acceptance-parked` with the verdict), and a SURFACE line names it. This proposal ratifies that parking as the uniform NEEDS_ATTENTION disposition and widens only the GUARD — which conditions produce the verdict — not the disposition machinery.

RELATIONSHIP TO THE RULED PRIOR ART, so nothing is re-litigated:

- `bd-ib-au4t` (shipped via PR 1783; ledger status `acceptance` — shipped but not yet accepted, a coordination point for the accepting revise) made zero-parsed-checks FAIL instead of PASS — the right direction (never auto-accept on absent criteria) for the wrong destination (FAIL manufactures a judgment and triggers rework spend). This proposal KEEPS the never-PASS-on-empty property and retires FAIL-on-empty in favor of the third verdict; `bd-ib-1dbg`'s own analysis ("the verdict be reached before the spend") endorses exactly this direction.
- `bd-ib-1dbg` (P1) requires the pre-dispatch refusal: criteria read through the same merged store path the acceptance pass uses (a metadata-held criteria field is not absent), the description "Exit criteria" fallback honored, a refusal exit code distinct from the admission (3) and ledger-conformance codes, and a recorded disposition for the already-filed population. All four are carried below; the already-filed items are left to refuse at the wall on contact (with the advise surfaces showing the parse), which this proposal states explicitly.
- `bd-ib-tfpdya` (pending-approval) records the wrapped-fragment defect. Measured at repair time (2026-08-25): `criteria_lines` now JOINS indented wrapped continuations and drops header-only lines (commit `8cc2d2dd`); the surviving arm is NON-indented wraps, which still split into standalone false-failing "criteria" — and, for the WALLS below, still count as gradeable lines that mask a genuinely empty criteria set. Reviewer fable's finding 4(a) is binding: building new refusal points on the defective parse institutionalizes it. The primitive below is therefore ratified at the ASSERTION level (the line-based parse is the current, known-defective approximation; its repair IS `bd-ib-tfpdya`), and the implementation children of this proposal's walls MUST land together with or after that repair.
- `bd-ib-5z0g` (closed) fixed an earlier keyword-matcher defect in the same module; disjoint, cited for completeness.

WHY THE WALL SITS AT READY/PRE-DISPATCH AND NOT AT FILING (fable 4(b), adopted verbatim): a hard refusal at capture conflicts with the capture front-ends' ratified consent-gated shape — nothing in §"`capture-impl-gaps`" requires criteria at capture, and a backlog item legitimately acquires criteria at groom time. The ratified precondition-error pattern already lives at entry-to-`ready` and pre-dispatch; the walls land there, and the capture/groom front-ends DISPLAY the parse so the author fixes the text on the spot (the matrix row's own prose).

COMPOSITION WITH THE PENDING REWORK PROPOSAL (`proposed_changes/acceptance-rework-state-machine.md`, filed minutes before this one from the same plan thread): NEEDS_ATTENTION never stamps the `rework:pending` marker — only a dispositive FAIL does. The two proposals partition the failing-pass outcomes cleanly: observed failing evidence -> FAIL -> executable rework; absent evidence -> NEEDS_ATTENTION -> human parking. Alignment with the other in-flight proposals (`wip-cap-bound-honesty`, `wip-cap-naming-collision`, `factory-headroom-preflight`) was checked: orthogonal, no conflicts.

ATTENTION-SURFACE NOTE (kept runtime-independent, per the program's R4 sequencing). A NEEDS_ATTENTION-parked item is an orchestrator-owned human wait already inside the console's ratified composition classes (homelab research/009 R1 lists "acceptance NEEDS_ATTENTION" among them); surfacing it requires NO new attention kind and NO shared-runtime change. The broader needs-attention completeness work is a separate filing sequenced on the livespec-runtime attention-surface baseline.

### Proposed Changes

All changes use BCP14 normative language and land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the three new `## Scenario` H2 headings.

#### 1. `contracts.md` §"Post-merge acceptance (`acceptance → done`)" — three verdicts and the evidence rule

Replace, in the `accept` bullet, "yielding a PASS or FAIL verdict" with "yielding a PASS, FAIL, NEEDS_ATTENTION, or NO_CHANGE_NEEDED verdict", and append after that bullet's policy list:

> **The evidence rule.** A verdict MUST NOT be manufactured from absent evidence. The pass judges three evidence legs — the merged diff, the effective acceptance criteria (§"Effective acceptance criteria"), and the run/telemetry outcome — and:
>
> - **PASS** requires every leg OBSERVED and passing: an observed green outcome, a gradeable merged diff, and a non-empty effective-criteria check set with every check passing.
> - **FAIL** requires OBSERVED failing evidence: an observed failing outcome, or at least one effective criterion judged failing against observed evidence. A FAIL is dispositive rework input (§"Post-merge acceptance" FAIL route).
> - **NEEDS_ATTENTION** is the verdict when the pass CANNOT OBSERVE what a judgment needs: the merged diff is unobservable or ungradeable, the effective criteria parse to zero gradeable assertions, or the run/telemetry leg is unobservable (distinct from observed-failing). Absence of evidence is never failure evidence and never passing evidence.
> - **NO_CHANGE_NEEDED** requires OBSERVED evidence that the item's change is no longer applicable — already present on the default branch, or superseded — and, under a to-`done` policy, closes the item with resolution `no-longer-applicable` (the shipped, tested auto-close branch). It is a disposition verdict, not a judgment that work was done well; it MUST NOT be reached from absent evidence. (The verdict is currently UNREACHABLE through the acceptance pass — `_verdict` emits only the other three — and this ratification makes it a ratified verdict with stated semantics rather than an undocumented dead branch; wiring a reachable producer is implementation work this proposal does not scope.)

#### 2. `contracts.md` — new subsection `### The NEEDS_ATTENTION verdict`, placed inside §"Post-merge acceptance" after the FAIL-route bullets

Full text:

> ### The NEEDS_ATTENTION verdict
>
> Under EVERY effective `acceptance_policy` — `ai-only`, `ai-then-human`, and `human-only` alike — a NEEDS_ATTENTION verdict MUST park the item in `acceptance` for a human and MUST NOT dispose of it: it MUST NOT accept the item to `done`, MUST NOT route it to rework, MUST NOT stamp the `rework:pending` marker, MUST NOT move it to `blocked`, and MUST NOT consume `dispatcher.acceptance_rework_cap`. A cannot-judge verdict is a truly-unresolvable decision in the sense of §"Every needs-human escalation still reaches a human": no policy setting MAY auto-dispose it, including `ai-only` — the delegation `ai-only` grants is the authority to act ON evidence, not the authority to act without it.
>
> The parking MUST be journaled with the verdict and the absent evidence leg(s), MUST be surfaced (the existing parked-in-acceptance surfacing), and the parked item is an orchestrator-owned human wait for the attention surface — composed through the EXISTING composition classes (a parked acceptance awaiting the human `accept`/`reject` valves); this clause introduces no new attention kind. The human disposes of the parked item with the existing `accept:<work-item-id>` and `reject:<work-item-id>:rework|regroom` valve actions.
>
> The pass itself still satisfies the "no release with zero verification" floor: a NEEDS_ATTENTION verdict is a completed AI pass whose finding is that the evidence was unobservable — it is not a skipped pass.

#### 3. `contracts.md` — new subsection `### Effective acceptance criteria`, placed before §"Post-merge acceptance"

Full text:

> ### Effective acceptance criteria
>
> Exactly ONE public primitive resolves a work-item's effective acceptance criteria, and every producer and consumer gate MUST use it — the capture and groom front-ends' parse display, the entry-to-`ready` wall, the pre-dispatch wall, and the post-merge acceptance pass. No surface may re-derive criteria by another path. The resolution order:
>
> 1. The item's MATERIALIZED criteria value — the merged store read the acceptance pass already uses, in which the native `acceptance_criteria` field wins over a metadata-held one and a criteria field held only in metadata by an older writer is NOT treated as absent — when it yields gradeable content. (This is ONE step, not two: the materialization IS the merged read; no surface re-reads raw metadata separately.)
> 2. Otherwise the item description's "Exit criteria" section (a heading whose title case-insensitively equals "Exit criteria"; the section body is the criteria text).
>
> The resolved source is reported as one of exactly two values: `criteria-field` (the merged value) or `description-exit-criteria`.
>
> Gradeability is defined at the ASSERTION level: an effective-criteria set is empty when it contains zero gradeable assertions. A physical-line parse that counts wrapped continuation fragments as assertions is a known-defective approximation of this definition (`bd-ib-tfpdya`); the walls below MUST NOT be implemented against a parse that counts non-assertable fragments as gradeable. The completion criterion for that gate is mechanical, not an item reference: the walls MAY land once (a) a formatting-independence test exists proving the same criteria text reflowed to different column widths yields the same gradeable-assertion count, and (b) the discriminating control holds — a genuinely unmet real criterion still fails while a wrapped fragment no longer does.

#### 4. `contracts.md` — the two walls

Add a wall clause at the `approve` transition in §"Work-item state semantics" (NOT in the admission valve's mechanical-conditions list — that valve's ratified precondition is `ready` membership, and a rule about ENTERING `ready` cannot be one of its conditions):

> **Gradeable acceptance criteria (AI-dispositive items):** an item whose EFFECTIVE `acceptance_policy` is `ai-only` or `ai-then-human` and whose effective acceptance criteria (§"Effective acceptance criteria") parse to zero gradeable assertions MUST NOT enter `ready`: the human `approve` valve MUST refuse it and an `auto` admission policy MUST withhold it, in both cases surfacing the parse result, the item id, and the remedy (author criteria via groom or edit; or set the item's `acceptance_policy` to `human-only` where machine grading is genuinely inapplicable). The item RESTS where it is; it is not moved to `backlog` or `blocked` on these grounds.

Add to the Dispatcher's dispatch preconditions (the `dispatch` / `loop` pre-dispatch gate):

> The Dispatcher MUST refuse to dispatch an AI-dispositive item whose effective acceptance criteria parse to zero gradeable assertions — before any factory run is created, for both the drain and the hand-picked `dispatch --item` path. The refusal MUST name the work-item id, state that the effective acceptance criteria are empty or ungradeable, and exit with the dedicated documented exit code `5` (ungradeable-acceptance-criteria refusal), distinct from the precondition exit `3` and every other documented code. Already-filed items that predate this wall are LEFT TO REFUSE ON CONTACT — no backfill pass and no exemption list; the capture, groom, and approve surfaces display the parse so each item is repaired when it is next touched.

Add a NEW ratified subsection `### Dispatcher exit codes` (no ratified exit-code enumeration exists today — this proposal creates it, documenting the shipped codes plus the new one):

> ### Dispatcher exit codes
>
> `0` — success / all dispatched green. `1` — non-skipped findings present or any terminal failed dispatch. `2` — usage error. `3` — precondition error (missing repo / workflow / item not ready). `4` — dispatch completed at a live human-gate blocked state with no terminal failures. `5` — ungradeable-acceptance-criteria refusal (§"Effective acceptance criteria" walls). `skipped`-severity findings never flip the exit code.

The capture and groom front-ends MUST display the effective-criteria parse result (the gradeable-assertion count, and the resolved source: native field, metadata, or "Exit criteria" section) whenever they create or redraft an item, and MUST NOT refuse on an empty parse — filing remains consent-gated and criteria MAY legitimately arrive at groom time.

#### 5. `scenarios.md` — three new scenarios

```gherkin
## Scenario 69 — Zero-criteria AI-dispositive work is walled before any spend

Feature: Ungradeable acceptance criteria refuse before the factory, not after the merge
  As a maintainer paying for dispatches
  I want an unverifiable item stopped at ready and at dispatch
  So that a guaranteed acceptance failure is discovered before a single token is spent

Scenario: The pre-dispatch wall refuses with the dedicated exit code
  Given an item whose effective acceptance_policy is ai-only or ai-then-human
  And its effective acceptance criteria parse to zero gradeable assertions
  When the drain or dispatch --item reaches it
  Then the dispatch is refused before any factory run is created
  And the refusal names the item id and states the criteria are empty or ungradeable
  And the exit code is 5, distinct from the precondition exit 3

Scenario: The approve valve refuses and the item rests in place
  Given a pending-approval item with the same empty effective criteria and an AI-dispositive policy
  When a human approves it or an auto admission policy considers it
  Then entry to ready is refused or withheld with the parse result surfaced
  And the item rests at pending-approval

Scenario: Criteria that yield gradeable assertions through the merged read or the fallback pass the wall
  Given an item whose gradeable criteria reach the primitive only through the metadata-merged value, or only through a description section titled Exit criteria
  When the walls evaluate it
  Then its effective criteria parse to at least one gradeable assertion and it is dispatched normally rather than refused

## Scenario 70 — Absent evidence parks; it never manufactures a verdict

Feature: The NEEDS_ATTENTION verdict is the absent-evidence disposition under every policy
  As a maintainer relying on the acceptance valve
  I want a pass that cannot observe its evidence to park the item for me
  So that no judgment is rendered with no evidence examined

Scenario: Unobservable telemetry with a readable diff parks instead of failing
  Given an item in acceptance whose run telemetry is unobservable
  And its merged diff is readable
  When the AI acceptance pass runs under any acceptance_policy
  Then the verdict is NEEDS_ATTENTION
  And the item stays parked in acceptance
  And no rework is triggered and acceptance_rework_cap is not consumed
  And the parking is journaled with the absent evidence leg
  And the human disposes of it with the existing accept or reject valve

Scenario: Zero parsed checks past the wall park instead of failing
  Given an item in acceptance whose effective criteria parse to zero gradeable assertions
  When the AI acceptance pass runs
  Then the verdict is NEEDS_ATTENTION and the item is not auto-accepted and not reworked

## Scenario 71 — One effective-criteria authority for every gate

Feature: Every gate reads the same effective acceptance criteria
  As an item author
  I want capture advice, the walls, and the acceptance pass to agree on my criteria
  So that a criteria text that passes one gate is never absent at another

Scenario: The same resolution order is used at capture, ready, dispatch, and acceptance
  Given an item whose criteria resolve through the native field, the metadata-merged read, or the description Exit criteria section
  When the capture front-end displays the parse, the ready wall evaluates it, the pre-dispatch wall evaluates it, and the acceptance pass judges it
  Then all four surfaces resolve the identical effective criteria text through the single public primitive
```

#### 6. Revise-time co-edits and sequencing

The accepting revise pass MUST add `tests/heading-coverage.json` entries for `## Scenario 69`, `## Scenario 70`, and `## Scenario 71`, and MUST sequence the implementation children it cuts together with or after the `bd-ib-tfpdya` parser repair (the walls' gradeability test) — ratification of this proposal does not close `bd-ib-tfpdya`, `bd-ib-1dbg`, or `bd-ib-5z0g`; it gives the first two their contract.
