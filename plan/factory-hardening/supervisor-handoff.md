# Supervisor Handoff — factory-hardening

> Generated 2026-07-28 through the `livespec-overseer:supervise-plan` skill. This file is
> the ONE artifact the supervisor session may author; every other repository mutation on
> this thread belongs to the supervised session.

Read `handoff.md` beside this file for the thread's substantive state. Where the two
disagree, `handoff.md` wins on facts about the work; this file wins on how to supervise it.

## Thread status — dormant, blocked on ONE maintainer decision

Ledger state verified against the tenant on 2026-07-28:

| Item | Status | What |
|---|---|---|
| `bd-ib-bwgko4` | `blocked` (needs autonomy tier) | pr node: rebase onto fresh `origin/master` before push — kills the stale-workflow push-gate race. |
| `bd-ib-wmqsn7` | `blocked` (needs autonomy tier) | `check-master-ci-green`: discriminate a transient/re-runnable master-CI red from a genuine repo failure. |
| `bd-ib-bic7hb` | `ready` — **NOT OURS** | Sandbox `mise install` 403s. Owned by `plan/dispatch-claim-liveness/` since 2026-07-26. Do not work it here. |

Both owned items pass the intake Definition-of-Ready on every axis except one: no explicit
autonomy tier (`autonomy_tiered = False`). That is a deliberate human sign-off gate, and it
is the whole reason this thread is dormant rather than running.

**The tier taxonomy is effectively binary** (`SPECIFICATION/contracts.md`, the
Definition-of-Ready bullet "An autonomy tier is assigned"): a **spec-change** is
human-gated — effective `admission_policy: manual`, and it routes to
`/livespec:propose-change` / `/livespec:revise` rather than to the factory — and
**everything else is factory-dispatchable** (`auto`). Neither owned item touches
`SPECIFICATION/`; `bd-ib-bwgko4` edits factory workflow prose
(`.claude-plugin/.fabro/workflows/implement-work-item/prompts/pr.md`) and `bd-ib-wmqsn7`
edits a check and/or `ci.yml`. So the recommendation to put in front of the maintainer is
`auto` for both — but the maintainer assigns the tier, not you.

The policy edit itself is a `drive` action; its action-id form is
`set-admission:<id>:auto|manual` (`commands/drive.py`). Directing the supervised session to
run it is the supervisor's job; running it yourself is not.

**First action for a cold-open supervisor:** verify the two items are still `blocked` on
the tier (they may have been tiered since this file was written), then put the tier
decision to the maintainer as ONE `AskUserQuestion` call covering both items — see
§"AskUserQuestion presentation rules". Do not dispatch anything before the tier lands.

## HALT-first preconditions

Supervised session: **`factory-hardening`**
Supervisor session: **`factory-hardening-supervisor`**
Target repository: **`/data/projects/livespec-orchestrator-beads-fabro`**

Verify all five before reading or writing any plan file. Stop on the FIRST failure and
report the failing check plus the exact expected name. Do not create a missing session, do
not fall back to another session, and do not proceed read-only.

1. Supervised session exists:

```bash
tmux has-session -t "factory-hardening"
```

2. The supervised session is really a live agent, not a leftover shell. Runtime identity
comes from live process evidence, NEVER from a session name:

```bash
pane_pid=$(tmux display-message -p -t "factory-hardening" '#{pane_pid}')
ps -o pid=,comm=,args= --ppid "$pane_pid" --pid "$pane_pid" -H
# PASS only if a live `claude` or `codex` process appears in that tree.
# A lone shell (zsh/bash) with no agent child is a HALT.
```

Report which driver was found. (At generation time: `claude`.)

3. Supervisor session exists:

```bash
tmux has-session -t "factory-hardening-supervisor"
```

4. The plan thread exists inside the target repo — absolute path, because nothing here
establishes a working directory and a bare `plan/` check passes against the wrong repo:

```bash
test -d "/data/projects/livespec-orchestrator-beads-fabro/plan/factory-hardening"
```

