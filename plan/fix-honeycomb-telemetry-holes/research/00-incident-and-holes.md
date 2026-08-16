# Incident & the Honeycomb telemetry holes it exposed

Provenance: authored 2026-08-16 by the `debug-fabro` session while investigating a
factory failure reported from Codex session `bd-ib-8f89`. Current-state claims below
were checked live against the running host (fabro `0.254.0 (8de6611)`), the Honeycomb
`livespec` env via the Honeycomb MCP, the fabro fork git history, and the fleet repo
tree. Treat every filed-item reference as a timestamped claim to re-verify, not fact.

## The incident (what we could NOT see)

A dispatched Codex ACP implement turn in `livespec-orchestrator-beads-fabro` died
("ACP turn failed"), stranding its work-item `active`. When we tried to root-cause it
we found we were **blind**: there is no queryable per-turn telemetry for the Codex
ACP path, and the fabro workflow swallows the real terminal error. The operator
(`bd-ib-8f89`) was reduced to guessing ("the Stop hook emits no JSON") because the
observability that would have shown the turn's command and stop reason was absent.

This plan exists to close every telemetry hole that made the incident un-diagnosable,
and to PROVE the closure by reproducing the incident's failure class in a sample
factory run and inspecting the now-present telemetry in Honeycomb.

## Confirmed holes (live-verified 2026-08-16)

1. **`run_turn` spans do not reach Honeycomb at all.** The `fabro` Honeycomb dataset's
   newest event is ~2026-07-30 (≈ when the current host binary was pinned); a live
   dispatch produced ZERO spans in the `fabro` dataset over 45m. The O4 `run_turn`
   emitter IS present in the running binary (`8de6611` = `b9b63a8` "add run_turn ACP
   span" + one commit; `git grep run_turn` hits `fabro-workflow/src/handler/llm/acp.rs`).
   So the break is DOWNSTREAM of emission — in the OTLP export / receiver / routing
   path — not the emitter. `run_turn` carries `command`, `config_name`, `visit`,
   `stop_reason`, `node_id`: exactly the fields that name which command a turn ran and
   how it ended. This is THE incident-critical hole. It is a regression WORSE than the
   attribute-drop the `otel-receiver-attr-verification` thread tracked (there the span
   arrived with attributes stripped; now the span does not arrive).

2. **The terminal ACP error is swallowed.** A failed turn records only
   `error="ACP turn failed"`; the verbatim provider/adapter error lives in the
   `stage.failed` event's `properties.failure.causes` and never reaches `fabro logs`
   at ERROR level, the escalate interview text, the dispatcher JSON envelope, or any
   queryable span attribute. Already filed as **bd-ib-g56f** (backlog, p1). Even a
   working `run_turn.stop_reason` would not carry the real cause string.

3. **Codex ACP turns have no Claude-parity enrichment.** Claude ACP turns emit rich
   spans to the `claude-code` dataset (`claude_code.llm_request`, `gen_ai.request.attempt`,
   `claude_code.tool*`) via Claude Code's native OTEL export (env-projected into the
   sandbox by `_dispatcher_projection.py`). The Codex adapter (`@zed-industries/codex-acp`)
   has no equivalent, so per-turn LLM/tool telemetry for Codex turns is absent beyond
   what `run_turn` would carry. (Depth of Codex-native OTEL availability is an open
   research question handed to the emission-architecture note.)

## Prior art (MUST reconcile, do not duplicate)

