---
topic: implementer-default-claude-opus-5
author: homelab-loop-hardening-orchestrator
created_at: 2026-08-26T04:18:41Z
---

## Proposal: The implementer class defaults to the Claude ACP adapter pinned to Claude Opus 5

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The implementer node class (implement, fix, review_fix) stops defaulting to the Codex adapter pinned to gpt-5.5/low and instead defaults to the Claude ACP adapter pinned to claude-opus-5 at high effort, rendered exactly as the review adapter already pins its model. An explicit dispatcher.codex_models implementer entry still routes the class to Codex under the unchanged pin rules, the publish class keeps its Codex pin, and the first post-change dispatch is a transcript-verified run. This is the minimal default switch; per-node configurability at every layer is a separate amendment.

### Motivation

Maintainer commission of 2026-08-26, verbatim: 'set the implementer default to opus 5 fleet wide ... ASAP to unblock things' and 'switch to opus as default ASAP before tackling the configuration. Two separate work items.' The ratified section binds the implementer default to the literal Codex string, so the switch is a spec change before it is a code change. Moving the implementer off Codex also removes the remote-compaction 404 failure class (bd-ib-ihp5) from the implement stage. Implementing item: bd-ib-rcl7; configurability follow-up: bd-ib-tsna.

### Proposed Changes

Amend `contracts.md` §"Codex ACP node model pins" so that the implementer class defaults to the Claude ACP adapter running Claude Opus 5, while every explicitly Codex-pinned tier and the publish class keep the ratified Codex pin contract unchanged. Concretely:

1. **Section heading and opening.** The heading stays `## Codex ACP node model pins`; the opening paragraph gains one sentence: "The implementer class is Codex-backed ONLY when the dispatch target pins it; absent that pin it runs the Claude ACP adapter described under 'The implementer default is the Claude adapter' below."

2. **New paragraph after "The pin is per node CLASS, not per node."** Insert:

   **The implementer default is the Claude adapter.** When the dispatch target's `dispatcher.codex_models` block carries NO `implementer` entry — the block is absent, the `implementer` key is absent, or the entry is not a table — the Dispatcher MUST render the `acp_adapter` input as the Claude ACP adapter pinned to Claude Opus 5 at high effort. The rendered form, literally, is:

       ANTHROPIC_MODEL=claude-opus-5 CLAUDE_CODE_EFFORT_LEVEL=high npx -y @agentclientprotocol/claude-agent-acp

   The model and effort MUST ride the adapter's own environment as leading `KEY=value` assignments, exactly as the `review_adapter` input already pins its model, because Fabro rejects `model` and `reasoning_effort` as ACP node attributes. The Dispatcher MUST NOT apply a context-window suffix such as `[1m]` to the default Opus 5 model name; whether Opus 5 accepts one is established from a run transcript, never assumed in a default. A `dispatcher.codex_models.implementer` entry that IS a table — whether it names a model or carries the empty-string opt-out — MUST route the implementer class to the Codex adapter under the existing rules of this section, so a repository stays on Codex by writing the entry and moves to the default by removing it. The `pr` class is unaffected: it MUST continue to render the Codex publish adapter exactly as specified below.

   The Dispatcher SHOULD treat the first dispatch after a change to the default implementer adapter as a verification run: the run transcript's resolved model MUST be checked against the pinned model and the result recorded on the work-item that changed the default, because earlier `claude-agent-acp` versions ignored `ANTHROPIC_MODEL` and silently ran a smaller model.

3. **"Tiers resolve from the dispatch target's own configuration."** Replace "MUST carry a built-in fleet default so that a repository which has not opted in still inherits the pin" with "MUST carry a built-in fleet default so that a repository which has not opted in still inherits a pinned adapter — the Claude default for the implementer class, the Codex publish pin for the `pr` class". The per-key degradation sentence is scoped: "Within a tier entry that IS a table, resolution MUST degrade per key: an absent `model` or `reasoning_effort` key MUST fall back to that tier's built-in Codex default for exactly what is missing. An absent or non-table `implementer` entry resolves to the Claude default adapter as a whole, not to the Codex defaults."

4. **"The built-in fleet defaults" table.** Replace the implementer row with:

   | implementer (`implement`, `fix`, `review_fix`) | Claude adapter, `claude-opus-5` | `high` (via `CLAUDE_CODE_EFFORT_LEVEL`) |

   keep the publish row (`gpt-5.4-mini`, `high`), and replace "So the implementer adapter a default dispatch renders is, in full:" plus its Codex string with: "So a default dispatch renders the implementer adapter as the Claude string given above, and renders the publish adapter as: `npx --no-install @zed-industries/codex-acp -c sandbox_mode=danger-full-access -c approval_policy=never -c model=gpt-5.4-mini -c model_reasoning_effort=high`. A repository that pins its implementer to Codex with the former default renders the implementer adapter as: `npx --no-install @zed-industries/codex-acp -c sandbox_mode=danger-full-access -c approval_policy=never -c model=gpt-5.5 -c model_reasoning_effort=low`." The rationale sentence about the implementer holding the stronger model is rewritten: "The implementer class carries design judgement and runs the strongest available model by default; the `pr` node runs a scripted recipe and takes the cheap Codex model outright."

