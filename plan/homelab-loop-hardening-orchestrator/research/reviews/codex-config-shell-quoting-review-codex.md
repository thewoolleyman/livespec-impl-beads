VERDICT: do-not-ratify-as-written

## BLOCKERS

### 1. The proposal does not reconcile shell quoting with the ratified general `env` rendering contract

**Claim checked.** The proposal says the three Codex literals gain one pair of
single quotes and asks for prose only in the Codex-model-pin section. It treats
that as sufficient to define the new rendered bytes.

**Primary source checked.** `SPECIFICATION/contracts.md:3249-3252` says an
adapter's declared `env` map is "rendered verbatim into the recorded adapter
string." The governing `## ACP node adapter configuration` section at
`contracts.md:3362-3381` defines `env` as a table of string values rendered as
leading `KEY=value` pairs and says the rendered adapter string MUST be exactly
the sorted env pairs, command, and args. The proposal neither names that section
nor amends the existing "rendered verbatim" rule. A full-proposal search for the
copied phrase `rendered verbatim` returned no hit; as a positive control, the
same search instrument found four `shell-quoted` hits in the proposal, and the
target contracts file contains the exact heading `## ACP node adapter
configuration` at line 3354.

**What I measured.** For the unpinned case, the configured JSON value is exactly

```text
{"approval_policy":"never","sandbox_mode":"danger-full-access"}
```

while the proposed recorded assignment is exactly

```text
CODEX_CONFIG='{"approval_policy":"never","sandbox_mode":"danger-full-access"}'
```

The recorded string therefore contains two quote bytes that are not in the env
value. The new requirement and "rendered verbatim" cannot both be byte-literal
requirements as currently written. The general renderer contract also leaves an
implementer no normative answer to whether quoting is special to `CODEX_CONFIG`
or applies to every string-valued `env` entry that needs shell protection.

**Required before ratification.** Amend both the earlier "rendered verbatim"
sentence and `## ACP node adapter configuration` to define the shell-encoding
boundary and deterministic quoting rule. It is acceptable to make
`CODEX_CONFIG` an explicit special case, or to define correct quoting for all
env values, but the proposal must decide. Merely changing the three examples
leaves contradictory ratified rules.

### 2. The `impl_followup` misses the live `dispatcher.acp_nodes.*.env` rendering path

**Claim checked.** The frontmatter follow-up says to render `CODEX_CONFIG`
shell-quoted in `codex_adapter()` and `CODEX_ADAPTER_BASE` in
`commands/_dispatcher_fabro_argv.py`, and to update the beside tests. That is
presented as the implementation seam for the ratified change.

