---
topic: acp-node-adapter-configuration
author: homelab-loop-hardening-orchestrator
created_at: 2026-08-26T05:02:05Z
---

## Proposal: Per-node ACP adapter configuration at three layers, provider-agnostic

### Target specification files

- SPECIFICATION/contracts.md

### Summary

A new contracts section makes every ACP node's adapter a configuration value of the shape (command, env map, args), resolved most-specific-wins through the workflow's defaults, the dispatch target's dispatcher.acp_nodes table, and a journaled per-dispatch argument; dispatcher.codex_models remains the per-repository shorthand for the Codex tiers; the supplying layer is journaled per node and per field; keys are committed-configuration-only; every layer has a negative control and the arbitrary-adapter proof is hermetic.

### Motivation

Maintainer commission of 2026-08-26, verbatim: 'We need to make the model for each node not hard-coded. If any are hardcoded to a specific model, that's a design flaw in the Dispatcher. It should be an easy config change with no code changes to switch out any implementer node for any model. Even open source models.' Refined: 'the models should be completely configurable to replace the defaults, at all the levels possible - fabro config, livespec config (per repo) and per-dispatch overridable', and 'I just want it to generically support any kind of models, using [local-llm] as an example.' The maintainer explicitly withdrew network-reachability, credential-projection, context-cap and capacity obligations from this scope. Implementing item bd-ib-tsna; supersedes bd-ib-un226z.

### Proposed Changes

Add a new H2 section to `contracts.md`, placed immediately AFTER §"Codex ACP node model pins":

## ACP node adapter configuration

Every ACP node of the `implement-work-item` workflow — `implement`, `fix`, `review_fix`, `pr`, `review`, `disposition` — runs an adapter the Dispatcher RESOLVES FROM CONFIGURATION, never from a code-level provider choice. Switching any node to any model behind any provider protocol, open-weight and local models included, MUST be a configuration change with no code change.

**The per-node value.** A node's adapter configuration is a table with three fields: `command` (string; the ACP adapter command, e.g. `npx -y @agentclientprotocol/claude-agent-acp` or `npx --no-install @zed-industries/codex-acp`), `env` (table of string to string; environment assignments prefixed onto the command as leading `KEY=value` pairs, the mechanism Fabro already parses), and `args` (array of strings; appended to the command verbatim, e.g. `-c model=gpt-5.5`). Model and reasoning effort are NOT fields of their own: they ride in `env` for adapters that read them from the environment (`ANTHROPIC_MODEL`, `CLAUDE_CODE_EFFORT_LEVEL`) and in `args` for adapters that read them from the command line (`-c model=…`, `-c model_reasoning_effort=…`). A provider behind an Anthropic-Messages or OpenAI-compatible endpoint is expressed the same way — `env` carries `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_MODEL` on the Claude adapter, `args` carries `-c model_provider=<name>` and its provider definition on the Codex adapter — so the shape is provider-agnostic by construction. The rendered adapter string MUST be exactly: the `env` pairs in sorted key order, then `command`, then `args` in order, single-space separated.

**Three resolution layers, most specific wins.** Each node's value MUST resolve through, in ascending precedence: (1) the WORKFLOW DEFAULTS — the declared inputs and their defaults in the workflow's own `workflow.toml` (`acp_adapter`, `pr_adapter`, `review_adapter`, `disposition_adapter` today), so a vendored workflow carries its own defaults and the built-in fleet defaults of §"Codex ACP node model pins" are expressed there; (2) the PER-REPOSITORY LAYER — the `dispatcher.acp_nodes` table in the dispatch TARGET's `.livespec.jsonc`, keyed by node name, read from the target repository exactly as the tiers are; (3) the PER-DISPATCH LAYER — an explicit `--acp-node <node>=<value>` argument on `dispatcher.py dispatch`, `dispatcher.py loop` and the `drive` operation's `impl:<id>` action. Resolution is per node and per FIELD: a more specific layer that sets `command` or `args` REPLACES that field; `env` MERGES with the more specific layer's keys winning. A layer that names a node not present in the workflow MUST refuse the dispatch before any run exists, naming the node.

**`dispatcher.codex_models` is the per-repository shorthand for the Codex tiers and remains valid.** At the per-repository layer it expands into the `implement`/`fix`/`review_fix` and `pr` entries exactly as §"Codex ACP node model pins" specifies, and an explicit `dispatcher.acp_nodes` entry for the same node wins over the expansion. That section's rendering rules for a Codex-pinned tier are unchanged by this one.

**The per-dispatch layer is a recorded argument, never an environment variable.** The no-environment-override rule of §"Codex ACP node model pins" holds for every layer: an ad-hoc shell MUST NOT be able to re-tier the factory with nothing in the committed record or the journal. The per-dispatch value MUST be journaled on the dispatch record. This argument is an OPERATOR argument: the console's factory-drain launcher of §"Control surface and audit" passes NO per-run argument, and this section does not change that.

**The supplying layer is visible in the run record.** For every node the Dispatcher MUST journal, on the dispatch record, the rendered adapter string AND which layer supplied each of `command`, `env` (per key) and `args`, so a reader can tell a workflow default from a repository override from a per-dispatch override without re-deriving it.

