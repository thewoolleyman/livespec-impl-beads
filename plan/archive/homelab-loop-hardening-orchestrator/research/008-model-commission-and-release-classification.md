# 008 — The model commission (items A, B, C) and the release classification of item A

Written 2026-08-26 by the homelab-loop-hardening-orchestrator session that
resumed this plan from its ledger timeline. Ledger-held state (handoff entries
16 and 17 and the second scope event on `bd-ib-ujihbw`) is authoritative for
status; this note records the reasoning that does not belong in a comment.

## The commission

Relayed verbatim through the homelab `steady-state-loop-hardening` session on
2026-08-26 between 04:05Z and 04:40Z, as a scoped extension of the
`bd-ib-1mjt` stand-down lift for this track:

- **Item A, `bd-ib-rcl7`.** "Set the implementer default to opus 5 fleet
  wide ... ASAP to unblock things", then "switch to opus as default ASAP
  before tackling the configuration. Two separate work items."
- **Item B, `bd-ib-tsna`.** Every node's model, provider and adapter as
  configuration "at all the levels possible — fabro config, livespec config
  (per repo) and per-dispatch overridable", generically supporting any model
  behind any provider protocol, with `/data/projects/local-llm` as the worked
  example. The maintainer explicitly withdrew a relay's five added constraints
  (network reachability, credential projection, context caps, desktop
  capacity, model aliases): "STOP. That is overdesigning it." The item's
  second comment supersedes its first for that reason.
- **Item C, `bd-ib-cnkf`.** Per-node timeouts configurable with a 30-minute
  default, plus the explanation of the "20-minute limit": there is no such
  timeout; the sub-20-minute rule was the wall-clock proxy for a Codex
  gpt-5.5/low turn reaching the remote-compaction endpoint that returns 404
  (`bd-ib-ihp5`). Research on the pinned Fabro 0.254 build shows a templated
  `timeout` attribute silently becomes *no* timeout (the DSL parser types a
  quoted duration at parse time and template expansion never re-types a
  rendered string), so the Dispatcher must write literal durations into its
  self-contained dispatch payload. That finding is the rider on `bd-ib-cnkf`.

## Why item A was a spec change first

`SPECIFICATION/contracts.md` §"Codex ACP node model pins" bound the
implementer default to the literal Codex adapter string with `gpt-5.5`/`low`
and promised that a reader can predict the rendered string from the section
alone. Flipping the default is therefore an amendment before it is code:
proposal `implementer-default-claude-opus-5` (PR #1882) was ratified as
**v080** (PR #1883) through the delegated revise with an independent `sonnet`
ratification review (`NO BLOCKERS`), and `bd-ib-rcl7` implemented it (PR
#1884, master `4db2ec47`).

## Why the release of item A is a MINOR bump, not a patch

The factory committed item A as `fix: switch implementer default adapter`,
and release-please computed **0.78.1**. That number is wrong for what landed,
and the maintainer's conclusion-over-proxy doctrine says to read it rather than
trust it. The change flips the fleet-wide implementer for every repository
that dispatches through this plugin from Codex `gpt-5.5` to Claude Opus 5 — a
new default behaviour ratified as a specification modification, not a repair
of a defect. Under conventional commits that is `feat`-class, which is a minor
bump. The export-inventory check passes it legitimately because `__all__` did
not change; that is the documented honest limit of that check, not a false
negative. This note's commit therefore carries a `Release-As: 0.79.0` footer
so release-please retitles the pending release pull request, and homelab pins
its consumption to `v0.79.0`.

The verification still owed on `bd-ib-rcl7` after that release: the first
dispatch that runs on the Opus implementer must have its run transcript checked
for the resolved model, because earlier `claude-agent-acp` versions ignored
`ANTHROPIC_MODEL` and silently ran a smaller model. The result is recorded on
the item, not assumed.
