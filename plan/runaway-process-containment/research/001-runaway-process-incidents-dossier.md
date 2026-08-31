# Dossier 001 — four runaway-process incidents, 2026-08-31, and the classes behind them

Evidence dossier for plan thread `runaway-process-containment`. Compiled
2026-08-31 00:05–00:30Z by the livespec-overseer foreman seat acting at the
maintainer's direction. Nothing was killed, removed or otherwise cleaned up;
this note investigates and plans only.

Every claim is labelled **dossier** (read from the foreman seat's runaway dossier
of 00:05–00:20Z, itself read live from the named host), **measured** (re-measured
by this session, with the instrument named), **inferred**, or **hypothesis**. Do
not strengthen a label when quoting. Two dossier claims are CORRECTED below by
measurement (H3's mechanism and V1's spinning process); the corrections are the
most useful content here.

Hosts: **hp** = `hp-xubuntu`, the fabro factory host (16 cores, 30 GiB;
`FABRO_MAX_CONCURRENT_RUNS=15`, each sandbox planned at `cpu: 4` — a deliberate
3.75x over-subscription recorded in `fabro-hosts/services/fabro-server/hosts/hp-xubuntu.env`).
**vps** = `vmi3006760`, the shared operator host (18 cores) where overseerd, the
foreman seats and every worker tmux session run.

## The four incidents

| id | host | what burned | evidence | timeline (UTC) | root-cause class |
|---|---|---|---|---|---|
| H1 | hp | `ugrep … -rl '"kind": *"succeeded"' /` — a recursive grep of the whole filesystem from a root Claude Code session (cwd `/repos/thewoolleyman/livespec-overseer`, grandparent `sleep infinity`); pid 2466470 at **360% CPU for ~67 min** | dossier (`ps` on hp at 00:10Z) | running by ~23:03Z; gone by 00:13Z | agent shell command with an unbounded search root on a shared host; no per-command budget, no cgroup, and no overseer registration for a root session on hp |
| H2 | hp | fabro run `01M1AEH7T0TWMN8BX01CRCPAFM` (`overseer-1a31.5.1`, ImplementWorkItem) at **397% CPU** — four `.venv/bin/python -u -c import sys;exec(eval(sys.stdin.readline()))` pytest-xdist workers — while its checkpoint commit hung | dossier (`docker stats` ~00:12Z); measured (`fabro logs`, `fabro inspect`, hp journal) | started 23:02:35Z; implement "ACP turn timed out" 23:32:37Z, retried 23:32:42Z, timed out again 00:02:43Z; checkpoint `git commit` for node `implement` began ~00:02:44Z, failed 00:12:45Z "timed out after 600000ms"; sandbox stop 00:12:45.7–00:12:47.4Z; dispatcher verdict `failed` 00:13:18Z | a 30-min stage timeout that ends the ACP turn but not the work inside the sandbox; a 600 s checkpoint commit run WITH git hooks on a saturated 4-core sandbox; a second parallel dispatch by the same worker against a host already at load |
| H3 | hp | container `fabro-run-01M10GV8HBQ87HF002QE67EAM8` (`overseer-tuif2n`) still `running` 3.9 days after its run finalized; sole process `sleep infinity`, 0% CPU, ~568 KiB, 8 GB memory limit and a 4-core quota reserved | dossier (`docker ps`/`docker stats`); measured (`docker inspect`, hp journal for fabro-server, dockerd, containerd; `fabro inspect --server hp`) | run 02:30:33Z 2026-08-27 → finalized 02:58:04Z; fabro stopped the sandbox 02:58:04–06Z; **re-started 02:59:01Z by `POST /api/v1/runs/<id>/ssh`**; running since | post-terminal sandbox RE-START by an operator tool (`fabro sandbox ssh`) with no matching re-stop; no surface reconciles running containers against terminal runs |
| V1 | vps | three `python3 /usr/local/bin/bd-guard-emit.py` processes (pids 1463783, 1464089, 1464855) at **~109% CPU each for 8.5 days**, PPID 1, stdio → `/dev/null` | dossier (`ps`, transcript of the predecessor foreman seat); measured (`/proc/<pid>/exe`, `/proc/<pid>/environ`, thread stats, a bounded reproduction) | started 2026-08-22 11:19:02–03Z by three `overseer/supervisor.py add --repo <fakerepo>` probe legs run with `HOME=<scratchpad>/fakehome`; all three still present at 00:28:53Z (etimes 738,591 s) | a fire-and-forget helper (`setsid python3 … &`, no timeout, no parent) whose `python3` resolves to the **mise shim**, and the mise shim spins instead of failing under a HOME that holds no mise installation; a test fixture exercised the real wrapper with its real side-effecting hook |

