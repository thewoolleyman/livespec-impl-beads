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

This checkpoint was written at `2026-08-07T11:22:46Z`. Re-measure every
timestamped claim before acting. The exact worker is idle at its prompt; do not
give it another instruction until the recorded provider-capacity wait expires
and the marker has been re-read through its append-only end.

Verified completed state:

- This repository's clean primary checkout, `origin/master`, and GitHub master
  were equal at `310c8657951e2bc1b689d6cec50b4dbe4fd0720c` when measured on
  2026-08-07. The plan anchor `bd-ib-3kolea` remained an unassigned `backlog`
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

- The worker is on tmux target `'=beads-v1-1-2-upgrade:'`, with node PID 3254176
  and Codex PID 3254220 at checkpoint time. Its transcript is
  `/home/ubuntu/.codex/sessions/2026/08/06/rollout-2026-08-06T11-02-45-019fd64f-8c75-7e72-96e6-c35b784d53d7.jsonl`.
- PR #1327 merged the reviewed residual-rehearsal filing correction at
  `310c8657951e2bc1b689d6cec50b4dbe4fd0720c`, and its worktree and refs were
  cleaned. The correction makes both creates target-root anchored, configured-
  wrapper/public-guard only, selector-free, and parent-free.
- The worker then created exactly two standalone plan rows: factory-safe
  preparation `bd-ib-8azd` and attended rehearsal `bd-ib-ao3j`. The attended
  row has exactly one same-tenant `blocks` dependency on the preparation row.
  No epic linkage, cross-tenant edge, duplicate item, or automated groom was
  used. `worker-status.log` lines 120 through 125 are the terminal receipts.
- `bd-ib-8azd` is exactly `ready`, unassigned, parentless, and prerequisite-
  free, with one dependent. `bd-ib-ao3j` remains exactly `backlog`, unassigned,
  and blocked only by `bd-ib-8azd`. The first factory attempt was correctly
  refused while the preparation was still backlog. After its single guarded
  admission, the only ready-item attempt failed at `run-config-overlay` before
  sandbox launch with provider HTTP 429 and no reset timestamp.
- That provider failure created no Fabro run, branch, PR, merge, or dispatch
  lock but temporarily claimed the item. Binding prior art `bd-ib-zp3u7y` was
  re-read, zero target runs were proved across 544 Fabro records, and the exact
  guarded `move:bd-ib-8azd:ready` valve released the claim once. At
  `2026-08-07T11:22:46Z`, the item was ready and unassigned, the exact lock was
  absent, and target branches, PRs, and Fabro runs were all zero.
- The worker is idle at its prompt after the terminal release receipt. It has
  no authorized in-flight action. Do not reuse the stale prompt text as an
  assignment, and do not restart or alter any other pane.

Fresh-session next action:

1. Run this binder's BOOT and all five HALT-first checks. Re-measure this repo,
   the plan ledger anchor, both residual-rehearsal rows and their sole edge, the
   exact worker state, and the full append-only marker. Never enter the archived
   governed plan's runtime.
2. Honor marker obligation `wait_for_factory_oauth_capacity_bd_ib_8azd`. Do not
   attempt another dispatch before `2026-08-07T13:18:10Z`. The two required
   independent escalation vetters both said not to interrupt the maintainer
   after this single sample: wait for rolling OAuth capacity, with no fourth
   option. Credential inspection or rotation, billing changes, hand-building,
   and blinding the gate remain unauthorized.
3. After that time, fetch and verify forge, then re-prove that `bd-ib-8azd` is
   ready and unassigned with no target run, lock, branch, or PR. Open one new
   durable dispatch obligation and send the worker at most one fresh supervised
   `drive` action for this exact item. Run it in the foreground through the
   configured wrapper and in-repo driver. Preserve unrelated factory runs.
4. If the fresh attempt again returns HTTP 429 before launch, prove the no-run
   shape, release only its partial claim through the guarded same-ID move valve,
   append exact receipts, and extend the rolling wait. Do not use
   `reconcile-merged`, edit the assignee directly, or retry immediately. If
   multiple spaced attempts or a full rolling window still fail, vet and then
   escalate the credential or billing decision to the maintainer.
5. If the dispatch creates a run, supervise only that exact run through the
   normal reviewed-PR, rebase-merge, post-merge, ledger, and cleanup receipts.
   The attended rehearsal remains blocked until its preparation is genuinely
   complete; this checkpoint authorizes no server, tenant, migration, backup,
   restore, image, host, secret, or Fabro-server mutation.

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
