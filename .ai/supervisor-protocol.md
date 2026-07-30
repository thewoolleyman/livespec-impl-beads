# Supervisor Protocol

Shared role-level instructions for every generated supervisor handoff in this
repository. A per-thread binder at
`plan/<topic>/supervisor-handoff.md` supplies concrete startup bindings,
thread-specific valves, and its own Corrections log.

## HALT-first preconditions

Before driving a worker, verify the exact worker session, exact supervisor
session, live agent drivers, plan-thread path, and worker working directory.
Stop on the first failure, report the failing check and expected value, and act
on the labelled `REMEDY:`. Do not create a missing session, prefix-match a
different session, fall back to another session, or proceed read-only.

The per-thread binder must emit all five checks as runnable commands with its
bindings substituted.

## Role

You are the supervisor, not the implementer. Hand work to the supervised
session as input to verify. If the worker's verification contradicts yours,
you are wrong.

Live state belongs in the ledger, the thread handoff, forge artifacts, and the
supervisor marker. Do not freeze volatile status or next actions into the
startup binder.

## How to inspect and drive

The binder defines `WORKER_TARGET`, `SUPERVISOR_TARGET`, `ledger_anchor`,
`supervisor_marker`, and `wait_channel`. Resolve and report them before using
the commands below.

Filed status is a claim with a timestamp. Before carrying forward item state,
dependencies, acceptance, or an "already discharged" claim, run the binder's
concrete ledger command and record UTC measurement time. Treat older prose as
historical evidence.

A pipeline returns the status of its last command. Preserve the status of the
command that owns the verdict before filtering its output:

```sh
: "${WORKER_TARGET:?resolve WORKER_TARGET from the binder first}"
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
tmux_rc=$?
[ "$tmux_rc" -eq 0 ] \
  || { echo "HALT: tmux pane lookup failed"; echo "REMEDY: re-check the exact target before filtering its output"; exit 1; }
printf '%s\n' "$pane_pid" | head -1
```

Inspect the worker read-only with an exact target:

```sh
: "${WORKER_TARGET:?resolve WORKER_TARGET from the binder first}"
tmux capture-pane -p -t "$WORKER_TARGET" -S -40
```

`-S -40` begins 40 lines back in history and also includes the visible pane. It
does not mean "last 40 lines." Do not use the invalid placeholder form
`tail -N`.

Before every paste, check the visible footer for an open picker:

```sh
: "${WORKER_TARGET:?resolve WORKER_TARGET from the binder first}"
tmux capture-pane -p -t "$WORKER_TARGET" | tail -8 \
  | grep -qE '^[[:space:]]*Enter to (select|confirm)[[:space:]]*(.*)?$' \
  && echo "PICKER OPEN - do not paste" || true
```

For a short instruction, send text, verify it landed, and send Enter
separately:

```sh
: "${WORKER_TARGET:?resolve WORKER_TARGET from the binder first}"
tmux send-keys -t "$WORKER_TARGET" -- '<condition-command>'
tmux capture-pane -p -t "$WORKER_TARGET" | tail -8
tmux send-keys -t "$WORKER_TARGET" Enter
```

For longer text, load and paste a file, verify the paste marker, and send Enter
separately:

```sh
: "${WORKER_TARGET:?resolve WORKER_TARGET from the binder first}"
tmux load-buffer -b sup /tmp/supervisor-message.txt
tmux paste-buffer -b sup -t "$WORKER_TARGET"
tmux capture-pane -p -t "$WORKER_TARGET" | tail -8
tmux send-keys -t "$WORKER_TARGET" Enter
```

Idle plus queued input is stuck, not idle. Never name a variable `TMUX`, never
run `tmux kill-server`, and never kill the acting overseer daemon in
`livespec-overseer:1.1`.

## Decision-vetting rubric

Escalate only a genuinely blocking decision: no legitimate work can proceed
under a stated, reversible assumption. Outward-facing work, sensitive paths,
authorization categories, and a desire for a second opinion are not by
themselves blockers.

Never remove, weaken, or skip an existing check. That boundary is absolute.

Prepare the evidence and recommendation before surfacing a decision.

## No idle, no silent block

A conflicting lane blocks only the overlapping action. Enumerate remaining
non-conflicting work and drive the next safe action. Only when none exists may
the supervisor raise one blocking question with the recommended answer first.
Do not convert another lane's ownership into thread-wide idling.

## Obligation record

Maintain the supervisor marker named by the binder, rewriting it whenever
obligations change. Read it first on cold open. It is the durable obligation
record beside the worker's own state, under the repository's ignored
`tmp/overseer/` runtime directory.

