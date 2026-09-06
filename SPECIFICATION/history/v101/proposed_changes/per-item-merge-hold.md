---
topic: per-item-merge-hold
author: claude-fable-5-1 (pluggable-factory-workflow-configs)
created_at: 2026-09-06T16:22:09Z
---

## Proposal: Add a per-item merge hold: a twelfth valve, a rendered per-item policy input, a pr stage that publishes without arming, and a host-side release

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- SPECIFICATION/README.md

### Summary

The Dispatcher and the bundled workflow cannot honor a per-item merge hold: the pr stage arms auto-merge unconditionally with the repository's declared merge_mode, and the Dispatcher's own auto-merge argv does the same, so dispatch and merge are one atomic act and a maintainer who wants an item IMPLEMENTED now but MERGED later has no route through the factory. This proposal adds one per-item policy field, the merge hold, in the class of the existing per-item cap overrides: a twelfth human valve action set-merge-hold:<work-item-id>:on|off that writes or removes the merge-hold label and never changes the item's status; a workflow input merge_hold (boolean, default false) rendered by the Dispatcher in the disjoint per-item policy-input family beside the review-fix visit cap and the merge-on-review-cap outcome, a family this proposal names in the seam-equivalence clause for the first time; a pr stage that, while the hold stands, pushes the branch and opens the pull request but arms no auto-merge and verifies none is armed; a Dispatcher auto-merge argv that likewise arms nothing while held and, on release of a hold against an open unmerged pull request, arms auto-merge from the host with the merge method of the contract journaled with that dispatch, without any re-dispatch; a held item that stays active with its green terminal run reclaimed exactly as any other, so it holds no capacity slot, that the stranded-state discriminator recognizes, and that needs-attention surfaces under the existing hygiene kind until released. There is deliberately no repository-level default for the hold. One scenario (119) states the behavior and tests/heading-coverage.json gains its entry.

### Motivation

Filed by plan pluggable-factory-workflow-configs (epic bd-ib-yqpdrt) as the spec carrier for bd-ib-vlhp, per the plan's 2026-09-06 scope event and research note plan/pluggable-factory-workflow-configs/research/003-b4-rescope-2026-09-06.md. The consumer is real and has waited since 2026-08-21: livespec-console-beads-fabro-ag0 re-keys every stored event and version identity and forces a fleet-wide re-observation, and the maintainer ruled to implement it now and pin the merge to a window they would clear; that ruling is not executable today, so the item sits parked at ready and deliberately undispatched. Three routes were weighed in the research note and this proposal records the choice so nobody re-derives it. A second variant shipped inside the plugin bundle whose pr prompt omits the arm would lift a standing deferral and drift alongside the bundle. A per-repository committed hold-merge variant, registered through the v099 named workflow-variant registry, works today and is recorded on bd-ib-vlhp as the stopgap the console tenant may use, but it copies the whole workflow into every repository that wants one hold. A per-item policy value rendered into the workflow is the shape the implementation already uses for the review-fix visit cap and the merge-on-review-cap outcome, which the Dispatcher passes as effective per-item policy values, so the hold joins that class rather than the RepoIntegrationContract schema: the contract types what the orchestrator requires of a repository, and a hold is a decision about one item, not a property of the repository. An independent objective doctor pass over the first draft (2026-09-06) found two blockers, both discharged below: the first draft kept a held item's claim counted against wip_cap, which contradicts the ratified rule that a green terminal outcome is reclaimed, so the held item now holds no slot; and the seam-equivalence clause's literal identity between workflow tokens, rendered contract inputs and schema fields left no room for a non-schema input, even though two such inputs already exist unnamed by the spec, so the clause now names that disjoint per-item policy-input family explicitly. The in-flight survey found one pending proposal, live-exercise-acceptance-admission, which concerns acceptance parking and does not touch these sections; this proposal aligns with it. It is independent of the consensus-gated-automated-groom-cut proposal filed the same day, except that both insert into "## Dispatcher policy settings" and that proposal retitles the rework-caps subsection; the insertion anchor below names both titles so either landing order resolves.

### Proposed Changes

In `SPECIFICATION/contracts.md`:

