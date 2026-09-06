---
topic: consensus-gated-automated-groom-cut
author: claude-fable-5-1 (pluggable-factory-workflow-configs)
created_at: 2026-09-06T16:22:08Z
---

## Proposal: Permit a consensus-gated automated groom cut, realized as a two-phase groom workflow variant answered through the ledger

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- SPECIFICATION/spec.md

### Summary

Section "Grooming and slice-size calibration" of contracts.md still says the groom cut is human in every case: touchpoint 2 files nothing until the human approves, and the gap-detectable clause restates it. livespec's spec-side-autonomy plan resolved on 2026-08-03 that the cut MAY leave the maintainer's hands, automated LAST and consensus-gated, with slice-size ceilings plus a regroom cap as REQUIRED rails, for the cut only, and named this section as amendable for exactly that. The amendment was never made. This proposal adds one subsection, "Consensus-gated automated groom cut", one gap-detectable clause line, one pointer sentence in touchpoint 2, and three small door edits. It permits the groom front-end to delegate its drafting to a registered groom workflow variant through a journaled groom dispatch, a two-phase run under "A factory run never awaits a human": the propose phase drafts and terminates at a needs-human outcome, the Dispatcher records the draft on the item as a ledger comment, approval arrives through the resolve-blocked valve and is itself the consent for the filing that follows, and the item's recorded workflow pin selects the groom variant again for the apply dispatch, which files the approved slices and regrooms the original out. Until livespec core ratifies the consensus tier the approving invoker MUST be a human operator, so the automated cut is permitted in principle and stays human-decided in fact; once the tier is ratified, and only where the repository has opted in through a committed key, the tier MAY own the approval of the FIRST cut of an intake-routed epic and nothing else: every re-groom of a Dispatcher non-convergence bounce stays human, behind the two required rails. Filing without a recorded approval MUST be refused, which is the mechanism bd-ib-ouoq asked for. One scenario (118) states the behavior and tests/heading-coverage.json gains its entry.

### Motivation

Filed by plan pluggable-factory-workflow-configs (epic bd-ib-yqpdrt) as the spec carrier for bd-ib-e38q, per the plan's 2026-09-06 scope event and research note plan/pluggable-factory-workflow-configs/research/003-b4-rescope-2026-09-06.md. The console plan console-control-plane-primitives deferred its b4 piece, workflow variants "with interview consent", to this plan and archived; the console sweep bd-ib-j81s re-parented bd-ib-e38q, bd-ib-ouoq and bd-ib-js1f here with the rationale that the groom cut becomes a dispatchable workflow. Three facts fix the shape. (1) The values call is already resolved by the maintainer and recorded in livespec's plan/archive/spec-side-autonomy/research/brainstorm.md, "Values calls" item 2, so this proposal carries it rather than re-deciding it; its preconditions were checked, not assumed: spec-side-autonomy Increments 1 and 2 are closed (livespec-jvdvx4.3, livespec-jvdvx4.4), and the consensus tier is NOT yet ratified in livespec core, whose spec reads that consensus "MUST escalate until the separately ratified consensus tier and its evidence are available"; core's own Increment 3 landed in that report-only shape, and this amendment takes the same one, including core's committed opt-in key precedent. (2) This repository's v093, "A factory run never awaits a human", forbids an interactive human-decision node whose answer resumes a run, so the console's "interview consent" is realized as a two-phase run answered through the resolve-blocked valve, never an in-run interview; the console session recorded this as a cross-repo tension on 2026-09-06 and for this repository's variants v093 governs. (3) The ledger-comment answer on resolve-blocked shipped on 2026-09-06 as bd-ib-uuohty (PR #2200) with no clause recording it; the third bullet of the new subsection ratifies that behavior for the groom case, closing that impl-to-spec drift where this proposal needs it. The named workflow-variant registry the groom variant registers through, and the per-item dispatch_workflow pin the apply dispatch relies on, were ratified in v099 and implemented the same day (bd-ib-27puvv, bd-ib-u7arwz, bd-ib-asrazi). An independent objective doctor pass over the first draft of this proposal (2026-09-06) found three blockers, each discharged in the text below: the tier-approved filing had no consent form under the store-write discipline (now the recorded approval is that consent, and tier ownership needs a committed opt-in); the re-groom of a bounced item is human-gated by design and the first draft let the tier re-cut it (now the tier may own only the first cut of an intake-routed epic); and a backlog item had no lawful door into a factory dispatch (now the groom front-end performs a journaled groom dispatch, named in the door rules and the Dispatcher's disposition set). Implementation follow-ups are filed under the plan epic after this revision is on master: the groom workflow variant child, and bd-ib-ouoq (the approval record on file_approved_slices), whose criterion 1 this proposal's third bullet resolves as candidate (a). The in-flight survey found one pending proposal, live-exercise-acceptance-admission, which concerns acceptance parking and does not touch these sections; this proposal aligns with it. It is independent of the per-item-merge-hold proposal filed the same day, which edits the drive valve enumeration; this proposal adds no valve.

