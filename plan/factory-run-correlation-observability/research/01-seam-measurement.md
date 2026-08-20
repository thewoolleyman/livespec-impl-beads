# Seam measurement — the answer that precedes grooming

The direction comment on `bd-ib-qfv9` names one measurement to run **before**
grooming: *establish whether the fabro emitter can see the resource attributes
the overlay already projects.* That single answer was supposed to decide between
seam A and seam B.

It is answered here. The answer is **no** — and running it turned up a third
seam that is cheaper than either, because a large part of the identity this plan
wants **is already in Honeycomb** and is being discarded by our own code rather
than never emitted.

Measured 2026-08-20T23:40–23:47Z: Honeycomb team `thewoolleyweb`, environment
`livespec`, 24h window, via the Honeycomb MCP surface; plus code reads on
`master` at `08965315` and on the archived O1 plan. Every claim below names how
it was checked. These are timestamped claims about a live system — re-measure
before relying on them, which is the entire point of this plan.

## 1. The prescribed measurement: no, the fabro emitter cannot see them

`cc_otel_overlay_env` (`commands/_dispatcher_projection.py:48`) builds
`OTEL_RESOURCE_ATTRIBUTES=service.namespace=livespec-family,work.item.id=…,livespec.dispatch.id=…`
and `_dispatcher_credentials.py:195` passes it to `render_run_config_overlay`,
which lands it in the rendered `[environments.livespec-ci.env]` table — the
**sandbox** environment. It is the agent's env inside the container.

The `run` spans in the `fabro` dataset are not emitted from there. Per the
archived O1 plan (`plan/archive/codex-factory-telemetry/o1-worker-exporter-plan.md`,
code-traced on `factory-integration` 2026-07-16) they come from two host-side
processes:

- the **fabro-server** (`server.rs:4339`, `info_span!("run", id = %id)`), a
  long-lived fleet-shared daemon under systemd; and
- the **`fabro __run-worker`** subprocess, whose env is `env_clear()`ed and then
  narrowly re-injected (`spawn_env.rs` `WORKER_ENV_ALLOWLIST`, plus explicit
  `cmd.env` calls at `worker_runtime.rs:89-98`).

That same plan states the conclusion in its own words, and it is worth quoting
rather than re-deriving: *"this overlay targets the AGENT's telemetry inside the
sandbox, not the fabro server/worker. O1 wires the fabro processes; do not
assume the agent overlay reaches them."*

**Seam A is not merely unwired, it is structurally bounded for the server half.**
The fabro server starts once per host and outlives every dispatch, so no
per-dispatch value can ever reach its process env. Only the worker is spawned
per run, and re-injecting a per-run attribute there means the dispatcher must
carry it through the run request into the server and then into the spawn — a
change in the fabro fork, which is the outward-facing, expensive class of work
this repo deliberately treats as a last resort.

## 2. The correction that matters: identity is already arriving, on span events

The `run` span carries 17 attributes and every one is infrastructural,
reproducing the anchor's inventory exactly (`get_span_details`, span `run`,
dataset `fabro`, 100 sampled spans). But the *dataset* carries `run_id` and
`id` columns, and the anchor did not say which spans populate them. Asked
directly — `list_spans(populates_attribute=…)`, same window:

| attribute | populated by | count | root_count |
| --- | --- | --- | --- |
| `run_id` | `Workflow run started` | 49 | 0 |
| `id` | `Sandbox initialized` | 50 | 0 |

Those two names are **span events**, not spans (the `run` spans carry 46–50
`span.num_events` apiece). The O4 comment block in `commands/_otel_scrub.py`
records why that distinction is load-bearing: *"Span EVENTS … bypass this
allowlist"*. So the fabro run's own identifier reaches Honeycomb today, in the
right trace, on a sibling event — and is simply not on the span, where a
`GROUP BY` could reach it.

## 3. And our own allowlist is dropping the span-side copy

`ATTRIBUTE_ALLOWLIST` in `commands/_otel_scrub.py` is fail-closed: 55 keys,
anything unnamed is dropped silently at `_otel_enrich.py` with no error and no
log line. Probed directly against the frozenset:

| key | in allowlist |
| --- | --- |
| `fabro.run_id` | **yes** |
| `work.item.id`, `livespec.dispatch.id` | **yes** |
| `node_id`, `command`, `config_name`, `visit`, `stop_reason` | yes (added by O4) |
| `id` | **no** |
| `run_id` | **no** |
| any factory key | **no** — none exists in any of the 9 datasets |

The server's `run` span is created as `info_span!("run", id = %id)`. Its `id`
field is therefore emitted and then **dropped by our host-side stage**, because
`id` is not allowlisted. For the fabro run identifier specifically, this is not
a missing key at the emitter — it is a discard at the receiver, in our code, in
this repo.

The anchor's framing ("Missing key at the emitter, not an enricher bug") holds
for `work.item.id`, `livespec.dispatch.id` and the factory. It does **not** hold
for the fabro run id. That is the difference the measurement bought.

## 4. Corroboration that the enricher already writes to these spans

`service.namespace = livespec-family` is populated on 100/100 `run` spans while
being **absent** from `ATTRIBUTE_ALLOWLIST` — it is a resource attribute,
handled outside the span-attribute gate. And `library.name` is
`livespec.otel.enrich` on 100/100. Both say the same thing: our host-side stage
is already stamping these spans on their way out. The enricher is not a seam we
would have to open; it is one that is already open and already writing.

Note also what `service.namespace` demonstrates in miniature: it is present on
every span and identical on every span, so it satisfies a presence check and
answers no question at all. That is exactly the failure mode acceptance
criterion 5 exists to catch.

## 5. Seam C — the cheap path this measurement opens

Stated as a proposal for the grooming pass to accept, amend, or reject; it is
not a decision taken here.

1. Learn the fabro run id host-side from the `Workflow run started` event's
   `run_id` (and/or `Sandbox initialized`'s `id`) within a trace, and stamp it
   onto that trace's `run` spans as the **already-allowlisted** `fabro.run_id`.
2. `_otel_enrich.py` already maintains `work.item.id → {livespec.dispatch.id,
   fabro.run_id}`, and `livespec-dispatcher` spans already carry
   `fabro.run_id` — so inverting that map on `fabro.run_id` backfills
   `work.item.id` and `livespec.dispatch.id` onto fabro spans through
   machinery that exists.
3. That satisfies acceptance criteria 1 and 3 with **no fabro fork change**.
4. The factory (criteria 2 and 4) stays seam B, but shrinks: once the dispatcher
   emits it as a new allowlisted attribute, it propagates onto fabro spans along
   the same path as the rest of the triple. The journal half is independent and
   independently valuable.

**Ordering constraint, and it is hard.** Any new attribute must be added to
`ATTRIBUTE_ALLOWLIST` *before or with* the code that emits it. Otherwise it is
dropped silently and the verification returns a confident false negative. This
repo has already paid for that lesson once: `plan/otel-receiver-attr-verification`
exists solely because O4's five attributes were emitted correctly and dropped by
this same gate.

## 6. The assumption in seam C that is NOT yet verified

Seam C needs the `Workflow run started` event to reach the enricher **before**
the `run` span it must stamp. Ordering is plausible and favourable — the event
fires at run start while the `run` span is exported at close, and observed `run`
durations here are 1,012s–1,309s — but *plausible is not measured*. Treat it as
the first thing the implementing child must prove, not as established. If it
does not hold, the stamp needs a short deferral buffer or a second pass, which
changes the size of the work.

## 7. Verification will lie to you unless execution context is established first

The OTLP receiver is a single host-wide listener on `172.17.0.1:4318`, owned by
whichever dispatcher process bound it first, **running from the installed plugin
cache rather than from this checkout**. A receiver-side change in this repo does
not reach the running factory until the installed plugin refreshes past the
commit *and* the process owning `:4318` restarts. The full procedure, including
the two preconditions to check before dispatching anything, is in
`plan/otel-receiver-attr-verification/research/handoff.md` — read it before
running a confirmation dispatch, not after one returns a false negative.

Do not kill another track's dispatcher loop to force a clean window.
