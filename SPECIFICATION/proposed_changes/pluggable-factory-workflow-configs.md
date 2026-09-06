---
topic: pluggable-factory-workflow-configs
author: claude-fable-5-1 (pluggable-factory-workflow-configs)
created_at: 2026-09-06T07:15:19Z
---

## Proposal: Ratify the shipped workflow resolution precedence and add a named workflow-variant registry

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Section "Self-contained plugin dispatch" of contracts.md still says an adopter's target-local workflow is "supplied today via the dispatcher's explicit --workflow override" and that any automatic target-local resolution "amends THIS section before it ships", while the Dispatcher has resolved the dispatch target's own committed .fabro/workflows/implement-work-item ahead of the bundle since 2026-07-20 (commit c8bde4a5). This proposal ratifies that three-step precedence as it runs, and extends it with a named workflow-variant registry: dispatcher.workflows maps a variant name to a target-relative directory holding a COMPLETE workflow (workflow.toml, workflow.fabro, prompts), dispatcher.default_workflow names the default, the name implement-work-item is reserved and undefinable, the selector resolves through a recorded --workflow-name argument, then the item's pinned dispatch_workflow metadata, then default_workflow, then the reserved name, with no environment layer, three pre-run refusals, a ledger pin and a journal field, and seam parity for every registered variant under the v092 integration checks. One scenario (116) states the behavior; tests/heading-coverage.json gains its entry.

### Motivation

Plan pluggable-factory-workflow-configs (epic bd-ib-yqpdrt) was parked on 2026-08-30 until typed-repo-integration-contract C5 landed, with the rider that a variant registry must satisfy R4 seam equivalence for every registered variant. C5 and its whole plan are closed. The 2026-09-06 reactivation survey (plan/pluggable-factory-workflow-configs/research/002-reactivation-survey-2026-09-06.md) found: (1) impl-to-spec drift, since the target-local precedence shipped without the amendment this section reserved; (2) three fleet repos carry a target-local implement-work-item fork today, one differing from the bundle by a single sandbox-image line that dispatcher.fabro_sandbox_image already overrides, two carrying the retired abandon/escalate nodes, and none seam-checked; (3) the v092 typed inputs removed every toolchain reason to fork, so what remains for a NAMED variant is a deliberately different graph, and that needs a first-class, seam-checked home rather than an unchecked copy; (4) the ACP node adapter contract already ratifies that a per-dispatch selector is a recorded argument and never an environment variable, which is the precedent this registry follows instead of the older LIVESPEC_FABRO_FACTORY one. Implementation children bd-ib-27puvv (registry and resolution), bd-ib-u7arwz (ledger pin and recorded argument) and bd-ib-asrazi (seam parity) are filed at backlog under the plan epic and are not to be admitted before this revision is on master.

### Proposed Changes

In `SPECIFICATION/contracts.md`, section "Self-contained plugin dispatch":

1. In the first paragraph, keep the sentence "The explicit `--workflow <path>` override remains the escape hatch." unchanged.

2. Replace the paragraph that begins "**Target-local workflow.** An adopter MAY carry its own `implement-work-item` workflow in the TARGET repo" through its final sentence "(Implementation tracked as `bd-ib-z2ctra`.)" with the following two paragraphs.

