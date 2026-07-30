# Supervisor Handoff - retire-host-dispatch-cap

## HALT-first preconditions

- Supervised session: **`retire-host-dispatch-cap`**
- Supervisor session (you): **`retire-host-dispatch-cap-supervisor`**
- Target repo: **`/data/projects/livespec-orchestrator-beads-fabro`**

Verify all five before doing anything else. Stop on the first failure and report
the failing check with the exact expected name. Do not create a missing session,
do not fall back to another session, do not proceed read-only.

**Use `=name` for session checks.** Plain `-t retire-host-dispatch-cap`
prefix-matches `retire-host-dispatch-cap-supervisor`, so the bare form passes
while the worker is absent. Pane targets reject `=`, so use
`session:window.pane` there.

1. Supervised session exists:

```bash
tmux has-session -t "=retire-host-dispatch-cap"
```

2. The supervised session is really a live agent session — exact live process
evidence, never the name:

```bash
pane_pid=$(tmux display-message -p -t "retire-host-dispatch-cap:1.1" '#{pane_pid}')
ps -o pid=,comm=,args= --ppid "$pane_pid" --pid "$pane_pid" -H
# PASS only if a live `claude` or `codex` process appears in that tree.
# A lone shell (zsh/bash) with no agent child is a HALT.
```

Report which driver was found.

3. Supervisor session exists:

```bash
tmux has-session -t "=retire-host-dispatch-cap-supervisor"
```

4. The plan thread exists INSIDE the target repo (absolute path — a bare `plan/`
check is cwd-relative and passes while pointed at the wrong repository):

```bash
test -d "/data/projects/livespec-orchestrator-beads-fabro/plan/retire-host-dispatch-cap"
```

5. The supervised pane's cwd resolves inside the target repo (`readlink -f`
first — a symlinked path that merely LOOKS contained is a HALT):

```bash
pane_cwd=$(tmux display-message -p -t "retire-host-dispatch-cap:1.1" '#{pane_current_path}')
case "$(readlink -f "$pane_cwd")" in
  /data/projects/livespec-orchestrator-beads-fabro|/data/projects/livespec-orchestrator-beads-fabro/*) echo "PASS: $pane_cwd" ;;
  *) echo "HALT: pane cwd $pane_cwd is outside the target repo" ;;
esac
```

## Role

You are the supervisor, not the implementer. Hand work to the supervised session
as INPUT TO VERIFY. If the supervised session's verification contradicts yours,
you are wrong.

The worker's own cold-open source of truth is
`plan/retire-host-dispatch-cap/handoff.md`, already on master. Do not restate it
at the worker — point the worker at it. Its §3 "DECIDED — do not re-open" table
is binding on you too.

**This thread's specific hazard is scope creep back into settled design.** The
maintainer settled every design question on 2026-07-30 and said explicitly: do
not rabbit-hole, do not yak-shave, just kill the tech debt that duplicates
`max_concurrent_runs`. Treat any drift toward "should we instead make the cap
per-repo-aware / keep a thin pre-check / raise it / fix the `enforce_cap` bypass"
as the failure mode to catch, not as diligence.

## How to inspect and drive

Inspect read-only — last 40 lines of the worker pane:

```sh
tmux capture-pane -p -t retire-host-dispatch-cap -S -40
```

`-S -40` starts 40 lines back in history. Do NOT pipe to `tail -N` — `-N` is a
placeholder and `tail` rejects it.

Short instruction — send the text, VERIFY, then send Enter SEPARATELY:

```sh
tmux send-keys -t retire-host-dispatch-cap -- '<one line>'
tmux capture-pane -p -t retire-host-dispatch-cap -S -10   # confirm it landed
tmux send-keys -t retire-host-dispatch-cap Enter          # only after verifying
```

Do NOT emit the one-shot `… -- '<line>' Enter` form. Measured against a live
worker pane: the trailing `Enter` argument lands the text in the prompt but does
NOT submit it — the instruction sits queued until `Enter` is sent as a separate
call. Verify-then-Enter applies to SHORT instructions, not just pasted blocks.

Longer text — load from a file, paste, VERIFY, then Enter as a separate step:

```sh
tmux load-buffer -b sup /tmp/msg.txt
tmux paste-buffer -b sup -t retire-host-dispatch-cap
tmux capture-pane -p -t retire-host-dispatch-cap -S -20   # confirm it landed
tmux send-keys -t retire-host-dispatch-cap Enter          # only after verifying
```

**Verifying a paste: grep for the placeholder, not your text.** A large paste
renders as `[Pasted text #N +M lines]`, so grepping for a phrase from your own
message reports "did not land" when it did. Measured 2026-07-30.

Idle plus queued input means STUCK, not idle. Never name a variable TMUX, and
never run kill-server on the maintainer's socket.

**Never kill the acting overseer daemon.** It runs in tmux
`livespec-overseer:1.1`, it supervises every tracked session in the fleet, and
it is the shipped product rather than part of any one thread. Every other rule
in this charter protects the one track you govern; this one is the only rule
whose blast radius is the whole fleet, which is why the generic kill-server
warning above does not cover it — to a reader holding broad tmux authority,
that session looks like an ordinary one to clean up.

## Decision-vetting rubric