### Proposed Changes

In `SPECIFICATION/contracts.md`, section "Grooming and slice-size calibration":

1. In "### The four maintainer touchpoints", item 2 ("Groom (the one new maintainer surface)"), after the final sentence "The draft is read-only until the human approves — it proposes; it files nothing until approval." (hard-wrapped across two lines in the committed file; match on the sentence, not on one line), append this sentence: The draft MAY instead be produced by a registered groom workflow variant through a journaled groom dispatch under §"Consensus-gated automated groom cut" below; the approval act, and who may perform it, are what that subsection governs.

2. Insert the following new subsection immediately after "### Resolved realization choices" and before "### Gap-detectable behavior clauses":

### Consensus-gated automated groom cut

This subsection carries the values call livespec's spec-side-autonomy plan
resolved on 2026-08-03 (design record: repository `thewoolleyman/livespec`,
`plan/archive/spec-side-autonomy/research/brainstorm.md`, "Values calls",
item 2): the groom cut MAY leave the maintainer's hands, but automated
LAST and consensus-gated, for the cut only. What may be delegated to a
factory run is the DRAFTING of a decomposition; what may later be delegated
to the consensus tier is the approval of the FIRST cut of an intake-routed
epic, and nothing else. The re-groom of a Dispatcher non-convergence bounce
is a decision that is human-gated by design under §"Every needs-human
escalation still reaches a human", and this subsection leaves it so.

- **The groom dispatch is the door.** The `groom` front-end (touchpoint 2)
  MAY delegate its drafting to a registered groom workflow variant by
  performing a JOURNALED GROOM DISPATCH of the `backlog` item: a dispatch
  under which the item enters `active` from `backlog` under a dispatch
  claim (the defined `admit` verb stays `ready → active`), records
  the groom variant as the item's `dispatch_workflow` pin (§"Self-contained
  plugin dispatch" → "Named workflow variants"), and journals itself
  exactly as a factory dispatch does. A repository that grooms this way
  MUST register the groom variant through that registry; the reserved
  `implement-work-item` workflow MUST NOT groom, and a groom variant MUST
  NOT implement. A groom dispatch is the ONLY way a `backlog` item enters
  `active`, and the Dispatcher MUST NOT admit a `backlog` item on its own
  initiative: the front-end's operator performs it.
- **Two phases, never a waiting run.** A groom variant MUST be a two-phase
  run under §"A factory run never awaits a human". Its propose phase MUST
  draft the decomposition exactly as the `groom` front-end drafts it —
  candidate slices pre-filled with acceptance, autonomy tier, dependency
  links, repo target and scope, arranged into dependency layers — MUST
  file nothing, and MUST terminate at a needs-human outcome carrying the
  draft, so that the item rests at `blocked / needs-human`. When the
  Dispatcher journals that termination it MUST record the draft on the
  item as a ledger comment, beside the preserve-by-reference pointer; that
  comment is where the draft rests, and it is what the apply phase reads.
  The apply phase MUST run only on a later dispatch of the same item whose
  rendered goal carries a recorded approval, and MUST then file the
  approved slices exactly as touchpoint 2 files them on human approval:
  via `capture-work-item`, with dependency edges linked, spec-change slices
  routed to `/livespec:propose-change` rather than the factory, and the
  original regroomed-out. The apply run's terminal disposition of the
  original is the `regroom-out` disposition of §"Machine-path exemption —
  the Dispatcher": the original closes as regroomed-out once its approved
  slices are filed, and the dispatch claim ends with it.
