---
topic: codex-config-shell-quoting
author: claude-opus-5
created_at: 2026-08-27T03:48:42Z
spec_commitments:
  impl_followups:
    - id_hint: codex-config-shell-quoting-impl
      description: |
        Render the CODEX_CONFIG value shell-quoted in codex_adapter() and in CODEX_ADAPTER_BASE (commands/_dispatcher_fabro_argv.py), so the JSON object survives Fabro's shlex tokenization of the adapter command string. Update the beside-tests that assert the rendered bytes, including the byte-identity opt-out assertion. A regression test MUST assert that the value recovered by shell tokenization parses as JSON, rather than asserting on the rendered string alone -- a string-shape assertion cannot distinguish a quoted value from an unquoted one after tokenization.
---

## Proposal: Shell-quote the CODEX_CONFIG value so the adapter's JSON survives tokenization

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The ratified Codex adapter string spells CODEX_CONFIG's value as bare JSON, but Fabro shell-tokenizes the adapter string with shlex before executing it, which strips the JSON's quotes. The adapter then dies in JSON.parse before doing any work, killing every run at its first Codex-backed node. This proposal requires the value to be shell-quoted and corrects the three literal strings the section spells out, changing nothing else about them.

### Motivation

A regression shipped in v0.82.0 that made every Codex-backed publication node in the fleet fail deterministically. Measured across five dead factory runs in two tenants, at two different stages and with three different configured models, with the mechanism located in the pinned Fabro fork's source and reproduced locally. The defect is in the ratified spelling itself, so it cannot be fixed implementation-side without contradicting the ratified byte-identity requirement.

### Proposed Changes

The rendered Codex adapter string is consumed by Fabro as a SHELL COMMAND STRING, not as
a structured record. `AcpProcessSpec::from_command_attr`
(`lib/components/fabro-acp/src/command.rs:39` in the pinned fork) runs
`shlex::split(trimmed)` on the raw adapter string before handing the tokens to
`AcpAgent::from_args`. `shlex` is POSIX-shell tokenization and it REMOVES QUOTE
CHARACTERS. The ratified base string spells the `CODEX_CONFIG` value as BARE JSON, so
every double quote in that JSON is stripped in transit and the adapter receives an
unquoted brace expression.

MEASURED CONSEQUENCE, not a hypothetical. The adapter calls `JSON.parse` on the value at
`startAcpServer` and dies before performing any work:

```
{approval_policy:never,model:gpt-5.6-terra,model_reasoning_effort:xhigh,sandbox_mode:danger-full-access}
 ^ SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)
   at JSON.parse (<anonymous>)
   at startAcpServer (/opt/livespec/codex-acp/lib/node_modules/@agentclientprotocol/codex-acp/dist/index.js:32872:39)
```

The process exits 1 (NOT 127, which would indicate a missing or stale baked adapter), and
the run dies at whichever Codex-backed node it reaches first. Reproduced locally against
the same tokenizer semantics: the bare form yields `{approval_policy:never,...}` and fails
`json.loads`; a shell-quoted form yields the JSON intact and parses.

THE CHANGE. The `CODEX_CONFIG` value MUST be SHELL-QUOTED in the rendered string so that
the JSON survives tokenization. The three literal strings this section spells out change
by exactly one pair of single quotes each, and nothing else about them changes: the
environment assignments keep their sorted key order, `INITIAL_AGENT_MODE` is untouched, the
baked path is untouched, and no argument is added or removed.

```diff
-    CODEX_CONFIG={"approval_policy":"never","sandbox_mode":"danger-full-access"} INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
+    CODEX_CONFIG='{"approval_policy":"never","sandbox_mode":"danger-full-access"}' INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
```

The same single-quote wrap applies to the two pinned example strings in this section.

PROSE TO ADD, so the requirement is stated rather than left implicit in an example. The
paragraph introducing the `KEY=value` environment assignments should state that the
`CODEX_CONFIG` value MUST be shell-quoted because the adapter string is shell-tokenized
before execution, and that an unquoted JSON object does not survive that tokenization. The
paragraph that spells out the un-pinned base string should note that the quoting is part of
the byte-identity referent, so an implementation rendering bare JSON is NOT byte-identical
to the base string.

WHY QUOTING RATHER THAN RESTRUCTURING. Fabro also accepts a structured `config` attribute
(`from_config_attr`) that skips shell parsing entirely. That is a LARGER change, not a
smaller one: it would replace the adapter's whole command-string representation, which this
section is built around and which Scenario 90 asserts against. Quoting one value preserves
every property the current form was chosen for.

SCOPE. Scenarios 90 and 91 assert byte-identity against "the un-pinned base string", which
is a REFERENT defined by this section's literal spelling rather than a literal repeated in
the scenarios. Correcting the spelling here therefore updates what those scenarios assert
without editing them.