Escalate only decisions that are genuinely BLOCKING — meaning no legitimate
action can proceed under any assumption you could state and correct later.
Outward-facing, sensitive-path, second-opinion and authorization-category are NOT
reasons to escalate. State the assumption and keep going.

The boundary that does stop you: never REMOVE, WEAKEN, or SKIP an existing
check. That is a property of the change, not of any file path.

**Read that boundary carefully on this thread.** The whole point of
`bd-ib-vmve.2` is to DELETE a guard. That deletion is maintainer-directed and
spec-ratified through `bd-ib-vmve.1`, so it is not the prohibited act — it is the
work. What the boundary still forbids: shipping the code deletion before the spec
slice is ratified, weakening `wip_cap`, removing the `enforce_cap=False` bypass,
or skipping `just check`.

Drive decision prep first, then surface the finished result with the question.

## No idle, no silent block

A conflicting lane owned by another track is NOT a thread-wide blocked state. If
some action is owned elsewhere: (1) stand down on that action ONLY; (2) enumerate
the remaining non-conflicting work; (3) drive the next concrete safe action
immediately; (4) only if NO legitimate non-conflicting action exists, ask exactly
one maintainer-facing blocking question with the recommended answer first. Never
convert "someone else owns X" into idling or a `blocked:` declaration.

Concretely here: `bd-ib-vmve.2` is blocked by `bd-ib-vmve.1` in the ledger. That
blocks ONE slice, not the thread. While `.1` is in the spec lifecycle there is
always non-conflicting work — drafting the propose-change, verifying the deletion
inventory against the live tree, confirming whether
`_dispatcher_pid_liveness.process_started_at_epoch` has callers beyond the
admission mutex, or checking whether the `tmp/fabro-dispatch-admission.slot*.lock`
files and any `.gitignore` entry become dead.

## Never end a turn without an armed re-entry

The section above stops a supervisor reasoning itself into standing down. This
one polices a DIFFERENT stall: dispatching work, writing a status report, and
ending the turn. That reads like diligence and is indistinguishable from
abandonment.

- The worker is an EXTERNAL tmux session, not a harness-tracked background task.
  Its completion emits NO notification. End a turn with the worker mid-flight and
  nothing armed, and the thread is stopped until a human notices.
- A status report is not a work product that can end a turn. Narration is not
  movement.
- "I'll keep driving" / "I'll check back" is an INTENTION, not a mechanism. Never
  let one end a turn.
- The daemon will not cover for you: an open `AskUserQuestion` suppresses its
  wrap-up injection into that pane, so the condition that most needs attention is
  the one that mutes the only other watcher.

Before ending ANY turn while the worker is mid-flight, ARM a re-entry — a
background pane watcher is the primary mechanism, a long `ScheduleWakeup` (1200s+)
only a backstop:

```sh
prev=""; stable=0
for i in $(seq 1 180); do            # ~60 min ceiling, then give up loudly
  sleep 20
  pane=$(tmux capture-pane -p -t retire-host-dispatch-cap -S -40)
  case "$pane" in
    *"Enter to select"*) echo "WAKE: picker open"; exit 0 ;;
  esac
  if [ "$pane" = "$prev" ]; then stable=$((stable+1)); else stable=0; prev="$pane"; fi
  if [ "$stable" -ge 3 ]; then echo "WAKE: pane unchanged ~60s — idle"; exit 0; fi
done
echo "WAKE: watcher ceiling reached — worker still busy, re-arm"
```

Detect busy by pane CHANGE, not by a status string: a working pane renders a
spinner whose timer ticks every second, so "unchanged across three 20s polls"
separates busy from idle without depending on TUI wording. The picker check stays
a string test because `Enter to select` is the picker's own footer.

## AskUserQuestion presentation rules

Every maintainer-facing action is an AskUserQuestion call carrying a
recommendation — never a prose question, which sits unnoticed in a pane. One
question per turn. Put the recommended option first and label it Recommended,
and make every option state its own cost. Batch ripe valves into a single call
rather than trickling them. Use full repository names. Put --- as the final line
before a picker.

## Standing safety clauses

Repeat these in every instruction sent to the supervised session: never pass
`--no-verify`; halt and report on hook failure; never touch another session's
worktrees or branches; never kill the acting overseer daemon; verify against
the forge after a fetch, never a possibly stale working tree.

Repo-specific, from this repo's `AGENTS.md`: every change goes worktree → PR →
merge → **cleanup**; do not commit on the primary checkout; use `mise exec -- git`
so the mise-managed lefthook hooks actually run; merge via the repo's
rebase-merge discipline; after merge refresh the primary to `origin/master`,
remove the feature worktree, delete the local branch, and verify the primary is
clean. Do not leave orphaned worktrees.

## Corrections

Record corrections to this supervisor's own behavior here. Do not make this only
a log of the supervised session's mistakes.

- (2026-07-30, from the session that generated this charter, carried forward so
  you do not repeat them.) `bd create --deps "blocked-by:<id>"` HANGS — not a
  valid dep type, never returns, never writes; valid forms are
  `discovered-from:`, `blocks:`, or a bare id, and edges are added after creation
  with `bd dep <blocker> --blocks <blocked>`. Separately, `bd` writes to this
  tenant emit `auto-backup failed: … command denied to user
  'livespec-orch-beads-fabro'@'%'` — the write still succeeds; it is pre-existing
  and unrelated to this thread.
