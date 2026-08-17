# beads-latency-collapse — root-cause research (2026-08-17)

## Symptom

Fleet-wide beads/"dolt" requests taking minutes to hours. Example: the
`fabro-on-hp` session's `list_work_items.py --json` calls repeatedly hit the
600 s Bash tool timeout, were moved to background, and completed after
2 h 14 m – 2 h 18 m. Host load averaged ~50 on 18 cores during the episode.

## The Dolt server is NOT the bottleneck

- `doltdb` journal shows connections opening and closing sub-second.
- Raw `bd list --status all --limit 0 --json` over the 523-item fabro tenant
  answers in <1.5 s of bd/Dolt time.
- The `dolt sql-server` process idles at ~4 % CPU; no D-state pileups; disk
  7–36 % utilized.

## Root causes (measured)

All evidence is queryable in Honeycomb env `livespec`, dataset `bd-guard`,
span `bd.invoke` (~40,131 spans/24 h; per-run attribution via
`bd.caller.ppid`, per-call argv via `bd.argv`).

1. **Per-invoke tenant validation triples every bd call.**
   `livespec_orchestrator_beads_fabro/effects/_beads_client_shell.py`
   `invoke()` calls `assert_repo_root_matches_config` before every bd
   command, spawning `bd config get dolt.database` + `bd config get
   dolt.server-user` subprocesses each time. Measured: 25,593 of 40,129
   daily bd invocations (64 %) are `config get`. Each invoke is ~350 ms p50,
   ~700 ms p95, ~1.1 s p99, outliers to 75 s under load.

2. **Listing N+1 over comments, including closed items.**
   `commands/list_work_items.py` `_dispatch_factories` calls
   `dispatch_factory_for` → `read_work_item_comments` (a `bd comments <id>`
   subprocess) for EVERY tenant item. Fabro tenant: 523 items, 371 (71 %)
   closed. One `list_work_items.py --json` run = 1 `bd list` + 522
   `bd comments` + 1,046 `bd config get` = **1,572 subprocesses ≈ 13 min of
   in-bd time at baseline p50** (SUM(duration_ms)=790 s for
   ppid 2498175), stretching to hours under contention.

3. **Per-invocation 1Password wrapper tax (~8.5 s wall / ~7 s CPU).**
   `with-livespec-env.sh` → `op run --environment` (OP_CACHE=false, op
   2.35.0-beta.01) burns ~7 s of a full core per invocation — userspace
   compute (flat perf profile), not network. Every interactive `bd` call
   from every agent session pays it: `wrapper -- true` = 8.5 s;
   `wrapper -- bd list --limit 1` = 8.9 s (beads/Dolt <0.5 s of that).
   ~40 distinct `op` processes churn per 30 s machine-wide.

4. **Congestion feedback loop.** Dozens of concurrent agent sessions run
   these listings + op churn + pytest → load ~50 on 18 cores (CPU PSI
   "some" ≈ 32 %) → per-call bd latency degrades → the N+1 runs stretch
   past the 600 s Bash timeout → they keep running in background while the
   session retries → more load. Classic congestion collapse with Dolt as
   innocent bystander.

## Fix inventory (rank order = urgency × leverage)

1. Memoize the tenant validation per process (or per (repo_root, database,
   server_user) key). Removes ~2/3 of all bd subprocess traffic. Tiny,
   factory-safe, Red-Green-Replay-able.
2. Stop reading comments for closed/out-of-filter items in
   `list_work_items` (−71 % immediately on the fabro tenant; bounded by the
   filtered live set).
3. Move the `livespec-dispatch-factory:` marker from per-item comments into
   the issue metadata JSON (single `bd list --json` already returns it);
   backfill migration; comment write may remain as audit trail.
4. Cross-repo/host: cache the 1Password environment host-side with a TTL
   (systemd-creds machinery already exists in
   thewoolleyman/1password-env-wrapper) instead of per-call `op run`;
   investigate the beta `op` build's 7 s CPU burn (test a stable op).
5. Verify fleet-wide effect post-landing in Honeycomb `bd-guard`:
   config-get share should collapse from 64 % to <5 %; a full listing
   should make ≤ live-item-count + a few calls and finish in well under a
   minute at baseline.

## Verification queries (Honeycomb, env `livespec`, dataset `bd-guard`)

- Volume/share: COUNT of `bd.invoke` broken down by `bd.subcommand`, 24 h.
- Per-run cost: COUNT + SUM(duration_ms) broken down by `bd.caller.ppid`
  filtered to `bd.caller.cmd` contains `list_work_items`.
- Latency: P50/P95/P99/MAX of `duration_ms`.

## Non-goals here (see scope event deferrals)

Fleet polling-cadence reduction, upstream beads batch-read API, op version
pin automation, DOLT_BACKUP denied-grant retry spam (dolt-server repo), and
op concurrency limiting are recorded as explicit deferrals on the plan epic.