H4 in the dossier (run `01M1AH8RBW8K6E7F995TYPYXS4`, 2% CPU) was healthy and is
context only. Also on hp at 00:13Z (dossier): a host-side pytest worker running as
root in `/repos/thewoolleyman/livespec-overseer/.venv` — the same root session as
H1 running this repo's suite outside any sandbox.

## What each incident actually was, with the corrections

### H2 — the timeline is measured; what the four workers WERE is not

- **Measured** (`fabro logs 01M1AEH7 --server https://hp-xubuntu.perch-rudd.ts.net:32276`,
  28 lines): sandbox `092a4986…` ready 23:02:09Z; run notice
  `github_token_refresh_limited`; implement failed "ACP turn timed out"
  `will_retry=true` at 23:32:37Z, retry after 5,329 ms; failed again
  `will_retry=false` at 00:02:43Z; "Metadata snapshot completed phase=checkpoint"
  00:02:44Z; "Checkpoint failed … git commit timed out after 600000ms
  exec_stdout_tail_bytes=0 exec_stderr_tail_bytes=17" 00:12:45Z; run failed
  `reason=workflow_error category=transient_infra`; sandbox stop 00:12:45.7Z →
  00:12:47.4Z. Wall time 4,210,173 ms = 2×1800 s + 600 s + overhead, so every
  number is a configured constant firing, not a measurement of work
  (`AGENTS.md`'s round-number rule).
- **Measured** (`fabro inspect`): `run.environment.resources = {cpu: 4, memory: 8GB}`,
  `lifecycle = {preserve: false, stop_on_terminal: true, auto_stop: null}`,
  `checkpoint = {skip_git_hooks: false, commit_timeout_ms: 600000}`; conclusion
  timing `inference_time_ms=0, active_time_ms=0, tool_time_ms=0`; implement
  adapter `claude-opus-5` via `claude-agent-acp` (NOT Codex — the dossier's
  "Codex ACP implementer is the unreliable leg" line does not describe this run;
  Codex is the `pr_adapter` here).
- **Inferred**: H3's surviving container carries `CpuQuota=400000` (docker
  default period 100 ms → 4 cores) from the same `cpu: 4` plan, so H2's 397% is a
  4-core cap SATURATED, not an unbounded container. H2's own container is gone,
  so this is inferred from a sibling.
