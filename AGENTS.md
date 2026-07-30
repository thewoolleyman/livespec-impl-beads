# Agent instructions

This file is the canonical agent-orientation surface for this repo;
`.claude/CLAUDE.md` is a symlink to it — never maintain a separate copy.
The sections through "Red-Green-Replay commit protocol" are the livespec
family-universal agent-instruction core (shared by every family member via
the impl-plugin template); repo-specific guidance is additive on top.

## Repository mutation protocol

Every repo change uses a worktree → PR → merge → cleanup path. Treat leaving
dirty state, committing on the primary checkout, or asking the user whether to
commit as failures of the workflow, not as acceptable stopping points.

1. Confirm the primary checkout before editing:

   ```bash
   git config --get livespec.primaryPath
   git status --short --branch
   ```

2. If the change will modify tracked files, create a dedicated worktree from the
   primary checkout's `master` and do all edits there. Every worktree lives under
   the per-user root `~/.worktrees/<repo>/<branch>` — NEVER as a peer of the
   clones under `/data/projects`, so the workspace holds only first-class clones:

   ```bash
   mise exec -- git worktree add -b <branch> "$HOME/.worktrees/livespec-orchestrator-beads-fabro/<branch>" master
   ```

   `just bootstrap` registers `~/.worktrees` as one of mise's
   `trusted_config_paths`, so a freshly created worktree's `.mise.toml` is
   auto-trusted and the first `mise exec` inside it never stalls on a "config not
   trusted" prompt.

3. Use `mise exec -- git commit ...` and `mise exec -- git push ...` so the
   mise-managed lefthook hooks actually run. Never pass `--no-verify`; if a hook
   fails, fix the cause or halt with the failure.
4. Open a PR, wait for required checks, and merge through the PR using the repo's
   rebase-merge discipline.
5. After merge, refresh the primary checkout to `origin/master`, remove the
   feature worktree, delete the local branch, and verify the primary checkout is
   clean on `master`.

Do not leave orphaned worktrees. If a session must stop before cleanup, record
the active worktree path, branch, PR, validation state, and next action in the
relevant handoff document.

## Agent prerequisites for plugin work

When investigating or changing anything related to the Claude Code plugin
installation, marketplace, or distribution, establish execution context FIRST —
do not assume how the system works:

1. Run `claude plugin marketplace list` to see which marketplaces are configured
   and whether they point to local files or remote repos. Changes to a local
   `marketplace.json` do NOT affect installs from a remote GitHub marketplace.
2. Trace where the actual install command fetches from (local vs remote) before
   changing anything, and verify your change affects that code path.
3. For remote marketplaces, push to GitHub then test; for local, use
   `/plugin marketplace add ./.claude-plugin/marketplace.json`. Never test local
   changes against a remote marketplace and assume they apply.

## Codex dogfooding (OpenAI Codex CLI/TUI)

This repo's `/livespec:*` and orchestrator surfaces can ALSO be dogfooded from
OpenAI Codex CLI/TUI, not just Claude Code. Unlike the Claude path (plugins
enabled PER PROJECT via a committed `.claude/settings.json`), Codex plugin
enablement is **HOST-WIDE**: each registration persists in `~/.codex/config.toml`
and applies to every project on the host. Codex offers no project-scoped plugin
enablement, so there is no committed-settings analogue for the Codex path.

Install the three plugins host-wide — livespec CORE (the artifact carrier that
ships the spec-side prose and wrappers), the `livespec-driver-codex` Codex Driver
(which supplies the `/livespec:*` operation surface over core's prose), and THIS
repo's own orchestrator plugin (whose name is declared in this repo's
`.claude-plugin/plugin.json` — e.g. `livespec-orchestrator-beads-fabro`,
`livespec-orchestrator-git-jsonl`; substitute it for `<orchestrator-plugin>`
below):

```bash
# livespec CORE (spec-side prose + wrappers; no skills of its own):
codex plugin marketplace add thewoolleyman/livespec
codex plugin add livespec@livespec

# The Codex Driver (supplies the spec-side /livespec:* operation surface):
codex plugin marketplace add thewoolleyman/livespec-driver-codex
codex plugin add livespec@livespec-driver-codex

# This repo's orchestrator plugin (ships its OWN cross-runtime Codex surface):
codex plugin marketplace add thewoolleyman/<orchestrator-plugin>
codex plugin add <orchestrator-plugin>@<orchestrator-plugin>
```

