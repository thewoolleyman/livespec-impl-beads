---
topic: typed-integration-fields-merge-strategy-and-sandbox-exemption
author: typed-repo-integration-contract
created_at: 2026-08-30T14:10:00Z
---

## Proposal: Two typed integration-contract fields — merge strategy and the sandbox commit-refuse exemption marker

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

Add two integration points to the `RepoIntegrationContract` field enumeration
ratified in §"Repository integration contract" (v092): the post-merge **merge
strategy** and the **sandbox commit-refuse exemption marker**. Both are integration
points the orchestrator requires of a governed repository — so under "One schema"
each MUST be a schema field — and today each is an ungoverned literal that an
adopter must fork the workflow to change (`_dispatcher_fabro_argv.py:315` and
`prompts/pr.md:84` hardwire `--rebase`; `workflow.toml:386` unconditionally sets
`git config livespec.sandboxExempt true`). This proposal makes each a DEFAULTED
schema field with a closed value space (`dispatcher.merge_mode` ∈ {`rebase`,
`squash`}, default `rebase`; `dispatcher.sandbox_exempt_marker` = the fixed fleet
value `livespec.sandboxExempt`), read through the one generic resolver and
projected once from the `ResolvedIntegrationContract`. Each carries its
members-and-adopters disposition per the closed-set rule (§ line 2987), co-edits
the ratified sites that still hardwire the old literals, and adds one binding
scenario. These are filed together as one proposal because both edit the same "One
schema" enumerating sentence. Design record: plan `typed-repo-integration-contract`
(epic `bd-ib-vblnq2`), scope-event comment R1+; the maintainer ruled 2026-08-30 to
ratify both.

### Motivation

Both are couplings the specification does not currently govern and that strand
adopters silently. The merge strategy decides how every dispatched item lands, and
it already drifted (the argv and the prompt both say `--rebase` with nothing making
them agree); an adopter that merges by squash (homelab, to `main`) must fork the
prompt. The sandbox-exemption marker is set by the orchestrator and MUST be honored
by a governed repository's commit-blocking hooks — an adopter whose hook ignores it
strands every dispatch as an empty-commit casualty, which is the measured homelab
failure. Ratifying each as a field with a validated referent and an adopter-fixture
obligation converts two discovered-one-dispatch-at-a-time couplings into declared,
validated integration points — the whole thesis of v092.

### Design note — merge_mode excludes a true merge commit; sandbox_exempt_marker is a single-value field