- **Two hypotheses for the four xdist workers, not yet discriminated**:
  - (a) children of the timed-out ACP turn that outlived the turn — fabro ends
    the agent process at the timeout but not its process tree — and were still
    running the implementer's own `just check` when the checkpoint began;
  - (b) the checkpoint commit's OWN pre-commit hook: `skip_git_hooks: false`
    means the checkpoint `git commit` fires livespec-overseer's lefthook
    pre-commit → `scripts/check-pre-commit.sh`, which for any staged `.py`
    runs the aggregate including pytest-xdist. That is `bd-ib-6ka`'s shape (the
    30 s → 600 s checkpoint budget was raised for exactly this), and on a
    saturated 4-core sandbox the overseer suite plausibly exceeds 600 s.
  - The discriminator is the workers' parent chain (`git → lefthook → just →
    pytest` versus `claude-agent-acp → bash → pytest`), which nobody captured.
    A zero-output turn (`inference_time_ms=0`, `active_time_ms=0`) is the same
    signature plan `acp-implement-zero-output-hang` (`bd-ib-b5dg`) records on
    its caught-alive specimen, and that epic's 2026-08-30 cross-repo comment
    records `tool_time_ms` as a hardcoded 0 on ACP stages, so these fields
    discriminate little here; whether H2's implementer emitted any bytes is
    unmeasured (the events endpoint was not read).
- **Dossier**: `overseer-1a31.4` was dispatched in parallel at 23:22:42Z by the
  same worker (override reason recorded on epic `overseer-1a31`), and
  `overseer-ebik5q.2` (run `01M18YN47DFTR5QGNX6EFGWYGT`) parked the same day at
  10:09Z after the same two-timeout shape.

### H3 — CORRECTION: fabro did not skip teardown; an operator tool re-started the container

The dossier's class "sandbox teardown skipped on the workflow_error path" is
falsified by hp's journal (**measured**, `journalctl` 02:58:04–02:59:10Z on
2026-08-27, fabro-server pid 3575064, run worker pid 317746, dockerd, containerd):

1. 02:58:01Z — the escalate gate was answered `[A] Abandon` (`fabro inspect`:
   `human.gate.selected = "A"`); the `abandon` node exited 1 with no outgoing
   fail edge → `workflow_error` / `deterministic`. That is `bd-ib-3al8`'s shape;
   the item closed 2026-08-30T17:00Z, AFTER this run, so the run predates the fix.
   The run had reached escalate because the `pr` node's Codex adapter died on
   `SyntaxError: Expected property name or '}' in JSON` from an unquoted
   `CODEX_CONFIG` — `bd-ib-qulf`, closed 2026-08-27T07:22Z, also after this run.
   Implement, janitor and review (`approve`) had all SUCCEEDED; the diff is on
   `fabro/run/01M10GV8…` at `fde1d612`.
2. 02:58:04.33Z — "Sandbox stop started"; dockerd: "Container failed to exit
   within 1s of signal 15 - using the force"; container `FinishedAt`
   02:58:05.5Z, exit 0; systemd scope deactivated ("Consumed 17min 14.775s CPU
   time over 27min 56.934s wall clock"); 02:58:06.25Z "Sandbox stop completed".
   **Teardown ran.**
3. 02:58:27–29Z — a `principal_kind="user"` client read `/state`, `/events`,
   `/logs`, three blobs and `/artifacts` for this run: the dispatcher's
   `preserve_checkpointed_work_reference` (`fabro dump`), matching the overseer
   journal's 02:58:28Z entry.
4. **02:59:01.58Z — fabro-server: "Sandbox start started provider=docker" …
   "Sandbox start completed duration_ms=169" … `POST /api/v1/runs/01M10GV8…/ssh
   status=201 principal_kind="user" user_auth_method="dev_token"`.** containerd
   "connecting to shim 5cc2ecf9…", systemd "Started docker-5cc2ecf9….scope",
   dockerd `sbJoin` for `fabro-run-01M10GV8…`. `docker inspect` agrees:
   `Created 02:30:08Z`, `StartedAt 02:59:01.6Z`, `RestartCount 0`,
   `RestartPolicy no`.
5. Nothing has stopped it since. `fabro sandbox ssh --help` (client 0.254.0):
   `--ttl <TTL>  SSH access expiry in minutes (default 60)` — the TTL governs the
   SSH credential, not the sandbox; 3.9 days later the container is still up
   (`docker ps` on hp at 00:21Z: `Up 3 days`).

Who ran the ssh is **not established**. Scope searched: every Claude transcript
under `~/.claude/projects/-data-projects-livespec-overseer/` and
`…/-data-projects-livespec-orchestrator-beads-fabro/` for the literal
`sandbox ssh` — no file carries it in the 2026-08-27 window (positive control:
eight overseer transcripts DO contain `fabro ssh`/`/ssh` from other dates). That
excludes the CLI-from-those-two-project-sessions route; the fabro web console's
terminal, a shell outside a Claude session, and a Codex session remain.

`fabro ps -a` reports the run as `failed 27m29s` and says nothing about a live
container, and no surface on either host lists `docker ps` against terminal
runs. That is why it stayed invisible: the record was terminal and correct, and
the world diverged from it 55 s later.

### V1 — CORRECTION: the spinning process is the mise shim; the emitter never started

- **Measured** (`/proc/1463783/exe` → `/usr/bin/mise`; `cmdline` →
  `/home/ubuntu/.local/share/mise/shims/python3 /usr/local/bin/bd-guard-emit.py`):
  the process that has burned ~1.1 cores for 8.5 days is the **mise shim binary
  itself**, which never exec'd Python. 19 threads; main thread state `R`;
  `/proc/<pid>/stat` utime 14,179,023 vs stime 34,636,459 ticks (71% system
  time); fds: three `/dev/null`, eventfd, two eventpoll, three sockets; task ids
  churn between reads. `environ`: `HOME=<scratchpad>/fakehome`, `BDG_MODE=fail`,
  `BDG_ARGV="list --type epic --status all --json"`, `BDG_OP=""`, cwd
  `<scratchpad>/fakerepo (deleted)`.
- **Measured** (bounded reproduction, this session, `v1repro/run.sh`: each
  variant under `setsid`, hard-killed at 8 s, no leftovers afterwards; mise
  `2026.2.7 linux-x64`):
  - real `HOME`, live cwd → prints, exit 0 (control);
  - real `HOME`, deleted cwd → `mise WARN Current directory does not exist`,
    prints, exit 0;
  - `HOME=<empty dir>`, live cwd → **alive at 6 s, exe `/usr/bin/mise`, 19
    threads, 112% CPU**, no output;
  - `HOME=<empty dir>`, deleted cwd → **alive at 6 s, 122% CPU**, no output.
  So the trigger is a HOME that holds no mise installation; the deleted cwd is
  incidental. The emitter script (`bd-guard/bd-guard-emit.py`, ~110 lines,
  `urlopen(timeout=2)`, no loop) is exonerated.
- **Unmeasured**: WHAT mise loops on. A 6 s `strace -p` attach returned nothing
  (likely ptrace scope); `MISE_DEBUG=1` on the bounded repro, or `strace -f` of
  a child this session owns, is the next probe.
- The launch path (**measured**, `bd-guard/bd-guard.sh:615-628`): `_bdg_emit_span`
  runs `setsid python3 "$_bdg_emit" >/dev/null 2>&1 </dev/null &` — `python3`
  by PATH lookup, so whatever shim the CALLER's PATH and HOME select runs
  detached, un-timed, unparented. Three probes → three shims → three orphans
  reparented to init.

## Why each was invisible for so long — the questions this plan must answer

1. **H1** — a root Claude session on hp is registered with no overseer (overseerd
   watches tmux sessions on vps) and hp has no per-process CPU budget. Which
   surface should own "a process on a factory host has exceeded N core-minutes
   outside any sandbox": overseerd (cross-host), fabro-server (it already owns
   the host), or a host-level watchdog in `fabro-hosts`?
2. **H2** — for 70 minutes the only signals were a fabro event stream nobody
   tails and a `docker stats` nobody ran. Should the dispatcher's watchdog
   (`bd-ib-tec5sz` family) read sandbox CPU/steal time? Which of hypotheses (a)
   and (b) is true, and does a stage timeout kill the ACP process TREE?
3. **H3** — `fabro ps -a` was correct and the container was invisible to it.
   What reconciles `docker ps --filter name=fabro-run-` against terminal runs,
   and where does it live (`_dispatcher_reconcile_runs_attribution.py`, the
   archived `factory-host-storage-reclamation` plan's host GC, or fabro itself)?
   Does `sandbox ssh` on a terminal run have any legitimate reason to leave the
   sandbox running past its TTL?
4. **V1** — a PPID-1 process on vps belongs to no tmux session, so overseerd's
   per-session attention rows cannot see it. Which fixtures exercise
   `/usr/local/bin/bd` for real, and should the wrapper ever spawn a helper
   without `timeout` and an absolute interpreter?
5. **All four** — none of the existing surfaces (overseerd attention rows, the
   fabro sandbox lifecycle, the bd-guard wrapper, cgroup quotas, per-command
   budgets in agent shells) is a HOST-level runaway detector. Is one needed, or
   is each class better closed at its own seam?

## Candidate prevention mechanisms — hypotheses to measure, not decisions

Each names its tier so children are never filed mixed-tier. Tiers: **fork** =
a change to `thewoolleyman/fabro` `factory-integration` (outward-facing
upstream-fork work; per `AGENTS.md` NOT factory-safe for this repo);
**dispatch-safe** = an in-repo code/config/docs change with no `SPECIFICATION/`
edit and no host-side act in its acceptance; **spec-tier** = requires a
`SPECIFICATION/` change first (route via `propose-change`); **host-only** = a
mutation of hp or vps that no sandbox can perform (a post-merge obligation,
never an acceptance criterion).

| # | mechanism | closes | tier | measure first |
|---|---|---|---|---|
| P1 | Sandbox leak detector: reconcile `docker ps` on each factory host against `fabro ps -a` terminal runs; report, then reap by the export-then-reap rule | H3 | dispatch-safe (code) + host-only (cron/install) | inventory hp now: how many `fabro-run-*` containers exist versus terminal runs |
| P2 | `sandbox ssh`/`cp` on a terminal run must not leave the sandbox running past its TTL (auto-stop on expiry, or refuse without an explicit flag) | H3 | fork | reproduce on a throwaway terminal run; check upstream `fabro-sh/fabro` for the same behaviour |
| P3 | Stage timeout kills the whole process tree of the ACP turn (cgroup or process-group kill), and the retry starts from a clean sandbox process table | H2 (hyp. a) | fork | discriminate H2 (a)/(b) on the next occurrence by capturing the xdist workers' parent chain |
| P4 | Checkpoint commits run hook-free (`skip_git_hooks`) or with a budget sized to the target repo's measured gate runtime; a checkpoint that times out must not burn 10 min on a saturated sandbox | H2 (hyp. b) | dispatch-safe if only `workflow.toml`/dispatcher config; **check `SPECIFICATION/contracts.md` §"ACP node timeouts" first** — if the checkpoint budget is ratified there, spec-tier | time livespec-overseer's `just check` under a 4-core quota |
| P5 | Load-aware admission: refuse or defer a dispatch when the factory host's load/steal exceeds a threshold, independent of the per-repo `wip_cap` | H2 (parallel dispatch) | spec-tier (admission policy is ratified) | measure hp load at each of the day's dispatches |
| P6 | cgroup CPU quotas for agent shells on shared hosts (`systemd-run --scope -p CPUQuota=` per worker session; a slice for root sessions on hp) | H1, V1 blast radius | host-only, plus a livespec-overseer change to launch workers inside a scope (cross-repo) | does a quota on a worker session break tmux/overseerd assumptions? |
| P7 | Fire-and-forget helpers self-limit: `bd-guard.sh` spawns the emitter under `timeout`, with an absolute interpreter path (bypassing PATH shims), and a beside test asserts both | V1 | dispatch-safe (code + `bd-guard/test`) + host-only (`bd-guard/install.sh` re-run) | bounded repro already shows the shim spins; confirm `timeout 10 /usr/bin/python3` exits under the fake HOME |
| P8 | Test fixtures must not exercise the real `/usr/local/bin/bd` wrapper with its real OTLP hook (`LIVESPEC_BD_GUARD_OTLP=off`, or a stub `bd` on PATH) | V1 | cross-repo (livespec-overseer tests) docs/code | which fixtures reach the real wrapper today |
| P9 | overseerd attention condition for host-level runaway processes (PPID-1 orphans above N core-minutes; sandbox containers with no live run) | H1, V1, H3 | cross-repo, spec-tier in livespec-overseer (attention conditions are governed there) | pointer only from this plan |
| P10 | Guidance: agent shell commands never search from `/`, always bound a search root, and wrap long-running host commands in `timeout` | H1 | docs, dispatch-safe in the owning repo (the family core lives in livespec's template) | none |

## Prior art already in this tenant (read before filing anything)

Scan scope: the full orchestrator ledger, `bd list --status all --limit 0 --json`,
880 records on 2026-08-31, filtered client-side for sandbox/leak/teardown/
cgroup/runaway/process-tree/checkpoint-timeout/xdist/fire-and-forget signatures.

- `bd-ib-6ka` (blocked) — checkpoint timeout shorter than gate-running hooks; the
  600 s budget is its partial remedy (`orchestrator-image/README.md` PR #552 row).
- `bd-ib-jm4efv` (ready) — checkpoint-budget expiry misclassified as
  `transient_infra`; H2's conclusion carries exactly that label.
- `bd-ib-kttyks` (backlog) — preserve committed work before container teardown;
  the opposite failure direction from H3 and the natural sibling of P1.
- `bd-ib-6o6h` (backlog) — a parked run's unpushed work is destroyed at the
  ceiling; same lifecycle seam.
- `bd-ib-3al8` (closed 2026-08-30) and `bd-ib-qulf` (closed 2026-08-27) — the two
  defects that put H3's run on the abandon path; both post-date the run.
- `bd-ib-tyxzhv` (closed) — the supervised host experiment that diagnosed the
  contended resource under concurrent dispatch; `bd-ib-uwshxy` (closed) was the
  interim host-wide mutex, later deleted by `bd-ib-vmve.2`.
- `bd-ib-efjsb4` (backlog) — exit-137 ambiguity / outcome-from-artifact rule.
- Plan `acp-implement-zero-output-hang` (`bd-ib-b5dg`, live) — the ACP timeout
  family H2 belongs to; plan `factory-host-storage-reclamation` (`bd-ib-bdcmok`,
  archived) — host GC on factory hosts, the natural home for P1's host leg.
- Nothing in the ledger tracks a post-terminal sandbox re-start, a mise-shim
  spin, or host-level runaway detection.

## Explicitly out of scope for this thread

- Killing H1/V1 processes or removing the H3 container: maintainer decision;
  the export-then-reap rule covers the RUN record, not a container a user
  re-started.
- The livespec-overseer side of P6/P8/P9 and the livespec side of P10: pointers
  are recorded here; the work is filed in those tenants when this plan's
  synthesis child routes it.