Once installed, Codex operations are driven via `codex exec` and NAME-selected as
`<plugin>:<op>` (e.g. `livespec:next`, `<orchestrator-plugin>:list-work-items`)
rather than as `/`-prefixed slash commands. The distributed Drivers resolve their
prose at runtime — no `AGENTS.md` skill→prose mapping is required. See
`livespec/SPECIFICATION/contracts.md` §"Plugin distribution" and
`livespec/SPECIFICATION/non-functional-requirements.md` §"Codex dogfooding
contracts" for the authoritative install and resolution contracts; each
orchestrator plugin's repository owns its own Codex Driver mapping. A temporary
local Codex marketplace registration used for testing MUST be removed afterward
unless you explicitly ask to keep it.

The Codex TUI picker displays skills by short name with the plugin as context.
In `/skills` → `List skills` (or the `@` picker), search `drive`; the
row renders as `drive (livespec-orchestrator-beads-fabro)` with kind
`Skill`. The colon-qualified form
`livespec-orchestrator-beads-fabro:drive` is still valid for prompt /
`codex exec` name selection and model-visible skill references, but it is not
the picker row operators should expect.

**A RAW `codex exec` invocation MUST redirect stdin from a source that reaches
EOF** — normally `< /dev/null` when the prompt is passed as an argument (or a
heredoc / file when using stdin-prompt mode). Never leave stdin inherited.
`codex exec` reads *additional* prompt text from stdin until EOF even when a
prompt argument is present (it prints `Reading additional input from stdin...`);
a background/detached or subagent-spawned call inherits an open **socket** that
never closes, so codex blocks on that read forever, before doing any work —
the process stays alive (a status check reports "running") while its output
never grows past that one line. A foreground call works only because it inherits
`/dev/null`. This trap hits ONLY raw `codex exec`; the plugin's own
`codex-companion.mjs` runtime spawns with `stdio: "ignore"` and is immune, so
prefer routing through the companion / `codex:codex-rescue`. When you must call
`codex exec` directly, use the redirect form, e.g.
`codex exec -s read-only -m gpt-5.5 "$(cat prompt.txt)" < /dev/null > out.log 2>&1`.
And NEVER treat "the process is alive" as proof of progress — verify the output
file is growing past the stdin line.

**The codex-companion runtime is patched to always run `danger-full-access`
(YOLO): full disk + network, no OS sandbox.** Upstream `openai/codex-plugin-cc`
hardcodes a restrictive sandbox on every plugin-launched thread (`read-only` /
`workspace-write`, both network-OFF), which silently cripples Codex reviews — an
adversarial review that cannot run `pytest`/`gh` passes code it never executed.
Upstream ships no toggle and has merged no fix (prior-art survey:
`plan/codex-yolo-sandbox/research.md`), so this repo self-carries a one-line
chokepoint rewrite in the plugin cache — `buildThreadParams` / `buildResumeParams`
in `lib/codex.mjs` resolve to `danger-full-access` — re-applied every session by
the distributed orchestrator plugin hook in `.claude-plugin/hooks/hooks.json`
(because a plugin refresh clobbers the cache).
To DOWNGRADE a single run, set `CODEX_COMPANION_SANDBOX` (e.g. `read-only` or
`workspace-write`) in the environment — that env var is the escape-hatch the
chokepoint honors. `~/.codex/config.toml` also carries
`sandbox_mode = "danger-full-access"` to cover the raw `codex exec` path.
Rationale, end-to-end proof, and the deferred fork / host-wide options are in
`plan/codex-yolo-sandbox/handoff.md`.

## Beads runtime prerequisites

This plugin's work-item store is a per-repo beads/Dolt TENANT on the shared
family dolt-server — NOT JSONL files. Installing the plugin does NOT provision
the backend; a clone connects to its tenant only when ALL of the following are
present:

- **`bd` CLI, pinned**, through the public lifecycle-guard entry point at
  `/usr/local/bin/bd`. This repo's mise config MUST NOT declare or install
  `bd`: an activated mise tool or regenerated shim can shadow that policy
  boundary. When `LIVESPEC_BD_PATH` is set it MUST point at
  `/usr/local/bin/bd`; otherwise `bd` on `PATH` MUST resolve there. Normal
  plugin, ledger, and operator calls MUST NOT invoke the guard's private
  delegate executable.
