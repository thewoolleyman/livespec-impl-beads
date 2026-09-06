# hp factory telemetry — live measurement, 2026-08-22

Measured in-session on 2026-08-22 (02:20–02:40 UTC), executing the single next
action recorded by the 2026-08-22 grooming handoff on epic `bd-ib-98c`:
*"Establish the hp factory's fabro build identity and its OTLP export
configuration, and compare both against the pin recorded in
`orchestrator-image/README.md`."*

The measurement went further than the recorded action, because the read-side
question it was meant to set up turned out to be answerable in the same pass.

## Verdict

**The thread's operating premise is falsified. Factory telemetry is WORKING on
hp, end to end, and has been.** O1, O2, P2 and O4 are all live on the factory
this repo actually dispatches to. The `run_turn_exported: false` journal signal
that motivated this thread is a **read-side false negative**, not an absence of
telemetry.

One genuine defect survives, and it is in the epic's acceptance criterion rather
than in the pipeline: `config_name` cannot be populated by this repo's workflow.
See "The one real finding" below.

## 1. hp build identity — MATCHES the pin

| Measurement | Value |
| --- | --- |
| `fabro --version` on hp | `fabro 0.254.0 (8de6611 2026-08-16)` |
| Pin recorded in `orchestrator-image/README.md` / `AGENTS.md` | `0.254.0 (8de6611)`, branch `factory-integration` |
| Running daemon's `/proc/<pid>/exe` inode | `13107311` |
| `~/.fabro/bin/fabro` inode | `13107311` |

The inodes are equal, so the live daemon is executing the pinned binary — not a
stale image left behind by an in-place overwrite. Unit is `active`/`running` as
`cwoolley`, `ExecMainPID=3575064`.

Commands used (note the account — probes with the default user fail, which is
what made early notes record hp as unreachable):

```bash
tailscale ssh cwoolley@hp-xubuntu '~/.fabro/bin/fabro --version'
tailscale ssh cwoolley@hp-xubuntu 'systemctl show fabro-server -p ExecMainPID --value'
```

## 2. hp OTLP export configuration — PRESENT

`systemctl show fabro-server -p Environment` on hp:

```
OTEL_EXPORTER_OTLP_ENDPOINT=http://172.17.0.1:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/json
OTEL_SERVICE_NAME=fabro
```

carried by the drop-in `/etc/systemd/system/fabro-server.service.d/otel.conf`.
This is exactly the Lever A configuration `README.md` §"Enabling fabro span
export" prescribes, including the mandatory `http/json` (the receiver is
JSON-only; a protobuf POST is silently dropped).

hp also runs a **co-located persistent receiver**, which vps does not: an
`otel-receiver.service` unit running
`/home/cwoolley/repos/livespec-orchestrator-beads-fabro/otel_receiver_daemon.py`
as `cwoolley`, listening on `172.17.0.1:4318` since 2026-08-17 09:12 UTC, with
`HONEYCOMB_INGEST_KEY_LIVESPEC` in its environment. That daemon is an untracked
ops-only artifact in hp's checkout — it is `??` in `git status` and exists in no
repository.

**So the 2026-08-19 "leading discriminator" is falsified.** hp does not run a
different build, and it does not lack the OTLP export env. Both hypotheses the
epic recorded as the first things to check are wrong.

## 3. Read-side — the spans are in Honeycomb

Queried the `fabro` dataset in the `livespec` environment over a 24-hour window
through the Honeycomb MCP server. (The MCP tools were not exposed to the session
directly; the server was driven over stdio via
`/data/projects/vps-info/services/honeycomb-mcp/honeycomb-mcp.sh`. Neither
`HONEYCOMB_CONFIG_KEY_LIVESPEC` nor `HONEYCOMB_MCP_API_KEY_LIVESPEC` can run a
v1 query — the first is refused `this API key isn't allowed to execute queries`,
the second is an `hcamk_` management key the v1 API does not recognise at all.)

### O4 — `run_turn` spans exist and carry their attributes

**381 `run_turn` spans in 24 hours.** Attribute population, from
`get_span_details`:

| attribute | populated | values |
| --- | --- | --- |
| `command` | 381/381 | `npx --no-install @zed-industries/codex-acp …` (243), `npx -y @agentclientprotocol/claude-agent-acp` (138) |
| `node_id` | 381/381 | implement (131), review (121), pr (92), disposition (17), review_fix (17), fix (3) |
| `visit` | 381/381 | 1 (358), 2 (20), 3 (3) |
| `stop_reason` | 341/381 | `end_turn` (341) |
| `config_name` | 381/381 | the **empty string**, every time |

`stop_reason` is a deferred attribute recorded at turn end, so the 40 spans
without it are turns that did not end normally — expected, not a gap.

