# Enemy Unit Tests for the Fabro dependency

## Why this thread exists

We are pinned to `fabro 0.254.0 (8de6611 2026-07-30)`, built from our fork's
standing `factory-integration` branch, because `SPECIFICATION/constraints.md`
§"Fabro runtime constraints" forbids modernizing past 0.256 (fabro #474
de-templates `acp.command`, which kills every dispatch with `exit 127`).
Deferred modernization is ledger item `bd-ib-6qu`.

The reason that pin is scary to move is not that fabro is unstable. It is that
**we have no executable statement of what we assume about fabro.** Our
assumptions are spread across argv builders, JSON field readers, stop-reason
string matching, and a workflow template — each one an unwritten contract that
an upgrade can break silently. Today the only way to discover a break is to
dispatch real work and watch it fail.

An **Enemy Unit Test** (Groboutils' term, from
<https://groboutils.sourceforge.net/testing-junit/art_eut.html>) is a test you
write against code you do *not* own, asserting the behavior you depend on. It
does not test our code; it tests the *dependency*, from our point of view. Run
the same suite against the old and the new version of the dependency and the
diff in results is exactly the upgrade risk. That is the pattern this thread
implements.

Notation used below: a "surface item" is one thing we call or parse. "Port"
means the thin facade we will introduce. "EUT" means Enemy Unit Test.

## What we actually depend on (inventory, verified 2026-08-19)

All paths are under
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/`.

### Invocation surface — argv we construct

Built in `commands/_dispatcher_fabro_argv.py`:

| Surface item | Builder | Notes |
| --- | --- | --- |
| `fabro run <workflow.toml> --goal-file <f> --input k=v … --no-upgrade-check` | `fabro_run_argv` | passes `acp_adapter`, `review_fix_visit_cap`, `merge_on_review_cap_outcome` as `--input` |
| `fabro auth login --dev-token <t> --server <url>` | `fabro_auth_login_argv` | |
| `fabro inspect <run-id> --json` | `fabro_inspect_argv` | |
| `fabro events <run-id> --json` | `fabro_events_argv` | liveness / watchdog source |
| `fabro ps -a --json` | `fabro_ps_argv` | run discovery, cost gate, stale sweep |
| `fabro rm -f <run-id>` | `fabro_rm_argv` | watchdog force-cancel |

A cross-cutting assumption is already documented in
`_fabro_server_suffix`: **`--server` is a per-subcommand flag, never
top-level** — `fabro --server <url> <cmd>` is a hard parse error on 0.254.0.
That is precisely the kind of claim an EUT should hold, because nothing but a
real invocation can confirm it still holds after an upgrade.

`FABRO_SERVER` is injected as environment rather than a flag by
`fabro_server_env`; that is a second, independent assumption about how the
server target is accepted.

### Parsing surface — JSON and text we read back

- `commands/_dispatcher_fabro_failure.py` — parses the structured failure
  block out of `fabro inspect --json`.
- `commands/_dispatcher_fabro_terminal.py` — maps a `fabro run` result to a
  terminal outcome; this is where stop-reason semantics live.
- `commands/_dispatcher_stale_run_sweep.py` — `_watchable_fabro_run` reads
  per-run records from `fabro ps -a --json`.
- `commands/_dispatcher_cost_gate.py` and `commands/_dispatcher_cost_wave.py`
  — read run records and token/cost telemetry from the same `ps` payload.
- `commands/_needs_attention_work_items.py` — its own `_watchable_fabro_run`
  reader over the same payload.
- `commands/_dispatcher_review_gate.py` — consumes the `fabro events` stream.

Four separate modules parse `fabro ps -a --json` records with four private
readers. That duplication is itself part of the problem: an upgrade that
renames one field has four independent places to break, and no single place
that declares what the record is supposed to contain.

### Resolution surface — where the binary and factory come from

`commands/_config.py`: `resolve_fabro_bin`, `resolve_fabro_factory`,
`resolve_fabro_sandbox_image`, `has_fabro_factory`, `has_fabro_factories`.
The binary resolves differently in the two deploy environments (host uses the
absolute `$HOME/.fabro/bin/fabro`; the orchestrator container uses
`/usr/local/bin/fabro` on `PATH`). This is the seam that makes a
*parameterized-over-binary* test suite natural: the resolution rule already
admits more than one binary path, so pointing the suite at a candidate build
is not a new concept, only a new caller.

### Prose / configuration surface

- `.claude-plugin/.fabro/workflows/implement-work-item/workflow.fabro` — the
  workflow definition, including the templated `acp.command` that fabro #474
  removes. This is the single most upgrade-fragile artifact we own.
- The `danger-full-access` sandbox chokepoint re-applied into the plugin cache
  each session (`AGENTS.md` §"Codex dogfooding"), which depends on
  `buildThreadParams` / `buildResumeParams` existing in `lib/codex.mjs`.
- The `FABRO_LOG` / OTLP export coupling that our fork-local P2 patch
  decouples.

### Useful fabro subcommands we do *not* currently use

`fabro --help` on 0.254.0 lists `validate`, `preflight`, `wait`, `ask`,
`version`, `doctor`, `settings`, `workflow`. Two matter for this thread:

- **`fabro validate <workflow>`** can check the workflow definition without
  executing anything. That gives us a fast, side-effect-free EUT for the
  `acp.command` templating contract — the exact thing that breaks at 0.256.
- **`fabro preflight`** validates run configuration without executing, which
  can cover much of the `run` argv contract without spending a dispatch.

This is significant for suite design: a large fraction of our assumptions can
be asserted **without launching a real workflow run**, which makes the suite
cheap enough to run on every upgrade candidate rather than only at ceremony
time.

## The gap

The existing seam in `_dispatcher_fabro_argv.py` is **argv-only**. It builds
command lines; it does not execute them, and it does not own the parsing of
what comes back. Execution and parsing are scattered across at least six
modules. Consequently:

1. There is no single object you could hand a different `fabro` binary and
   say "exercise everything we depend on."
2. Assumptions about response *shape* are asserted only incidentally, inside
   unit tests that use hand-written fixture JSON — fixtures that keep passing
   after the real fabro stops producing that shape. A fixture-backed test is
   the opposite of an Enemy Unit Test: it freezes our belief about the
   dependency instead of interrogating the dependency.
3. The upgrade decision therefore rests on reading fabro changelogs, which is
   how we got the 0.256 `exit 127` surprise in the first place.

## The shape of the fix

Two pieces, in order.

**1. A `FabroPort` facade.** One module that exposes only the operations above
— launch a run, log in, inspect a run, read a run's events, list runs, remove
a run, validate a workflow — as typed methods returning typed results. It owns
argv construction (absorbing `_dispatcher_fabro_argv.py`'s fabro half),
execution through the existing `CommandRunner` seam, and response parsing
(absorbing `_dispatcher_fabro_failure.py`, `_dispatcher_fabro_terminal.py`,
and the four private `ps`-record readers). Everything outside the port stops
knowing that fabro is a CLI at all. The port is constructed with a binary path
and a factory target, so pointing it at a candidate build is a constructor
argument.

Deliberately thin: if we do not use it, it is not on the port. `fabro fork`,
`rewind`, `steer`, `artifact`, `secret` and the rest stay off, because a
facade that mirrors the whole CLI would have to be re-verified wholesale on
every upgrade and would defeat the point.

**2. The Enemy Unit Test suite.** Tests that make real calls through the port
against a live fabro server, parameterized over `(binary path, expected
version)`. Green against `0.254.0`/`factory-integration` is the entry
condition — a suite that has never passed proves nothing. Then running it
against a candidate build turns "will the upgrade break us?" from a reading
exercise into a test result.

Design constraints that follow from this repo's rules:

- These are not `just check` tests. They need a live server on
  `127.0.0.1:32276`, real credentials, and in some cases a real run. They must
  be a separately-invoked suite so the hermetic aggregate stays hermetic and
  fast.
- Tests that require an actual dispatch cost real money and real time; the
  suite should be layered so the no-run tier (`validate`, `preflight`,
  `version`, `ps`, argv-parse-acceptance) can be run freely and the
  run-launching tier is opt-in.
- Assertions must target tokens that *cannot* be present unless the behavior
  is (per `AGENTS.md` §"Verification discipline" Rule 2). Asserting that
  `fabro ps --json` "returns JSON" is not an assumption test; asserting that
  each record carries the specific fields our four readers index into is.

## Open questions to settle before children are filed

1. Does the port absorb the janitor/PR/git argv builders that share
   `_dispatcher_fabro_argv.py`, or only the fabro half? (Leaning: only the
   fabro half — the janitor builders are `git`/`just`/`gh`, a different
   dependency.)
2. Which tier of EUT needs a real run, and can `fabro preflight` plus a
   deliberately trivial workflow substitute for a full dispatch?
3. Where does the candidate-build binary come from during a comparison run —
   a second checkout of the fork built to a scratch path, or a second
   installed prefix?
4. Does the suite assert against the *running server's* version as well as the
   client binary's? `fabro version` reports client and server separately, and
   our server is systemd-managed, so client-only parameterization may be
   testing half the upgrade.

## Relationship to existing threads and items

- `bd-ib-6qu` — deferred fabro modernization. This thread is the enabling
  work that makes that item decidable rather than speculative.
- `bd-ib-2nq.4` — fabro rollout/revert state for the current pin.
- `plan/fabro-otlp-telemetry`, `plan/fabro-token-refresh`, `plan/fabro-on-hp`
  — sibling fabro threads; each carries fork-local patches whose survival
  across an upgrade this suite would also cover.
