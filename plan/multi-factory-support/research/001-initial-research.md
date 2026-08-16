# Multi-factory support — initial research

## Problem

The Dispatcher (`dispatcher.py`) shells out locally to a `fabro` CLI
binary and never sets `--server` / `FABRO_SERVER`, so every dispatch
resolves against whatever `[cli.target]` is configured in the invoking
machine's `~/.fabro/settings.toml` — today, hardcoded to
`http://127.0.0.1:32276` per `SPECIFICATION/constraints.md` §"Fabro
runtime constraints". There is no config surface, env var, or CLI flag
in this repo that lets a single repo route different dispatches to
different fabro hosts.

## What fabro itself already supports (confirmed, not a gap)

Both our pinned fork (`thewoolleyman/fabro`, branch
`factory-integration`, 0.254.0 `8de6611`) and current upstream
(`fabro-sh/fabro`) support genuine remote dispatch at the CLI level:

- `fabro run` (and other subcommands) accept `--server <url>` or the
  `FABRO_SERVER` env var, overriding the `settings.toml` default
  per-invocation — no config-file edit required.
- The server side already advertises a Tailscale-reachable API URL
  (`[server.api] url = "https://vps.perch-rudd.ts.net:32276/api/v1"`)
  and supports `dev-token` bearer auth or GitHub OAuth session-cookie
  auth. fabro does not terminate TLS itself; it expects a reverse
  proxy in front (satisfied today by `tailscale serve`).
- None of this is fork-specific — it's unmodified upstream CLI
  plumbing, so nothing here is at risk from the fork's divergence.

So the remote-dispatch protocol and its auth already exist and are
proven reachable. The gap is entirely in the orchestrator's dispatch
call site, which never threads a target through.

## Bringing up a second host (prior art)

A written, largely reusable runbook already exists for the *existing*
host: `/data/projects/vps-info/services/fabro-server/README.md` +
`install.sh` + `fabro-server.service`. Steps (see prior research,
2026-08-15):

1. Build the pinned fork (`factory-integration` branch only — fabro
   ≥0.256 breaks `workflow.fabro`): `cargo clean --release -p
   fabro-spa && cargo dev build --release -p fabro-cli`.
2. Install the binary at `~/.fabro/bin/fabro` (systemd unit's
   readiness check hits `/login` + its JS bundle).
3. Credentials: `~/.fabro/storage/server.env` (0600) needs
   `SESSION_SECRET` + `FABRO_DEV_TOKEN`; GitHub App integration under
   `~/.fabro/`. OAuth-only — never put an LLM provider API key in the
   server env.
4. systemd unit (`fabro-server.service`), bound to
   `127.0.0.1:32276`, `Restart=always`.
5. `sudo install.sh` — root check, binary/env preflight, safe
   self-daemon migration, unit install, web-console verification.
   Only host-specific bits: `WorkingDirectory` project path and a
   cwd-assertion in the verify step.
6. Tailscale (`tailscaled` + `tailscale serve
   https://<host>.<tailnet>:32276 → 127.0.0.1:32276`) for remote
   reachability — each host gets its own node/URL.

## Sketch of an orchestrator-side design (not yet agreed)

Layered surface mirroring the existing `dispatcher.fabro_bin` /
`LIVESPEC_FABRO_BIN` pattern in
`livespec_orchestrator_beads_fabro/commands/_config.py`:

1. `.livespec.jsonc` `dispatcher.factories` map: named factory ->
   `{server, ...}`, plus `dispatcher.default_factory`. Credentials
   NOT in this checked-in file — resolved from an env var by
   convention (e.g. `FABRO_DEV_TOKEN__<factory-name>`), injected by
   the project's env wrapper the same way `BEADS_DOLT_PASSWORD` is
   today.
2. `LIVESPEC_FABRO_FACTORY` env override, same shape as
   `LIVESPEC_FABRO_BIN`, shifting the ambient default for a session.
3. Per-dispatch selection: `dispatcher.py dispatch --item <id>
   --factory <name>`, resolving to the configured `server` + token
   and setting `--server`/`FABRO_SERVER` on the `fabro run` invocation
   `dispatcher.py` already makes.

## Open design question — where factory choice is recorded

Ledger record, not just a CLI arg at dispatch time. A CLI-only record
disappears after the dispatch call returns; a ledger field on the
work-item (or a dispatch-record comment) makes `bd list` / `next`
surface which factory ran a given dispatch, and lets retry/re-dispatch
reuse the same target automatically. This mirrors how this repo
already treats dispatch state as durable (ledger-held, not
filesystem-shadowed) elsewhere in the plugin. Decided per maintainer
direction 2026-08-15: record factory selection on the ledger, not only
as a transient CLI argument.

## Scope not yet cut

No scope event has been recorded yet (requirement carriers / explicit
deferrals). That is Step 3's next action before any implementation
child work-item is filed.

## Regression shipped by this epic, found and fixed 2026-08-16 — bd-ib-1g01

Full account: comment on `bd-ib-hvmbxd` dated 2026-08-16 (debug-fabro
session). Summary for anyone reading this research file cold:

The child `bd-ib-dje2ae` ("thread `--factory` selection into
`dispatcher.py`'s fabro invocation", merged as `ebfc523c`) added
`_fabro_command_prefix()` in `_dispatcher_fabro_argv.py`, which places
`--server <url>` BEFORE the subcommand for every fabro invocation
(`run`/`inspect`/`events`/`ps`/`rm`) whenever a factory server resolves
to non-`None`. The pinned fabro CLI (0.254.0) only accepts `--server`
as a per-subcommand flag — `fabro --server <url> run ...` is a hard
clap parse error; `fabro run ... --server <url>` works. Because
`_dispatcher_loop.py` resolves a non-`None` factory server for
ORDINARY local dispatches by default (not only explicit `--factory`
selections — this violated this thread's own "single-repo repos see no
behavior change" requirement carrier), this broke **every** factory
dispatch on this host from 2026-08-15 until the fix landed. The
2026-08-15T23:22 independent completeness review did not catch it
because it reviewed the diff and the credential-wiring gap, not a live
`fabro` CLI invocation.

Fixed by `bd-ib-1g01` → PR #1430 (merged `6de3a8a1`): every
`_dispatcher_fabro_argv` function now appends `--server <url>` after
its own subcommand token.

**Before archiving this epic or dispatching the fleet-wide follow-on
`bd-ib-ja3j5s`:** verify a live `drive.py`/`dispatcher.py` dispatch
against a real factory target produces an actual `fabro_run_id`
post-fix, and consider adding a smoke test that exercises the built
argv against the REAL installed fabro CLI's arg parser (not just
comparing the argv list to a hand-written expected list) — a
list-equality unit test alone did not, and structurally cannot, catch
a CLI-shape mismatch like this one.
