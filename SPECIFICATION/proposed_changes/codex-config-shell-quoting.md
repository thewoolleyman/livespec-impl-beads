---
topic: codex-config-shell-quoting
author: claude-opus-5
created_at: 2026-08-27T03:48:42Z
spec_commitments:
  impl_followups:
    - id_hint: codex-config-shell-quoting-impl
      description: |
        Render every ACP adapter env value shell-quoted so that POSIX shell tokenization of the rendered adapter string recovers each value byte-for-byte. This spans BOTH renderers, not one: the shorthand path in commands/_dispatcher_fabro_argv.py (codex_adapter() and CODEX_ADAPTER_BASE) AND the generic explicit-table path in commands/_acp_node_adapters.py render_adapter(), which builds its pairs as f"{key}={adapter.env[key]}" and is the renderer that produced the measured failure. Use shlex.quote rather than a literal single-quote wrap; a naive wrap breaks on a value containing an apostrophe. Rendering MUST be idempotent under re-render so a shorthand-rendered adapter parsed and rendered again is not double-quoted. Co-edit the five test files carrying a literal CODEX_CONFIG= adapter string (tests/integration/test_codex_adapter_baked_path_scenarios90_91.py, tests/integration/test_dispatcher_codex_pins_and_provider_limits_scenarios64_65.py, tests/livespec_orchestrator_beads_fabro/commands/test_dispatcher_codex_model_tiers.py, tests/livespec_orchestrator_beads_fabro/commands/test_dispatcher_dual_cred.py, tests/livespec_orchestrator_beads_fabro/commands/test_dispatcher_codex_compaction_limit.py), including all four byte-identity opt-out assertions; their literals are restated rather than imported by deliberate double-entry, so each must be edited by hand. Regression tests MUST assert the round-trip property -- that the value recovered by POSIX shell tokenization parses as JSON and equals the configured object -- rather than asserting on the rendered string alone, because a string-shape assertion cannot distinguish a quoted value from an unquoted one after tokenization. At least one regression MUST exercise the explicit dispatcher.acp_nodes table path, and at least one MUST cover a value containing an apostrophe. Grade completion against ledger item bd-ib-qulf.
---

## Proposal: Shell-quote ACP adapter env values so the Codex adapter's JSON survives tokenization

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

The ratified Codex adapter string spells CODEX_CONFIG's value as bare JSON, but Fabro shell-tokenizes the adapter string with shlex before executing it, which strips the JSON's quotes. The adapter then dies in JSON.parse before doing any work, killing every run at its first Codex-backed node. This proposal places the requirement where it belongs -- on the general adapter rendering contract, as a round-trip property of every env value -- corrects the three literal strings the Codex section spells out, and adds the one scenario assertion that can detect a regression on the pinned path.

### Motivation

A regression shipped in v0.82.0 that made every Codex-backed publication node in the fleet fail deterministically. Measured across five dead factory runs in two tenants, at two different stages and with three different configured models, with the mechanism located in the pinned Fabro fork's source and reproduced locally. The defect is in the ratified spelling itself, so it cannot be fixed implementation-side without contradicting the ratified byte-identity requirement.

PRIOR ART. Ledger item `bd-ib-qulf` (P1, `backlog`, filed 2026-08-26) carries this
defect with its measured run ids, its 0.81.0 control run, and its ratification-impact
analysis, and is where the implementation follow-up gets graded. Note that item's own
"Fix direction" scopes the fix to `codex_adapter` alone and therefore carries the SAME
error this proposal corrects below; the correction should be mirrored onto the item.

### Proposed Changes

The rendered adapter string is consumed by Fabro as a SHELL COMMAND STRING, not as
a structured record. `AcpProcessSpec::from_command_attr` runs `shlex::split(trimmed)`
on the raw adapter string before handing the tokens to `AcpAgent::from_args`. At the
pinned fork build (`fabro 0.254.0 (8de6611)`, commit `8de661118` on
`factory-integration`) that is `lib/crates/fabro-acp/src/command.rs:38`, with
`AcpAgent::from_args` at lines 39-40. `shlex` is POSIX-shell tokenization and it
REMOVES QUOTE CHARACTERS; the pinned lockfile resolves `shlex 1.3.0`, whose own test
vector maps `foo"bar"baz` to `foobarbaz`. The ratified base string spells the
`CODEX_CONFIG` value as BARE JSON, so every double quote in that JSON is stripped in
transit and the adapter receives an unquoted brace expression.

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

THE REQUIREMENT, AND WHERE IT BELONGS. This is a property of the RENDERING CONTRACT, not
of one key. §"ACP node adapter configuration" currently closes with:

> The rendered adapter string MUST be exactly: the `env` pairs in sorted key order,
> then `command`, then `args` in order, single-space separated.

Read as written, an implementation that emits `KEY=value` verbatim is conformant -- which
is precisely the defect. That sentence MUST be amended to require that each `env` value be
shell-quoted such that POSIX shell tokenization of the rendered string recovers the value
BYTE-FOR-BYTE. Stating it as the round-trip property rather than as "wrap it in single
quotes" is deliberate and load-bearing: `model` is an arbitrary operator-supplied string
with no character validation, and `json.dumps` passes an apostrophe through untouched, so
a naive `'{value}'` wrap closes the quote early and yields
`AcpCommandError::InvalidCommandString` -- a more opaque failure than today's, naming
neither the key nor the value. The round-trip wording is satisfied by `shlex.quote` and
refuses the naive wrap.

The paragraph at the head of this section stating that an adapter's declared `env` map is
"rendered verbatim into the recorded adapter string" MUST likewise be adjusted, so that it
describes VALUE fidelity rather than BYTE fidelity. "Verbatim" is the word that has to
give; left as it is, the specification would carry two clauses in tension.

THE THREE LITERALS. The Codex section's three literal strings change by exactly one pair
of single quotes each, and nothing else about them changes: the environment assignments
keep their sorted key order, `INITIAL_AGENT_MODE` is untouched, the baked path is
untouched, and no argument is added or removed. All three are spelled out here rather than
leaving two to be reconstructed:

```diff
-    CODEX_CONFIG={"approval_policy":"never","sandbox_mode":"danger-full-access"} INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
+    CODEX_CONFIG='{"approval_policy":"never","sandbox_mode":"danger-full-access"}' INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
```

```diff
-    CODEX_CONFIG={"approval_policy":"never","model":"gpt-5.4-mini","model_reasoning_effort":"high","sandbox_mode":"danger-full-access"} INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
+    CODEX_CONFIG='{"approval_policy":"never","model":"gpt-5.4-mini","model_reasoning_effort":"high","sandbox_mode":"danger-full-access"}' INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
```

```diff
-    CODEX_CONFIG={"approval_policy":"never","model":"gpt-5.5","model_reasoning_effort":"low","sandbox_mode":"danger-full-access"} INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
+    CODEX_CONFIG='{"approval_policy":"never","model":"gpt-5.5","model_reasoning_effort":"low","sandbox_mode":"danger-full-access"}' INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
```

WHY QUOTING RATHER THAN RESTRUCTURING. Fabro also accepts a structured `config` attribute
(`from_config_attr`) that trims and hands raw JSON to `parse_config_server` without ever
calling `shlex`. That is a LARGER change, not a smaller one: `from_attrs` requires exactly
one of `acp.command` and `acp.config`, so adopting it would replace the adapter's whole
command-string representation, which this section is built around and which Scenario 90
asserts against. Quoting preserves that representation.

One caveat, recorded rather than glossed. This section twice states that a reader can
reconstruct the literal strings and "check them against `run_turn.command`". Measured at
the pin, that property is ALREADY NOT MET: `acp.rs:213` sets `command_display` from
`process_spec.to_string()`, whose `Display` renders program and args only, and a test in
the same file (`acp_started_event_omits_json_command_env_values`) asserts on purpose that
env values are withheld so credentials do not leak into the event stream. So no literal --
bare or quoted -- is checkable there, and the quoting change is invisible in that record.
This is a pre-existing gap of the v082 section, not one this change introduces, and this
proposal does not attempt to close it; the appeal to that property is withdrawn as a
justification.

SCOPE, AND THE ONE SCENARIO EDIT. No scenario repeats a Codex adapter literal, so
re-spelling the literals here does not strand a duplicated string. Scenario 91 asserts
byte-identity against "the un-pinned base string", a REFERENT defined by this section's
literal spelling rather than a literal repeated in the scenario, so correcting the
spelling updates what it asserts without editing it. Scenario 90 does NOT use that
referent -- its only byte-identity line is against the ratified CLAUDE default string, on
the adapter this change does not touch.

That leaves the pinned Codex path -- the common case, and the one every measured run died
on -- asserted by no scenario on the property being ratified. Scenario 90's first block
MUST therefore gain one assertion that the publish adapter's `CODEX_CONFIG` value parses
as JSON after POSIX shell tokenization. The addition introduces no new `## ` heading, so
`tests/heading-coverage.json` needs no co-edit.