- **A running Dolt `sql-server`** reachable over **TCP `127.0.0.1:3307`**. Family
  tenants force TCP (not the unix socket); `.beads/config.yaml` carries `dolt.*`
  host/port keys with NO `socket` key.
- **The tenant password** in env as a single **bare `BEADS_DOLT_PASSWORD`** —
  injected by THIS project's configured env wrapper. A FAMILY tenant shares the
  one family password via the family 1Password Environment wrapper
  `with-livespec-env.sh` (canonical copy at
  `/data/projects/1password-env-wrapper/with-livespec-env.sh`); an INDEPENDENT
  (non-family) tenant injects its own tenant password from its own 1Password
  Environment via its own `with-<project>-env.sh` wrapper. Either way `bd`
  consumes the same bare var — there is NO per-tenant
  `BEADS_DOLT_PASSWORD_<tenant>` variable and NO per-tenant→bare mapping. Real
  isolation comes from the per-tenant SQL user + DB-scoped grant, not from
  password distinctness or wrapper identity. Secrets are probe-only — `printenv
  NAME | wc -c`, never echo values — and NEVER committed to `.livespec.jsonc` or
  `.beads/`.
- **The `.beads/` pointer files**: `config.yaml` (committed; the `dolt.*` server
  keys) and `metadata.json` (gitignored, regenerable). NEVER run `bd init` inside
  a primary checkout or worktree — it auto-commits and clobbers `.beads/`.

**Run beads commands from the target repo root.** Per-command `bd` resolves its
connection from the current directory's `.beads/config.yaml` (auto-discovery),
NOT from any resolved config object — so run from the intended repo's root, or
`bd` silently operates on the wrong tenant.

**An "Access denied" / "no beads database found" failure almost always means you
are running OUTSIDE the wrapper** (the bare `BEADS_DOLT_PASSWORD` is absent), not
that a secret is missing. Re-run under your project's configured env wrapper
(`with-<project>-env.sh`) -- `<command>`. Never hand-hunt the secret or reach
around the seam with raw `mysql` / `dolt` / `sudo`.

**`bd list --status open` matches NOTHING here.** This store holds livespec
lifecycle statuses — `backlog`, `ready`, `blocked`, `active`, `acceptance`,
`pending-approval`, `closed`. The beads-native `open` / `in_progress` names are
normalized away (`_NATIVE_STATUS_REMAP` in
`commands/_dispatcher_ledger_close.py` maps `open`→`backlog`,
`in_progress`→`active`), so a native-name filter silently returns an empty set
rather than erroring. To survey the ledger, list everything and filter
client-side: `bd list --limit 0 --json`.

**Query the ledger for prior art BEFORE designing a fix — reading the source is
not sufficient.** Scan every non-closed item for the defect class you are about to
design for, and read the FULL description of anything that overlaps: maintainer
rulings and explicitly rejected options are recorded there and are binding
context. **Include `acceptance` and `blocked` items, not just `backlog`** —
parked items are where shipped-but-unaccepted work hides, which is precisely what
a source-only reading cannot see. Treat each filed item as a claim with a
timestamp, not as fact; verify its specifics against the forge before relying on
them. (Cost of skipping this, 2026-07-26: the `dispatch-claim-liveness` thread
verified the code exhaustively, published two design recommendations to a durable
handoff on `master`, and had to retract both — `bd-ib-lza6` sat in `acceptance`
having already shipped the `reconcile-merged` valve that one recommendation would
have broken, and a filed item asserted a dispatch produced "no PR" when its PR had
in fact merged.)

## Host Fabro server (self-hosted dark factory)

