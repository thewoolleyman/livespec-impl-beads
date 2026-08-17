# fabro-on-hp — initial research

## Goal

Provision a fabro dark-factory server on the newly-provisioned
`hp-xubuntu` host (Tailscale: `100.68.193.50`, untagged, owner
`thewoolleyman@`) and make it available as a SECOND dispatch/build
factory, consumable through the `dispatcher.factories` mechanism
shipped by `multi-factory-support` (epic `bd-ib-hvmbxd`, PRs
#1398/#1403/#1405/#1414/#1417, plus the fleet default-factory rollout
`bd-ib-ja3j5s` -> #1426/#33/#9).

## What's already solved (the consuming side) -- do not re-derive

The orchestrator can ALREADY target an arbitrary fabro server once one
exists and is reachable:

- `.livespec.jsonc` `dispatcher.factories.<name>.server` +
  `dispatcher.default_factory`, resolved by
  `commands/_config.py::resolve_fabro_factory` (env
  `LIVESPEC_FABRO_FACTORY` > CLI `--factory` > config > implicit
  loopback default).
- `dispatcher.py dispatch --item <id> --factory <name>` threads the
  resolved `server` into `--server`/`FABRO_SERVER` on every `fabro`
  CLI call (`commands/_dispatcher_fabro_argv.py`).
- Per-factory dev-token auth is REAL, not just plumbed: a resolved
  `FABRO_DEV_TOKEN__<factory-name>` env value flows through
  `DispatchPlan.fabro_factory_dev_token` and
  `run_fabro_factory_auth_login()` (`commands/_dispatcher_engine.py`,
  `_dispatcher_io_fabro_launcher.py`) actually runs `fabro auth login
  --server <url> --dev-token <token>` before `fabro run`.
- Ledger-recorded factory selection: which factory a dispatch used is
  recorded on the work-item so retries reuse it
  (`_store_dispatch_factory.py`, `_dispatcher_factory_ledger.py`).

So THIS thread is entirely about the supply side: standing up a real,
reachable, credentialed fabro server on hp-xubuntu, then adding one
`dispatcher.factories` entry (e.g. `"hp": {"server":
"https://hp-xubuntu.perch-rudd.ts.net:32276"}`) to opt a repo/dispatch
into it. No further orchestrator-side code should be needed for the
happy path.

## Bring-up runbook (from the existing vps host, `vps-info/services/fabro-server/`) -- mostly host-agnostic

Verified live against the CURRENT files on 2026-08-16 (README.md,
fabro-server.service, install.sh, fabro-server-verify-web):

1. Build the pinned fork: `thewoolleyman/fabro` branch
   `factory-integration` ONLY (fabro >=0.256 breaks `workflow.fabro`,
   per SPECIFICATION/constraints.md). `cargo clean --release -p
   fabro-spa && cargo dev build --release -p fabro-cli` (targeted
   clean required, plain `cargo build` does not refresh the embedded
   SPA assets).
2. Install the built binary at `~/.fabro/bin/fabro` on hp-xubuntu.
3. Populate `~/.fabro/storage/server.env` (mode 0600) with
   `SESSION_SECRET` + `FABRO_DEV_TOKEN` (Fabro generates these itself
   on first browser-auth run -- `install.sh` requires them present,
   does not create them).
4. `fabro-server.service` (systemd unit): needs exactly TWO per-host
   edits from the vps copy -- `WorkingDirectory=` (currently
   `/data/projects/livespec-orchestrator-beads-fabro`; needs a stable
   PRIMARY checkout path on hp-xubuntu, not a worktree) and the
   hardcoded cwd-assertion string in `install.sh`'s
   `start_and_verify()` (`[[ "${cwd}" ==
   "/data/projects/livespec-orchestrator-beads-fabro" ]]`) must match.
   `fabro-server-verify-web` is ALREADY host-agnostic --
   `FABRO_BASE_URL`/`FABRO_CANONICAL_HOST` are overridable env vars,
   no edit needed there.
5. `sudo install.sh`: root check, binary/env preflight
   (`SESSION_SECRET`/`FABRO_DEV_TOKEN` present, binary executable),
   refuses to interrupt an active run, migrates/stops any legacy
   self-daemon by verified PID+inode match, installs the unit,
   `systemctl enable/restart`, then verifies via
   `fabro-server-verify-web` AND asserts the running process's `cwd`
   matches the expected path.
6. Tailscale reachability: `tailscale serve https://hp-xubuntu.<tailnet>:32276
   -> 127.0.0.1:32276`, run ON hp-xubuntu itself (per-node local
   `tailscaled` state, not something settable remotely). Current vps
   pattern (`tailscale serve status`): tailnet-only (not funneled to
   the public internet), matches "full access from VPS" / same-tailnet
   framing.

## What is NOT yet known / blocks immediate execution

**Blocker #1 -- no shell access to hp-xubuntu yet.** Confirmed live,
2026-08-16: `tailscale ping hp-xubuntu` succeeds (network-layer
reachable, 29ms via direct connection) but BOTH `ssh hp-xubuntu`
(port 22, connection refused) and `tailscale ssh hp-xubuntu` (502 Bad
Gateway / connection refused) fail. hp-xubuntu's sshd is not running/
listening and Tailscale SSH is not enabled on its side. Nothing past
this point can be verified or executed remotely until SOME shell
access exists -- either the maintainer enables one of these on
hp-xubuntu directly, or provides another access path (console,
cloud-init, etc). This is the first concrete action item.

**Unknowns once shell access exists (need live inspection, not
assumption):**
- OS/toolchain baseline: Ubuntu version, whether Rust/cargo, Docker,
  `mise`, `just`, `gh`, `jq`, `curl` are already present (needed for
  the fabro build + install.sh + the sandbox's own docker runtime for
  running dispatched work).
- Disk/CPU/RAM sizing vs the vps host's `cpu: 4, memory: 8GB` sandbox
  resource plan (`fabro inspect` showed this per-run) -- confirm
  hp-xubuntu can sustain at least one concurrent sandboxed dispatch.
- Whether `docker` (the sandbox provider fabro uses,
  `environment.provider: docker` per a live run's `run_spec`) is
  installed/usable, and whether the same
  `ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-agent-v1.24.0`
  image pulls cleanly there.

**Credential/identity decisions -- need the maintainer's call, not
assumed:**
- GitHub App reuse vs separate installation: the vps fabro server's
  `settings.toml` names `app_id = "3668528"` (`[server.integrations.
  github] strategy = "app"`) -- confirmed live. Reusing the SAME App
  installation (its private key material, however it's currently
  sourced into the vps's fabro vault) on hp-xubuntu is the natural
  default -- a GitHub App install is repo-scoped, not host-scoped --
  but the private key needs to reach hp-xubuntu through SOME secure
  channel (1Password Environment injection, matching this fleet's
  existing pattern, is the presumed answer but unverified: need to
  find where/how the vps's fabro GitHub App credential is actually
  sourced today before replicating it).
- Dev-token / OAuth: server.env's `FABRO_DEV_TOKEN` is
  server-generated per-install (not shared) -- hp-xubuntu gets its own,
  which is what a client then supplies via
  `FABRO_DEV_TOKEN__<factory-name>` to `fabro auth login`. No
  cross-host sharing needed here, this part is already
  host-independent by design.
- OAuth-only posture (no `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` in the
  server env) must hold on hp-xubuntu too, per the same fleet
  constraint.

## Scope not yet cut

No scope event recorded yet -- this is still open research. Once shell
access to hp-xubuntu exists and the toolchain/credential unknowns above
are resolved (or explicitly deferred), the next planning pass should
record requirement carriers (bring-up steps in scope) and explicit
deferrals (e.g. funnel/public exposure, HA/failover, non-Tailscale
access) before any implementation child work-item is filed.
