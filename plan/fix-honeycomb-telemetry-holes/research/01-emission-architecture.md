# Telemetry EMISSION architecture (how spans are produced and shipped)

Compiled 2026-08-16 from a read-only code survey. `file:line` pointers are into
`/data/projects/livespec-orchestrator-beads-fabro` unless another repo is named.
One hypothesis from the survey is CORRECTED inline by live host verification (see D).

## Two independent ingest planes

1. **Sandbox/dispatch plane** (carries `claude-code`, `fabro`, `fabro-sandbox`,
   `livespec-dispatcher`): sandbox emitter → `http://172.17.0.1:4318` (Docker bridge)
   → host-local Python `OtelReceiver` (`commands/_otel_receive.py`, port 4318, armed by
   `_dispatcher_otel_wiring.arm_otel_egress`) + file-tail `OtelEnrichDriver` →
   enrich/scrub (`_otel_enrich.py`) → `HoneycombHttpExporter` **direct OTLP/HTTP to
   `https://api.honeycomb.io/v1/traces`** (`_otel_enrich_export.py:22`) with
   `HONEYCOMB_INGEST_KEY_LIVESPEC`. A bespoke, stdlib-only processor — NOT an otelcol.
2. **Host otelcol plane** (`/data/projects/otel-collector/config.yaml`): gRPC
   `127.0.0.1:4317` (host Claude Code) + `4319` (debug). Deliberately omits 4318
   (reserved for the Python receiver). Exports `bd-guard` + host/docker metrics only.

The incident holes are ALL on plane 1.

## A. `livespec.otel.enrich` (v0.1.0) — bespoke, single-repo

Lives only in this repo: `commands/_otel_enrich_export.py:132` stamps the scope
`{"name":"livespec.otel.enrich","version":"0.1.0"}` + `service.namespace=livespec-family`;
`honeycomb_dataset_for` (`:53-60`) derives the Honeycomb dataset straight from a span's
`service.name` (fallback `livespec-unknown`). Core enrich/scrub: `_otel_enrich.py`
(`enrich_span :189-225` allowlist scrub + fail-closed reject + correlation-triple stamp;
`CorrelationJoin :114-158`). Tail/driver: `_otel_enrich_tail.py`, `_otel_enrich_driver.py`.
Receiver: `_otel_receive.py`, `_otel_scrub.py`, `_otel_http_handler.py`, `_otel_parse.py`.

## B. How Claude ACP turns reach `claude-code`

Claude Code's OWN native OTEL self-instrumentation, switched on by env projected into
the sandbox: `_dispatcher_projection.py:48-73 cc_otel_overlay_env()` sets
`CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_{METRICS,LOGS,TRACES}_EXPORTER=otlp`,
`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`, `OTEL_EXPORTER_OTLP_ENDPOINT=http://172.17.0.1:4318`,
`OTEL_EXPORTER_OTLP_PROTOCOL=http/json`, correlation triple in `OTEL_RESOURCE_ATTRIBUTES`.
`service.name` left as CC's default → `claude-code` dataset. Nothing in the enrich lib
synthesizes these; they exist only because CC self-instruments.

## C. Why Codex ACP turns emit NOTHING (the gap is total)

`@zed-industries/codex-acp` honors none of the CC/OTEL env knobs and never initializes an
OTEL provider. In-repo, code-verified research:
`plan/archive/codex-factory-telemetry/research/codex-otel-support.md` — verdict
`no-native-otel` for codex-acp@0.16.0: adapter installs a fmt-only `tracing_subscriber`,
never calls codex-core `build_provider`; codex-core reads OTLP endpoint/protocol ONLY from
`~/.codex/config.toml [otel]`, NOT from `OTEL_*` env. The factory runs
`CODEX_IMPLEMENTER_ADAPTER` (`_dispatcher_fabro_argv.py:83-86`) on implement/fix/pr/review_fix
(`fabro_run_argv :208-228`). `honeycomb_dataset_for` has no `codex` service mapping.
**Consequence: the fabro-side `run_turn` span is the ONLY telemetry that can ever exist for
a Codex turn** — which is why its export break (D) is the crux of the incident.

## D. The fabro `run_turn` span + why the `fabro` dataset went stale (~2026-07-30)

