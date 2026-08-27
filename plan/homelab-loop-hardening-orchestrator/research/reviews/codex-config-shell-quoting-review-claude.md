# Adversarial review of `codex-config-shell-quoting` — reviewer claude

Commissioned 2026-08-27 by the homelab-loop-hardening-orchestrator session. Run as
the CLAUDE leg of a two-leg independent adversarial review (a separate Codex leg ran
the same brief concurrently; no coordination). Read-only against worktree
`/home/ubuntu/.worktrees/livespec-orchestrator-beads-fabro/spec-codex-config-shell-quoting`
@ `b2e660ed` (one commit ahead of master `ef71058c`), the pinned Fabro fork, and the
live beads tenant. Nothing was modified, committed, or pushed.

## VERDICT

`do-not-ratify-as-written`

2 blockers, 4 majors, 5 minors.

## Executive summary

The diagnosis is correct and I reproduced it first-hand with the actual Rust `shlex`
1.3.0 crate that the pinned fork depends on: the bare form loses its quotes, the
single-quoted form survives intact. The rejected-alternative characterization is fair.
The "three literal strings" count is complete. Scenarios 90 and 91 repeat no literal,
so the SCOPE claim's operative conclusion holds.

What blocks it is scope, and the evidence is the proposal's own. The adapter string
whose failure the proposal quotes verbatim — the `gpt-5.6-terra` / `xhigh` review node
— is **not produced by `codex_adapter()` or `CODEX_ADAPTER_BASE`**. It is produced by
`render_adapter()` in `_acp_node_adapters.py` from this repository's committed
`.livespec.jsonc` `dispatcher.acp_nodes.review.env` table, a second renderer governed
by a *different* ratified paragraph that the proposal leaves unamended. Implementing
the `impl_followup` exactly as written fixes the `pr` node and leaves the node that
actually died still rendering bare JSON. I rendered both through the real
three-layer merge to confirm this.

## BLOCKERS

### B1 — The `impl_followup` names the wrong renderer: the measured failure comes from `render_adapter()`, not `codex_adapter()`

**Claim under review.** `impl_followups[0].description`: "Render the `CODEX_CONFIG`
value shell-quoted in `codex_adapter()` and in `CODEX_ADAPTER_BASE`
(`commands/_dispatcher_fabro_argv.py`)". Those are the only two symbols named.

**What I measured.** I resolved this repository's real adapters through the real
three-layer merge and the real argv builder, by driving the repo's own
`tests/integration/test_codex_adapter_baked_path_scenarios90_91.py::_rendered_adapters`
against `_REPO_ROOT` under `uv run --no-sync`. Two nodes render a `CODEX_CONFIG`:

```
pr     -> CODEX_CONFIG={"approval_policy":"never","model":"gpt-5.4-mini","model_reasoning_effort":"high","sandbox_mode":"danger-full-access"} INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
review -> ANTHROPIC_MODEL=claude-opus-4-8[1m] CLAUDE_CODE_EFFORT_LEVEL=high CODEX_CONFIG={"approval_policy":"never","model":"gpt-5.6-terra","model_reasoning_effort":"xhigh","sandbox_mode":"danger-full-access"} INITIAL_AGENT_MODE=read-only /opt/livespec/codex-acp/bin/codex-acp
```

Only the first comes from `codex_adapter()`. The `review` line's `gpt-5.6-terra` /
`xhigh` pin exists **nowhere** in `dispatcher.codex_models` — `.livespec.jsonc:195-197`
declares only `"pr": { "model": "gpt-5.4-mini", "reasoning_effort": "high" }`. It comes
from `.livespec.jsonc:226-235`, the `dispatcher.acp_nodes.review` table, whose
`env.CODEX_CONFIG` is a hand-written unquoted JSON string, rendered by:

```python
# .claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_acp_node_adapters.py:168
pairs = [f"{key}={adapter.env[key]}" for key in sorted(adapter.env)]
```

No quoting. I confirmed the equivalence by calling `render_adapter()` directly on that
env map and getting the byte-identical string.

**Why this is the failing string and not a sibling.** Feeding the rendered `review`
line to the real `shlex::split` (crate 1.3.0, the version `Cargo.lock` pins at
`8de661118`) yields:

```
"ANTHROPIC_MODEL=claude-opus-4-8[1m]"
"CLAUDE_CODE_EFFORT_LEVEL=high"
"CODEX_CONFIG={approval_policy:never,model:gpt-5.6-terra,model_reasoning_effort:xhigh,sandbox_mode:danger-full-access}"
"INITIAL_AGENT_MODE=read-only"
"/opt/livespec/codex-acp/bin/codex-acp"
```

The third token is **byte-identical** to the stderr the proposal quotes in its
MEASURED CONSEQUENCE block, down to the key order and the `gpt-5.6-terra` /
`xhigh` values. The proposal's own evidence is the `acp_nodes` path.

**Anticipating the counter-argument.** The proposal's PROSE TO ADD would sit in the
paragraph at `contracts.md:3263-3268`, which does say the assignments work "exactly as
§'ACP node adapter configuration' requires of every node's `env` map" — so one could
argue a `CODEX_CONFIG`-scoped MUST there binds any renderer. That is not enough, for
three reasons. (a) The `impl_followup` is the seam by which ratified prose becomes
implementation work, and it names two symbols in one module; an implementer discharging
it literally never touches `_acp_node_adapters.py`. (b) The rendering MUST that actually
governs `render_adapter` is `contracts.md:3379-3381` and it is left unamended — see B2.
(c) The defect is not `CODEX_CONFIG`-specific: **any** `env` value carrying a shell
metacharacter breaks identically, and `contracts.md:3376` explicitly names
`ANTHROPIC_AUTH_TOKEN` as an `env` value — a credential is exactly the kind of value
most likely to contain one, and it would fail silently by mangling rather than loudly by
`JSON.parse`.

**Remedy.** Quote at the shared producer chokepoint — `render_adapter()` — so every
consumer repo is fixed by the plugin release rather than by editing each
`.livespec.jsonc`, and name that symbol in the followup alongside `codex_adapter()` and
`CODEX_ADAPTER_BASE`.

### B2 — The ratified rendering MUST that governs that path is unamended and now contradicts the new requirement

**Claim under review.** SCOPE: "Correcting the spelling here therefore updates what
those scenarios assert without editing them." The proposal amends `contracts.md`'s
Codex-pins section only, and its "Target specification files" list is
`SPECIFICATION/contracts.md` with no section qualification beyond the Codex adapter
section it works in.

**What I read.** `SPECIFICATION/contracts.md:3379-3381`, in §"ACP node adapter
configuration":

> The rendered adapter string MUST be exactly: the `env` pairs in sorted key order,
> then `command`, then `args` in order, single-space separated.

That sentence is the contract `render_adapter()` implements — its docstring cites the
order as "contractual" — and it says nothing about quoting. Read as written, an
implementation that emits `KEY=value` verbatim is conformant, which is precisely the
defect. After ratifying the Codex section's quoting MUST, the specification carries two
clauses in tension: one requiring the `CODEX_CONFIG` value to be shell-quoted, one
defining the rendered string as the env pairs, unqualified. `contracts.md:3249-3252`
compounds it — the adapter's own declared `env` map is "rendered **verbatim** into the
recorded adapter string" — and "verbatim" is the word that has to give.

**Remedy.** Amend `3379-3381` to require that each `env` value be shell-quoted such
that POSIX tokenization of the rendered string recovers it byte-for-byte, and adjust the
"verbatim" wording at `3249-3252` so it describes value fidelity rather than byte
fidelity. This is where the requirement belongs: it is a property of the rendering
contract, not of one key.

## MAJORS

### M1 — The Fabro source citation is from the wrong revision; it does not resolve in the pinned fork

**Claim.** "`AcpProcessSpec::from_command_attr` (`lib/components/fabro-acp/src/command.rs:39`
in the pinned fork) runs `shlex::split(trimmed)`".

**What I measured.** `git show 8de661118:lib/components/fabro-acp/src/command.rs` in
`/data/projects/fabro` returns `fatal: path 'lib/components/fabro-acp/src/command.rs'
exists on disk, but not in '8de661118'`. At the pinned commit the path is
`lib/crates/fabro-acp/src/command.rs` and `shlex::split` is at **line 38**, not 39.
`lib/components/…:39` is the path and line in the clone's **working checkout**, which
`git status` puts on `fix/classify-provider-spend-limit-not-transient` at version
`0.310.0-nightly.2` — a different revision from the pin. The crate directory was renamed
between the two.