**Keys are committed-configuration-only.** `dispatcher.acp_nodes` joins `dispatcher.codex_models` in the committed-configuration-only class of §"Control surface and audit"; it is outside the API-configurable key set and does not trigger the console Settings lockstep.

**Verification.** A negative control per layer MUST exist: for each of the three layers, a test that sets a value at that layer and a conflicting value at every less specific layer, and asserts the more specific value renders. Proving that an arbitrary adapter with an `env` map and a provider definition renders and takes precedence MUST be done hermetically — a stub endpoint or the fake backend — and MUST NOT require network reachability of any real provider from the factory.

Ownership note at the end of the section: "Implemented by ledger item `bd-ib-tsna`; `bd-ib-un226z` (per-node provider assignment) is superseded by this section."

`tests/heading-coverage.json` co-edit (revise `resulting_files[]` for the spec files; the coverage map rides the same change as a plain co-edit): add an entry for `## ACP node adapter configuration` with `test` `"TODO"`, `work_item` `bd-ib-tsna`.

## Proposal: Scenarios 87 and 88 for layered adapter resolution and arbitrary adapters

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

Scenario 87 covers repository-over-workflow, per-dispatch-over-repository with journaling, the no-environment rule and the unknown-node refusal; Scenario 88 covers an env-map Claude adapter against an Anthropic-compatible endpoint, a Codex adapter with a provider definition, and the hermetic proof.

### Motivation

Maintainer commission of 2026-08-26, verbatim: 'We need to make the model for each node not hard-coded. If any are hardcoded to a specific model, that's a design flaw in the Dispatcher. It should be an easy config change with no code changes to switch out any implementer node for any model. Even open source models.' Refined: 'the models should be completely configurable to replace the defaults, at all the levels possible - fabro config, livespec config (per repo) and per-dispatch overridable', and 'I just want it to generically support any kind of models, using [local-llm] as an example.' The maintainer explicitly withdrew network-reachability, credential-projection, context-cap and capacity obligations from this scope. Implementing item bd-ib-tsna; supersedes bd-ib-un226z.

### Proposed Changes

Append two scenarios after Scenario 86.

```gherkin
## Scenario 87 — A node's adapter resolves through three layers and the record names the supplying layer

Feature: Per-node adapter configuration resolves most-specific-wins
  As a maintainer who wants to switch any node to any model with a config change
  I want workflow defaults, per-repository configuration and a per-dispatch argument to layer predictably
  So that the factory's model choice is always a recorded configuration decision

Scenario: A repository entry overrides the workflow default for one node only
  Given a workflow whose acp_adapter default names the Claude adapter
  And a dispatch target whose "dispatcher.acp_nodes" table sets the implement node's command to a different adapter
  When the Dispatcher renders the workflow adapter inputs
  Then the implement node's rendered adapter carries the repository command
  And every other node's rendered adapter carries its workflow default
  And the dispatch record names the repository layer for the implement node's command

Scenario: A per-dispatch argument overrides the repository entry and is journaled
  Given a dispatch target whose "dispatcher.acp_nodes" table sets the implement node's env ANTHROPIC_MODEL
  And a dispatch invoked with an "--acp-node implement=…" argument setting a different ANTHROPIC_MODEL
  When the Dispatcher renders the workflow adapter inputs
  Then the implement node's rendered adapter carries the per-dispatch ANTHROPIC_MODEL
  And the repository's other env keys for that node are preserved
  And the dispatch record carries the per-dispatch argument and names the per-dispatch layer for that key

Scenario: A per-dispatch value cannot arrive through the environment
  Given an environment variable that names a model for a node
  And no per-dispatch argument
  When the Dispatcher renders the workflow adapter inputs
  Then the rendered adapter is unaffected by the environment variable

Scenario: A layer naming an unknown node refuses the dispatch
  Given a dispatch target whose "dispatcher.acp_nodes" table names a node the workflow does not declare
  When the Dispatcher prepares the dispatch
  Then it refuses before any run exists naming the unknown node
```

```gherkin
## Scenario 88 — An arbitrary adapter with an env map and args renders without a code change

Feature: Any model behind any provider protocol is a configuration value
  As a maintainer who runs open-weight models behind a local router
  I want a node's adapter expressed as a command, an env map and args
  So that a local or open-source model needs no orchestrator code change

Scenario: A Claude-adapter node pointed at an Anthropic-compatible endpoint renders its env map
  Given a dispatch target whose "dispatcher.acp_nodes" table sets the implement node's env with ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN and ANTHROPIC_MODEL naming a router-qualified model
  When the Dispatcher renders the implement node's adapter
  Then the rendered adapter is the env pairs in sorted key order, then the Claude adapter command
  And no orchestrator code names the endpoint or the model

Scenario: A Codex-adapter node with a provider definition renders its args
  Given a dispatch target whose "dispatcher.acp_nodes" table sets the pr node's args to a model_provider definition and a model
  When the Dispatcher renders the pr node's adapter
  Then the rendered adapter is the Codex adapter command followed by those args in order

Scenario: The rendering is proven hermetically
  Given a test that renders an adapter against a stub endpoint or the fake backend
  When the test runs
  Then it passes without reaching any real provider over the network
```

`tests/heading-coverage.json` co-edit: entries for `## Scenario 87 — …` and `## Scenario 88 — …` with `test` `"TODO"`, `work_item` `bd-ib-tsna`.