`merge_mode` admits `{rebase, squash}` and excludes a true `--merge` commit. The
real reason is not the branch-cleanup signals (the `no-stale-worktree` /
reconcile-merged machinery resolves through forge merged-state and is merge-method
agnostic): it is that two post-merge code paths read the merge commit directly and
break on a merge commit's combined diff. Acceptance's fallback merged-diff read is
`git show --format= <merge_sha>` (`_dispatcher_acceptance_diff.py:86`), whose output
is EMPTY for a clean merge commit, tripping the "merged diff is empty" refusal; and
the `reject:regroom` valve reverts with `git revert --no-edit <merge_sha>`
(`_drive_valves.py:282`), which fails on a merge commit because it carries no `-m`
parent selector. Both `rebase` and `squash` land a single non-merge commit that
both paths handle (squash's `git show` fallback shows the FULL diff, strictly better
than rebase's series-tip fallback). Admitting `merge` is a separate obligation that
must ratify those two code-path changes; per the closed-set rule it is not smuggled
in here.

`sandbox_exempt_marker` is a field whose admitted value space is CLOSED to the
single fleet value `livespec.sandboxExempt`. It is a field rather than a prose
clause because §"One schema" states a point that is not a field is not a requirement
the orchestrator may impose, and this is a requirement (an unhonored marker breaks
the sandbox); v092 itself establishes fields whose value does not vary (the
ratified-as-no-op arm is "a schema field whose FleetDefault is an explicit no-op
VALUE"). The value space is closed to one because the wheel-shipped canonical hook
body reads a HARDCODED `livespec.sandboxExempt` (`justfile:219`, `lefthook.yml:25`),
so a declared alternate key would be set by the projection and ignored by every
fleet hook — a stranded dispatch, contract-sanctioned and uncatchable. Key variance
is a separate future ratification requiring a key-parameterized hook body, symmetric
with merge_mode's merge-commit exclusion.

### Proposed Changes

## contracts.md — §"One schema", add both fields to the enumeration (one edit)

```diff
@@ contracts.md §"Repository integration contract" — "One schema." paragraph, the enumerating sentence @@
-`RepoIntegrationContract` schema shipped in the plugin payload: the
-check-suite per venue (host janitor and in-sandbox gate), the bootstrap
-recipe, the master-CI pipeline, the core-provisioning repository and ref,
-the prepare-toolchain premises, and the default branch. An integration
+`RepoIntegrationContract` schema shipped in the plugin payload: the
+check-suite per venue (host janitor and in-sandbox gate), the bootstrap
+recipe, the master-CI pipeline, the core-provisioning repository and ref,
+the prepare-toolchain premises, the default branch, the post-merge merge
+strategy, and the sandbox commit-refuse exemption marker. An integration
```

## contracts.md — two new MECHANISM clauses, as bold intra-section paragraphs immediately before §"Members-and-adopters-identical audit of the step and preflight set."

```diff
@@ contracts.md — insert immediately before the paragraph beginning "**Members-and-adopters-identical audit of the step and preflight set.**" @@
+**Merge-strategy resolution.** The strategy by which a dispatched item's
+approved pull request lands on the default branch is the schema field
+`dispatcher.merge_mode`, resolved through the one generic resolver and read as
+the SEMANTICS of that field. It is a DEFAULTED field: an absent key resolves to
+the `FleetDefault` value `rebase`, preserving today's behaviour, and a present
+key MUST be one of the closed enum `rebase` or `squash` — any other value
+resolves to `Defective` naming `dispatcher.merge_mode`. A true merge commit is
+NOT an admitted value: two post-merge paths read the merge commit directly and
+break on its combined diff — acceptance's fallback merged-diff read
+(`git show --format= <merge_sha>`, empty for a clean merge) and the
+`reject:regroom` revert (`git revert --no-edit <merge_sha>`, which needs an `-m`
+parent selector on a merge commit) — so admitting `merge` is a separate
+obligation that must ratify those changes. The resolved value projects, per
+"Resolve once, project everywhere", into BOTH the Dispatcher's auto-merge argv
+(the `gh pr merge` method flag) and the `pr.md` prompt variable the in-run agent
+uses to arm auto-merge — two seams of one resolved object, neither authoritative,
+kept in agreement by the seam-equivalence check — and it is one of the fields
+that check ranges over. Only the merge-METHOD flag is projected; the branch
+rebases the workflow performs onto the default branch before pushing are a
+different operation unaffected by this field.
+
+**Sandbox commit-refuse exemption resolution.** A Fabro sandbox is a fresh full
+clone, structurally indistinguishable from a primary checkout, so a governed
+repository's commit-blocking hooks would refuse the sandbox's Red-Green-Replay
+commits. The git-config marker key that exempts those commits is the schema field
+`dispatcher.sandbox_exempt_marker`, resolved through the one generic resolver and
+read as the SEMANTICS of that field. Its admitted value space is CLOSED to the
+single `FleetDefault` value `livespec.sandboxExempt`; any other declared value
+resolves to `Defective` naming `dispatcher.sandbox_exempt_marker`, because the
+canonical commit-refuse hook body reads that key literally and a divergent key
+would be set but never honored. The resolved value has two ratified halves.
+First, the orchestrator MUST set that marker to `true` in the sandbox before any
+Red-Green-Replay commit, as a PROJECTION of the field into the prepare step,
+never a hardcoded literal. Second, a governed repository's COMMIT-BLOCKING hooks
+MUST HONOR the marker: when the resolved marker key reads `true` in the sandbox's
+git config, the hook MUST NOT refuse a commit on primary-checkout-detection
+grounds, while every Red-Green-Replay gate the hook delegates still fires. Honor
+is a governed-repository obligation the adopter fixture (§"Governed-repository
+integration constraints") exercises. The marker is local git config only and
+never leaves the ephemeral sandbox (a push carries refs, not config).
```

## contracts.md — members-and-adopters audit, append two disposition rows

```diff
@@ contracts.md — append after the "Factory-sandbox toolchain premises (...)" bullet and before the "- Every step and preflight, by construction:" bullet @@
+- `merge-strategy` (post-merge auto-merge method): made declaration-based by
+  "Merge-strategy resolution" via `dispatcher.merge_mode` with a declared
+  `FleetDefault` of `rebase`. A fleet member that declares nothing keeps rebase
+  (satisfying this repo's inherited member-scoped "rebase-merge-only master"
+  constraint, `constraints.md`); an adopter that merges by squash declares
+  `squash`. Neither carries a divergent workflow fork for the merge method.
+- `sandbox-exempt-marker` (in-sandbox commit-refuse exemption): made
+  declaration-based by "Sandbox commit-refuse exemption resolution" via
+  `dispatcher.sandbox_exempt_marker` with a declared `FleetDefault` of
+  `livespec.sandboxExempt` and a value space closed to that one value. A fleet
+  member honors it through the canonical commit-refuse hook body; an adopter MUST
+  honor the same resolved marker in its own commit-blocking hooks, and the
+  adopter fixture fails if it does not.
```

## contracts.md — §"Post-merge acceptance", refer to the resolved merge method

```diff
@@ contracts.md §"Post-merge acceptance (`acceptance → done`)" — the "**`complete` (`active → acceptance`)**" bullet @@
-  **`complete` (`active → acceptance`)** MUST **merge-on-green**: the
-  Fabro impl run keeps today's `gh pr merge --rebase --auto`; entering
+  **`complete` (`active → acceptance`)** MUST **merge-on-green**: the
+  Fabro impl run merges via `gh pr merge` with the resolved
+  `dispatcher.merge_mode` method (default `rebase`) and `--auto`; entering
```

## contracts.md — §"Dispatch-time baseline conformance gate", refer to the resolved marker field

```diff
@@ contracts.md — the baseline-gate prepare-chain sentence naming the marker @@
-structural commit-refuse hook (concern #1 Worktree-discipline,
-Mechanism) and declare the sandbox's `livespec.sandboxExempt` marker
-(concern #1 Exemption), and it MUST then run the baseline Verifiers over
+structural commit-refuse hook (concern #1 Worktree-discipline,
+Mechanism) and set the sandbox's resolved `dispatcher.sandbox_exempt_marker`
+(default `livespec.sandboxExempt`; concern #1 Exemption) as a projection of the
+field per §"Repository integration contract", and it MUST then run the baseline
+Verifiers over
```

## scenarios.md — two new scenarios appended after Scenario 106

Append (H2 headings OUTSIDE the fences, `Scenario:` blocks indented two spaces, per the Scenario 106 house format):

```text
## Scenario 107 — An adopter's declared merge strategy projects to both the argv and the prompt
```
````gherkin
Feature: Merge strategy is a typed integration-contract field
  As the maintainer of an adopter repository that merges by squash
  I want the declared merge strategy to drive both the auto-merge argv and the prompt
  So that I never fork the workflow to change how my items land

  Scenario: An adopter declares squash
    Given a governed repository whose declaration sets dispatcher.merge_mode to squash
    When the Dispatcher resolves the integration contract at plan build
    Then the resolved merge strategy is squash
    And the projected gh pr merge argv names the squash method
    And the pr.md prompt variable for the merge method is squash

  Scenario: A fleet member declares nothing
    Given a governed repository whose declaration omits dispatcher.merge_mode
    When the Dispatcher resolves the integration contract at plan build
    Then the resolved merge strategy is the fleet default rebase

  Scenario: An unsupported merge method is defective
    Given a governed repository whose declaration sets dispatcher.merge_mode to a value outside rebase and squash
    When the Dispatcher validates the declaration before dispatch
    Then the merge strategy point resolves to Defective naming dispatcher.merge_mode
    And the dispatch is refused as a pre-dispatch precondition error
````

```text
## Scenario 108 — A governed repository's commit-blocking hook honors the resolved sandbox-exemption marker
```
````gherkin
Feature: The sandbox commit-refuse exemption marker is a typed integration-contract field
  As the maintainer of a governed repository dispatched to the factory
  I want the sandbox-exemption marker set and honored through the contract
  So that a fresh-clone sandbox can make its Red-Green-Replay commits

  Scenario: The orchestrator sets the resolved marker in the sandbox
    Given a governed repository whose declaration omits dispatcher.sandbox_exempt_marker
    When the Dispatcher resolves the integration contract at plan build
    Then the resolved marker key is the fleet default livespec.sandboxExempt
    And the sandbox prepare step sets that marker to true as a projection of the field

  Scenario: The adopter fixture's commit-blocking hook honors the marker
    Given the adopter fixture carrying a commit-blocking hook and a sandbox-shaped checkout with the resolved marker set to true
    When a Red-Green-Replay commit is attempted
    Then the commit-blocking hook does not refuse it on primary-checkout grounds
    And the Red-Green-Replay gates still run

  Scenario: An adopter fixture whose hook ignores the marker fails
    Given the adopter fixture mutated so its commit-blocking hook ignores the resolved marker
    When the parametrized dispatch-path seam test runs against that fixture
    Then the sandbox-exemption obligation fails on the adopter leg
````

## tests/heading-coverage.json — co-edit (full owned entries)

Append two entries, each with the complete schema and an owning `work_item`, matching the Scenario 104–106 pattern:

```json
{
  "heading": "## Scenario 107 — An adopter's declared merge strategy projects to both the argv and the prompt",
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "test": "TODO",
  "reason": "Bound by plan typed-repo-integration-contract (epic bd-ib-vblnq2). merge_mode lands with C1 (schema field), C2 (argv projection), C3 (Defective/refusal), and C5-payload (pr.md prompt projection).",
  "work_item": "bd-ib-vblnq2"
}
```
```json
{
  "heading": "## Scenario 108 — A governed repository's commit-blocking hook honors the resolved sandbox-exemption marker",
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "test": "TODO",
  "reason": "Bound by plan typed-repo-integration-contract (epic bd-ib-vblnq2). sandbox_exempt_marker lands with C1 (schema field), C2 (resolve-once), C5-payload (prepare-step projection), and C6 (adopter-fixture commit-blocking hook honor plus non-honoring negative variant).",
  "work_item": "bd-ib-vblnq2"
}
```

No existing heading is removed or renamed.

### Implementation

No new implementation followup is created; both fields ride the approved cut of
plan `typed-repo-integration-contract` (epic `bd-ib-vblnq2`, scope-event comment):
C1 (`bd-ib-oahwsi`, FILED, held from dispatch pending this ratification) defines both
fields on the schema; C2 (to be filed per the scope event) resolves once and
projects the merge method to the auto-merge argv and the marker to the prepare step;
C3 (to be filed) enumerates a `Defective` merge-method value in its pre-dispatch
refusal; C5-payload (to be filed, ATTENDED) projects the merge method to `pr.md:84`
and the marker-set to the prepare step; C6 (to be filed) gives the adopter fixture a
commit-blocking hook that honors the marker plus a non-honoring negative variant —
an extension of C6's recorded zero-tooling fixture scope, recorded on the epic. Each
item's filed acceptance criteria carry these fields. This closes the marker half of
the superseded `declared-sandbox-toolchain` followup (`bd-ib-2kpo7r`, already closed
under plan `bd-ib-6pshji`, deferral D4). C1's dispatch-hold releases only when this
proposal ratifies.