**The substance survives; the citation does not.** The pin is real and reachable:
`git log --oneline -1 factory-integration` returns `8de661118`, matching the documented
pin `fabro 0.254.0 (8de6611)`, and `git show factory-integration:Cargo.toml` reports
`version = "0.254.0"`. At that commit `from_command_attr` runs
`shlex::split(trimmed)` (line 38) and hands the tokens to `AcpAgent::from_args` (lines
39-40), exactly as described. So the mechanism verifies; the file path and line number
do not, and a successor re-checking the pinned build with the cited coordinates gets a
`fatal:` and no answer. Repoint it to `lib/crates/fabro-acp/src/command.rs:38` and say
which commit it was read at.

### M2 — "shell-quoted" is underspecified; a naive single-quote wrap produces a *worse* failure on an unvalidated input

The proposal's normative sentence is "The `CODEX_CONFIG` value MUST be SHELL-QUOTED",
and its supporting sentence is that the literals "change by exactly one pair of single
quotes each". An implementer reading the pair as the algorithm writes
`f"CODEX_CONFIG='{rendered_config}'"`, which is not escaping-correct.

`model` is an arbitrary operator-supplied string with **no character validation**:
`_codex_model_tiers.py:187-195` takes `table.get("model")` and only checks
`isinstance(..., str)`. `json.dumps` escapes `"` but passes `'` through untouched. So a
tier pinned to a model whose name contains an apostrophe closes the wrap early. Measured
with the real crate:

```
APOSTROPHE-NAIVE-WRAP: shlex::split -> None (InvalidCommandString)
```

`from_command_attr` maps that `None` to `AcpCommandError::InvalidCommandString`, whose
message is "failed to parse acp.command as a shell command" — a different and more
opaque failure than today's `JSON.parse` error, and one that names neither the key nor
the value. State the requirement as the round-trip property the `impl_followup`'s test
already gestures at: *the value recovered by POSIX shell tokenization of the rendered
string MUST be byte-identical to the JSON object*. That wording is satisfied by
`shlex.quote` and refuses the naive wrap, and it is the same property for every `env`
value under B2.

### M3 — The new MUST is exercised by no scenario on the path that carries it

The SCOPE paragraph argues that no scenario needs editing. That is true as far as
*byte-identity referents* go, but it stops short of the traceability question. After
ratification the section carries a new normative requirement whose entire content is a
property of the rendered bytes, and:

- **Scenario 91** covers it only transitively and only for the opt-out: "the rendered
  adapter is byte-identical to the un-pinned base string" inherits the quoting because
  the base-string literal is being re-spelled. That is the *un-pinned* path.
- **Scenario 90** asserts nothing quoting-sensitive. Its four blocks assert env
  assignments in sorted order followed by the baked path; `model` and
  `model_reasoning_effort` present inside `CODEX_CONFIG`; no `-c model` argument;
  `INITIAL_AGENT_MODE` values; no `npx` package-name resolution; and byte-identity of
  the *implementer* adapter to the ratified **Claude** default string. Every one of them
  returns the same answer whether the value is quoted or bare. So the **pinned** path —
  the common case, and the one both measured runs died on — has no scenario coverage of
  the property being ratified.

Add one `And` to Scenario 90's first block asserting the survival property (for example:
*And the publish adapter's CODEX_CONFIG value parses as JSON after POSIX shell
tokenization*), and say so in SCOPE instead of claiming no scenario edit is needed. Note
that this addition changes no `## ` heading, so `tests/heading-coverage.json` needs no
co-edit either way — I checked that separately.

### M4 — The section's twice-stated rationale ("check them against `run_turn.command`") is false against the pinned fork, and the proposal reaffirms it

WHY QUOTING RATHER THAN RESTRUCTURING closes with "Quoting one value preserves every
property the current form was chosen for." One of those properties, stated twice in the
section being amended (`contracts.md:3303-3305` and `3326-3328`), is that a reader can
reconstruct the literal strings and "check them against `run_turn.command`".