Emitter: `factory-integration:lib/crates/fabro-workflow/src/handler/llm/acp.rs:338`
`tracing::info_span!("run_turn", node_id, command, config_name, visit, stop_reason=field::Empty)`
(commit `b9b63a8a6`). OTLP export module: `factory-integration:lib/crates/fabro-cli/src/otel.rs`
— `otel_layer()` **activates ONLY when `OTEL_EXPORTER_OTLP_ENDPOINT`/`_TRACES_ENDPOINT` is set**.
P2 decouple from `FABRO_LOG`: `logging.rs:377,403,433,470` (commit `9048a8d52`).

CORRECTION to the survey's leading hypothesis — VERIFIED LIVE 2026-08-16:
- The survey saw the fabro WORKING TREE checked out on `fix/classify-provider-spend-limit-not-transient`
  (v0.310, no otel.rs) and inferred the running binary had drifted off-pin. That inference
  is about the working tree, not the server.
- The RUNNING server binary is `fabro 0.254.0 (8de6611 2026-07-30)` — the correct pinned
  `factory-integration` tip. `git grep run_turn 8de6611` DOES hit `acp.rs`. So the emitter IS
  present in the running binary. **Do NOT conclude "re-pin fabro" without checking the env.**
- Most-likely actual cause: **fabro's `otel_layer()` is inactive because the fabro-server
  systemd unit exposes NO `OTEL_EXPORTER_OTLP_ENDPOINT`** (verified: `systemctl show
  fabro-server -p Environment` has no OTEL/OTLP var). With no endpoint, `otel_layer()` never
  installs an OTLP exporter and `run_turn` spans are emitted into a layer that ships nothing.
  The ~July-30 staleness coincides with the current binary's pin date — a unit/env change at
  re-pin is the prime suspect. Diagnosis must confirm whether the worker (O2 re-injects
  worker-OTLP env) actually receives an endpoint at process launch.
- Also possible/compounding: a stale plugin-cache `:4318` receiver dropping run_turn (this is
  the `bd-ib-98c.2` never-verified axis). Both must be checked; they are not exclusive.

## E. The swallowed terminal error — dropped at BOTH layers

- **fabro side (message flattening):** `fabro .../handler/llm/acp.rs:593,597` `map_acp_error`
  maps every arm to top-line `message="ACP turn failed"`. The verbatim cause survives in
  `error.rs:580-590 causes()` / `to_failure_detail() :675-690` → `FailureDetail{message,
  causes, category, signature, exec_output_tail}` on the `StageFailed` event / fail Outcome.
  (Tests `error.rs:2424-2452` confirm the real cause is in `detail.causes`.)
- **livespec side (never reads it):** `_dispatcher_engine.py:308-315` — on `fabro.exit_code!=0`
  the `DispatchOutcome.detail` is just `tail(fabro.stderr)`. It never parses `fabro inspect
  --json` / `fabro events --json` `failure.causes` (those argv builders exist at
  `_dispatcher_fabro_argv.py:260-283` but are used only for liveness/watchdog).
- **Fix loci:** (1) fabro-side — mirror `FailureDetail.causes/category/signature` into the
  `run_turn` span's `stop_reason=field::Empty` slot on the failing arms
  (`acp.rs:393 StopReason`, generic `Err :405-410`). (2) livespec-side — in
  `_dispatcher_engine.py:308-315`, read `fabro inspect --json` failure block and surface
  `failure.causes[0]` into `DispatchOutcome.detail` and a span attribute via enrich.

## F. Endpoint topology (summary)

Sandbox/dispatch spans reach Honeycomb DIRECTLY from the plugin's Python receiver/enrich
exporter, bypassing the otelcol. `otel-collector/config.yaml:9-19` documents 4318 being
reserved for that Python receiver. So a fix to run_turn/error surfacing touches the fabro
server OTLP env + the beads-fabro Python receiver/enrich/export code — not the otelcol.

## Uncertain / to confirm during diagnosis
- The actually-running server binary version was inferred correct (0.254.0/8de6611) via
  `fabro --version`; confirm the worker process gets an OTEL endpoint at launch (O2 path).
- Whether the `:4318` receiver (pid 472831, plugin cache) carries the PR #777 allowlist fix.
- The exact ~July-30 change that stopped fabro OTLP (env/unit diff, or a receiver swap).