The Dispatcher's host-direct path (`dispatcher.py loop` run on the host, NOT in
the orchestrator container) connects to a long-lived Fabro server on
**`127.0.0.1:32276`**. Installing the plugin does NOT start it; the maintainer
runs it directly from `~/.fabro/bin/fabro`. As of 2026-07-30 the host binary is
`fabro 0.254.0 (8de6611)`, built from **`factory-integration`** — the ONE standing
branch in our fork (`thewoolleyman/fabro`) that carries every fabro fix the
factory needs but upstream has not released (today: PR #568 credential refresh,
the env-configurable daemon-readiness timeout, PR #552 configurable checkpoint
git timeout, PR #576 OTLP export transport, the fork-local O1 worker-OTLP env
re-injection + O2 W3C-traceparent join that light that transport up for the Codex
era, the fork-local P2 that decouples OTLP export from `FABRO_LOG` so quieting
logs cannot silently zero telemetry, and the fork-local O4 `run_turn` ACP turn
span that makes per-turn command/stop-reason queryable).
Never pin a fabro build from any other branch, and never modernize the base: any
fabro ≥ 0.256 breaks `workflow.fabro` (fabro #474 de-templates `acp.command`, so
every dispatch dies `exit 127`). These rules are NORMATIVE — `SPECIFICATION/constraints.md`
§"Fabro runtime constraints" (ratified in `v035`). The build/pin/rollback commands are in
`orchestrator-image/README.md`. Rollout/revert state is ledger `bd-ib-2nq.4`; deferred
modernization is `bd-ib-6qu`.

- **Start / restart** (OAuth-only — no wrapper, no `ANTHROPIC_API_KEY`):

  ```bash
  ~/.fabro/bin/fabro server start --bind 127.0.0.1:32276 --no-web --no-upgrade-check
  ```

  It daemonizes. `--no-web`: the fork binary ships no bundled web-UI assets. The
  ~6s SlateDB store open exceeds stock 0.254's 5s daemon-readiness cap, so the
  fork makes it env-configurable — `FABRO_SERVER_START_READY_TIMEOUT_SECS`
  (default 60s); stock 0.254 would fail to start against this store.
- **OAuth-only posture — do NOT put `ANTHROPIC_API_KEY` in the SERVER env.** It
  bills API cost and can leak into the sandbox. The agent's model auth is
  `CLAUDE_CODE_OAUTH_TOKEN`, injected into the *sandbox* by the Dispatcher per
  dispatch. In `fabro doctor`, `[✗] LLM Providers (none configured)` is therefore
  CORRECT.
- **Credentials live in `~/.fabro/`** (the GitHub App integration from the vault;
  `auth.json`; the SlateDB `storage/`). `fabro doctor` should show GitHub App
  **configured**; if it is not, the server's vault did not load — do NOT "fix" it
  by adding `ANTHROPIC_API_KEY`.
- **Fleet-shared + Tailscale-served.** `tailscaled` holds a standing
  `tailscale serve` proxy `https://vps.perch-rudd.ts.net:32276 → 127.0.0.1:32276`;
  it persists across restarts and simply returns refused while the loopback
  backend is down. A `:32276` listener owned by `tailscaled` (not `fabro`) means
  the proxy is up but the server is not.
- **Never `pkill -f 'fabro server'`** — it self-matches the killing shell and can
  reap unrelated shells. Match real daemons via `/proc/<pid>/exe` and kill by PID.

## Daily commands

- `just bootstrap` — first-touch setup on a fresh clone; idempotently sets
  `livespec.primaryPath`, installs the canonical commit-refuse hook at
  `.git/hooks/pre-commit` + `.git/hooks/pre-push`, installs lefthook hooks, and
  resolves plugin dependencies.
- `just check` — the full enforcement aggregate (lint, types, tests, coverage,
  AST checks). It is the load-bearing safety net; it runs locally, in pre-push,
  and in CI.

## Revise co-edit discipline — `tests/heading-coverage.json`

Every revise pass that adds, changes, or removes a `## ` heading in any spec file
MUST update `tests/heading-coverage.json` in the same change (via the revise
`resulting_files[]` mechanism) so the heading-coverage map stays in lockstep with
the spec. Diff the proposed `## ` heading set against the current spec file's H2
set; add an entry (`test` MAY be the literal `"TODO"` with a non-empty `reason`)
for each new heading, and drop entries for removed headings.

## Red-Green-Replay commit protocol

Product `.py` changes are committed via a 2-step single-commit TDD ritual,
enforced by the `red_green_replay` commit-refuse hook (it inspects the staged
tree and writes `TDD-*` trailers). The final result is ONE commit carrying the
test, the impl, and both trailer sets.