Measured at the pin: `lib/crates/fabro-workflow/src/handler/llm/acp.rs:213` sets
`command_display = process_spec.to_string()`, `Display` delegates to
`to_shell_command()` (`command.rs:116-125`), and that renders **program + args only**,
each passed through `shell_quote`. The env map is not in it. There is a test in the same
file asserting this on purpose — `acp_started_event_omits_json_command_env_values` —
which checks the recorded command contains `python3` and does **not** contain
`OPENAI_API_KEY` or `secret-key`. Env values are deliberately withheld so credentials do
not leak into the event stream.

So none of the three literal strings — bare or quoted — can be checked against
`run_turn.command`, and the quoting change is invisible there too. This is a pre-existing
defect of the v082 section rather than one this proposal introduces, and I am not asking
it to fix the observability gap. But the proposal leans on that property as its
justification for choosing quoting over restructuring, and the argument should either
drop the appeal or note that the property is already not met.

## MINORS

1. **SCOPE misdescribes Scenario 90.** It says "Scenarios 90 and 91 assert byte-identity
   against 'the un-pinned base string'". Scenario 90 never uses that referent. Its only
   byte-identity line is `scenarios.md:2220`, "the implementer adapter is byte-identical
   to the ratified Claude default string" — a different referent, on the adapter this
   change does not touch. The conclusion (no literal is repeated in either scenario)
   survives; the premise as stated is wrong for one of the two.

2. **"the byte-identity opt-out assertion" is singular; there are four, in four files.**
   `tests/integration/test_codex_adapter_baked_path_scenarios90_91.py:186-187` (two, one
   against a restated literal and one against the imported constant);
   `tests/integration/test_dispatcher_codex_pins_and_provider_limits_scenarios64_65.py:133`;
   `tests/livespec_orchestrator_beads_fabro/commands/test_dispatcher_codex_model_tiers.py:144`;
   `tests/livespec_orchestrator_beads_fabro/commands/test_dispatcher_dual_cred.py:371` and
   `:798`. The followup's claim that such an assertion exists is **true** — I verified it
   — but "the" understates the co-edit.

3. **"the beside-tests that assert the rendered bytes" is not enumerated.** Five test
   files carry a literal `CODEX_CONFIG=` adapter string: the four above plus
   `tests/livespec_orchestrator_beads_fabro/commands/test_dispatcher_codex_compaction_limit.py:51`.
   Their literals are restated rather than imported by deliberate double-entry
   (`test_codex_adapter_baked_path_scenarios90_91.py:42-47` explains why), so every one
   must be edited by hand or the suite goes red. Enumerate them.

4. **Prior art is not cited.** `bd-ib-qulf` is a live P1 in `backlog` — "(BUG) Release
   0.82.0 Codex adapter cannot start: shlex tokenization strips the CODEX_CONFIG JSON
   quotes, so every Codex-backed node exits 1" — filed 2026-08-26. It carries the two
   measured run ids, the 0.81.0 control run, the ratification-impact analysis this
   proposal restates, and six acceptance criteria. The proposal should name it, both for
   traceability and because the ledger item is where the followup's completion gets
   graded. Note also that `bd-ib-qulf`'s own "Fix direction" makes the **same**
   `codex_adapter`-only scoping error as B1, and its Symptom section quotes the
   `gpt-5.6-terra` string that proves the error — so the proposal inherited the mistake
   rather than introducing it, and fixing it here should be mirrored onto the item.

5. **Only one of the three literals is shown as a diff.** The two pinned examples at
   `contracts.md:3319` and `:3324` are handled by the prose sentence "The same
   single-quote wrap applies to the two pinned example strings in this section." Since
   the whole proposal is about exact bytes, and since the section's premise is that a
   reader can predict those bytes, show all three replacement lines literally rather than
   asking the revise pass to reconstruct two of them.

## What the proposal gets right

- **The mechanism is correct and I reproduced it independently**, twice, including with
  the actual Rust crate rather than a same-semantics stand-in.
