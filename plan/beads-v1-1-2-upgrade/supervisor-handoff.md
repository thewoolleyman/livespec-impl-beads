# Supervisor Handoff - beads-v1-1-2-upgrade

## Shared Protocol

Read `.ai/supervisor-protocol.md` before driving. Validate this binder together
with that shared layer; neither layer is complete by itself.

Regeneration must preserve both Corrections sections byte-for-byte:

- `.ai/supervisor-protocol.md` `## Corrections` for role-level corrections.
- This binder's `## Corrections` for thread-specific corrections.

Preserve spelling, punctuation, code formatting, blank lines, and ordering
exactly. The `Restart checkpoint` below is the one exception to the normal rule
that live thread state stays out of this binder: Overseer restarts this session
with only this file, so every wind-down must replace that checkpoint with the
latest durable state. Re-measure its timestamped claims before acting.

The marker is APPEND-ONLY and corrections land at its END, so a head-only read
is the worst possible cut: it can hand you an open obligation whose retraction
sits below the cut. Read it whole when it is short, and head-plus-tail with an
explicit truncation notice when it is not — never a bare fixed cap, which no
constant survives (one was written at 220 lines against a file that reached 528,
then 697 within hours).

```sh
supervisor_marker="/data/projects/livespec-orchestrator-beads-fabro/tmp/overseer/beads-v1-1-2-upgrade/.supervisor-state"
[ -n "${supervisor_marker:-}" ] \
  || { echo "HALT: supervisor_marker is unset or empty"; echo "REMEDY: bind it from the Bindings table before reading it — 'test ! -f \"\"' is TRUE, so an unset binding prints nothing and exits 0"; exit 1; }
test -f ".ai/supervisor-protocol.md" \
  || { echo "HALT: missing shared supervisor protocol .ai/supervisor-protocol.md"; echo "REMEDY: regenerate the two-layer supervisor handoff before driving"; exit 1; }
printf '%s\n' "BOOT: read .ai/supervisor-protocol.md, this binder, and the supervisor marker if it exists"
if [ -f "$supervisor_marker" ]; then
  marker_lines=$(wc -l < "$supervisor_marker")
  if [ "$marker_lines" -le 200 ]; then
    cat "$supervisor_marker"
  else
    sed -n '1,120p' "$supervisor_marker"
    printf 'TRUNCATED: lines 121-%d of %d NOT SHOWN; the last 80 follow\n' "$((marker_lines - 80))" "$marker_lines"
    tail -80 "$supervisor_marker"
  fi
fi
```

## Restart checkpoint

This checkpoint was written at `2026-08-03T04:30:48Z` for the next fresh
`beads-v1-1-2-upgrade-supervisor` session. No command or worker process from the
supervisor remains in flight.

Completed and cleaned up:

- Guarded-image code landed through PR #1221. The exact reviewed head was
  `54342d6b112c2e3c08ab8e0e3d41634dd69c10d6`; the rebase-merge is
  `976caf9744b8a6c1159434da8f2102081935f419`.
- The exact head passed the full foreground gate and all 95 forge checks. The
  sanctioned `dispatcher.py reconcile-merged` valve then passed its fresh
  post-merge janitor gate.
- The guarded-image code item `bd-ib-1rz6` is closed with PR and merge audit
  evidence. Its feature worktree, local branch, remote branch, and stale
  tracking ref are absent.
- The separate attended proof item `bd-ib-dwv` remains unassigned in `backlog`
  with `factory-safety:needs-privileged-host`; its code prerequisite is closed.
  It has not been built, run, inspected, tagged, loaded, pushed, or closed.
- At wind-down, the primary checkout was clean and equal to origin and GitHub
  master at `c3d41a53e5e5458617d182d52d705b731abb4786`; the guarded-image merge is
  an ancestor. The public guarded Beads command still reported v1.0.5.

Exact remaining ownership and blockers:

- This Beads upgrade plan owns `bd-ib-dwv`, the privileged guarded-image build
  and ephemeral Tier-1 proof. The maintainer has not authorized image mutation.
  Do not execute it until the maintainer explicitly authorizes that narrow
  attended action. Such authorization does not imply permission for
  `/usr/local/bin`, production-tenant, or production Dolt-data mutation.
- The separate `governed-repo-bootstrap` plan owns the `dolt-server`
  default-branch `ci-green` prerequisite. This plan may consume a result the
  maintainer or that plan publishes, but MUST NOT contact, instruct, diagnose,
  restart, mutate, or inspect that plan's supervisor, worker, marker, log,
  worktrees, or branches. Dependency is not execution authority.
- After that external prerequisite is published, this plan owns the canonical
  factory-safe restore source/target seam already represented by
  `dolt-server-wgy`; do not duplicate it. Re-measure before any sanctioned
  dispatch.
- The later live restore rehearsal, direct host binary replacement, and
  all-tenant migration/rollback window are attended actions and remain
  unauthorized. Current documentation/audit closure follows their recorded
  dependency order in `handoff.md`.