1. In "#### `drive`", in the sentence that reads "an `impl:` dispatch action, one of the eleven human valve/policy actions (`approve:` / `accept:` / `reject:` / `resolve-blocked:` / `set-admission:` / `set-acceptance:` / `set-workflow-scope-override:` / `set-merge-on-review-cap:` / `set-review-fix-cap:` / `set-acceptance-rework-cap:` / `move:`)" (hard-wrapped in the committed file; match on the sentence), replace "eleven" with "twelve" and insert "`set-merge-hold:` / " immediately before "`move:`".

2. In the paragraph beginning "**Human valve actions.** `drive` additionally accepts the eleven human operator action ids", replace "eleven" with "twelve" and replace "the three per-item cap overrides, and the guarded queue-control `move`" with "the three per-item cap overrides, the per-item merge hold, and the guarded queue-control `move`". In the same paragraph, immediately after the sentence that ends "and the guarded queue-control action `move:<work-item-id>:backlog|ready|blocked|active`.", insert this sentence: The per-item merge hold action `set-merge-hold:<work-item-id>:on|off` writes or removes the item's `merge-hold:` label (§"Dispatcher policy settings" → "The per-item merge hold") and, as its one other effect, arms or disarms the pull request's auto-merge request on the forge. Then, in the sentence that follows, replace "A policy-edit, workflow-scope assertion, OR cap-override action MUST modify ONLY the named policy, override, or cap field of an existing item (realized on beads as the `admission:` / `acceptance:` policy label, or the `merge-on-review-cap:` / `review-fix-cap:` / `acceptance-rework-cap:` cap label, through the store seam)" with "A policy-edit, workflow-scope assertion, cap-override, OR merge-hold action MUST modify ONLY the named policy, override, cap, or hold field of an existing item (realized on beads as the `admission:` / `acceptance:` policy label, the `merge-on-review-cap:` / `review-fix-cap:` / `acceptance-rework-cap:` cap label, or the `merge-hold:` hold label, through the store seam)".

3. In the same section, in the sentence "This is the published surface the console invokes for the two human-delegable gates — `approve` and `accept` — the blocked-resolution, the policy-edit actions, the three cap overrides, and the guarded `move`", replace "the three cap overrides, and the guarded `move`" with "the three cap overrides, the merge hold, and the guarded `move`"; and in the sentence "The operator-action behavior is exercised by `scenarios.md` Scenario 31 (the two gates, `reject:`, and the two policy edits), Scenario 46 (the cap overrides and clear-to-inherit), and Scenario 47 (the guarded `move`).", replace "and Scenario 47 (the guarded `move`)." with "Scenario 47 (the guarded `move`), and Scenario 119 (the merge hold).".

4. In "## Store-write consent discipline", in the sentence listing "The human-triggered operator commands (`drive` `approve:`/`accept:`/`reject:`/`resolve-blocked:`/`set-admission:`/`set-acceptance:`/`set-workflow-scope-override:`/`set-merge-on-review-cap:`/`set-review-fix-cap:`/`set-acceptance-rework-cap:`/`move:` action ids, per §"`drive`")", insert "`set-merge-hold:`/" immediately before "`move:`".

5. In "### Rework-pending re-dispatch", in the bullet beginning "**Stranded-state discrimination.** Any surface that derives a stranded, abandoned, or leaked-claim finding from" (its quoted phrase is written with plain double quotes in the committed file, and the bullet is hard-wrapped), replace "MUST treat `rework:pending` as a discriminator and MUST NOT report a marked item as stranded." with "MUST treat `rework:pending` and the `merge-hold:` label (§"Dispatcher policy settings" → "The per-item merge hold") as discriminators and MUST NOT report a marked or held item as stranded.", and in the same bullet replace "the marker partitions the two populations cleanly" with "the two markers partition the populations cleanly".

6. In "### Repository integration contract", in the paragraph "**Typed workflow inputs and the seam-equivalence check.**", immediately after the sentence "The set of `inputs.*` tokens the workflow references, the set of inputs the Dispatcher renders from the `ResolvedIntegrationContract`, and the schema's projectable fields MUST be identical.", insert this sentence: The identity ranges over the integration inputs. Two further disjoint families share the workflow's input table and the check MUST classify each explicitly and hold it to the same resolved-position rule: the ACP-adapter inputs of §"Codex ACP node model pins", and the PER-ITEM POLICY INPUTS — the review-fix visit cap, the merge-on-review-cap outcome, and `merge_hold` (§"Dispatcher policy settings" → "The per-item merge hold") — which are not schema fields but projections of the item's effective policy, resolved host-side at plan-build time and journaled on the dispatch record so the record and the run agree. A declared input belonging to none of the three families MUST fail the check. The paragraph "**Merge-strategy resolution.**" stands unchanged: its two seams — the Dispatcher's auto-merge argv and the `pr.md` prompt variable — are exactly the two seams the new subsection gates while a hold stands, and no schema field is added, changed or removed.

