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

This checkpoint was written at `2026-08-20T06:20:00Z`, replacing one dated
`2026-08-07T11:22:46Z` whose obligations are all now discharged. Re-measure
every timestamped claim before acting.

**The authoritative live record is the LEDGER TIMELINE on epic `bd-ib-3kolea`,
now 29 entries.** Read it with
`read_timeline(config=..., epic_id="bd-ib-3kolea")` from
`livespec_orchestrator_beads_fabro.commands.plan`. This checkpoint is a summary
for a cold restart; the timeline is the record.

### The 2026-08-07 obligations are DISCHARGED — do not re-execute them

The previous checkpoint told a successor to honour a factory-capacity wait for
`bd-ib-8azd` and then dispatch it. **That work is complete.** `bd-ib-8azd`
closed `2026-08-19T03:26:02Z` (`resolution:completed`) via salvage PR #1543,
merge `3e1251891a9e7bff9aba2f666573191f8f190a48`. Do not reopen, re-dispatch,
or duplicate it. There is no outstanding provider-capacity wait.

### Verified state

- `bd-ib-3kolea.1` (backup preflight) **CLOSED** `2026-08-20T01:22:01Z`,
  `resolution:completed`, closed through
  `.claude-plugin/scripts/bin/close_work_item.py` after the maintainer
  exercised its `acceptance:human-only` valve. All four criteria discharged:
  Dolt→S3 (337 runs / 14 days / zero failures, fresh objects for all 14
  tenants), Arq (VPS half plus maintainer-confirmed Restore-view record), Contabo
  (browser-verified, Auto Backup enabled, 10 retained), and redundant beads
  coverage verified by inspecting snapshot CONTENTS rather than exclude lists.
- **Restore from the S3 `DOLT_BACKUP` layer for any migration rollback.** Arq,
  Contabo, and restic all copy the LIVE Dolt directory and are crash-consistent,
  not quiesced; only S3 goes through the running server's stored procedure.
- **The v1.2.1 landmine has NOT been stepped on.** No v1.1.x/v1.2.x binary
  exists on this host (only the guard and delegate, both v1.0.5 `6a3f515ce`),
  and all 14 live tenants still record `.beads/.local_version` = `1.0.5`. The
  retarget starts from a uniform v1.0.5 baseline. Caveat: `.local_version` is a
  per-clone record, not a server-side schema read; an authoritative read belongs
  in the attended rehearsal window, NOT an ad-hoc probe, because
  `bd migrate schema --json` is known to write.
- Host pins re-measured `2026-08-19` and matching their 2026-07-30 values:
  guard `/usr/local/bin/bd` sha256 `5f55fbfb…37a3`; delegate
  `/usr/local/bin/bd-real` sha256 `463b7655…4486`, reporting v1.0.5.
- The v1.0.5 binary is **NOT** a single point of failure — an earlier claim to
  that effect was retracted. The Arq snapshot carries `bd-real` byte-identical,
  and restic snapshot `8a847de1` contains it too.

### Open decisions — BOTH are maintainer-side; do not self-resolve

1. **Retarget.** `bd-ib-3kolea.4` (P1, `ready`, `admission:manual`): v1.1.2 is
   superseded by **v1.2.2** (2026-08-15), a recovery release upstream describes
   as "the v1.1.2 code under a higher version number". Corroborated at source:
   the `v1.1.2...v1.2.2` compare shows **zero migration files changed** and only
   four Go files differing, all additive apart from the version string — so the
   schema target stays **v53** and the adapter surface cannot have changed. Not
   yet verified: that the published BINARY was built from that tag (criterion 2's
   checksum chain) and the behavioural EUT delta (criterion 3).
   This item also inherited `factory-safety:mutates-host-machinery`, which is
   **inaccurate** for a decision-and-verification item. It was **flagged, not
   changed** — relabeling a safety class to make an item dispatchable is
   guard-loosening and must not be done unilaterally.
2. **EUT scope.** A standing hold instructed this thread not to start Enemy Unit
   Test work because the `fabro-enemy-unit-tests` session dispatched
   `bd-ib-okr5ru`. But that item is **FabroPort** (the fabro surface, epic
   `bd-ib-bcwa6e`), whereas `bd-ib-3kolea.3` is a **BeadsPort** (the Beads CLI
   surface, this epic). They are two applications of one technique to two
   DIFFERENT dependencies. The hold has not been overturned and `bd-ib-3kolea.3`
   is **unstarted**. Do not start it until the maintainer settles this.

### Epic children

`bd-ib-3kolea.1` closed. `bd-ib-3kolea.4` ready. `bd-ib-3kolea.3` (BeadsPort)
and `bd-ib-ao3j` (attended rehearsal) both `backlog` with zero open blockers but
`admission:manual`. `bd-ib-3kolea.2` (final gate) blocked by `.3`, `.4` and
`ao3j`. **Neither unblocked item is factory-eligible** — one mutates host
machinery, the other needs a privileged host — so factory-window timing is moot
for this epic. Factory dispatch is separately forbidden while P1 defects
`bd-ib-9ek4` and `bd-ib-w8sj` remain open.

### Merged this session

PRs #1562, #1569 (EUT usage inventory + family sweep), #1572, #1573 (ledger-survey
and `bd ready` documentation fixes), #1601 (release-target restatement + a dated
SUPERSEDED banner on `qualification.md`), #1607 (the v1.2.0/v1.2.1 prohibition in
`AGENTS.md`). Findings filed in OWNING tenants: `dolt-server-b6e`,
`dolt-server-3iv`, `livespec-console-beads-fabro-zfcp`, `livespec-lubo`,
`livespec-cift`, plus evidence comments on `livespec-9mpc`.

### Standing safety, unchanged

Never pass `--no-verify`; halt on hook or gate failure; touch no other session's
worktree or branch; fetch then verify forge state; tracked edits go worktree →
reviewed PR → rebase-merge → refresh/cleanup with `mise exec -- git`; product
Python uses Red-Green-Replay; gates run foreground; Beads never runs through mise
or its private delegate; and no `/usr/local/bin`, production-tenant, Dolt-data,
image, or Fabro-server mutation is authorized by this checkpoint.

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