**Primary source checked.** The current repository config at
`.livespec.jsonc:226-233` routes the review node to Codex through an explicit
`dispatcher.acp_nodes.review` table whose `env` contains a raw `CODEX_CONFIG`
JSON value. That path bypasses `codex_adapter()`. It is materialized by
`_acp_node_layers.ResolvedAcpNode.rendered` and
`_acp_node_adapters.render_adapter()`; the latter currently emits
`f"{key}={adapter.env[key]}"` at
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_acp_node_adapters.py:168`.
Scenario 90 explicitly covers a node routed through the `dispatcher.acp_nodes`
table (`SPECIFICATION/scenarios.md:2227-2230`).

**What I measured.** I resolved the real committed workflow and this repository's
real `.livespec.jsonc` through `resolve_acp_node_overlays`,
`resolve_acp_nodes`, and the production renderer. The review adapter contained
this exact assignment:

```text
CODEX_CONFIG={"approval_policy":"never","model":"gpt-5.6-terra","model_reasoning_effort":"xhigh","sandbox_mode":"danger-full-access"}
```

After POSIX shell tokenization, the recovered value was exactly

```text
{approval_policy:never,model:gpt-5.6-terra,model_reasoning_effort:xhigh,sandbox_mode:danger-full-access}
```

and `json.loads` returned `JSONDecodeError: Expecting property name enclosed in
double quotes: line 1 column 2 (char 1)`. As a positive behavior control, the
proposal's exact quoted base

```text
CODEX_CONFIG='{"approval_policy":"never","sandbox_mode":"danger-full-access"}' INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp
```

tokenized back to
`{"approval_policy":"never","sandbox_mode":"danger-full-access"}` and parsed
successfully as a JSON object.

Changing only `codex_adapter()` and `CODEX_ADAPTER_BASE` cannot alter the
explicit-table path, so the follow-up as written would leave this repository's
Codex review node deterministically broken.

**Required before ratification.** Broaden the `impl_followup` to cover every
resolved `CODEX_CONFIG` env-map path, including the generic ACP adapter renderer
used by an explicit `dispatcher.acp_nodes` table. Require a regression that
exercises that table path and asserts that the post-tokenization value parses as
JSON, in addition to the shorthand/base and byte-identity checks. The follow-up
should also guard against double-quoting when a shorthand-rendered adapter is
parsed and rendered again.

## MAJORS

### 1. The Fabro source citation is not a citation to the pinned checkout as written

**Claim checked.** The proposal identifies
`lib/components/fabro-acp/src/command.rs:39` as the source in "the pinned fork."

**Primary source checked.** `/home/ubuntu/.local/bin/fabro --version` returned
`fabro 0.254.0 (8de6611 2026-07-30)`. Commit
`8de661118f24c43ad5b3516b9b7820525f5a5932` is reachable from
`origin/factory-integration`. However, `/data/projects/fabro` is checked out at
`3b37818887c8daf80bbb28fb6e30056a32b22db1` on
`fix/classify-provider-spend-limit-not-transient`, with workspace version
`0.310.0-nightly.2`; it does not correspond to the pinned build. The proposal's
path exists in that newer checkout and its `shlex::split` call is indeed line
39.

**What I measured.** At the binary-reported pinned commit, that path does not
exist. The corresponding source is
`lib/crates/fabro-acp/src/command.rs`; `shlex::split(trimmed)` is line 38 and
`AcpAgent::from_args(parts)` follows at lines 39-40. Per the review brief, I
treat the parenthetical citation as unverified as written rather than silently
substituting the newer checkout. Separately, inspecting the exact `8de6611`
Git object verifies the underlying mechanism. Its lockfile pins `shlex 1.3.0`,
whose own test vector maps the input bytes `foo"bar"baz` to `foobarbaz`, directly
confirming quote removal.

Correct the proposal to cite the pinned revision and its actual path/line. This
does not overturn the mechanism, but primary-source traceability is materially
wrong today.

## MINORS

### 1. The SCOPE paragraph overstates what Scenario 90 says

The proposal says "Scenarios 90 and 91 assert byte-identity against 'the
un-pinned base string'." Only Scenario 91 does so, at lines 2244 and 2252.
Scenario 90 asserts structural properties of the publish adapter and byte
identity of the *Claude default string* at line 2220. Correct the sentence to
say that neither scenario repeats the Codex literal and that Scenario 91 uses
the unpinned referent.

This is not the requested literal-repeat blocker. A search for the exact copied
literal opener `CODEX_CONFIG={` across all of `scenarios.md` returned no hit.
The positive control `CODEX_CONFIG` returned lines 2218, 2239, 2250, and 2251,
so the instrument was aimed at the correct file and could find the token. No
adapter literal is repeated in either Scenario 90 or 91.

## WHAT I VERIFIED AND HOW

- Read the proposed change in full with `sed -n '1,260p'` and verified its
  branch identity with `git status`, `git rev-parse`, and `git log`: worktree
  HEAD is `b2e660ed9bcb3bdf678f2c58dfecc136fcea259e`, with parent/master
  `ef71058c8e2a570dbbe026024f92fdadcc6bd87c`; the only commit diff is the new
  proposal file.
- Read `AGENTS.md` section `Verification discipline (repo-additive)` and applied
  scoped searches, copied tokens, positive controls, and `set -o pipefail` to
  the shell pipelines used in this review.
- Read the named contract region and the full general ACP adapter section with
  numbered lines: `contracts.md:3235-3455`.
- Read Scenarios 90 and 91 in full (`scenarios.md:2206-2253`). Ran
  `rg -F 'CODEX_CONFIG={'` over the whole scenarios file (no hit), then the
  positive control `rg -F 'CODEX_CONFIG'` (four hits), and searched the copied
  referent phrase `the un-pinned base string` (two hits, both in Scenario 91).
- Checked Fabro identity using `git -C /data/projects/fabro status`, `rev-parse`,
  `describe`, the current `Cargo.toml`, and
  `/home/ubuntu/.local/bin/fabro --version`. Used
  `git branch -r --contains 8de6611` to establish that the binary-reported commit
  is on `origin/factory-integration` despite the unrelated working checkout.
- Read the exact pinned source without switching revisions using
  `git show 8de6611:lib/crates/fabro-acp/src/command.rs`. It showed
  `shlex::split` before `AcpAgent::from_args`; the pinned lockfile showed
  `shlex 1.3.0`. Read that crate's local source and its quote-removal test
  vector.
- Checked the rejected alternative in the exact pinned source.
  `from_config_attr` trims and sends raw JSON directly to
  `parse_config_server`, which uses `serde_json` to construct an MCP stdio
  server; it does not call `shlex`. The pinned Fabro integration tests spell the
  alternative as `acp.config=<JSON>`, while `from_attrs` requires exactly one of
  `acp.command` and `acp.config`. The proposal's characterization is fair: using
  it would replace the current `acp.command` command-string representation and
  the workflow/input contracts built around that representation.
- Read `codex_adapter`, `CODEX_ADAPTER_BASE`, and all live `CODEX_CONFIG` uses
  with `rg`; read the byte assertions in
  `test_dispatcher_dual_cred.py`,
  `test_dispatcher_codex_pins_and_provider_limits_scenarios64_65.py`, and
  `test_codex_adapter_baked_path_scenarios90_91.py`. The empty-model
  byte-identity assertion exists at `test_dispatcher_dual_cred.py:790-800` and
  again at the integration level at
  `test_codex_adapter_baked_path_scenarios90_91.py:174-187`.
- Read `_acp_node_adapters.py`, `_acp_node_layers.py`,
  `_acp_node_repository.py`, and this repository's committed `acp_nodes.review`
  table. Ran a read-only `uv run --no-sync` Python probe with bytecode writing
  disabled to resolve the actual review adapter, tokenize it, and parse the
  recovered value. The bare form failed; the exact proposed quoted base passed.
- Read
  `plan/homelab-loop-hardening-orchestrator/research/reviews/phase2-proposals-review-codex.md`
  for review-shape precedent, without adopting its findings.
- Re-ran `git status --short --branch` in the primary repository, the proposal
  worktree, and `/data/projects/fabro` after all checks. All three retained their
  original clean state.

## WHAT I COULD NOT VERIFY

- I did not inspect the five dead factory-run artifacts cited in Motivation, so
  the exact run count, tenant count, stage distribution, and pasted
  `codex-acp` stack trace remain unverified by this leg. The failure mechanism
  itself was independently verified from pinned source and local tokenization.
- I did not execute `AcpProcessSpec::from_command_attr` from a build produced at
  `8de6611`; doing so would have required creating/building a matching checkout.
  I instead inspected the exact pinned Git object, its exact pinned `shlex`
  dependency source, Fabro's pinned env-assignment unit test, and a compatible
  local POSIX-tokenization probe.
- I did not query a separate remote factory host or daemon. Build identity was
  established from the installed local binary's self-reported
  `0.254.0 (8de6611)` and Git reachability from `origin/factory-integration`.
- The installed Codex `livespec:critique` binding could not resolve its required
  `livespec@livespec` core prose, so I could not run the packaged critique
  wrapper. I performed the requested adversarial checks directly against the
  named repository sources and recorded the limitation rather than substituting
  an unverified core path.
