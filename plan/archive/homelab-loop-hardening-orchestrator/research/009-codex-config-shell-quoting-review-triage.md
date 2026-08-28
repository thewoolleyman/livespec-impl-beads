# 009 — codex-config-shell-quoting: adversarial review triage

Commissioned and triaged 2026-08-27 by the `homelab-loop-hardening-orchestrator`
session, resuming plan epic `bd-ib-ujihbw`. Same two-leg pattern as research/003 and
research/005: one Claude reviewer and one Codex reviewer, run concurrently against an
identical brief, with no coordination between them.

Reviews as delivered:

- `reviews/codex-config-shell-quoting-review-claude.md` — `do-not-ratify-as-written`,
  2 blockers, 4 majors, 5 minors.
- `reviews/codex-config-shell-quoting-review-codex.md` — `do-not-ratify-as-written`,
  2 blockers, 1 major, 1 minor.

Both legs reported. Neither was silent, so this triage rests on two opinions rather
than one.

## The convergence, which is what makes the blockers credible

The two legs were given the same brief and no channel to each other, and they landed
on the SAME two blockers from opposite directions. That is the signal worth recording:
a single reviewer finding a scope error is a claim, two independent reviewers finding
the identical scope error is a measurement.

**Blocker A — the proposal named the wrong renderer** (claude B1, codex Blocker 2).
The adapter string whose failure the proposal quotes verbatim — the `gpt-5.6-terra` /
`xhigh` review node — is not produced by `codex_adapter()` or `CODEX_ADAPTER_BASE` at
all. It is produced by `render_adapter()` in `commands/_acp_node_adapters.py` from this
repository's committed `.livespec.jsonc` `dispatcher.acp_nodes.review.env` table. Both
legs resolved the real adapters through the real three-layer merge to establish this;
the claude leg drove the repo's own
`test_codex_adapter_baked_path_scenarios90_91.py::_rendered_adapters` against the real
repo root, and the codex leg drove `resolve_acp_node_overlays` / `resolve_acp_nodes`
and the production renderer. Verified again first-hand during triage:
`_acp_node_adapters.py:168` builds its pairs as `f"{key}={adapter.env[key]}"`, with a
positive control confirming the file defines `render_adapter` (1 hit), so the probe
could have returned the opposite answer.

Consequence: implementing the follow-up exactly as it was written would have fixed the
`pr` node and left the node that actually died still rendering bare JSON. This is the
expensive kind of miss — the change would have merged, released, and appeared to work.

**Blocker B — the governing rendering contract was left unamended** (claude B2, codex
Blocker 1). §"ACP node adapter configuration" closes with "The rendered adapter string
MUST be exactly: the `env` pairs in sorted key order, then `command`, then `args` in
order, single-space separated", and the paragraph at `contracts.md:3249-3252` says an
adapter's declared `env` map is "rendered verbatim into the recorded adapter string".
Ratifying a quoting MUST in the Codex section alone would have left the specification
carrying two clauses in tension, with no normative answer to whether quoting is special
to `CODEX_CONFIG` or general to every env value.

## Dispositions

Every finding from both legs is accepted and repaired in place. Nothing was rejected.

| Finding | Leg | Disposition |
|---|---|---|
| Wrong renderer named in `impl_followup` | claude B1 / codex B2 | Repaired: follow-up now spans both renderers, requires a regression on the explicit-table path, and requires idempotence under re-render. |
| Governing rendering contract unamended | claude B2 / codex B1 | Repaired: the requirement now lands on §"ACP node adapter configuration" as a round-trip property of every env value, and the "rendered verbatim" sentence is amended to describe value fidelity. |
| Fabro citation is from the wrong revision | claude M1 / codex Major 1 | Repaired: repointed to `lib/crates/fabro-acp/src/command.rs:38` at commit `8de661118`, with `shlex 1.3.0` and its quote-removal test vector cited. |
| "shell-quoted" underspecified; naive wrap breaks on an apostrophe | claude M2 | Repaired: stated as the round-trip property, `shlex.quote` named, the naive-wrap failure mode recorded. |
| New MUST exercised by no scenario on the pinned path | claude M3 | Repaired: Scenario 90's first block gains one assertion; `scenarios.md` added to the target list. |
| `run_turn.command` rationale is false at the pin | claude M4 | Repaired: the appeal is withdrawn and the pre-existing gap recorded rather than glossed. |
| SCOPE misdescribes Scenario 90 | claude Minor 1 / codex Minor 1 | Repaired: SCOPE now says only Scenario 91 uses the un-pinned referent. |
| Byte-identity assertions are four, not one | claude Minor 2 | Repaired: follow-up says all four. |
| Beside-tests not enumerated | claude Minor 3 | Repaired: all five test files named. |
| Prior art `bd-ib-qulf` not cited | claude Minor 4 | Repaired: cited, with the note that the item carries the same scoping error and must be mirrored. |
| Only one of three literals shown as a diff | claude Minor 5 | Repaired: all three spelled out. |

## What the reviews did NOT overturn

The mechanism. Both legs reproduced it independently, the claude leg against the actual
Rust `shlex` 1.3.0 crate the pinned fork depends on. The rejected-alternative
characterization was checked in the pinned source by the codex leg and found fair. The
"three literal strings" count is complete. No scenario repeats a Codex adapter literal,
so the operative half of the original SCOPE conclusion survives.

## Instrument notes earned in this pass

- The first Codex leg **failed and still exited 0**: `gpt-5.6` is not available to this
  account, the run produced two `ERROR` lines and no review, and the harness reported
  exit code 0. Retried on the configured `gpt-5.6-sol`. A leg's exit status is not
  evidence that the leg ran.
- `grep -c ERROR` on the retry log returned 3, of which one was the word ERROR occurring
  inside the review's own prose. A count is not a verdict; the hits had to be read.
- The `bd-ib-qulf` prior-art claim came from a reviewer, so it was verified against the
  ledger before being written into the proposal rather than relayed on trust.

## Next action

One action: run the delegated `--only-topic codex-config-shell-quoting` revise pass to
cut v083, under the authority record already on this epic. The `--only-topic` narrowing
is load-bearing — `SPECIFICATION/proposed_changes/` holds four other threads' pending
proposals (`factory-headroom-preflight`, `wip-cap-bound-honesty`,
`wip-cap-naming-collision`, `dry-run-not-picked-reasons`) and a bare revise would
dispose them.
