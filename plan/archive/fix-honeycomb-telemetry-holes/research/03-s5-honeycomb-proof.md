# S5 proof: an operator can now RCA a failed Codex ACP turn from Honeycomb alone

Captured 2026-08-17 during live S5 execution (`bd-ib-rdbtzo.5`).

## Scope note — what this proves, and what it doesn't

The reproduction below is a Codex ACP turn that FAILED at the application layer
(Codex correctly determined an impossible task and reported failure cleanly,
`stop_reason=end_turn`), not the original incident's protocol-level crash
(`error="ACP turn failed"`, no clean `stop_reason`). Deliberately forcing that
exact crash signature would mean crashing/OOMing a sandbox process on shared
`hp-xubuntu` infra — assessed as not worth the risk today (see the maintainer's
call recorded on this plan's ledger timeline). The reproduction below still
proves the core exit criterion: an operator can now see `command`, `node_id`,
`stop_reason`, and `duration_ms` for ANY failed turn in Honeycomb, which
session `bd-ib-8f89` (the original incident) could not do at all — it had
ZERO queryable telemetry for the failing turn and had to guess.

## Reproduction

A throwaway work-item (`bd-ib-rdbtzo.8`, filed and closed same-day, NOT real
product work) instructed the Codex implementer to open-and-append to a file
whose parent directory does not exist, retrying the identical failing command
5+ times before giving up. Dispatched via `dispatcher.py dispatch --item
bd-ib-rdbtzo.8` against the `hp` factory. The agent correctly retried six
times, made no repo mutation, and reported a structured failure via its own
outcome JSON. No PR was opened; the fabro run stalled at a human-decision
interview (expected — reflection has no auto-resolution for a "task is
genuinely impossible" outcome) and was removed with `fabro rm -f` after this
proof captured its telemetry.

## The exact queries an operator runs

1. **Discover the failed turn's span** — Honeycomb MCP `list_spans` (or the
   UI equivalent: New Query on dataset `fabro`, Visualize `COUNT`, Group By
   `stop_reason`, `node_id`) scoped to `environment_slug=livespec`,
   `dataset_slug=fabro`, `span_name=run_turn`, a recent time range. This
   alone answers "did a turn run and how did it end" — before this plan, the
   `fabro` dataset had received NOTHING since ~2026-07-30.

2. **Inspect one turn's attributes** — `get_span_details` (or UI: click a
   `run_turn` row) on the same scope surfaces `command` (the exact adapter
   argv — proves it's the Codex implementer, not Claude), `node_id`
   (`implement`/`pr`/`review` — which workflow stage), `visit` (retry
   count), `stop_reason`, and `duration_ms`, without composing a query by
   hand.

3. **A representative live sample from this reproduction window**
   (2026-08-17T11:26-11:28 UTC, `run_turn` spans, `node_id=implement`,
   `command` containing `codex-acp`):

   | command | node_id | stop_reason | duration_ms | visit |
   |---|---|---|---|---|
   | `npx --no-install @zed-industries/codex-acp -c 'sandbox_mode=danger-full-access' -c 'approval_policy=never'` | implement | end_turn | 41973.13 | 1 |
   | `npx --no-install @zed-industries/codex-acp -c 'sandbox_mode=danger-full-access' -c 'approval_policy=never'` | implement | end_turn | 56465.25 | 1 |

   Query PK: `4UUB9pkd4tC` —
   `https://ui.honeycomb.io/thewoolleyweb/environments/livespec/datasets/fabro/result/4UUB9pkd4tC`

4. **The real failure cause** (S3's fix, `bd-ib-rdbtzo.3`, PR #1492): for a
   turn whose fabro-side `error` is the generic `"ACP turn failed"`, the
   Dispatcher now reads `fabro inspect --json`'s `failure.causes[0]` and
   surfaces it into `DispatchOutcome.detail` and a span attribute, instead of
   only the truncated stderr tail — closing the gap that made session
   `bd-ib-8f89` unable to see anything beyond "the Stop hook emits no JSON".

## Contrast with the original incident

`bd-ib-8f89` (the incident operator) had: zero `run_turn` spans in Honeycomb
(dataset stale since ~2026-07-30), a swallowed real cause, and no fleet-wide
regression guard — so root-causing required guessing. Today, for ANY failed
Codex ACP turn: `run_turn` telemetry is live end-to-end from the actual
production factory host (`hp-xubuntu`, via the newly-built persistent
`otel-receiver.service` + Lever A), the real cause is surfaced rather than
swallowed (S3), and a dispatcher-loop assertion (S4, PR #1501) flags a
dispatch whose `run_turn` span never lands at all.