- **The rejected alternative is characterized fairly.** `from_config_attr`
  (`command.rs:46-54` at the pin) routes through `parse_config_server`, which
  `serde_json::from_str`s the raw value into an `McpServer` with `command` / `args` /
  `env` fields. It is a different node attribute (`acp.config`, and `from_attrs` refuses
  both attributes together), and it does replace the whole command-string representation.
  "A LARGER change, not a smaller one" is accurate.
- **"Three literal strings" is exactly right.** `grep -n "codex-acp"` over live
  `contracts.md` returns nine hits: three literal command strings (3279, 3319, 3324), the
  bare baked path at 3261 and 3365, and four prose mentions. Live `scenarios.md` mentions
  `codex-acp` twice and repeats no literal.
- **The "no scenario repeats a literal" conclusion holds**, which was the brief's
  designated blocker condition on that axis. It is not met.
- **The v0.82.0 attribution is correct.** `CHANGELOG.md:31-36` puts "render the Codex ACP
  adapter at its baked path via CODEX_CONFIG" (`1d08013`) in 0.82.0, and that commit's
  diff removes `-c sandbox_mode=danger-full-access -c approval_policy=never` — an
  argument channel with no quote characters, and therefore lossless under `shlex` — and
  replaces it with the JSON object. The regression claim is exact.
- **One hazard I checked and did not find.** `parse_adapter_string`
  (`_acp_node_adapters.py:135-155`) decomposes an adapter string with plain
  `text.split()`, not `shlex`, and its docstring makes the
  `render_adapter(parse_adapter_string(...))` round-trip explicitly load-bearing. A
  quoted value could have broken that. It does not: `_ENV_ASSIGNMENT_RE` is
  `^[A-Za-z_][A-Za-z0-9_]*=`, which constrains only the key, and the rendered JSON uses
  `separators=(",", ":")` so the quoted token contains no whitespace. The round trip is
  preserved.

## WHAT I VERIFIED AND HOW

Every command below is re-runnable.

**The artifact and its base.** `git log --oneline -3` and `git status --short --branch`
in the review worktree: `b2e660ed` on branch `spec/codex-config-shell-quoting`, sitting directly on
`ef71058c`, clean.

