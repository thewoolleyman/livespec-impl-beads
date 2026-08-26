---
topic: codex-acp-adapter-succession
author: homelab-loop-hardening-orchestrator
created_at: 2026-08-26T08:36:21Z
spec_commitments:
  impl_followups:
    - id_hint: codex-acp-adapter-succession-impl
      description: |
        Implement the baked-path Codex adapter and the CODEX_CONFIG / INITIAL_AGENT_MODE env channel in commands/_dispatcher_fabro_argv.py, update the CODEX_ADAPTER_BASE rationale comment, repoint orchestrator-image/acceptance-live-golden-master.sh at the successor under --prefix /opt/livespec/codex-acp, re-measure the reachable gpt-5.6 tier set from the sandbox against the projected credential, and route this repository's review node to gpt-5.6-terra at xhigh via dispatcher.acp_nodes. Tracked as ledger item bd-ib-nr3pon under plan epic bd-ib-ujihbw.
---

## Proposal: Codex ACP adapter succession: baked-path identity and the CODEX_CONFIG env channel

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Amends the Codex ACP adapter's ratified identity from the npm package name resolved through `npx --no-install @zed-industries/codex-acp` to the successor package invoked at its baked path `/opt/livespec/codex-acp/bin/codex-acp`, and moves the model, reasoning effort, sandbox and approval settings off the `-c key=value` argument channel onto the adapter's own declared environment via `CODEX_CONFIG` and `INITIAL_AGENT_MODE`. The npx-by-name form is retired because it was MEASURED to be a non-identity: with both packages installed globally it renders one package and executes another. The amendment also states explicitly that the no-environment-override rule constrains ad-hoc shells and not an adapter's own committed env map, so the new channel does not contradict the rule it appears to touch.

### Motivation

Leg (b) of ledger item bd-ib-nr3pon (commission item E2) under plan epic bd-ib-ujihbw, which its own description records as OWED BEFORE DISPATCH. The upstream half is already ratified: livespec-dev-tooling PR 1644 merged 2026-08-26T07:09:34Z as v053, whose sections `### Pin autodiscovery rules` and `### codex-acp factory gate` require the successor to be installed under the dedicated npm prefix /opt/livespec/codex-acp, which owns no global bin link, and require every consumer to invoke it at its baked path. This repository's contracts.md still names the predecessor literal and the -c channel in its "rendered form, literally" paragraphs, its built-in-defaults table and its "Reachable tiers are bounded by the baked adapter" paragraph, and §"ACP node adapter configuration" repeats the npx form in its per-node-value example. Implementing the succession without this amendment would make the code assert what the specification denies.

The load-bearing measurement, taken by the livespec-runtime session and re-taken by this session against the released image rather than the transitional layer: npx resolves a package's bin through the SHARED global bin link, so with both packages installed `npx --no-install @zed-industries/codex-acp --version` printed `@agentclientprotocol/codex-acp 1.6.2`. The rendered adapter string would have read as the predecessor while executing the successor, defeating this section's own opening claim that a reader can predict the literal adapter string and check it against `run_turn.command`. On release image python-agent-v1.35.0, verified by this session on BOTH hp and vps, the baked path reports `@agentclientprotocol/codex-acp 1.6.2` while npx-by-name still runs the predecessor, so the two coexist safely and this repository's current renderer is unaffected until this amendment is implemented.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Codex ACP node model pins":

Replace the base adapter command in the **The rendered form, literally** paragraph. The base adapter command MUST become the successor package invoked at its baked path:

    /opt/livespec/codex-acp/bin/codex-acp

A pinned adapter MUST carry its model, reasoning effort, sandbox posture and approval posture as leading `KEY=value` environment assignments on that command rather than as `-c key=value` arguments. The `CODEX_CONFIG` assignment MUST carry a JSON object merged into the adapter's session configuration, holding the `model`, `model_reasoning_effort`, `sandbox_mode` and `approval_policy` keys. The `INITIAL_AGENT_MODE` assignment MUST carry `agent-full-access` for the implementer and publish classes and `read-only` for a node that performs no writes. Environment assignments MUST be rendered in sorted key order ahead of the command, exactly as §"ACP node adapter configuration" already requires of every node's `env` map.