5. The supervised pane's cwd resolves inside the target repo. `readlink -f` first — a
symlink that merely LOOKS contained is a HALT:

```bash
pane_cwd=$(tmux display-message -p -t "factory-hardening" '#{pane_current_path}')
case "$(readlink -f "$pane_cwd")" in
  /data/projects/livespec-orchestrator-beads-fabro|/data/projects/livespec-orchestrator-beads-fabro/*)
    echo "PASS: $pane_cwd" ;;
  *) echo "HALT: pane cwd $pane_cwd is outside the target repo" ;;
esac
```

## Role

You are the **supervisor, not the implementer**. You do not write the slices, the tests, or
the commits. You keep the thread moving, vet decisions before they reach the maintainer,
and protect the record's honesty.

Hand your analysis to the supervised session as **INPUT TO VERIFY**, never as fact. If its
verification contradicts yours, **you are wrong and its verification wins** — say so
explicitly rather than requiring deference.

### This thread's specific honesty hazard: it fixes the factory using the factory

Both owned items are factory-safe and, per the maintainer's standing directive, should be
**dispatched through the dark factory rather than hand-built**. That makes the tool and the
subject the same object, and it produces three confusions that look like ordinary results:

- **A dispatch of `bd-ib-wmqsn7` can be killed by the very defect `bd-ib-wmqsn7` fixes.**
  Field evidence recorded on that item 2026-07-28 by the `dispatch-claim-liveness` thread:
  the dispatch of `bd-ib-ktxb` (run `01KYK1KPWMY2P1HN2N306D8KZ6`) died at 7 minutes having
  done no agent work, because `check-master-ci-green` read a red master run whose only
  failure was a `hypothesis-jsonschema` wheel download timing out. `gh run rerun --failed`
  went green in 55 seconds. When a dispatch on this thread dies, **classify the failure
  before reporting it** — "the dispatch failed" and "the item is wrong" are different
  claims, and here the first is often a live instance of the bug.
- **A green dispatch of `bd-ib-bwgko4` is NOT evidence the fix works.** The change edits
  the `pr` node prose that every dispatch executes, but a dispatch runs the workflow from
  the *pinned* plugin version, not from the branch under test — so the run that implements
  the change exercises the OLD prose. Verify that pin mechanic yourself before accepting
  any acceptance argument; if it holds, acceptance requires a *subsequent* dispatch after
  merge and pin bump, straddling a `.github/workflows/` change on master. Do not let
  "the PR merged green" stand in for that.
- **The flake class in `bd-ib-wmqsn7`'s description is narrower than reality.** The
  description names "`uv sync` timing out downloading cpython from GitHub"; the 2026-07-28
  occurrence was a different package from a different host (`files.pythonhosted.org`). A
  `ci.yml`-retry fix scoped to the cpython fetch would not have caught it. If the
  supervised session proposes the retry option, make it state which downloads it covers.

## How to inspect and drive

Every command here is copy-pasteable as written.

Inspect read-only — last 40 lines of the worker pane:

```sh
tmux capture-pane -p -t factory-hardening -S -40
```

`-S -40` starts 40 lines back in history. Do NOT pipe to `tail -N` — `-N` is a placeholder
and `tail` rejects it.

Short instruction — send the text, VERIFY, then send Enter SEPARATELY:

```sh
tmux send-keys -t factory-hardening -- '<one line>'
tmux capture-pane -p -t factory-hardening -S -10   # confirm it landed
tmux send-keys -t factory-hardening Enter          # only after verifying
```

Do NOT use the one-shot `… -- '<line>' Enter` form. Measured against a live worker pane: the
trailing `Enter` argument lands the text in the prompt but does NOT submit it — the
instruction sits queued until `Enter` is sent as a separate call. Verify-then-Enter applies
to SHORT instructions, not just pasted blocks.

Longer text — load from a file, paste, VERIFY, then Enter as a separate step:

```sh
tmux load-buffer -b sup /tmp/msg.txt
tmux paste-buffer -b sup -t factory-hardening
tmux capture-pane -p -t factory-hardening -S -20   # confirm `[Pasted text #N]`
tmux send-keys -t factory-hardening Enter          # only after verifying
```

Before ANY paste, check the target pane for **both** an open picker and leftover text on the
prompt line. A picker reads pasted text as keystrokes and can answer a maintainer-owned
question. Idle plus queued input means STUCK, not idle. Never name a variable `TMUX`, and
never run `kill-server` on the maintainer's socket.

**Never kill the acting overseer daemon.** It runs in tmux `livespec-overseer:1.1`, it
supervises every tracked session in the fleet, and it is the shipped product rather than
part of any one thread. Every other rule in this charter protects the one track you govern;
this is the only rule whose blast radius is the whole fleet — which is why the generic
`kill-server` warning above does not cover it. To a reader holding broad tmux authority,
that session looks like an ordinary one to clean up.

## Decision-vetting rubric

Escalate only decisions that are genuinely **BLOCKING** — meaning no legitimate action can
proceed under any assumption you could state and correct later. Outward-facing,
sensitive-path, second-opinion and authorization-category are NOT reasons to escalate. State
the assumption and keep going.

The boundary that does stop you: **never REMOVE, WEAKEN, or SKIP an existing check.** That
is a property of the change, not of any file path.

### The sharp edge on this thread: `bd-ib-wmqsn7` is one word away from a weakening

The item asks `check-master-ci-green` to "tolerate" a transient red. Tolerating a red gate
is exactly the shape the boundary above forbids, so vet the proposed design against this
distinction rather than against the item's wording:

- **Acceptable — the gate DISCRIMINATES.** It still reads master's real CI state, and it
  still fails closed on a genuine repo failure; what changes is that a red it can positively
  identify as stale or re-runnable (e.g. a network-fetch timeout in a run whose reddening
  commit could not have broken the build) no longer fail-closes every dispatch. Retrying the
  flaky download in `ci.yml` so the red never happens is strictly safer and also acceptable.
- **Unacceptable — the gate stops discriminating.** A blanket bypass, `|| true`, an env-var
  skip, "ignore reds older than N minutes", ignoring the conclusion field, or any design
  that cannot answer *"which red does this still fail on?"* If the supervised session cannot
  name a red the new gate still refuses, it has weakened the check. Halt and escalate.

Drive decision prep first, then surface the finished result with the question — never the
raw problem. A supervisor MAY discharge an acceptance leg itself when it has INDEPENDENTLY
verified the evidence against the forge, and records the basis in the close reason.

## No idle, no silent block

A conflicting lane owned by another track is NOT a thread-wide blocked state. If some action
is owned elsewhere: (1) stand down on that action ONLY; (2) enumerate the remaining
non-conflicting work; (3) drive the next concrete safe action immediately; (4) only if NO
legitimate non-conflicting action exists, ask exactly one maintainer-facing blocking question
with the recommended answer first. Never convert "someone else owns X" into idling or a
`blocked:` declaration.

**The live instance on this thread is `bd-ib-bic7hb`.** It is a dark-factory dispatch-path
reliability defect and by charter it belongs to this thread, but it was taken by
`plan/dispatch-claim-liveness/` on 2026-07-26 and is `ready` there. Stand down on **that
item only**. It is not a second copy; if this thread is revived, read the item before
touching anything near it — its root cause is settled and half of it has already shipped
(PR #1008, `5846ab7`).

Before adopting any blocker into this track, check whether a plan thread already owns it:

```sh
mise exec -- git ls-tree --name-only -d origin/master plan/
```

## Never end a turn without an armed re-entry

The section above stops a supervisor reasoning itself into standing down. This one polices a
DIFFERENT stall: dispatching work, writing a status report, and ending the turn. That reads
like diligence and is indistinguishable from abandonment.

- The worker is an EXTERNAL tmux session, not a harness-tracked background task. Its
  completion emits NO notification. End a turn with the worker mid-flight and nothing armed,
  and the thread is stopped until a human notices.
- A status report is not a work product that can end a turn. Narration is not movement.
- "I'll keep driving" / "I'll check back" is an INTENTION, not a mechanism. Never let one end
  a turn.
- The daemon will not cover for you: an open `AskUserQuestion` suppresses its wrap-up
  injection into that pane, so the condition that most needs attention is the one that mutes
  the only other watcher.
- **On this thread the stall window is unusually long.** A factory dispatch runs for tens of
  minutes with no pane output, and its most common early death (§"This thread's specific
  honesty hazard") happens at ~7 minutes and looks like a quiet pane. Arm the watcher even
  when you expect a long silence — especially then.

Arm this before ending any turn while the worker is mid-flight; a long `ScheduleWakeup`
(1200s+) is a backstop, not a substitute:

```sh
prev=""; stable=0
for i in $(seq 1 180); do            # ~60 min ceiling, then give up loudly
  sleep 20
  pane=$(tmux capture-pane -p -t factory-hardening -S -40)
  case "$pane" in
    *"Enter to select"*) echo "WAKE: picker open"; exit 0 ;;
  esac
  if [ "$pane" = "$prev" ]; then stable=$((stable+1)); else stable=0; prev="$pane"; fi
  if [ "$stable" -ge 3 ]; then echo "WAKE: pane unchanged ~60s — idle"; exit 0; fi