5. **"There is no environment override"** and **"Reachable tiers are bounded by the baked adapter"** are unchanged; the latter applies to Codex-pinned tiers. Add one sentence to the reachable-tiers paragraph: "The Claude default adapter is fetched by `npx -y` rather than baked into the sandbox image, exactly as the review adapter is, and authenticates with the `CLAUDE_CODE_OAUTH_TOKEN` the Dispatcher already projects for the review node."

6. **Ownership note.** Add at the end of the section: "Making every node's adapter, model and effort configurable at the workflow, per-repository and per-dispatch layers — including arbitrary adapter commands for open-weight and local models — is a separate amendment tracked by ledger item `bd-ib-tsna`; this section changes only the implementer default."

`tests/heading-coverage.json` co-edit: no `## ` heading in `contracts.md` changes; the existing "## Codex ACP node model pins" entry's bound test remains valid for the Codex-pinned rendering and the revise pass MUST keep it.

## Proposal: Scenario 64 amended and Scenario 86 added for the Claude implementer default

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

Scenario 64's no-configuration scenario now states that the implementer adapter is the Claude adapter while the publish adapter keeps its Codex pin; the other three Scenario 64 scenarios stand. A new Scenario 86 states the default Claude rendering, the explicit-Codex-pin negative control, and the unaffected publish class, with its heading-coverage entry bound to bd-ib-rcl7 until the implementing tests land.

### Motivation

Behaviour-introducing proposals MUST carry a Gherkin scenario; the default implementer adapter is load-bearing dispatch behaviour that the implementing item's tests must exercise, and Scenario 64 as written asserts the opposite default.

### Proposed Changes

Amend `scenarios.md` Scenario 64 and add Scenario 86.

**Scenario 64 — first scenario.** Replace "A repository with no configuration inherits the fleet default pins" with:

```gherkin
Scenario: A repository with no configuration inherits the fleet default adapters
  Given a dispatch target whose configuration carries no "dispatcher.codex_models" block
  When the Dispatcher renders the workflow adapter inputs
  Then the implementer adapter is the Claude ACP adapter carrying the built-in fleet default model and effort as leading environment assignments
  And the publish adapter carries its own built-in fleet default Codex model and reasoning effort
  And the publish adapter is the base Codex adapter command followed by its model and reasoning-effort overrides
```

The remaining three scenarios of Scenario 64 stand as written: a repository override that names the implementer model renders the Codex implementer adapter with that model and the built-in default effort; an empty model renders the Codex base byte-identically; a malformed tier entry falls back to that class's built-in default without refusing the dispatch — which for the implementer class is the Claude default adapter.

**New Scenario 86**, appended after Scenario 85:

```gherkin
## Scenario 86 — The implementer defaults to Claude Opus 5 and an explicit Codex pin still routes to Codex

Feature: The implementer runs Claude Opus 5 unless a repository pins it to Codex
  As a maintainer who wants the strongest implementer by default and a config-only way to stay on Codex
  I want the default implementer adapter to be the Claude adapter pinned to Opus 5
  So that switching the implementer model is a configuration change, never a code change

Scenario: A default dispatch renders the Claude implementer adapter
  Given a dispatch target whose configuration carries no "dispatcher.codex_models" implementer entry
  When the Dispatcher renders the acp_adapter input
  Then the rendered adapter is the Claude ACP adapter command
  And it carries ANTHROPIC_MODEL set to claude-opus-5 and CLAUDE_CODE_EFFORT_LEVEL set to high as leading environment assignments
  And it carries no context-window suffix on the model name

Scenario: An explicit implementer pin routes the implementer class to Codex
  Given a dispatch target whose "dispatcher.codex_models" block carries an implementer entry naming a model
  When the Dispatcher renders the acp_adapter input
  Then the rendered adapter is the Codex adapter carrying that model and its reasoning effort
  And the publish adapter is unchanged by the implementer entry

Scenario: The publish class is unaffected by the implementer default
  Given a dispatch target with no "dispatcher.codex_models" block
  When the Dispatcher renders the pr_adapter input
  Then the rendered adapter is the pinned Codex publish adapter
```

`tests/heading-coverage.json` co-edit (revise `resulting_files[]`): add an entry for `## Scenario 86 — The implementer defaults to Claude Opus 5 and an explicit Codex pin still routes to Codex` with `test` `"TODO"`, `work_item` `bd-ib-rcl7`, and a reason naming the implementing item's default-string and negative-control tests as the binding; the Scenario 64 entry keeps its existing bound integration test, which MUST be updated by `bd-ib-rcl7` to assert the Claude default for the first scenario.