Replace the rationale for the invocation form. The section MUST state that the adapter is resolved AT ITS BAKED PATH rather than via `npx --no-install`, and MUST retain the four properties the previous form was chosen for: the invocation is version-free, it performs no npm registry round-trip so it runs under `--network none`, and the baked image remains the single source of truth for the adapter version. It MUST additionally state the property the previous form lacked: a baked path is an unambiguous identity, whereas package-name resolution through a shared global bin link can render one package and execute another. The section MUST forbid relying on package-name resolution to distinguish the successor from the predecessor.

Update the literal example strings so the section continues to satisfy its own opening claim. A default dispatch's publish adapter MUST render as the `CODEX_CONFIG` and `INITIAL_AGENT_MODE` assignments in sorted key order followed by the baked path, with `model` `gpt-5.4-mini` and `model_reasoning_effort` `high` inside `CODEX_CONFIG`. The former Codex implementer pin example MUST be restated in the same form rather than in the `-c` form. The built-in fleet defaults table is otherwise unchanged: the implementer class stays on the Claude adapter at `claude-opus-5` and `high`, whose rendered string is unchanged by this proposal and MUST remain byte-identical.

Restate the empty-model opt-out for the new channel. A tier whose `model` is the empty string MUST render the adapter with NO `model` key inside `CODEX_CONFIG`, rather than with an empty model value, and MUST otherwise be byte-identical to the un-pinned base string. It remains a true no-op rather than a differently-spelled default.

Amend **There is no environment override** so the two mechanisms are not conflated. The rule MUST be stated as constraining AD-HOC SHELL environment seams: no environment variable read from the orchestrator host's ambient environment may re-tier the factory. It MUST state explicitly that an adapter's own declared `env` map is NOT such a seam, because it is committed configuration resolved through the three layers of §"ACP node adapter configuration" and rendered verbatim into the recorded adapter string and the dispatch journal. Without this clarification the section forbids the very channel this proposal adopts.

Replace **Reachable tiers are bounded by the baked adapter**. The 2026-08-22 measurement recorded there was taken against the predecessor at `@zed-industries/codex-acp@0.16.0`, which vendors a Codex generation that refuses the gpt-5.6 slugs; it does not describe the successor. The section MUST record that the reachable tier set is a property OF THE BAKED ADAPTER VERSION and MUST be re-measured from the sandbox against the real projected credential whenever that version changes, MUST name the adapter version the recorded table was measured against, and MUST NOT carry a tier table attributed to a version the image no longer bakes. The concrete post-succession table is produced by ledger item bd-ib-nr3pon leg (d) and is not asserted by this proposal.

In `SPECIFICATION/contracts.md` §"ACP node adapter configuration":

Update the per-node-value example so it does not name the retired form. The `command` field's illustrative values MUST cite `/opt/livespec/codex-acp/bin/codex-acp` for the Codex adapter instead of `npx --no-install @zed-industries/codex-acp`, and the `args` field's illustrative value MUST NOT be `-c model=gpt-5.5`, since model and effort no longer ride the argument channel for that adapter. The paragraph's provider-agnostic claim is unchanged and MUST be preserved: `env` still carries an Anthropic-Messages provider's base URL, token and model on the Claude adapter, and the Codex adapter's provider selection still rides `args`. The three resolution layers, the per-field precedence with `env` merging, the refusal on an unknown node, the `dispatcher.codex_models` shorthand, the journaling of the supplying layer, the committed-configuration-only classification and the hermetic negative-control requirement are all unchanged by this proposal.

Implementation obligation stated so the code's reasoning and the ratified text do not diverge: the four-property rationale comment above `CODEX_ADAPTER_BASE` in `commands/_dispatcher_fabro_argv.py` MUST be updated in the same change that implements this amendment, so the comment's stated justification names the baked path and the identity property rather than the npx round-trip argument.

In `SPECIFICATION/scenarios.md`, add one `## Scenario` exercising the rendered identity and the env channel together: Given a dispatch whose publish node resolves to the Codex tier and whose implementer node resolves to the Claude default, When the Dispatcher renders both adapters, Then the publish adapter string carries its environment assignments in sorted key order followed by `/opt/livespec/codex-acp/bin/codex-acp`, carries `model` and `model_reasoning_effort` inside `CODEX_CONFIG` and carries no `-c model` argument, and the implementer adapter string is byte-identical to the ratified Claude default. Add a second `## Scenario` for the opt-out: Given a Codex tier whose `model` is the empty string, When the adapter is rendered, Then `CODEX_CONFIG` carries no `model` key and the rendered string is byte-identical to the un-pinned base string. Both scenarios MUST be added to `tests/heading-coverage.json` in the same change, per this project's revise co-edit discipline.