Fresh-session next action:

1. Run this binder's BOOT and all five HALT-first checks, then re-measure only
   this repository, this plan's ledger items, and its forge artifacts through
   the configured wrapper and public `/usr/local/bin/bd`.
2. Do not reopen or duplicate the completed guarded-image code work.
3. If the maintainer explicitly authorizes the narrow privileged image proof,
   supervise `bd-ib-dwv` under the attended safety envelope. Otherwise report
   that exact maintainer decision as the immediate blocker and start nothing.
4. Treat any separately published `dolt-server` prerequisite result as an
   external input only; never drive its owning plan.

Standing safety remains unchanged: never pass `--no-verify`; halt on hook or
gate failure; touch no other session's worktree or branch; never alter or kill
`livespec-overseer:1.1`; fetch and then verify forge state; tracked edits use
worktree -> reviewed PR -> rebase-merge -> refresh/cleanup with
`mise exec -- git`; product Python uses Red-Green-Replay; gates run foreground;
Beads never runs through mise or its private delegate; and no `/usr/local/bin`,
production-tenant, Dolt-data, image, or Fabro-server mutation is implied.

## Bindings

Resolve and report these startup bindings before driving. They contain no live
status, next action, or date-gated behavior.

| Binding | Value |
|---|---|
| `repo_primary` | `/data/projects/livespec-orchestrator-beads-fabro` |
| `thread_dir` | `plan/beads-v1-1-2-upgrade/` |
| `topic` | `beads-v1-1-2-upgrade` |
| `worker_session` | `beads-v1-1-2-upgrade` |
| `supervisor_session` | `beads-v1-1-2-upgrade-supervisor` |
| `WORKER_TARGET` | `'=beads-v1-1-2-upgrade:'` |
| `SUPERVISOR_TARGET` | `'=beads-v1-1-2-upgrade-supervisor:'` |
| `runtime_dir` | `${repo_primary}/tmp/overseer/${topic}/` |
| `supervisor_marker` | `${runtime_dir}/.supervisor-state` |
| `wait_channel` | `${runtime_dir}/worker-status.log` |
| `ledger_anchor` | `bd-ib-3kolea` |

Placeholder classes declared by this binder:

- Concretely bound: `repo_primary`, `thread_dir`, `topic`, `worker_session`,
  `supervisor_session`, `WORKER_TARGET`, `SUPERVISOR_TARGET`, and
  `ledger_anchor`.
- Composed bindings resolved transitively to a fixed point: `runtime_dir`,
  `supervisor_marker`, and `wait_channel`.
- Runtime slots intentionally left for later commands:
  `<condition-command>`, `<short-slug>`, and `<branch>`.
- No generation-time placeholder remains in this binder's fenced commands.
  Uppercase values in the shared protocol's YAML schema are illustrative field
  forms, not command substitutions.

## Thread-specific Valves

- The worker's source of truth is
  `plan/beads-v1-1-2-upgrade/handoff.md`, merged by PR #1165. Point the worker
  to it; do not restate or silently weaken its gates.
- Never install or invoke Beads through mise. `mise exec -- git` remains
  mandatory for repository git writes because it activates hooks.
- `/usr/local/bin/bd` is the lifecycle guard. Normal calls and
  `LIVESPEC_BD_PATH` must use it. The private delegate
  `/usr/local/bin/bd-real` is only the direct-copy target named by the plan,
  never the normal command path.
- Do not mutate `/usr/local/bin`, a production tenant, the Dolt data directory,
  or the orchestrator image until the exact prerequisite rehearsal and attended
  cutover gates in the worker handoff have passed.
- Do not use `bd-guard/rollback.sh` for the version rollback; it would remove
  the required guard.
- The separate lane named `fix-bd` owns remaining mise-removal work. Rebase
  after its relevant merges and stand down only on overlapping paths.
- Do not restart or alter the Fabro server as part of this thread.
- Factory-safe implementation slices should go through the dark factory.
  Privileged backup, migration, host-copy, and rollback actions remain attended.
- Epic `bd-ib-3kolea` is the lifecycle anchor. Groom it only after this
  supervision binder is reviewed and merged.
- Any claim that all writers are quiesced must cover every tenant on the shared
  Dolt server, including non-family tenants, and must use the handoff's
  connection-absence probe.

## Verification Discipline

Re-measure the ledger anchor through the public guard and configured family
environment before carrying forward any status claim:

```sh
cd /data/projects/livespec-orchestrator-beads-fabro
ledger_anchor='bd-ib-3kolea'
/data/projects/1password-env-wrapper/with-livespec-env.sh -- \
  /usr/local/bin/bd show "$ledger_anchor" --json \
  || { echo "HALT: cannot re-measure ledger item '$ledger_anchor'"; echo "REMEDY: fix ledger access before using any filed status claim"; exit 1; }
date -u '+MEASURED_AT: %Y-%m-%dT%H:%M:%SZ'
```

