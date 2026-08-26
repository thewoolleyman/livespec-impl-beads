---
topic: acp-node-timeouts
author: homelab-loop-hardening-orchestrator
created_at: 2026-08-26T05:02:06Z
---

## Proposal: Per-node timeouts as configuration with a 30-minute default, rendered as literal durations

### Target specification files

- SPECIFICATION/contracts.md

### Summary

A new contracts section makes every node timeout and the stall watchdog configuration (dispatcher.node_timeouts, dispatcher.stall_timeout_seconds) with 1800-second and 7200-second defaults, resolved through the same three layers as adapter configuration, written into the self-contained dispatch payload as literal durations because the pinned Fabro build cannot template a timeout, with the subprocess ceiling derived from the resolved graph and the reduction from the former literals recorded as deliberate.

### Motivation

Maintainer commission of 2026-08-26, verbatim: 'explain why there's a 20 minute limit. That should be configurable per-node too, and have a default of 30 minutes.' There is no 20-minute timeout; the sub-20-minute rule was the wall-clock proxy for a Codex turn reaching the dead remote-compaction endpoint (bd-ib-ihp5), removed for the implementer by v080. Fabro 0.254 research (rider on bd-ib-cnkf): a templated timeout attribute silently becomes no timeout, which fixes the rendering rule. Implementing item bd-ib-cnkf.

### Proposed Changes

Add a new H2 section to `contracts.md`, placed immediately AFTER §"ACP node adapter configuration" (or after §"Codex ACP node model pins" if that section is not yet present):

## ACP node timeouts

Every node timeout of the `implement-work-item` workflow, and the run's stall watchdog, MUST resolve from configuration rather than from literals hard-coded in the workflow graph.

**Keys.** `dispatcher.node_timeouts` is a table keyed by node name (`implement`, `fix`, `review_fix`, `pr`, `review`, `disposition`, `janitor`) whose values are positive integers of seconds; `dispatcher.stall_timeout_seconds` is a positive integer of seconds for the run-level stall watchdog. A node with no configured value MUST resolve to **1800** seconds; the stall watchdog with no configured value MUST resolve to **7200** seconds. A non-positive or non-integer value MUST be rejected before any run exists, naming the key. Both keys are committed-configuration-only, alongside `dispatcher.codex_models` and `dispatcher.acp_nodes`, and do not trigger the console Settings lockstep.

**Resolution layers.** The same three layers and precedence as §"ACP node adapter configuration" apply: the workflow's own declared defaults, the dispatch target's `.livespec.jsonc`, then a per-dispatch `--node-timeout <node>=<seconds>` argument that MUST be journaled on the dispatch record; the record MUST name the supplying layer per node.

**Rendering, literally.** The pinned Fabro build types a quoted duration attribute at parse time and its template expansion never re-types a rendered string, so a templated `timeout` attribute silently becomes NO timeout. The Dispatcher therefore MUST NOT template a timeout attribute from a workflow input. It MUST write each resolved value into the self-contained dispatch payload's workflow graph as a literal duration (`timeout="1800s"`, `stall_timeout="7200s"`) before invoking `fabro run`, and a test MUST assert that no timeout attribute in the rendered graph contains a template opener.

**The subprocess ceiling follows the graph.** The Dispatcher's `fabro run` subprocess ceiling MUST be derived from the resolved node timeouts and the resolved stall timeout — the graph's worst-case path plus a fixed margin — rather than from a hard-coded constant, so that lengthening a node cannot outrun the poller and shortening one is not masked.

**The 30-minute default is a deliberate reduction.** It lowers `implement` from the previously shipped 14400 seconds and `janitor`/`fix` from 3600 seconds, against recorded legitimate turns near 120 minutes. A repository that needs longer turns sets them; the default is the maintainer's ruling and the reduction is recorded in the implementing item's triage record.

**Codex compaction limit.** A Codex-backed node's `model_auto_compact_token_limit` is an adapter argument and rides the node's `args` under §"ACP node adapter configuration"; this section adds no separate key for it.

Ownership note at the end of the section: "Implemented by ledger item `bd-ib-cnkf`."

`tests/heading-coverage.json` co-edit: add an entry for `## ACP node timeouts` with `test` `"TODO"`, `work_item` `bd-ib-cnkf`.

## Proposal: Scenario 89 for configured node timeouts

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

Scenario 89 covers the all-default rendering, a single configured node, the derived subprocess ceiling, and the invalid-value refusal.

### Motivation

Maintainer commission of 2026-08-26, verbatim: 'explain why there's a 20 minute limit. That should be configurable per-node too, and have a default of 30 minutes.' There is no 20-minute timeout; the sub-20-minute rule was the wall-clock proxy for a Codex turn reaching the dead remote-compaction endpoint (bd-ib-ihp5), removed for the implementer by v080. Fabro 0.254 research (rider on bd-ib-cnkf): a templated timeout attribute silently becomes no timeout, which fixes the rendering rule. Implementing item bd-ib-cnkf.

### Proposed Changes

Append one scenario after Scenario 88 (or after the last existing scenario).

```gherkin
## Scenario 89 — Node timeouts resolve from configuration and land as literal durations

Feature: Per-node timeouts are configuration, rendered literally
  As a maintainer whose implementer no longer dies on compaction
  I want each node's timeout to be a configured value with a 30-minute default
  So that the node timeout is the only ceiling and it is always a decision

Scenario: A default target renders every node at 1800 seconds
  Given a dispatch target with no "dispatcher.node_timeouts" table
  When the Dispatcher renders the dispatch payload's workflow graph
  Then every node's timeout attribute is the literal duration 1800s
  And the run's stall_timeout attribute is the literal duration 7200s
  And no timeout attribute contains a template opener

Scenario: A configured node keeps its value and the others keep the default
  Given a dispatch target whose "dispatcher.node_timeouts" sets implement to 7200
  When the Dispatcher renders the dispatch payload's workflow graph
  Then the implement node's timeout attribute is the literal duration 7200s
  And every other node's timeout attribute is the literal duration 1800s
  And the dispatch record names the repository layer for the implement timeout

Scenario: The subprocess ceiling follows the resolved graph
  Given a dispatch target whose resolved node timeouts sum to a longer worst-case path than the default
  When the Dispatcher computes its fabro run subprocess ceiling
  Then the ceiling exceeds that worst-case path by the fixed margin

Scenario: An invalid timeout refuses the dispatch
  Given a dispatch target whose "dispatcher.node_timeouts" sets a node to zero or to a non-integer
  When the Dispatcher prepares the dispatch
  Then it refuses before any run exists naming the key
```

`tests/heading-coverage.json` co-edit: entry for `## Scenario 89 — …` with `test` `"TODO"`, `work_item` `bd-ib-cnkf`.