- **The approval is the consent.** Approval of a drafted cut MUST arrive
  through the `resolve-blocked:<work-item-id>:ready` valve, MUST be
  recorded as a ledger comment on the item BEFORE the status transition,
  naming the approving invoker, and the Dispatcher MUST fold that comment
  into the item's next rendered goal. An item so approved rests at `ready`
  for its APPLY dispatch, not for implementation: a groom-pinned item at
  `ready` is authorized for its apply dispatch and carries the approved
  draft in place of an acceptance, its `dispatch_workflow` pin still names
  the groom variant, and the admission valve dispatches it under that
  variant through the recorded-pin step of the registry precedence. An
  apply dispatch of an item carrying an approved groom draft whose
  resolution is anything other than a registered groom variant — an
  explicit `--workflow-name` naming the reserved workflow or a non-groom
  variant, or a cleared pin that falls through to
  `dispatcher.default_workflow` — MUST be refused before any Fabro run
  exists, as a further cause of the journaled pre-run refusal of
  §"Self-contained plugin dispatch" → "Named workflow variants".
  `resolve-blocked:<work-item-id>:backlog` MUST send the draft back for
  re-drafting and MUST NOT file anything. The recorded approval IS the
  apply phase's consent under §"Store-write consent discipline": it is an
  up-front, per-operation decision the approving operator made through the
  valve, so the filing that follows is user-consented and needs no waiver.
  The filing seam (`file_approved_slices`) MUST require an approval record
  naming the approver identity and how the approval was obtained, MUST
  stamp that record on every filed slice and on the regroomed-out original
  in a field a later reader can query, and MUST refuse a call that carries
  none.
- **Human until the tier exists, and opted in even then.** Until livespec
  core ratifies the consensus tier, the approving invoker MUST be a human
  operator: the automated cut is permitted in principle and stays
  human-decided in fact. Once core ratifies the tier and its evidence is
  present, fresh and conforming, the tier MAY own the approval of a drafted
  cut ONLY where the governed repository has opted in through the committed
  policy setting **`dispatcher.groom_cut_approval`** (enum `human` |
  `consensus`, default **`human`**), a §"Dispatcher policy settings"
  setting whose per-item label override MAY only lower an item to `human`
  and MUST NOT raise one to `consensus`. Under that opt-in the tier MAY own
  only the FIRST CUT of an item that intake routed to `backlog` as an
  epic — an item for which no slice has yet been filed and which entered
  `backlog` only by intake routing, never by a Dispatcher bounce or a
  `reject:regroom`. Where the setting is `consensus`, the
  committed setting IS the standing consent for tier-approved first-cut
  filings: a ratified, explicit exception to the no-persist rule of
  §"Store-write consent discipline" → "Operation-class waiver", in the
  shape of livespec core's `spec_governance.drift_acceptance_mode` opt-in,
  covering exactly that one operation class and nothing else. It MUST NOT
  own the re-groom of an item the Dispatcher bounced to
  `backlog` on non-convergence, a spec-change slice, or any other decision
  that is human-gated by design; every such approval stays a human
  operator's.
