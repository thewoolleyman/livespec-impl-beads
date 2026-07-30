# Supervisor Handoff - beads-v1-1-2-upgrade

## Shared Protocol

Read `.ai/supervisor-protocol.md` before driving. Validate this binder together
with that shared layer; neither layer is complete by itself.

Regeneration must preserve both Corrections sections byte-for-byte:

- `.ai/supervisor-protocol.md` `## Corrections` for role-level corrections.
- This binder's `## Corrections` for thread-specific corrections.

Preserve spelling, punctuation, code formatting, blank lines, and ordering
exactly. Live thread state is not in this binder; re-measure it from the ledger,
the worker handoff, forge artifacts, and the supervisor marker.

```sh
supervisor_marker="/data/projects/livespec-orchestrator-beads-fabro/tmp/overseer/beads-v1-1-2-upgrade/.supervisor-state"
test -f ".ai/supervisor-protocol.md" \
  || { echo "HALT: missing shared supervisor protocol .ai/supervisor-protocol.md"; echo "REMEDY: regenerate the two-layer supervisor handoff before driving"; exit 1; }
printf '%s\n' "BOOT: read .ai/supervisor-protocol.md, this binder, and the supervisor marker if it exists"
test ! -f "$supervisor_marker" || sed -n '1,220p' "$supervisor_marker"
```

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