1. **Red commit.** Stage the test file ALONE — no impl — and commit with a
   `fix:`/`feat:` subject. The hook runs pytest on the staged tree; the staged
   test MUST fail on pytest (non-zero exit). An `ImportError` or a collection
   error counts as a failure to the hook, BUT you SHOULD prefer a genuine
   assertion failure so Red proves the behavior is actually unimplemented
   rather than merely unimportable — see the new-module stub technique below.
   It records `TDD-Red-*` trailers (test path, failure reason, test-file
   checksum, output checksum, captured-at).
   - Gotcha: the impl must be UNMODIFIED on disk at the Red commit, because the
     hook's pytest reads the on-disk module. If the impl already carries the
     change the test passes, and the hook rejects with `test-passed-at-red`.
2. **Green amend.** Stage the impl and run `git commit --amend`. The hook sees
   the `TDD-Red-*` trailers + the staged impl, re-runs the SAME test (now
   passing), and records `TDD-Green-*` trailers. The test file bytes MUST be
   byte-identical across the Red→Green pair; to change the test, author a fresh
   Red commit.

### New-module stub technique (avoiding false reds)

When the impl module under test does NOT exist yet, the natural Red would be an
`ImportError` or a collection error rather than an assertion failure. The hook
accepts that as a failing Red, but it does not prove the behavior is
unimplemented — only that the module is unimportable. To make Red fail on a
genuine assertion instead:

1. At Red time, create the impl module as a minimal **stub** on disk — enough
   that the test imports and runs, but its assertion FAILS (e.g. a function
   that returns a wrong/sentinel value, or raises `NotImplementedError` only
   when that still yields an assertion failure rather than a collection error).
2. The stub must NOT make the test pass — a passing test at Red trips the
   hook's `test-passed-at-red` gate.
3. Then the **Green amend** replaces the stub with the real implementation that
   makes the assertion pass.

This keeps Red honest: it proves the behavior is unimplemented, not merely that
the module is missing.

### Execution gotchas

Three failure modes that cost dispatched agents real time:

1. **Multi-test-file Red.** The Red commit must stage EXACTLY ONE test file
   (zero impl). The commit-msg `red_green_replay` hook rejects more than one
   staged test file with `multi-test-file`, AND lefthook's pre-commit only takes
   the fast coverage-skip Red path when `test_count == 1 && impl_count == 0`
   (otherwise it runs full `just check` and fails at <100% coverage). When a
   change needs multiple new/changed test files, stage only ONE at Red (a genuine
   failing assertion), then add the remaining test files + the impl + ride-along
   docs at the Green `--amend`. (The old `LIVESPEC_PRECOMMIT_RED_MODE` env
   override is gone.)
2. **Preserve the Red trailer block at Green.** On the Green `git commit
   --amend`, do NOT pass a fresh `-m` that overwrites the message — that wipes the
   inline `TDD-Red-*` trailers the hook wrote at Red. For a commit that touches a
   PRODUCT-IMPL path, the pre-push *range* replay check greps the FINAL commit body
   for BOTH `TDD-Red-Test-File-Checksum:` AND `TDD-Green-Verified-At:`; if the Red
   block is gone, the push is rejected. Use `--amend --no-edit` (or re-include BOTH
   trailer blocks). The Red and Green test-file bytes must stay byte-identical.
   **SCOPE — do not read this clause as unconditional:**
   `red_green_replay._commit_violates` derives `product_paths` from the same
   `_IMPL_PREFIXES` tuple the commit-msg leg uses and returns early when that list
   is empty, so a commit touching NO product-impl `.py` is EXEMPT from the
   both-trailers requirement rather than passing it. A dangling Red block on such a
   commit is harmless. NEVER hand-forge a `TDD-Green-*` trailer to satisfy a check
   that cannot fire — read `_IMPL_PREFIXES` and confirm whether your paths are even
   in scope before concluding you are blocked.
3. **Working-tree gate, not just staged.** lefthook's pre-commit runs the
   structural / dev-tooling checks over the WORKING TREE, not only the staged set.
   So "revert only the impl for Red" is INSUFFICIENT when the change also ADDS
   files that a working-tree gate inspects (e.g. a new structural check that
   asserts certain dirs are absent, while you've already created those dirs on
   disk). At Red, make the WHOLE working tree master-consistent: move new
   untracked files aside (e.g. to scratch) and revert modified non-test files,
   leaving only the one staged test divergent; then restore everything for the
   Green `--amend`.

**Exempt:** changesets with no product `.py` (docs, spec, work-items, shell,
config) use `chore(...)` / `docs(...)` / `chore(spec):` subjects and skip the
ritual entirely. Always use `mise exec -- git ...` so the hooks fire; never
pass `--no-verify`.