**The pinned fork's identity.** In `/data/projects/fabro`: `git log --oneline -1
8de6611` → `8de661118 feat(config): make the per-node checkpoint commit timeout
configurable (#552)`; `git log --oneline -1 factory-integration` → the same SHA;
`git show factory-integration:Cargo.toml | grep '^version'` → `0.254.0`. The primary
checkout is on `fix/classify-provider-spend-limit-not-transient` at `0.310.0-nightly.2`,
so I read the pinned revision through `git show 8de661118:<path>` throughout rather than
from the working tree. The pinned tree is also checked out at
`/home/ubuntu/.worktrees/fabro/factory-integration`.

**The cited symbol.** `git show 8de661118:lib/components/fabro-acp/src/command.rs` →
`fatal: … exists on disk, but not in '8de661118'`. `git grep -n "shlex::split"
8de661118` → one hit, `lib/crates/fabro-acp/src/command.rs:38`. Read lines 1-60 and
60-185 of that file at the pin: `from_attrs` dispatches to `from_command_attr` or
`from_config_attr`; `from_command_attr` runs `shlex::split` then `AcpAgent::from_args`;
`parse_config_server` is a `serde_json` decode of an MCP stdio server object;
`shell_quote` uses `shlex::try_quote` with a manual `'\''` fallback.

**The env channel end to end.** `Cargo.toml:13` at the pin pins
`agent-client-protocol-tokio = "0.11.1"`; that crate's
`src/acp_agent.rs:392-442` consumes leading `KEY=value` tokens through `parse_env_var`
(`:447-461`), taking everything after the first `=` verbatim as the value, then treats
the first non-assignment token as the program. So the post-`shlex` token *is* what the
adapter's environment receives.

**The tokenizer, for real.** `Cargo.lock` at the pin gives `shlex 1.3.0`. I built a
throwaway crate with a path dependency on
`~/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/shlex-1.3.0` and ran
`cargo run --offline` on three inputs. Bare base string → 3 tokens, first is
`CODEX_CONFIG={approval_policy:never,sandbox_mode:danger-full-access}`. Quoted base
string → 3 tokens, first is `CODEX_CONFIG={"approval_policy":"never","sandbox_mode":"danger-full-access"}`.
Naive-wrap-with-apostrophe-in-model → `shlex::split -> None`. I also tokenized the real
rendered `review` string (B1) and got the byte-identical failing token. A Python
`shlex.split` cross-check agreed on the first two.

**The two renderers.** `codex_adapter()` at
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_fabro_argv.py:127-166`
and `CODEX_ADAPTER_BASE` at `:117-120`; `render_adapter()` at
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_acp_node_adapters.py:158-169`,
called from `_acp_node_layers.py:78`. `.livespec.jsonc:195-197` (`codex_models`, `pr`
only) and `:226-235` (`acp_nodes.review`). Rendered both paths: `render_adapter()` called
directly on the review env map, and the full three-layer resolution via
`_rendered_adapters(repo=_REPO_ROOT)` under `uv run --no-sync` (note: `mise exec --
python` fails here; `uv run` works).

**Spec surfaces.** `grep -rn "CODEX_CONFIG" SPECIFICATION/` (all files, live and
history) and `grep -n "codex-acp" SPECIFICATION/contracts.md SPECIFICATION/scenarios.md`
— the enumeration behind "three literals" and "no literal in the scenarios". Read
`contracts.md:3230-3345` (Codex pins section) and `:3354-3400` (§"ACP node adapter
configuration"), and `scenarios.md:2200-2253` (Scenarios 90 and 91) in full.

**Tests.** `grep -rn "CODEX_ADAPTER_BASE\|CODEX_CONFIG"` over `tests/`, then read
`tests/integration/test_codex_adapter_baked_path_scenarios90_91.py:40-200`.

**Ledger prior art.** `bd list --status all --limit 0 --json` under
`with-livespec-env.sh` → 814 items, filtered client-side on `CODEX_CONFIG` / `shlex` /
`tokeniz` / `codex-acp` / `JSON.parse` → 23 hits, of which `bd-ib-qulf` is the direct
match. Read it with plain `bd show bd-ib-qulf` (not `--json`, which carries no comments).

**Positive controls, per this repo's verification discipline.** The `CODEX_CONFIG` sweep
returned hits in `SPECIFICATION/history/v082/` and in five test files as well as the two
live spec files, so it could have surfaced a literal outside the three — it did not, and
that absence is informative. The `codex-acp` sweep returned nine `contracts.md` hits
including four non-literal prose mentions, so it was not keyed to the literal form. The
`parse_adapter_string` check in "What the proposal gets right" is a case where the probe
*could* have returned a hit and correctly did not; I read the regex rather than inferring
from the round-trip passing.

## WHAT I COULD NOT VERIFY

- **The factory-side measurements.** "five dead factory runs in two tenants, at two
  different stages and with three different configured models", and the claim that the
  process "exits 1 (NOT 127)". I did not query `hp`. `bd-ib-qulf` records **two** runs
  (`01M0YVK5KHMH`, `01M0YWEHW3F5`), both at the `review` node, both `gpt-5.6-terra` —
  which is narrower than the proposal's summary on all three axes. That is not a
  contradiction (the proposal may draw on later runs and on homelab), but the wider
  figure rests on evidence I did not see, and the ledger item is the only written source
  I could reach.
- **That the running host binary is `8de661118`.** I verified the fork branch tip and its
  Cargo version match the documented pin. I did not inspect the binary at
  `~/.fabro/bin/fabro` or query the factory for its build, so "the pinned host build runs
  this code" is established by documentation plus branch state, not by execution.
- **The `codex-acp` adapter's own source.** The `startAcpServer` /
  `dist/index.js:32872` frame in the traceback is inside the baked sandbox image, which I
  have no local copy of. That `JSON.parse` is called on the value is taken from the
  quoted traceback.
- **Fleet blast radius beyond this repo.** I did not read homelab's `.livespec.jsonc` or
  any other consumer's `acp_nodes` table, so "every repository consuming 0.82.0's Codex
  nodes" is uncorroborated here. It does bear on B1's remedy: quoting at
  `render_adapter()` fixes every consumer through the plugin release, whereas quoting
  only in `codex_adapter()` leaves each consumer's own `acp_nodes` table broken.
- **Whether the Codex leg reached the same findings.** By design, no coordination
  occurred.