- **Two rails, required.** When the consensus tier owns an approval, two
  rails are REQUIRED, not optional. Every slice the apply phase files MUST
  be at or below the calibrated ceiling of §"Gate type determines hard
  versus advisory"; the intake size gate stays ADVISORY for a human-approved
  cut exactly as that section says, and the ceiling becomes hard only for a
  tier-approved one, so while no ceiling has been calibrated and adopted
  the tier MUST NOT approve and the draft MUST rest for a human. A regroom
  cap, the committed policy setting **`dispatcher.automated_regroom_cap`**
  (integer, default **`2`**, with a per-item label override like the two
  rework caps), MUST bound how many times the tier may send one item's
  draft back for re-drafting; at the cap the draft MUST rest at
  `blocked / needs-human` for a human operator, who alone may approve it
  or send it back further.

3. In "### Gap-detectable behavior clauses", after the paragraph beginning "An item MUST enter `backlog` on an intake Definition-of-Ready epic failure", insert this clause paragraph:

A registered groom workflow variant, entered only by the groom front-end's journaled groom dispatch of a `backlog` item, MUST draft the decomposition and terminate at a needs-human outcome without filing anything, with the Dispatcher recording the draft on the item as a ledger comment; MUST file the approved slices only on a later dispatch under the item's groom-variant pin whose rendered goal carries an approval recorded as a ledger comment through `resolve-blocked:<work-item-id>:ready` naming the approving invoker, that approval being the filing's consent; MUST stamp the approval record on every filed slice and on the regroomed-out original and refuse a filing that carries none; and MUST accept only a human operator's approval until livespec core ratifies the consensus tier, after which the tier MAY approve only the first cut of an intake-routed epic, only under `dispatcher.groom_cut_approval: consensus`, and only behind the calibrated slice-size ceiling and `dispatcher.automated_regroom_cap`.

4. "### Dispatcher grooming behavior" and §"Every needs-human escalation still reaches a human" are untouched: the non-convergence bounce still routes back to the groom front-end, which the new subsection may realize as a variant, and the re-groom of a bounced item stays the human-gated-by-design decision that section names, which the new subsection's fourth bullet defers to by reference and never lets the tier own.

In `SPECIFICATION/contracts.md`, section "Store-write consent discipline", subsection "### Machine-path exemption — the Dispatcher":

5. In the sentence enumerating the lifecycle verbs, replace "the non-convergence `backlog` bounce, and — when the effective `admission_policy` is `auto`" with "the non-convergence `backlog` bounce, the `regroom-out` disposition (closing a groomed original as regroomed-out once its approved slices are filed by an apply dispatch under §"Grooming and slice-size calibration" → "Consensus-gated automated groom cut"), and — when the effective `admission_policy` is `auto`".

In `SPECIFICATION/contracts.md`, section "Store-write consent discipline", subsection "### Operation-class waiver":