## Working with the maintainer (repo-additive)

- **Spell out "Definition-of-Ready" in full** — the acronym "DoR" is BANNED
  (maintainer-declared 2026-07-04: non-intuitive, carries no meaning). Never
  use it in any prose, document, work-item, commit, or report; always write
  "Definition-of-Ready". (Quoting pre-existing text verbatim for mechanical
  replacement targeting is the only exception.)
- **Maintainer-facing documents must explain their own notation.** Define
  every symbol before or beside its first use (an arrow, a column, a tally),
  make headings match their content, and write complete sentences over
  compressed fragments.
- **Drive authorized work to completion; do not over-ask** (maintainer-declared
  2026-07-06). When the maintainer names a goal and says to finish or continue
  it ("get this entire track finished", "continue", "don't hold it"), execute
  the WHOLE arc — implement, dispatch, merge, iterate, archive — without pausing
  to confirm each already-authorized step. Ask ONLY for input the maintainer
  alone can give: irreversible/destructive actions, or genuinely ambiguous
  requirements that cannot be settled from the code, spec, or context. An
  operator-flow step that says "present options and let the user select" is
  satisfied by a standing directive once the goal is named — do not re-prompt.
  Surface real blockers and true judgment calls; drop routine "should I
  proceed?" confirmations. Default to acting, then reporting outcomes.
- **Revert decisively; do not diagnose first** (maintainer-declared
  2026-07-11). When something erroneously landed and the corrective action is
  already unambiguous (a throwaway/mistaken change on `master` that must be
  undone), execute the revert/undo IMMEDIATELY — do NOT first spend cycles
  investigating whether it is "really" broken or why. Diagnosis is warranted
  BEFORE acting only when it changes WHAT you do; when you already know the
  action, do it first (worktree → revert PR → merge) and diagnose only if it
  serves a follow-up. (Context: a throwaway proof dispatch auto-merged to
  `master` and a post-merge janitor reported a red check; the revert was the
  correct action regardless of the check result, so pausing to diagnose the
  red was wasted ceremony.)
- **Prefer factory dispatch for factory-safe work; do not default to
  hand-building it** (maintainer-declared 2026-07-15). When a work-item is
  factory-safe (in-repo, dispatchable Python/config — NOT outward-facing upstream
  fabro work), default to running it THROUGH the dark factory
  (`dispatcher.py dispatch --item <id>`), not implementing it in-session. Do NOT
  present the factory path as the heavier or less-preferred option — dogfooding the
  factory is the point ("we should be running things to the factory whenever we
  can"). The "it needs a Codex credential" objection is usually hollow: check
  `~/.fabro/bin/fabro ps` for an in-flight dispatch first; a running dispatch is
  live proof the credential works. The dispatcher self-wraps for credentials but
  often cannot reach the credstore alone — run it already inside
  `with-<project>-env.sh`. Hand-build only when the work is genuinely NOT
  factory-safe (outward-facing upstream fabro PRs, e.g. the codex-factory-telemetry
  O-track) or the maintainer explicitly asks. (Context: after re-planning the
  telemetry emitter, the factory-safe slice F1 was first offered as "hand-build
  (recommended) vs dispatch (heavier)"; the maintainer corrected that the
  factory-safe slice is exactly what should be dispatched.)
- **Name the OWNING SESSION when attributing work to another session**
  (maintainer-declared 2026-07-26). When you report that another session made a
  change — a dirty file, a live branch, an in-flight PR, a concurrent worktree —
  identify it by its **session name** (its `/rename` value), not merely by
  project directory or session UUID. The maintainer runs many concurrent
  sessions across the family and coordinates them BY NAME (the names are the
  tmux window names), so "a session in `livespec-console-beads-fabro`" is not
  actionable — it does not say which window to look at. Establish the name
  BEFORE asking any question whose answer depends on what that session is
  doing. Recover it by grepping the session transcript
  (`~/.claude/projects/<project-slug>/<session-id>.jsonl`) for
  `Session renamed to:` — a `type: system` / `subtype: local_command` record
  carrying the `/rename` args — and report it as `<session-name>` (project
  `<project>`, session `<uuid>`), leading with the name. (Context: a revise
  pass blocked on a stale-branch precondition tripped by another session's
  live branch; the options were presented without naming the owner, and the
  maintainer's reply was simply "you need to tell me the name of the session
  which is making this change." Naming it also resolved the block — that
  session's own transcript showed it had already merged the branch and had no
  intent to revise.)
- **Verify every changed path belongs to YOUR thread before you push**
  (maintainer-declared 2026-07-28). Run
  `mise exec -- git diff --name-only origin/master...<your-branch>` as a
  standing pre-push step — every time, not only when you suspect a problem —
  and confirm each path is one the thread you are working owns. Several
  sessions commit to `master` concurrently here, and each
  `plan/<topic>/handoff.md` is owned by its own thread, so "I only meant to
  edit ours" is not evidence. **If you believe your version of another
  thread's file says something theirs does not, do NOT resolve it by editing
  their file.** Drop it from your branch
  (`mise exec -- git checkout origin/master -- <path>`, then
  `--amend`), keep your own thread's edits, and report the difference to the
  maintainer to route to that thread — naming the owning session per the rule
  above. The maintainer's framing: "their thread's record is theirs to write,
  exactly as ours is ours" — the same principle as "never touch another
  session's worktrees or branches", one level up. (Context: a
  `plan/factory-hardening/` branch also carried that thread's
  `handoff.md` — now `plan/archive/dispatch-claim-liveness/handoff.md` — while
  it had PR #1098 open performing the same discharge edit; the collision was
  caught by the maintainer, not by the pushing session.)