- **`plan/otel-receiver-attr-verification/`** (OPEN, ledger `bd-ib-98c.2`): its sole job
  is confirming the five `run_turn` attributes reach Honeycomb after the receiver
  allowlist widening (PR #777, `_otel_scrub.py ATTRIBUTE_ALLOWLIST`). Never confirmed —
  blocked on an execution-context trap: the `:4318` receiver is a single host-wide
  listener owned by whichever loop starts first, from the INSTALLED PLUGIN CACHE, not
  repo master. This plan SUBSUMES that verification (its DoD is a subset of this plan's
  exit criteria) — but note the failure has since regressed from "attributes dropped"
  to "span absent", so its diagnosis is necessary-but-not-sufficient.
- **`plan/fabro-otlp-telemetry/`** (OPEN, `bd-ib-i4r`): upstream fabro OTLP *logs* export
  (Bryan's Quarry design, PR #576). Outward-facing, maintainer-coordination-gated, NOT
  factory-safe. Adjacent, not the same axis; keep separate.
- **`plan/archive/codex-factory-telemetry/`** (ARCHIVED, epic `bd-ib-98c`): the O1–O5
  track that built factory observability for the Codex era — O2 traceparent join, O4
  `run_turn` span, the OTLP-vs-FABRO_LOG decouple. O5 token/cost (`bd-ib-98c.8`) and the
  O2 capture-site test guard (`bd-ib-98c.11`) remain open. This plan is the operational
  successor: the O-track BUILT the telemetry; we now must prove it actually flows and is
  regression-guarded.

## The live export topology (verified 2026-08-16)

- `172.17.0.1:4318` — OTLP receiver, `python3` pid 472831 (the beads-fabro E1
  enrich/scrub receiver, from plugin cache). This is the single host-wide listener.
- `127.0.0.1:4317` — `otelcol-contrib` (the central OTel Collector,
  `/data/projects/otel-collector/config.yaml`, listens 4317/4319; 4318 reserved for the
  E1 receiver).
- The fabro-server systemd unit exposes NO `OTEL_*`/`OTLP` endpoint env — a prime
  suspect for why fabro's own `run_turn` spans go nowhere.
- Emission architecture (WHY run_turn is lost) is detailed in a companion research note.

## Fleet & adopter scope (inventory 2026-08-16)

Maintainer scope: ALL livespec fleet members + dolt-server + homelab adopters; other
adopters out of scope unless there is server-/Honeycomb-side low-hanging fruit needing
no repo-code change.

Key inventory finding that shapes the plan: **the first-party enrich/emit code
(`livespec.otel.enrich`, the `_otel_*` receiver/scrub, the sandbox OTEL projection) is
bespoke to `livespec-orchestrator-beads-fabro` — it is NOT vendored into `livespec-runtime`
or any other member.** So the core incident fix is single-repo, NOT a fleet propagation.
The genuinely fleet-wide surfaces are narrower:

- **CI telemetry (`github-ci`)**: the shared `export-ci-telemetry.sh`, templated in
  `livespec/templates/orchestrator-plugin/` and copied into ~9 members. A fix there
  propagates per-repo. `livespec-console-beads-fabro` has NO telemetry wiring at all
  (a gap to flag).
- **The other orchestrator, `livespec-orchestrator-git-jsonl`**, also drives factory
  dispatches and needs run_turn/error-surfacing parity.
- **Server-side (no repo code)**: dataset routing, OTTL transforms, and env/key
  selection all live in `otel-collector/config.yaml` (one file, one host); Honeycomb
  triggers/SLOs. Much of the *rollout* is server-side.
- **dolt-server adopter**: backup observability via direct Honeycomb Events API
  (`scripts/lib/common.sh emit_honeycomb_event`), dataset `dolt-backup`, likely the
  agent-activity env (verify). The sql-server itself emits no telemetry.
- **homelab adopter**: independent NixOS `nix/modules/telemetry.nix` — comin heartbeat
  (Events API, `fleet`/homelab env) + otelcol-contrib hostmetrics. Deploys via comin
  pull-convergence.

## Exit criteria (maintainer-specified — the plan is not done until ALL hold)

1. The missing telemetry for THIS incident is present in Honeycomb: a Codex ACP turn's
   `run_turn` span (with `command`, `stop_reason`, and the failure cause surfaced)
   is queryable in the `livespec`/`fabro` dataset.
2. The incident's failure class (a Codex ACP turn failing) can be REPRODUCED in a
   sample factory run.
3. That reproduction's telemetry can be INSPECTED in Honeycomb and shows the cause —
   i.e. an operator hitting the same failure today could root-cause it from Honeycomb
   alone, without guessing.
4. The fix holds across the in-scope fleet members and the dolt + homelab adopters (per
   each surface's fix locus above), with a regression guard so `run_turn` silently
   ceasing to reach Honeycomb is caught, not discovered 17 days later by an incident.

## Open questions handed to the emission-architecture note / grooming

- Exactly where in export→receiver→routing is `run_turn` lost (fabro server OTLP env?
  the E1 receiver dropping non-allowlisted span *names*? collector routing? the plugin
  cache running pre-fix code?).
- Does a stale plugin-cache receiver on `:4318` account for both the incident and the
  never-confirmed `bd-ib-98c.2`?
- Can the swallowed `stage.failed` cause be exported as a `run_turn`/span attribute
  safely (secret-scrub parity, `ATTR_MAX_LEN`)?
- What is the minimal always-on regression guard (a Honeycomb trigger on `run_turn`
  absence? a post-dispatch assertion in the loop)?