5a. After the sentence "Absent a waiver, per-operation consent is required." (hard-wrapped across two lines in the committed file; match on the sentence, not on one line; and apply edit 7 before checking this sentence's citation, because the title it cites exists only after that retitle), append this sentence: One committed exception exists: `dispatcher.groom_cut_approval: consensus` (§"Dispatcher policy settings" → "The four policy settings") is a ratified standing consent for exactly one operation class, the consensus tier's approval of a FIRST groom cut filed under §"Grooming and slice-size calibration" → "Consensus-gated automated groom cut", in the shape of livespec core's `spec_governance.drift_acceptance_mode` opt-in; no other committed key MAY stand in for a waiver, and a human operator's approval through `resolve-blocked` is consent under the up-front operation decision form above, not under this exception.

In `SPECIFICATION/contracts.md`, section "Self-contained plugin dispatch", paragraph "Named workflow variants":

5b. In the refusal sentence that reads "The Dispatcher MUST refuse the dispatch before any Fabro run exists, in the same shape as the layer-names-an-absent-node refusal of §"ACP node adapter configuration" — a journaled pre-run refusal whose stage names every cause that applies — when: the selected name matches no registry entry and is not the reserved name; the selected registry directory lacks `workflow.toml` or `workflow.fabro`; or a registry entry is named `implement-work-item`." (hard-wrapped in the committed file; match on the sentence), replace "; or a registry entry is named `implement-work-item`." with "; or a registry entry is named `implement-work-item`; or the work-item carries an approved groom draft awaiting its apply dispatch and the selected name is not a registered groom variant (§"Grooming and slice-size calibration" → "Consensus-gated automated groom cut").".

In `SPECIFICATION/contracts.md`, subsection "#### Door rules — every transition has exactly one journaled owner":

6. In the bullet beginning "`active` is entered ONLY by a journaled dispatch — factory dispatch or `driver-dispatch` — OR by a rework return from `acceptance`" (hard-wrapped across two lines in the committed file; match on the sentence, not on one line), replace "factory dispatch or `driver-dispatch`" with "factory dispatch, `driver-dispatch`, or the groom front-end's groom dispatch of a `backlog` item (§"Grooming and slice-size calibration" → "Consensus-gated automated groom cut")". The `backlog` row of "#### Per-lane valid operator verb sets" is unchanged: its "groom (every backlog item, uniformly)" verb is the verb the groom dispatch belongs to.

In `SPECIFICATION/contracts.md`, section "Dispatcher policy settings":

7. In "### The three policy settings", append a fourth bullet after the `dispatcher.merge_on_review_cap` bullet: **`dispatcher.groom_cut_approval`** (enum `human` | `consensus`, default **`human`**) — who may approve a drafted groom cut under §"Grooming and slice-size calibration" → "Consensus-gated automated groom cut": `human` ⇒ only a human operator's `resolve-blocked` answer approves; `consensus` ⇒ the ratified consensus tier MAY approve the first cut of an intake-routed epic, and only that. Per-item override: a per-item label that MAY only lower an item to `human` and MUST NOT raise one to `consensus`. Until livespec core ratifies the tier, `consensus` behaves as `human`. The subsection heading "### The three policy settings" is retitled "### The four policy settings" and its lead-in sentence is unchanged.

8. In "### The two rework caps", append a third bullet after the `dispatcher.acceptance_rework_cap` bullet: **`dispatcher.automated_regroom_cap`** (integer, default **`2`**) — how many times the consensus tier MAY send one item's drafted groom cut back for re-drafting before the draft rests at `blocked` / `blocked_reason: needs-human` for a human operator (§"Grooming and slice-size calibration" → "Consensus-gated automated groom cut"). It is inert while `dispatcher.groom_cut_approval` is `human`. The subsection heading "### The two rework caps" is retitled "### The three rework caps" and its lead-in sentence "each bounds one of the two INDEPENDENT rework loops" becomes "each bounds one of the three INDEPENDENT rework loops".

9. No H2 heading of contracts.md is added, changed or removed; two H3 headings are retitled as edits 7 and 8 say, and neither is a `## ` heading, so `tests/heading-coverage.json` carries no contracts.md change for them. Inside contracts.md no §-citation names either old H3 title. Three prose mentions outside contracts.md go stale with the retitle and are dispositioned here: `SPECIFICATION/spec.md` is co-edited by edit 10 below; the `reason` of the `## Dispatcher policy settings` entry in `tests/heading-coverage.json` ("the three policy settings ... the two rework caps") SHOULD be updated to "the four policy settings ... the three rework caps" in the same revise co-edit; and the committed comment in `.livespec.jsonc` citing §"The three policy settings" is a follow-up edit for the implementation child, not a spec change.

In `SPECIFICATION/spec.md`:

10. In the sentence "The wire surface (the setting keys and their safe defaults, the per-item override labels, the two rework caps, the pass/fail AI acceptance pass, the per-disposition audit journal, and the API-configurable completeness principle) is specified in `contracts.md` §"Dispatcher policy settings"" (hard-wrapped in the committed file), replace "the two rework caps" with "the three rework caps".

In `SPECIFICATION/scenarios.md`, append the following scenario after Scenario 117:

## Scenario 118 — A groom workflow variant drafts a cut, parks it in the ledger, and files only on a recorded approval

```gherkin
Feature: The groom cut may be drafted by a factory run without a run ever awaiting a human
  As a maintainer who owns the cut
  I want the groom front-end to delegate drafting to a registered groom variant and park the draft in the ledger
  So that the approval stays a ledger act I perform, and later the consensus tier may perform for a first cut, and no run ever pauses on me

  Scenario: The groom dispatch is the only door and the propose phase files nothing
    Given a backlog item that intake routed there as an epic
    And a registered groom workflow variant
    When the groom front-end performs a groom dispatch of the item under that variant
    Then the dispatch is journaled and the item's dispatch_workflow pin names the groom variant
    And the run terminates at a needs-human outcome carrying the drafted slices
    And no slice is filed
    And the item rests at blocked / needs-human with the draft recorded on it as a ledger comment

  Scenario: The Dispatcher never admits a backlog item on its own
    Given a backlog item and a registered groom workflow variant
    When the Dispatcher loop runs with no operator groom dispatch
    Then the item stays at backlog
    And no groom run exists

  Scenario: A human approval files the approved slices on the apply dispatch
    Given an item resting at blocked / needs-human with a drafted cut and a groom-variant pin
    When an operator answers resolve-blocked with ready and an approval
    Then the approval is a ledger comment on the item written before the transition and naming the invoker
    And the item rests at ready for its apply dispatch
    And the admission valve dispatches it under the groom variant, never under implement-work-item
    And the apply dispatch files the approved slices with dependency edges linked
    And every spec-change slice is routed to propose-change rather than the factory
    And the original item closes as regroomed-out
    And every filed slice and the regroomed-out original carry the approval record in a queryable field

  Scenario: Sending the draft back re-drafts and files nothing
    Given an item resting at blocked / needs-human with a drafted cut
    When an operator answers resolve-blocked with backlog
    Then no slice is filed
    And the item rests at backlog for the groom front-end to dispatch again

  Scenario: A filing without an approval record is refused
    Given a drafted cut and no approval record
    When the filing seam is called
    Then the call is refused
    And no slice is filed
    And the original item keeps its status

  Scenario: Until the consensus tier is ratified only a human operator approves
    Given livespec core has not ratified the consensus tier
    And an item resting at blocked / needs-human with a drafted cut
    When no human operator has answered resolve-blocked
    Then the item stays at blocked / needs-human
    And no dispatch applies the draft

  Scenario: The tier approves only where the repository opted in and only a first cut
    Given the consensus tier is ratified with present, fresh and conforming evidence
    And a repository whose dispatcher.groom_cut_approval is consensus
    And a drafted first cut of an item that intake routed to backlog as an epic
    When the tier approves the draft
    Then the approval is recorded as a ledger comment naming the tier as the invoker
    And the apply dispatch files the slices

  Scenario: The re-groom of a bounced item stays a human's
    Given the consensus tier is ratified and the repository opted in
    And an item the Dispatcher bounced to backlog on non-convergence
    When its draft cut awaits approval
    Then the tier does not approve it
    And the draft rests at blocked / needs-human for a human operator

  Scenario: The regroom cap parks a repeatedly sent-back draft for a person
    Given the tier owns approvals for a repository
    And the tier has already sent one item's draft back for re-drafting as many times as dispatcher.automated_regroom_cap allows
    When a further draft is produced for it
    Then the draft rests at blocked / needs-human for a human operator
    And the tier does not approve or send it back again
```

Co-edit (resulting_files): `tests/heading-coverage.json` MUST gain one entry for the new heading `## Scenario 118 — A groom workflow variant drafts a cut, parks it in the ledger, and files only on a recorded approval` with `spec_root` "SPECIFICATION", `spec_file` "scenarios.md", `test` "TODO", `work_item` "bd-ib-yqpdrt", and a `reason` stating that the exercising integration-tier test is owed by plan pluggable-factory-workflow-configs once the groom workflow variant child (filed under bd-ib-yqpdrt at this revision's revise pass) and bd-ib-ouoq land, and that until then the behavior has no implementation to bind to. If Scenario 118 is taken by a revision that lands first, the revise pass MUST renumber this scenario and its coverage entry together, as v099 did for Scenario 117.