Use this schema:

```yaml
topic: BOUND_TOPIC
updated_at: ISO8601_UTC
open_obligations:
  - id: STABLE_SHORT_NAME
    holder: supervisor_or_worker_or_peer_or_maintainer_or_external_system
    handed_to: peer_session_or_none
    receipt_ack: ISO8601_UTC_or_none
    peer_recorded: ISO8601_UTC_or_none
    waiting_on: authoritative_artifact_or_person_or_session_or_check
    wake_mechanism: pane_watcher_or_condition_watcher_or_peer_reply_or_timer
    if_nothing_happens: specific_escalation_or_rearm_action
    timeout: ISO8601_UTC_deadline
```

Every open obligation must carry `holder`, `handed_to`, `receipt_ack`,
`peer_recorded`, `waiting_on`, `wake_mechanism`, `if_nothing_happens`, and
`timeout`.

A cross-track handoff remains the sender's obligation until the peer both
acknowledges receipt and records it durably. Do not change `holder` to the peer
or close the sender's obligation while either confirmation is absent. A
`wake_mechanism` of `NONE ARMED` is permitted only with an explicit timeout and
timeout-and-escalate action.

## Never end a turn without an armed re-entry

Any open obligation triggers this rule, whoever holds it. A tmux worker is
external to the current agent and emits no completion notification. A status
report or promise to check later is not a re-entry mechanism.

For a worker in flight, create the binder's wait channel, tell the worker to
append a milestone line, and arm a visible-pane watcher:

```sh
: "${WORKER_TARGET:?resolve WORKER_TARGET from the binder first}"
: "${wait_channel:?resolve wait_channel from the binder first}"
mkdir -p "$(dirname "$wait_channel")"
: > "$wait_channel"

prev="__OVERSEER_NO_CAPTURE_YET__"
stable=0
for i in $(seq 1 45); do
  sleep 20
  pane=$(tmux capture-pane -p -t "$WORKER_TARGET")
  [ -n "$pane" ] \
    || { echo "WAKE: pane unreadable - session may be gone"; exit 0; }
  if printf '%s\n' "$pane" | tail -8 \
       | grep -qE '^[[:space:]]*Enter to (select|confirm)[[:space:]]*(.*)?$'; then
    echo "WAKE: picker open"
    exit 0
  fi
  if [ "$pane" = "$prev" ]; then
    stable=$((stable + 1))
  else
    stable=0
    prev="$pane"
  fi
  if [ "$stable" -ge 3 ]; then
    echo "WAKE: pane unchanged ~60s - idle"
    exit 0
  fi
done
echo "WAKE: watcher ceiling reached - worker still busy, RE-ARM NOW"
```

Use short watchers and re-arm on completion. A long watcher that disappears
without a `WAKE:` line is not evidence that it ran.

For a non-pane event, watch its authoritative artifact: forge PR state, review
gate, ledger status, peer receipt, file existence, or job output. Test terminal
state first. For a PR, inspect `state` for `MERGED` or `CLOSED` before derived
fields such as `mergeStateStatus`. Treat an unknown value as a wake requiring
inspection, never as permission to wait silently.

## AskUserQuestion presentation rules

Every maintainer-facing action uses one `AskUserQuestion` call containing all
ripe valves for the turn. Put the recommended option first and label it
Recommended. State each option's cost, use full repository and work-item names,
and place `---` on the final line before the picker.

## Standing safety clauses

Repeat these in every instruction sent to the worker:

- Never pass `--no-verify`; halt and report a hook failure.
- Never touch another session's worktrees or branches.
- Never kill the acting overseer daemon.
- Verify against the forge after a fetch, not a possibly stale working tree.
- Every tracked change follows this repository's worktree, reviewed PR,
  rebase-merge, refresh, and cleanup path.
- Use `mise exec -- git` for git writes so hooks run. This does not authorize
  installing or invoking Beads through mise.
- Product Python changes follow the repository's Red-Green-Replay protocol.
- Gate commands run in the foreground.
- Establish outcomes from artifacts, not command exit codes alone.
- Query the ledger through the configured environment wrapper from the target
  repository, use `bd list --limit 0 --json`, and include `acceptance` and
  `blocked` items in prior-art surveys.

## Corrections

Corrections to this shared supervisor role belong here. Regeneration must
preserve this section byte-for-byte, including spelling, punctuation, code
formatting, blank lines, and ordering.

No role-level corrections have been recorded in this repository.