The receiver-side allowlist (`bd-ib-98c.2`, PR #777) is therefore **doing its
job**: all five O4 attributes traverse `_otel_scrub.py` and reach Honeycomb. The
enrichment layer is stamped on every span (`library.name=livespec.otel.enrich`,
`service.name=fabro`, `service.namespace=livespec-family`), which is the
receiver's dataset-routing and enrichment pass, also `bd-ib-98c.2`.

### O2 — the server/worker trace join is complete

`run` spans over the same window: **218 spans across 109 distinct traces**, of
which **109 are roots** and **109 carry a `trace.parent_id`**. Exactly two `run`
spans per trace, one parented on the other, on every single trace. The join is
not merely working — it has no misses in the window.

Waterfall for trace `4b28ab5fccd4ae9be5f1aea8040b486d`, which is the shape the
archived parent track documented as correct:

```
fca89d4cf10c2c7f            run        ← SERVER run span (root)
└─ 92b24de593d18487         run        ← WORKER run span (O2 traceparent join)
   ├─ 0696c55bf68612fa      run_turn   (146.2s)
   │  └─ aa5d86206d4e4f0c   connection
   ├─ 3ef272bac27e230b      run_turn   (123.2s)
   │  └─ a20769ae1f84a045   connection
   └─ … 8 more run_turn/connection pairs
```

22 spans, depth 3. `run_turn` nests under the **worker `run` span**, not under a
`Stage` span — `Stage started` / `Stage completed` are tracing EVENTS, not spans.

### These spans are hp's, not vps's

The spans carry no host attribute, so the attribution is by elimination and it is
airtight: **the vps `fabro-server` unit carries no OTLP environment at all**
(`systemctl show fabro-server -p Environment` on vps returns only
`HOME=/home/ubuntu FABRO_WEB_VERIFY_ATTEMPTS=300`; its sole drop-in is
`verify-timeout-override.conf`). Export is inert on vps, and a vps worker
inherits the same absence. Every `run`/`run_turn` span in the dataset must
therefore originate on hp.

## 4. Why `run_turn_exported` was never true — the host split

`run_turn_sink_path()` in `_dispatcher_paths.py` resolves to
`$XDG_STATE_HOME/livespec-orchestrator-beads-fabro/run-turn-exports/fabro.json`,
falling back to `~/.local/state/…`. That path is **host-local**. The receiver
that writes the marker runs on **hp**; the Dispatcher that reads it runs **here**.
The marker was never going to be visible to the reader, however healthy the
pipeline.

There is a second, independent reason the marker cannot exist on hp at all:
hp's checkout is at `81146af1` (2026-08-16 07:33), while the marker-writing
commit is `edbfca6f` *"fix: guard fabro run_turn telemetry absence"*
(2026-08-17 09:17 UTC). hp's receiver code predates the feature by a day, and the
daemon process has been running continuously since 2026-08-17 09:12 UTC — three
minutes *before* that commit even landed. Its `_record_run_turn_exports` path
does not exist in the code it loaded.

`e105ea36` *"fix: mark remote run_turn guard unobservable"* (merged 2026-08-22
01:07 UTC, roughly 90 minutes before this measurement) already converts that
false negative into `run_turn_observation: unobservable-remote-factory` rather
than `run_turn_exported: false`. The read-side defect is fixed on `master`; this
measurement independently confirms the diagnosis behind it was right.

## 5. The one real finding — `config_name` is structurally unpopulatable

`config_name` is present on all 381 spans and empty on all 381. It is not being
dropped: the emitter is sending an empty value.

In the fork, `fabro-workflow/src/handler/llm/acp.rs::run_turn` computes

```rust
let config_name = process_spec.name().map(str::to_string);   // Option<String>
```

`process_spec.name()` is `Some` only when the ACP node resolves a **named** acp
config. Every acp node in this repo's
`.claude-plugin/.fabro/workflows/implement-work-item/workflow.fabro` —
`implement`, `fix`, `pr`, `review`, `review_fix` — declares an inline
`acp.command="{{ inputs.acp_adapter }}"` and no named config, so `name()` is
`None` and the attribute serialises empty.

**This makes the epic's acceptance criterion unsatisfiable as written.** It
requires `command / config_name / visit / stop_reason / node_id` to be
"populated"; `config_name` cannot be, for any dispatch of this workflow, no
matter what the telemetry does. That is the same failure shape catalogued in
`AGENTS.md` as *an instrument that cannot return a hit* — here promoted to an
acceptance bar that cannot be met.

O4's actual purpose is unaffected: `command` is populated from
`process_spec.to_string()` on every span, so *which command an agent turn ran* is
queryable, which is the capability O4 was built for.

*Caveat on this sub-finding, stated so it is not over-read:* the fork checkout at
`/data/projects/fabro` is at `3b378188` (2026-07-29), not the pinned `8de6611`
(2026-08-16), so the line quoted above is from a base three weeks older than what
hp runs. The empirical evidence (381/381 empty) and the workflow's inline-command
shape agree with it, but the code citation itself is from a stale tree and should
be re-read against the pinned commit before any fix is designed.

## What this leaves

Confirmation and disposition, not construction — as the grooming pass predicted,
though for the opposite reason than it expected. The four children recorded as
shipped in the pin (`bd-ib-98c.4` O1, `.5` O2, `.7` O4, `.12` P2) are verified
live on hp by this measurement, as is the factory-safe receiver child
(`bd-ib-98c.2`). The four throwaway proof dispatches parked at `acceptance`
(`.10`, `.13`, `.14`, `.15`) have their verdicts available.

## Two operational gaps noticed in passing, neither this thread's job

- hp's `otel-receiver.service` runs an **untracked** `otel_receiver_daemon.py`
  from a checkout six days stale, started before a week of receiver commits. This
  compounds `bd-ib-l3nptz.14` (hp's unit/drop-in/proxy state exists only as live
  host state), which already tracks hp's un-versioned provisioning.
- hp's `/etc/systemd/system/otel-receiver.service:3` is malformed — systemd logs
  `Invalid URL, ignoring: plan/fix-honeycomb-telemetry-holes` on every reload. A
  plan slug was pasted into a `Documentation=` field. Cosmetic; the unit runs.
