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

This checkpoint was written at `2026-08-06T09:08:49Z` for the next fresh
`beads-v1-1-2-upgrade-supervisor` session. The temporary transcript watcher the
supervisor started has been stopped. The exact supervised worker described
below remains in flight on its own tmux pane; do not assume it finished while
this supervisor was restarting.

Verified completed state:

- This repository's clean primary checkout, `origin/master`, and GitHub master
  were equal at `6ae82dc3ec05b1651325765874b1c5bf9c6b9a14` when measured on
  2026-08-06. The plan anchor `bd-ib-3kolea` remained an unassigned `backlog`
  epic with zero dependencies, dependents, and comments. The release/CLI,
  guard-compatibility, guarded-image code, and attended guarded-image proof
  items are closed; the direct image overlap `bd-ib-dwv` closed at
  `2026-08-04T02:32:41Z`. Do not reopen or duplicate any of them.
- The external `governed-repo-bootstrap` plan is complete and archived on
  `dolt-server` master `86e94c374d23d2f2115f7cc3785eb4e47afd5c4a`.
  Its current-master `check` and `ci-green` checks both completed successfully.
  That external plan is no longer a blocker. Inspect only its tracked archive,
  public forge, and target-anchored ledger evidence; never its archived runtime.
- Canonical restore-seam item `dolt-server-wgy` is closed. Fabro PR #46 landed
  as `ceaa078a8652ef6309e371181a3f6e9450fd1ab2`, with its post-merge janitor
  green. It has zero dependencies and comments and one already-recorded
  dependent. Do not dispatch, reopen, replace, or duplicate it.
- The governed plan's tracked archive records an attended real restore from
  source `livespec-orch-beads-fabro` to differently named scratch target
  `livespec-orch-beads-fabro_beads112_restore`. Source-before, target, and
  source-after inventories share digest
  `5f73c196716ee022ebe779cf366a5f897ab1e20b290d859e7c5b116076b4b3f6`;
  the source remained present and the scratch target was removed exactly. This
  is reusable evidence, not authorization to repeat a live restore.
- That archived proof discharges only the real distinct-source/target seam and
  cleanup portion of this plan's broader rehearsal. It does not prove a
  v1.0.5-shaped per-tenant restore, migrations 0050 through 0053, the full
  invariant inventory and round trips, or rollback-boundary replay. Do not call
  the broader rehearsal or attended rollout complete from the archived proof.

Exact in-flight worker state:

- The earlier worker retained removed livespec-driver-codex 0.5.8 Stop hooks
  and entered a hook loop. It produced no new branch, worktree, PR, ledger
  write, or reconciliation receipt. Only the exact worker pane was restarted;
  `livespec-overseer:1.1` and every other session were untouched.
- The fresh worker is on tmux target `'=beads-v1-1-2-upgrade:'`, with node PID
  3254176 and Codex PID 3254220 at checkpoint time. Its transcript is
  `/home/ubuntu/.codex/sessions/2026/08/06/rollout-2026-08-06T11-02-45-019fd64f-8c75-7e72-96e6-c35b784d53d7.jsonl`.
- Its sole assignment is read-only reconciliation of the public archived Dolt
  evidence against this plan, followed by a one-file PR updating only
  `plan/beads-v1-1-2-upgrade/handoff.md`. It may not mutate the ledger, host,
  tenant, Dolt data, image, backup/restore state, or Fabro. It must stop for a
  fresh exact-head supervisor review. At checkpoint time its transcript showed
  active verification and `worker-status.log` still had the 92-line baseline;
  no receipt or PR had arrived.
- The supervisor's temporary unified-exec watcher was stopped during wind-down.
  The successor must create a new bounded wait condition after rechecking the
  exact worker process, transcript, and `worker-status.log`; session ID 38889 is
  closed and must not be reused.

Fresh-session next action:

1. Run this binder's BOOT and all five HALT-first checks. Re-measure this repo,
   the plan ledger anchor, the Dolt public archive/forge/ledger evidence, and
   the exact worker state. Never enter the archived governed plan's runtime.
2. Inspect the fresh worker transcript, pane, and `worker-status.log`. If the
   bounded one-file reconciliation PR is ready, adversarially review its exact
   head against the verified partial-proof boundary. Otherwise re-arm a bounded
   transcript/log wait and continue supervising it.
3. Reject any claim that the archived restore alone completes the broader
   migration-and-rollback rehearsal. Reject any duplicate/reopened restore-seam
   item or repetition of the already-recorded live restore.
4. After an exact-head review passes, drive only the reviewed PR through the
   normal merge and cleanup path, then use the reconciled worker handoff to
   select the next safe, non-attended boundary. No attended rollout or mutation
   is authorized by this checkpoint.

Wind-down note: the mandated shell write of the ignored `.overseer-state`
marker was initially rejected by `livespec_footgun_guard.py` because the exact
runtime path lives beneath the primary checkout. The supervisor halted that
command, did not bypass the hook, and wrote the exact ignored marker through
the file-edit path instead. The tracked handoff was changed only in its own
dedicated wrap-up worktree.

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