- **Vet an escalation before spending the maintainer's attention on it**
  (maintainer-declared 2026-07-30). Before asking the maintainer a question,
  submit it to BOTH an Opus sub-agent and a Codex sub-agent and see whether they
  agree it is worth the maintainer's attention — or whether they can agree on an
  answer between themselves. Escalate only if that vetting supports it. **Why:**
  this is the operational teeth on "drive authorized work to completion; do not
  over-ask" above. It converts a judgment call about interrupting into a cheap,
  checkable procedure instead of leaving it to one agent's self-calibration.
  **How to apply:** spawn both vetters in ONE message so they run concurrently;
  give each the SAME tightly-framed brief — the verified facts, the concrete
  options with their costs, and the standing rules that bear on it; require a
  YES/NO first word plus an explicit "no fourth option" rather than an invented
  one; have them answer independently, and tell them a genuine split is more
  useful than agreement. Keep driving the conforming default while they run —
  vetting is never a reason to idle. This authorizes the Agent tool for THAT
  purpose specifically; it is not blanket permission to delegate ordinary work.
  - *Worked example, which is what proved the rule.* The
    `retire-host-dispatch-cap` thread's factory dispatch of `bd-ib-vmve.2` was
    refused by the very `host_dispatch_cap` guard it was deleting: two runs from
    OTHER repos held a cap of 2 while eight Fabro scheduler slots sat idle, so
    this repo was refused with zero runs of its own in flight. The candidate
    escalation offered three options — wait for a drain, transiently commit a key
    the spec ratified minutes earlier forbids, or hand-build the deletion against
    the handoff's factory-only mandate. Both vetters independently returned
    NO-do-not-interrupt, take the wait, and no fourth option; both also
    independently confirmed the fail-open prohibition below. The wait was
    correct — capacity freed after 38 minutes and the dispatch went green.
  - *Known limitation: this protocol can silently degrade to one leg.* In this
    harness the Opus sub-agent channel returned THREE empty idle notifications
    before it eventually answered, and the failure mode is the dangerous kind —
    an idle notification carrying NO CONTENT reads as completion rather than as
    failure. A protocol requiring two opinions therefore has a quiet path to
    running on one without announcing it. Treat a missing answer as a MISSING
    ANSWER: count it as absent rather than as assent, say so explicitly, and
    state how many legs actually reported when you cite the vetting. Silence is
    not agreement. A direct follow-up request is worth making before writing a
    leg off — in this instance that is what finally produced the answer.
  - *A fourth option WAS constructed and rejected; do not reinvent it.* The
    strongest candidate was to bump the cap in an UNCOMMITTED `.livespec.jsonc`
    inside a throwaway worktree, which clears the spec's literal "committed
    configuration key" wording. It is rejected: it is the commit-the-key option
    with the evidence removed — the same minutes bought, but leaving no diff a
    reviewer could ever see. Satisfying a rule's letter by making the violation
    invisible is not compliance.
  - *General principle: never defeat a live check to get past it — and note that
    blinding a check is WORSE than the honest violation, not a milder version of
    it.* A gauge that FAILS OPEN when it cannot observe its input is a standing
    temptation: blinding the input (an unresolvable binary, a doctored `PATH`,
    anything that makes the observation fail) converts a refusal into a pass
    instantly. That is worse than openly taking the forbidden option because it
    MANUFACTURES A COUNTERFEIT ENVIRONMENTAL FAULT — the record then reads as a
    genuine incident, so the one artifact a reviewer would use to reconstruct why
    the work proceeded has been falsified. Committing a forbidden key is at least
    legible in a diff; blinding a gauge lies in the journal. This holds even when
    the check is the very thing you are authorized to delete: removing a guard by
    the sanctioned path and evading it by engineering its blind spot are not the
    same act. If a fail-open warning appears on a retry you did not engineer,
    STOP and report it rather than riding the fail-open through. (The instance
    that motivated this — the dispatch admission mutex's `fabro ps` gauge, which
    proceeded "on the capacity-slot gauge alone" when `ps` was unobservable — was
    deleted with that mutex by `bd-ib-vmve.2` in `0eeca13`. The principle is
    recorded because fail-open checks recur, not because that gauge still
    exists.)

