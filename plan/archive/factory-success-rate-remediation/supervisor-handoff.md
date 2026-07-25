# Supervisor Handoff — factory-success-rate-remediation

**CAMPAIGN COMPLETE 2026-07-24 17:00Z — bd-ib-cvgjop CLOSED, thread archived
(PR #934), plan/ moved to plan/archive/, primary clean on master. The factory
runs parallel at cap 2 (config-raiseable). No active supervision loop remains;
this file is the record. Open follow-ups: 81l0 + p16s ready next round; blk3
host-only via needs-attention; qsti (probe-C all-rejected leg); 6vu fork-track;
kttyks/gbu3k6/efjsb4/imzx24/eha3wh held for grooming; one spec-polish chore
from doctor warns.**

*Rewritten 2026-07-24 ~12:35Z by the successor supervisor after the overnight
parallelism campaign COMPLETED. Live-state claims have a shelf life of minutes —
RE-MEASURE before acting. Self-sufficient: this file + the two status logs.*

## 0. Who you are

Supervisor of the tmux session `factory-success-rate-remediation` (Claude
session in `/data/projects/livespec-orchestrator-beads-fabro`, Fable 5, xhigh).
You drive it via tmux (load-buffer → paste-buffer -p → verify chip → Enter as a
SEPARATE call), vet its decisions, keep it moving, escalate only genuine
human-only matters. Working dir / event log:
`/data/projects/livespec/tmp/factory-success-rate-remediation-supervisor/status.log`
(briefs numbered; check the log for the last number). Charter:
`factory-success-rate-remediation-supervisor-prompt.md` (same tmp dir).

## 1. THE HEADLINE — parallelism is DONE, verified live

**bd-ib-sd8o CLOSED (resolution:completed) 12:32:48Z.** The one-at-a-time cap is
gone: the admission mutex is now a `host_dispatch_cap` COUNTING CAP (config-keyed,
default 2, slot files, two host-global gauges, remedy-naming refusals).
Chain of record: spec v047 (livespec-orchestrator-beads-fabro PR #909) → cap impl
(PR #912) → live probe caught a FAIL-OPEN gauge (bare `fabro` not on wrapper
PATH) → fail-closed fix (PR #917) → rollout v0.46.7 to BOTH mutex-carrying roots
(/data/projects/livespec-orchestrator-beads-fabro and /data/projects/livespec,
build 6e94b35ec7f3, SHA-verified) → over-cap refusal PASSED live (3rd dispatch
refused, both run-ids + both remedies named) → 2x concurrency to merged PRs
(cross-track pums+wxq; two-of-ours mqr7wr PR #919 + 18r PR #921). Doctrine
retired: livespec PR #1712 rewrote `.ai/dispatcher-drain-operations.md` (the
"--network host forbids parallelism" claim was falsified by bd-ib-tyxzhv).
Serialization protocol: RETIRED fleet-wide (fleet-pin 07:11Z concurrence).
Raising the cap beyond 2 is CONFIG-ONLY, but only 2x is live-verified.

## 2. Current state (RE-MEASURE)

- Drain items closed tonight: nga9, lgv, qq7f, 4sy, uwshxy, pums, 18r, mqr7wr,
  w2ah; tyxzhv + sd8o closed. REMAINING QUEUE: n7ce4n → fe574e → S3 (p3sjiy),
  plus 6vu (fork-track). Worker continues the drain; items may overlap up to
  cap 2 where file-safe.
- Follow-ups filed, backlog, flagged for promotion: j4clfi (pid-reuse guard —
  scope-check vs the new slot structure at promotion), blk3 (apparmor userns
  host-constant — the REAL fix for bwrap-in-container), 81l0 (reconcile valve
  bare fabro_bin straggler), eha3wh, gbu3k6, efjsb4, imzx24, js4t57.
- Worker session was ~60% ctx at completion; overseer restarts it below 50%
  (it resumes from the on-master plan handoff in
  livespec-orchestrator-beads-fabro `plan/factory-success-rate-remediation/handoff.md`).

## 3. Supervisor apparatus (re-arm if you are fresh)

1. Monitor: `tail -n 0 -F <our status.log>` (milestones), persistent.
2. Monitor: worker pane poll — billing/picker immediate alarm, 20-min idle
   debounce, persistent.
3. Monitor: coordination-log stall (quiet 25min + zero fabro containers).
4. Monitor: `docker ps` fabro container SET (names only — do NOT compare the
   ticking Status field).
5. ScheduleWakeup heartbeat, currently 3600s (drain-watch); same prompt pattern
   re-armed each firing. If ALL monitors die, the heartbeat still wakes you.

## 4. Standing protocols (all learned the hard way)

- **Spend-limit picker** (stop-and-wait / usage-credits / Team-plan): NEVER
  select a paid option. `tmux send-keys Escape` then a short resume nudge —
  recovered incidents #1-#3 this way. If it recurs rapidly back-to-back:
  worker journals PARKED + stops cleanly; PushNotification the maintainer
  (billing is human-only).
- **Ownership by argv** before ANY container action: `ps -eo pid,args` →
  `/tmp/fabro-run-config-<item>.toml`. Never by image/timing/elimination.
- **Outcomes from artifacts** (merged PR / ledger / journal), never exit codes;
  exit 137 is ambiguous.
- **Coordination log** `/data/projects/livespec/tmp/fleet-pin-propagation-supervisor/status.log`:
  post material factory moves, `date -u +%Y-%m-%dT%H:%M:%SZ` timestamps ONLY.
- **Container inspection LABELS ONLY** — never print `.Config.Env`.
- Worker briefs: never `--no-verify`; halt on hook failure; own worktrees only;
  RGR for product .py; secrets probe-only.
- Answer worker pickers yourself (no human gates in autonomous mode); dismiss a
  picker with Escape ONLY when you must deliver text that answers it.

## 5. Escalate vs resolve

Maintainer-only: billing; product/values/architecture authority; irreversible
outward-facing acts; secrets/host mutation. Everything else: research, decide,
journal the disposition. AskUserQuestion with "(Recommended)" first, full repo
names (never bare "beads-fabro"), `---` as the last line before the picker.