7. In "## Dispatcher policy settings", insert the following new subsection immediately after the rework-caps subsection — titled "### The two rework caps" today, or "### The three rework caps" if the consensus-gated-automated-groom-cut proposal has landed first — and before "### `wip_cap` — the one setting with no per-item override":

### The per-item merge hold

A merge hold is a per-item policy field with NO repository-level default:
it is set on one item, by a person, for one merge, and it is the one field
in this section that exists only per item. It does not weaken the
`wip_cap` clause below, which is about settings that lack a per-item
override; the hold is not a setting.

- **`merge_hold`** (boolean, per item only, default **`false`**) — while
  `true`, the item's approved pull request MUST NOT be merged by any
  automated path. It is set and released through the human valve action
  `set-merge-hold:<work-item-id>:on|off` (§"`drive`"), realized on beads
  as the `merge-hold:` label through the store seam: `on` writes the label,
  `off` removes it, and the label's presence is the hold. Like every policy
  edit it MUST modify only that field of the ledger record and MUST NOT
  change the item's status; unlike the other policy edits it ALSO performs
  one forge write, arming or disarming the pull request's auto-merge
  request, and that write is the action's only other effect.
- The Dispatcher MUST render the item's effective `merge_hold` as the
  workflow input `merge_hold`, a member of the per-item policy-input family
  that §"Repository integration contract" → "Typed workflow inputs and the
  seam-equivalence check" names, beside the review-fix visit cap and the
  merge-on-review-cap outcome inputs, and the token MUST sit in a position
  resolved before the sandbox executes it exactly as that clause requires of
  every input. The bundled workflow MUST declare it with its default, and a
  registered variant MUST declare it too, because the seam check holds a
  variant to the bundle's token set.
- While the hold stands, the pr stage MUST push the branch and open the
  pull request exactly as it does today, MUST NOT arm auto-merge, MUST
  verify that no auto-merge request exists on the pull request, and MUST
  report `MERGE_HOLD=held` beside the PR-number line the pr stage already
  reports in its final reply. The Dispatcher's auto-merge argv (the
  `gh pr merge` method flag of "Merge-strategy resolution") MUST NOT arm
  auto-merge for a held item either. Both seams read the one rendered value;
  neither is authoritative.
- A held item's run terminates green at the pr stage; the run never waits
  (§"A factory run never awaits a human"). The item MUST remain `active`,
  and its green terminal run is reclaimed under §"Per-repo WIP cap" exactly
  as every green terminal outcome is, so a held item holds NO capacity
  slot. A terminal run whose item is `active` under a matching journaled
  run id is not an orphan, so reconciliation MUST leave it alone; and the
  `merge-hold:` label is a discriminator for §"Rework-pending re-dispatch"
  → "Stranded-state discrimination", so a held item is never reported as
  stranded, abandoned, or leaked.
- Every held item MUST be surfaced by `needs-attention` under the
  existing `hygiene` kind as `hygiene:merge-hold:<work-item-id>`, per
  §"Orchestrator-owned attention facts", with a `summary` naming the pull
  request and a `handoff` naming `set-merge-hold:<work-item-id>:off` as
  the release. A hold MUST NOT become invisible: the attention row stands
  until the hold is released or the item leaves `active`, and it is the
  ONLY attention id a held item produces for the hold.
- Releasing the hold (`set-merge-hold:<work-item-id>:off`) against an item
  whose pull request is open and unmerged MUST arm auto-merge from the host
  with the merge method of the `ResolvedIntegrationContract` journaled with
  the dispatch that opened the pull request (never re-derived from
  configuration), and MUST NOT re-dispatch; the merge then lands
  server-side and the existing post-merge path — the post-merge janitor,
  `reconcile-merged`, acceptance — proceeds unchanged. Releasing a hold on
  an item that has no open pull request changes only what the next dispatch
  renders. Setting the hold on an item whose pull request is already armed
  MUST disarm the auto-merge request; setting it on a merged item is refused
  as a no-op naming the merge.