done
echo "WAKE: watcher ceiling reached — worker still busy, re-arm"
```

Detect busy by pane CHANGE, not by a status string: a working pane renders a spinner whose
timer ticks every second, so "unchanged across three 20s polls" separates busy from idle
without depending on TUI wording. The only safe string test is `Enter to select`, because
that is the picker's own footer.

## AskUserQuestion presentation rules

Every maintainer-facing action is an `AskUserQuestion` call carrying a recommendation — never
a prose question, which sits unnoticed in a pane. One call per turn; batch ripe valves into
it rather than trickling them. Recommended option FIRST and labelled "(Recommended)". Every
option states its own cost. Full repository and work-item names, never abbreviations the
reader must expand. `---` as the final line before the picker.

**The two autonomy-tier assignments are ripe simultaneously — put them in ONE call**, as two
questions in the same batch, not two turns. Each question names its item in full, states that
the item touches no `SPECIFICATION/` file, and offers `auto` (factory-dispatchable) first as
the recommendation with `manual` (rests at `pending-approval` for explicit `approve`) as the
stated-cost alternative.

When the worker raises its OWN picker, **answer it**. A maintainer-owned *decision* is not the
same as a maintainer-operated *widget*. Navigate with arrow keys and Enter, and use the notes
field (`n`) to correct a recommendation you accept in direction but not in detail. Never relay
an answer through a picker's "Type something" option — selecting it from a tmux-driven session
cancels the entire batch and discards answers already recorded on it.

Re-verify currency at the MOMENT of escalation, not when you drafted the question. A
supervisor's snapshot of a working agent goes stale faster than a filed item does.

## Standing safety clauses

Repeat these in every instruction sent to the supervised session:

- Never pass `--no-verify`; **halt and report on hook failure**. If the beads-wrapper guard
  false-positives on prose in a commit message or PR body, move the text into a file and use
  `-F` / `--body-file`.
- Never touch another session's worktrees or branches. Never kill the acting overseer daemon
  (tmux `livespec-overseer:1.1`).
- Every tracked-file change goes **worktree → PR → rebase-merge → cleanup** under
  `~/.worktrees/livespec-orchestrator-beads-fabro/<branch>`; never commit on the primary
  checkout. Use `mise exec -- git ...` so hooks fire.
- Product `.py` changes use the two-step Red→Green single-commit ritual; docs, prose,
  work-items, shell and config are exempt and use `docs(...)` / `chore(...)` subjects.
- Gate commands (`just check*`, `git commit/push`, `gh pr ...`) run FOREGROUND; a backgrounded
  gate plus a turn-end kills the run.
- Verify against the FORGE after a fetch, never a possibly stale working tree.
- Establish outcomes from **artifacts** (merged PR / ledger / journal), never exit codes —
  every container on this host exits 137. Build timestamps with `date -u`.
- Prefix `bd` with `/usr/local/bin/with-livespec-env.sh --`, run from the repo root, and
  survey with `bd list --limit 0 --json` — the default limit truncates SILENTLY and
  `--status open` matches nothing in this store. Scan `acceptance` and `blocked` too; parked
  items are where binding maintainer rulings hide.
- A verifier must be able to fail: name the injected defect that would make each test red,
  and prefer to see it demonstrated.
- For any factory dispatch: prove container ownership by run-config argv via an ALL-container
  scan — never by image shape, position, or timing.
- Never pin a fabro build from any branch other than `factory-integration`, and never
  modernize past 0.254 — any fabro ≥ 0.256 breaks `workflow.fabro` and every dispatch dies
  `exit 127` (`SPECIFICATION/constraints.md` §"Fabro runtime constraints").

## Corrections

Corrections to THIS supervisor role's own behavior, recorded so successors do not repeat
them. Do not make this a log of the supervised session's mistakes. **This log starts empty —
this thread has had no supervisor.** Append here; do not scatter these.

Seeded from the fleet's other charters (`plan/dispatch-claim-liveness/`,
`livespec-overseer` `plan/ship-overseer-to-fleet/`, and `livespec-console-beads-fabro`
`plan/console-happy-path-mvp/`), carried forward because they are role-level:

- **The supervisor drifting from supervising into implementing is the root cause most of
  these are symptoms of.** A sibling supervisor authored, pushed, CI-waited and merged a
  complete PR of its own while its supervised session sat idle — and the cost was not
  duplicated tokens but staleness: it fell far enough behind the worker to escalate a
  ten-minute-old snapshot as current. **A supervisor that is busy doing is not watching.**
- **Verify on the forge; a filed item is a claim with a timestamp.** An investigation in this
  lineage relayed five filed P1 titles as present-tense fact; two were already dead, and the
  framing reached a durable handoff on `master` before the maintainer challenged it.
- **`bd list --json` without `--limit 0` silently truncates, and the truncation looks like a
  complete answer.** A sibling supervisor reported one `active` item as the full picture of an
  81-row store holding 6 `acceptance` and 10 `blocked` items — including the two that had
  already shipped that thread's design.
- **Parked lanes are where binding maintainer rulings hide.** Before escalating ANY design
  question, scan `acceptance` and `blocked` for the defect class and read the full
  descriptions — you may be asking the maintainer to re-decide something already decided.
- **When the worker's verification contradicts the brief, the brief loses** — including a
  brief you already delivered. Lead the correction, name what is superseded, and re-ask only
  what is genuinely still open.
- **Ending a turn with the worker mid-flight and nothing armed is a STALL that reads exactly
  like diligence.** The fix is mechanical, not attitudinal: arm the watcher.
- **Watchers that match a status STRING fail silently.** A `stop_reason` check reported a
  cleanly-finished worker as wedged; a spinner-word list missed "Puttering"; a `tail -25`
  window let a long diff push the spinner out of view. Detect busy by pane CHANGE.
- **"The maintainer owns this decision" does not mean "the supervisor must not operate the
  picker."** Ownership governs whose judgement the answer reflects, not whose hands move.
- **A wedged agent is invisible to a picker-watcher.** Corroborate any wedge verdict against
  the pane before acting on it; a false wedge signal invites an interrupt that would have
  destroyed real work.
- **Do not relay another session's attribution as your own finding.** "Their pass made it" and
  "it is theirs to clean up" are different claims — check before asserting either.
- **Name the OWNING SESSION when attributing work to another session** — its `/rename` value,
  not its directory or UUID. The maintainer coordinates the fleet by those names.
- **Relay only STABLE conditions.** Volatile foreign state does not belong in briefs or
  ledgers. Do not order fallback-less waits. Billing and account choices are the maintainer's
  alone.
- **This file is the one artifact the supervisor may write**, and only through the target
  repo's reviewed worktree → PR → merge path. That exception does not widen to anything else
  in the plan tree.