Preserve the tmux lookup verdict before filtering:

```sh
WORKER_TARGET='=beads-v1-1-2-upgrade:'
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
tmux_rc=$?
[ "$tmux_rc" -eq 0 ] \
  || { echo "HALT: tmux pane lookup failed for 'beads-v1-1-2-upgrade'"; echo "REMEDY: re-check the exact target before filtering its output"; exit 1; }
printf '%s\n' "$pane_pid" | head -1
```

## HALT-first preconditions

Expected worker session: `beads-v1-1-2-upgrade`.

Expected supervisor session: `beads-v1-1-2-upgrade-supervisor`.

Target repository:
`/data/projects/livespec-orchestrator-beads-fabro`.

Run these in order before doing anything else. Stop on the first failure and
act on its labelled `REMEDY:`.

1. The worker session exists:

```bash
WORKER_TARGET='=beads-v1-1-2-upgrade:'
tmux has-session -t "$WORKER_TARGET" \
  || { echo "HALT: expected worker session 'beads-v1-1-2-upgrade'"; echo "REMEDY: ask the maintainer whether to start that worker session"; exit 1; }
```

2. The worker session contains a live agent:

```bash
WORKER_TARGET='=beads-v1-1-2-upgrade:'
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
[ -n "$pane_pid" ] \
  || { echo "HALT: empty pane_pid for 'beads-v1-1-2-upgrade'"; echo "REMEDY: re-check the exact worker target and stop if it still resolves empty"; exit 1; }
ps -o pid=,comm=,args= --ppid "$pane_pid" --pid "$pane_pid" -H
# PASS only if a live `claude` or `codex` process appears in that tree.
# A lone shell (zsh/bash) with no agent child is a HALT.
# REMEDY: if no live agent appears, ask the maintainer whether to restart the worker.
```

Report which live driver was found.

3. The supervisor session exists, contains a distinct live agent, and does not
prefix-resolve to the worker pane:

```bash
WORKER_TARGET='=beads-v1-1-2-upgrade:'
SUPERVISOR_TARGET='=beads-v1-1-2-upgrade-supervisor:'
tmux has-session -t "$SUPERVISOR_TARGET" \
  || { echo "HALT: expected supervisor session 'beads-v1-1-2-upgrade-supervisor'"; echo "REMEDY: switch to the correct supervisor session or ask the maintainer to bootstrap it"; exit 1; }
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
supervisor_pane_pid=$(tmux display-message -p -t "$SUPERVISOR_TARGET" '#{pane_pid}')
[ -n "$supervisor_pane_pid" ] \
  || { echo "HALT: empty pane_pid for 'beads-v1-1-2-upgrade-supervisor'"; echo "REMEDY: re-check the exact supervisor target and stop if it still resolves empty"; exit 1; }
[ "$supervisor_pane_pid" != "$pane_pid" ] \
  || { echo "HALT: supervisor and worker resolve to the SAME pane"; echo "REMEDY: re-check both exact targets — a prefix match puts both names on one pane, and the worker's agent then reads as the supervisor's"; exit 1; }
ps -o pid=,comm=,args= --ppid "$supervisor_pane_pid" --pid "$supervisor_pane_pid" -H
# PASS only if a live `claude` or `codex` process appears in that tree.
# A lone shell (zsh/bash) with no agent child is a HALT.
# REMEDY: if no live agent appears, ask the maintainer to start the agent in that session.
```

4. The plan thread exists at the absolute target path:

```bash
test -d "/data/projects/livespec-orchestrator-beads-fabro/plan/beads-v1-1-2-upgrade" \
  || { echo "HALT: missing plan thread /data/projects/livespec-orchestrator-beads-fabro/plan/beads-v1-1-2-upgrade"; echo "REMEDY: create or choose the correct plan topic before supervising"; exit 1; }
```

5. The worker's resolved working directory is inside the target repository:

```bash
WORKER_TARGET='=beads-v1-1-2-upgrade:'
pane_cwd=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_current_path}')
[ -n "$pane_cwd" ] \
  || { echo "HALT: empty pane_current_path for 'beads-v1-1-2-upgrade'"; echo "REMEDY: re-check the exact worker target and stop if it still resolves empty"; exit 1; }
case "$(readlink -f -- "$pane_cwd")" in
  /data/projects/livespec-orchestrator-beads-fabro|/data/projects/livespec-orchestrator-beads-fabro/*) echo "PASS: $pane_cwd" ;;
  *) echo "HALT: pane cwd $pane_cwd is outside the target repo"; echo "REMEDY: move the worker into the target repo or start the correct worker session"; exit 1 ;;
esac
```

## Corrections

Thread-specific corrections belong here. Regeneration must preserve this
section byte-for-byte, including spelling, punctuation, code formatting, blank
lines, and ordering.

No thread-specific corrections have been recorded.