## Verification discipline (repo-additive)

Three rules from a 2026-07-28 three-way exchange between the
`dispatch-claim-liveness`, `console-happy-path-mvp` and `factory-hardening`
tracks, in which **three sessions independently reached confident wrong answers
on the same question in one day**. Each bad method produced a **confident wrong
answer rather than an obviously empty one**, which is why none self-announced.
Full account, with every measurement:
`plan/archive/dispatch-claim-liveness/handoff.md` §"THE THREE STANDING RULES".

Provenance, because a rule with a visible author is harder to dismiss:
`console-happy-path-mvp-supervisor` authored Rule 1's form and Rule 3's example;
`factory-hardening-supervisor` contributed Rule 2's sharper variant and caught
the third near-miss.

1. **Asserting an absence requires stating the scope searched.** "No call site",
   "no release", "no occurrence" — say what population you searched, and make it
   the whole workspace unless there is a reason it cannot be. If the check could
   not have returned the other answer, it is not evidence.
   *Worked example:* "no released build carries this fix" came from sampling two
   plugin caches that were **created before the fix commit existed**, so their
   lacking it was guaranteed and carried zero information. When the question is
   "was this released", ask `git tag --contains <sha>`.

2. **Verify the absence of the RIGHT token — a count is not a behavior test.**
   Pick a token that *cannot appear unless the behavior is there*, and say which
   token you chose and why.
   *Worked example:* a fork's `pr.md` was judged to lack a rebase-before-push fix
   because it contained 2 `rebase` mentions against our 6. **Both of its 2 were
   innocent** — a title, and a `gh pr merge --rebase --auto` arm — so six
   mentions in auto-merge context would have reported the fix PRESENT. The
   discriminating token was `fetch`: ours 2, theirs 0. **The count was
   directionally right and still not evidence.**
   - *Corollary — prefer a PROVENANCE question to any content probe.* Before
     grepping a file's contents for a fix, ask whether it *could* contain it:
     that same fork's `pr.md` had exactly ONE commit in its history, 18 days
     older than the fix. `git log -- <file>` has no wrong-answer failure mode.
   - *Corollary — search for a literal COPIED from the artifact*, never one
     reconstructed from memory. Four probes failed this way in one session
     (missing backticks; a line break inside a code block; another repo's
     invocation syntax; a `| head` that truncated the hits). **A verification
     that can only fail silently is not a verification.**

3. **An instruction can outlive the condition that made it correct.** The danger
   is not writing something false — it is writing something **true that stops
   being true while still reading as authoritative**, in the section a successor
   trusts *instead of* checking. A "do not re-derive this" list is the
   highest-risk place in any document for exactly that reason: date such entries
   and re-verify before quoting one.
   *Worked example:* "expect the stale-base refusal, apply the known recovery"
   was true while a worker ran a week-old plugin and false the moment it
   restarted — and it reached a merged handoff either way.

**Run these on your own work, not only on other people's.** Every instance above
was caught by a second signal disagreeing, never by the check announcing itself.
Passing a check you never ran is luck, not method.