8. In "### `wip_cap` — the one setting with no per-item override", the sentence "It is the ONE setting among this section's policy settings with **no per-item override**" stands unchanged: the merge hold is not a setting, and the new subsection says so.

9. No H2 heading of contracts.md is added, changed or removed.

In `SPECIFICATION/README.md`, in the sentence listing the `drive` human actions "(`approve:` / `accept:` / `reject:` / `resolve-blocked:` / `set-admission:` / `set-acceptance:` / `set-merge-on-review-cap:` / `set-review-fix-cap:` / `set-acceptance-rework-cap:` / `move:`)", insert "`set-merge-hold:` / " immediately before "`move:`". (That list already lacks `set-workflow-scope-override:`, which is pre-existing drift outside this proposal's scope; this proposal adds only its own action.)

In `SPECIFICATION/scenarios.md`, append the following scenario after the highest-numbered scenario at revise time (118 if the groom-cut proposal lands first, otherwise renumber as v099 did for Scenario 117):

## Scenario 119 — A per-item merge hold publishes the pull request and merges only on release

```gherkin
Feature: A maintainer holds one item's merge without holding its implementation
  As a maintainer who wants an item implemented now and merged in a window I choose
  I want a per-item hold that the factory honors at the pr stage
  So that dispatch and merge stop being one atomic act, and the hold is visible until I release it

  Scenario: The pr stage publishes but arms nothing while held
    Given a ready work-item carrying the merge-hold label
    When the item is dispatched and its run reaches the pr stage
    Then the branch is pushed and the pull request is opened
    And no auto-merge request exists on the pull request
    And the final reply carries MERGE_HOLD=held beside the PR-number line
    And the run terminates green

  Scenario: A held item stays active, holds no slot, is not stranded, and is surfaced once
    Given an active item whose run terminated green with a held pull request
    When the Dispatcher reconciles runs, the admission accounting counts claims, and needs-attention composes its snapshot
    Then the item remains active
    And its green terminal run is reclaimed so the item holds no capacity slot
    And the run is not treated as an orphan
    And no stranded, abandoned, or leaked-claim finding names the item
    And the snapshot carries exactly one attention id for the hold, hygiene:merge-hold:<work-item-id>, naming the pull request and the release valve

  Scenario: Releasing the hold arms the merge from the host without re-dispatch
    Given an active item with an open unmerged pull request and the merge-hold label
    When an operator drives set-merge-hold:<work-item-id>:off
    Then the merge-hold label is removed and the item's status is unchanged
    And auto-merge is armed on the pull request with the merge method journaled with the dispatch that opened it
    And no new dispatch is created
    And the attention row for the hold disappears from the next snapshot

  Scenario: Setting the hold disarms an already-armed pull request
    Given an active item whose pull request has auto-merge armed
    When an operator drives set-merge-hold:<work-item-id>:on
    Then the merge-hold label is written
    And the auto-merge request is removed
    And the item's status is unchanged

  Scenario: The hold is rendered as a per-item policy input resolved before the sandbox runs
    Given a work-item carrying the merge-hold label
    When its dispatch plan is built
    Then the rendered inputs carry merge_hold true beside the other per-item policy inputs
    And the seam-equivalence check classifies merge_hold in the per-item policy-input family and finds it declared by the bundle and by every registered variant

  Scenario: A hold has no repository-level default
    Given a repository whose .livespec.jsonc declares no merge hold key
    When any work-item without the merge-hold label is dispatched
    Then merge_hold renders false
    And the pr stage arms auto-merge exactly as it did before this section existed
```

Co-edit (resulting_files): `tests/heading-coverage.json` MUST gain one entry for the new heading `## Scenario 119 — A per-item merge hold publishes the pull request and merges only on release` with `spec_root` "SPECIFICATION", `spec_file` "scenarios.md", `test` "TODO", `work_item` "bd-ib-yqpdrt", and a `reason` stating that the exercising integration-tier test is owed by plan pluggable-factory-workflow-configs once the implementation child filed under bd-ib-vlhp at this revision's revise pass lands, and that until then the behavior has no implementation to bind to. If the scenario is renumbered at revise time, the heading text, edit 3's Scenario 119 citation, and this entry MUST be renumbered together.
