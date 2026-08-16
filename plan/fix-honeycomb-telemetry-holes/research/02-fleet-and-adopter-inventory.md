# Fleet & adopter telemetry inventory (rollout surface)

Compiled 2026-08-16 from a read-only survey. This grounds the "fleet-wide + dolt/homelab"
scope and shows where each fix lands (repo code vs server-side).

## Three telemetry paths — different "fix once vs per-repo" answers

1. **Central OTel Collector** — `/data/projects/otel-collector/config.yaml`. Routing brain:
   receives agent spans/metrics, fans out to Honeycomb datasets by `service.name`. Dataset
   routing / OTTL transforms / env-key selection are **server-side, one file, no repo code**.
2. **Python enrich/scrub data-plane** — ONLY in `livespec-orchestrator-beads-fabro`
   (`commands/_otel_*`). The only first-party OTLP emit/receive code. **Single-repo.**
3. **CI-telemetry shell exporter** — `.github/scripts/export-ci-telemetry.sh`, templated in
   `livespec/templates/orchestrator-plugin/` and COPIED into each fleet member. Emits the
   `github-ci` dataset. **Fix once in the template, propagate per-repo.**

The shared runtime lib `livespec-runtime` (vendored as `_vendor/livespec_runtime/`) contains
NO OTel code. So the core enrich/emit fix is single-repo, NOT a fleet propagation. No
`livespec-impl-*` clones exist under /data/projects.

## Fleet members

| Repo | Runtime OTel wiring | Dataset / service.name | Fix locus |
|---|---|---|---|
| **livespec** (canonical) | CI exporter only; OWNS the CI template | `github-ci` | template edit → propagate |
| **livespec-orchestrator-beads-fabro** | FULL OTLP emit + E1 enrich/scrub + `:4318` receiver + sandbox OTEL projection | `livespec-dispatcher`, `fabro-sandbox`, `claude-code` (+ `fabro` via server) | **CODE — primary target** |
| **livespec-orchestrator-git-jsonl** | drives factory dispatches too; CI exporter | `github-ci` (+ factory telemetry parity) | verify parity — may need code |
| **livespec-dev-tooling** | `otel_step_timer.py` (sandbox step timing → `fabro-sandbox`); `ci-runner/observability/ci-runner-heartbeat.sh` (`livespec.ci_runners.active` gauge, `service.name=ci-runner-liveness`); CI exporter | `fabro-sandbox`, `livespec-host-metrics`, `github-ci` | CODE if step-timer/heartbeat change |
| **livespec-runtime** | CI exporter only (IS the shared lib; no otel in it) | `github-ci` | template/CI only |
| **livespec-driver-claude / -codex / -pi** | CI exporter only | `github-ci` | CI template only |
| **livespec-overseer** | CI exporter only | `github-ci` | CI template only |
| **livespec-console-beads-fabro** | **NONE — no CI exporter, no runtime OTel** | none | **GAP — flag** |

Evidence (beads-fabro): `_otel_enrich_export.py:22-24,53-60,123-132`; `_dispatcher_otel_wiring.py:42,72,139,170-181`;
`_dispatcher_projection.py:38-73`; `_reflector_spans.py:17` + siblings (`_OTLP_SERVICE_NAME="livespec-dispatcher"`).
CI exporter: `livespec/.github/scripts/export-ci-telemetry.sh` — `DATASET=github-ci`,
`NAMESPACE=livespec-family`, key `HONEYCOMB_GITHUB_CI_INGEST_KEY_LIVESPEC` → `livespec` env.

## Adopter: dolt-server (`/data/projects/dolt-server`)

Backup observability only, via **direct Honeycomb Events API** (not OTLP, not the collector):
`scripts/lib/common.sh:349 emit_honeycomb_event()` → `POST .../1/events/${HONEYCOMB_DATASET}`,
no-op unless `HONEYCOMB_INGEST_KEY` + `HONEYCOMB_DATASET` set. Producers: `backup-sync.sh:167`
(heartbeat, `otel_status_code` 1/2), `backup-alert.sh:62` (`unit_failure` via systemd `OnFailure=`).
Dataset `dolt-backup` (`setup-backup-alerts.sh:101`). Alerting is server-side Honeycomb triggers.
The running Dolt sql-server (127.0.0.1:3307) emits NO telemetry itself. **Flag:** which Honeycomb
ENV `dolt-backup` lands in is key-dependent (comments imply the agent-activity/claude-collector
key, likely NOT `livespec`) — verify before writing triggers. Fix locus: dataset/env + triggers
= server-side; event-shape / adding sql-server OTel = CODE in `scripts/`.

## Adopter: homelab (`/data/projects/homelab`)

Independent of livespec enrich code. NixOS module `nix/modules/telemetry.nix` (enabled by
default), Honeycomb env `homelab`:
1. **Heartbeat** — shell script via `systemd.timers.heartbeat` (1min): reads `comin status --json`,
   computes convergence gap + closure drift, `POST .../1/events/${DATASET}` (Events API). Default
   dataset `fleet`. Source of "comin heartbeat" + "closure drift".
2. **otelcol-contrib** — `services.opentelemetry-collector`: host_metrics + prometheus (comin at
   127.0.0.1:4243) → `otlp_http/honeycomb`. Source of "hostmetrics".
Key from AWS SSM Parameter Store → `/run/telemetry/honeycomb.env`. Alerting = server-side triggers.
Fix locus: trigger/dataset = server-side; emitted fields / pipelines = CODE in `telemetry.nix`
(deploys via comin pull-convergence, not a manual push).

## Code-change vs server-side (at a glance)

- **Server-side only (no repo code):** dataset routing / OTTL transforms / env-key selection in
  `otel-collector/config.yaml`; all Honeycomb triggers/SLOs/dead-man alerts (livespec, homelab,
  dolt-backup envs); ingest-key rotation.
- **Needs repo CODE:** beads-fabro enrich/emit + sandbox projection + receiver (primary);
  dev-tooling step-timer/heartbeat; the CI exporter template (then propagate to ~9 members);
  dolt-server `scripts/`; homelab `telemetry.nix`.

## Gaps to fold into scope
- `livespec-console-beads-fabro` has NO telemetry wiring at all.
- Which process binds `:4318` in production was asserted-but-deferred in `_otel_enrich.py`;
  live-verified 2026-08-16: it is the beads-fabro Python receiver (pid 472831, plugin cache).
- `dolt-backup`'s Honeycomb ENV not pinned in-repo (key-dependent); verify target env.