```diff
-**Target-local workflow.** An adopter MAY carry its own
-`implement-work-item` workflow in the TARGET repo
-(`<target>/.fabro/workflows/implement-work-item/`), supplied today via
-the dispatcher's explicit `--workflow` override. Prepare steps are
-TARGET-TOOLCHAIN facts, not fleet constants: the plugin-default
-payload's prepare chain (uv / lefthook / `livespec_dev_tooling`) is
-the FLEET toolchain realization, and a non-Python adopter's equivalent
-steps are that adopter's own facts. Any future automatic target-local
-resolution (the target's `.fabro/workflows/...` taking precedence over
-the plugin payload) amends THIS section's plugin-root resolution rule
-before it ships. (Implementation tracked as `bd-ib-z2ctra`.)
+**Workflow resolution precedence.** The Dispatcher MUST resolve the
+committed workflow a dispatch runs in this order, most specific first:
+(1) an explicit `--workflow <path>` argument, the raw-path escape hatch;
+(2) the named variant selected per "Named workflow variants" below,
+when that selection is not the reserved name; (3) for the reserved name
+`implement-work-item`, the dispatch TARGET's own committed
+`<target>/.fabro/workflows/implement-work-item/` when it exists, else
+the plugin payload's bundled workflow resolved via the plugin root.
+Step (3) is the automatic target-local resolution this section
+previously reserved for a future amendment; it has been the
+Dispatcher's behavior since 2026-07-20 and is ratified here as it runs.
+Prepare steps remain TARGET-TOOLCHAIN facts expressed through the typed
+integration inputs of §"Repository integration contract", not a reason
+to carry a workflow copy. The resolved committed path MUST be journaled
+on the dispatch-id record as `workflow_toml`.
+
+**Named workflow variants.** A dispatch target MAY declare
+`dispatcher.workflows`, a table mapping a variant name to a directory
+path relative to the target repository root, and
+`dispatcher.default_workflow`, a variant name. Each registered directory
+MUST hold a COMPLETE workflow — `workflow.toml`, `workflow.fabro` and
+its prompt files — and the Dispatcher MUST NOT merge a variant with the
+bundle or with another variant; a variant is a whole directory, never a
+partial overlay. The name `implement-work-item` is reserved: it is
+always defined, it resolves by step (3) above, and a registry entry
+MUST NOT redefine it. The variant a dispatch uses MUST resolve, most
+specific first: (a) an explicit `--workflow-name <name>` argument on
+`dispatcher.py dispatch`, `dispatcher.py loop` and the `drive`
+operation's `impl:<id>` action; (b) the name a prior dispatch of the
+same work-item recorded in its `dispatch_workflow` metadata, so a retry
+re-runs the variant the first attempt ran, provided that name is still
+registered or reserved; (c) `dispatcher.default_workflow` when it names
+a registered entry; (d) `implement-work-item`. The selector MUST NOT be
+read from an environment variable: the per-dispatch value is a recorded
+argument, for the reason §"ACP node adapter configuration" gives — an
+ad-hoc shell MUST NOT be able to change which graph the factory runs
+with nothing in the committed record or the journal to show for it.
+Every dispatch MUST write the resolved name to the work-item's
+`dispatch_workflow` metadata, a top-level metadata key beside
+`dispatch_factory`, and MUST journal it as `workflow_name` on the
+dispatch-id record beside `workflow_toml`. The Dispatcher MUST refuse
+the dispatch before any Fabro run exists, with a journal stage naming
+the cause, when: the selected name matches no registry entry and is not
+the reserved name; the selected registry directory lacks
+`workflow.toml` or `workflow.fabro`; or a registry entry is named
+`implement-work-item`. The `check-seam-equivalence` and
+`check-no-fleet-toolchain-literals` gates of §"Repository integration
+contract" MUST read the bundle AND every directory this repository
+registers under its own `dispatcher.workflows`, applying their
+discovery control per directory, so a registered variant is held to
+the same integration-input parity as the bundle and a variant whose
+scan reaches nothing fails loudly rather than reporting clean.
+(Implementation: plan epic `bd-ib-yqpdrt`, children `bd-ib-27puvv`,
+`bd-ib-u7arwz` and `bd-ib-asrazi`.)
```

In `SPECIFICATION/scenarios.md`, append after Scenario 115:

```gherkin
## Scenario 116 — Named workflow variants resolve by recorded precedence and refuse before any run

Feature: A dispatch target selects a complete named workflow variant
  As a maintainer whose repository needs a deliberately different Fabro graph
  I want to register the variant by name and select it through recorded configuration
  So that a variant is never an unchecked copy and a retry never silently changes graph

  Scenario: An explicit workflow name wins
    Given a dispatch target whose dispatcher.workflows registers a variant named fast
    And dispatcher.default_workflow names implement-work-item
    When a dispatch is made with --workflow-name fast
    Then the committed workflow resolved is the fast variant's directory
    And the work-item's dispatch_workflow metadata records fast
    And the dispatch-id record carries workflow_name fast beside workflow_toml

  Scenario: A retry reuses the recorded variant
    Given a work-item whose dispatch_workflow metadata records fast
    And fast is still registered
    When the work-item is dispatched again with no --workflow-name
    Then the committed workflow resolved is the fast variant's directory

  Scenario: The configured default applies when nothing more specific chooses
    Given a dispatch target whose dispatcher.default_workflow names a registered variant
    And a work-item with no dispatch_workflow metadata
    When the work-item is dispatched with no --workflow-name
    Then the committed workflow resolved is that variant's directory

  Scenario: The reserved name resolves target-local then bundle
    Given a dispatch target with no dispatcher.workflows table
    When a work-item is dispatched
    Then the committed workflow resolved is the target's own committed implement-work-item workflow when it exists
    And otherwise the plugin payload's bundled workflow

  Scenario: An unregistered name is refused before any run
    Given a dispatch target whose dispatcher.workflows does not register a variant named missing
    When a dispatch is made with --workflow-name missing
    Then the dispatch is refused before any Fabro run exists
    And the journal stage names the unregistered variant

  Scenario: An incomplete variant directory is refused before any run
    Given a registered variant whose directory lacks workflow.fabro
    When a dispatch selects that variant
    Then the dispatch is refused before any Fabro run exists
    And the journal stage names the missing file

  Scenario: No environment variable selects the variant
    Given an environment variable naming a registered variant
    When a work-item is dispatched with no --workflow-name
    Then the committed workflow resolved ignores the environment variable

  Scenario: A registered variant is held to the bundle's seam parity
    Given this repository registers a variant whose graph carries an integration token in a position the engine does not render
    When check-seam-equivalence runs
    Then it reports a finding naming that variant's directory
    And the bundle still passes
```

Co-edit (resulting_files): `tests/heading-coverage.json` MUST gain one entry for the new heading `## Scenario 116 — Named workflow variants resolve by recorded precedence and refuse before any run` with `spec_root` "SPECIFICATION", `spec_file` "scenarios.md", `test` "TODO", `work_item` "bd-ib-yqpdrt", and a `reason` stating that the exercising integration-tier test is owed by the plan's coverage item once bd-ib-27puvv, bd-ib-u7arwz and bd-ib-asrazi land. No H2 heading of contracts.md is added, changed or removed by this proposal, so the existing "## Self-contained plugin dispatch" entry stands.
