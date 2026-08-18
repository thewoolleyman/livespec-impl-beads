# Honeycomb telemetry follow-ups

Follow-up thread from `plan/archive/fix-honeycomb-telemetry-holes` (epic
`bd-ib-rdbtzo`, closed and archived 2026-08-17). That plan's independent
completeness reviewer, and a second independent verification pass by a
fresh agent against live Honeycomb + the forge, both confirmed the core
fix holds: `run_turn` telemetry is flowing again with the expected
attributes, the adopter (dolt-server + homelab) triggers are live, and all
5 fleet-CI PRs are genuinely merged. Two shortfalls from that review were
documented but left without a ledger carrier at archive time; a third,
smaller precision gap surfaced during the follow-up verification pass.
This thread exists to carry them to closure.

## Independent verification findings (2026-08-17/18, second pass)

Re-queried live, from primary sources, after the plan archived — not taken
on report from the first completeness reviewer:

- **`run_turn` spans are genuinely live**: 79 spans in the trailing 24h in
  the `livespec` Honeycomb environment's `fabro` dataset, freshest sampled
  at 16:40:03Z with real dispatch data (`node_id=pr`, `command=codex-acp`,
  `stop_reason=end_turn`). All five originally-broken attributes
  (`command`, `stop_reason`, `node_id`, `visit`, `config_name`) are
  populated on real (non-test) spans.
- **Attribute-location imprecision** (requirement carrier EC1/EC3,
  delivered by S3/`bd-ib-rdbtzo.3`): the failure-cause attributes
  (`category`, `signature`, `cause_count`) do NOT live on the `run_turn`
  span itself — they live on separate failure-event spans (e.g. a
  "Pipeline cancelled" span carrying `category=canceled`, `cause_count=0`,
  `error=true`, `level=ERROR`). S3's own Done text says the cause string
  is "queryable in Honeycomb on the dispatch/`run_turn` span", which reads
  as (and may have been intended as) "the `run_turn` span" — that is not
  where the data actually lands. The underlying capability (an operator
  can RCA a failure from Honeycomb alone) is real and verified; only the
  span-name claim is imprecise. See item 3 below.
- **Homelab adopter triggers**: exactly 7 enabled triggers on the fleet
  dataset, covering the 5 Observability-floor requirements — matches S7's
  close_reason claim exactly, independently re-verified.
- **Dead-man trigger honesty check**: the `livespec` Honeycomb environment
  has exactly 3 triggers (release-pipeline, 2x bd-guard), none on the
  `fabro` dataset. `bd-ib-ehrdid`'s "not yet built" framing is accurate,
  not a concealed gap. See item 1 below.
- **Fleet-CI PRs**: independently re-verified 3 of the 5 merges directly
  via `gh api` (livespec-runtime#566, livespec-orchestrator-git-jsonl#664,
  livespec-console-beads-fabro#667), including #566 — the one PR the
  first completeness-review pass caught as falsely-believed-merged by an
  earlier session. All three: `merged=true`, `state=closed`.

Not independently re-checked in this pass (explicitly out of scope, not a
silent gap): livespec#2394 and livespec-driver-claude#514's merge state
(covered by the plan's own re-verification evidence instead); the causal
systemd/OTel-receiver mechanism (effect verified, not the mechanism); the
S4 regression guard's actual runtime behavior under an induced failure
(PR #1501 merged per ledger, not exercised in this pass).

## Requirement carriers for this thread

- **F1** — Build the Honeycomb-side dead-man trigger on zero `run_turn`
  spans in the `fabro` dataset over a rolling window, pairing it with the
  existing per-dispatch guard (`bd-ib-rdbtzo.4` / PR #1501). Already filed
  as `bd-ib-ehrdid` (status `ready`), standalone, not a child of the
  closed `bd-ib-rdbtzo` epic. Design intent and Accept criteria are on
  that item and in `orchestrator-image/README.md`'s "Fabro `run_turn`
  absence guard" section (corrected by PR #1522 to state plainly that the
  trigger does not exist yet).
- **F2** — Scope and build `livespec-orchestrator-git-jsonl` dispatcher
  `run_turn`/error-surfacing telemetry parity (the S2/S3 patterns from
  `bd-ib-rdbtzo`). Already filed as `bd-ib-tgmbcn` (status `backlog`,
  epic-shaped — explicitly deferred pending its own dedicated scoping
  pass, since that repo has no dispatcher/OTel infrastructure at all and
  this is a from-scratch subsystem build, not a mechanical port).
- **F3** — Correct the attribute-location imprecision above: either (a)
  amend S3/`bd-ib-rdbtzo.3`'s historical Done text is not editable (closed
  item, historical record — leave it), so instead (b) add a short, precise
  note to `orchestrator-image/README.md` (or wherever the run_turn/failure
  surfacing behavior is documented for operators) stating explicitly that
  the failure cause is queryable via a separate failure-event span in the
  same trace, not as a `run_turn` span attribute, so an operator building
  a Honeycomb query knows which span to filter on. Not yet filed as a
  dispatchable work-item — decide scope/wording during this thread's first
  working session.

## Explicit deferrals (inherited, not reconsidered here)

- Deep Codex-native OTEL, upstream fabro OTLP-logs export, O5/O2
  pre-existing O-track items, the fabro-fork `run_turn.error` attribute
  mirror, adopter repos beyond dolt-server + homelab, and parallel-branch
  span orphaning: all remain out of scope per `bd-ib-rdbtzo`'s original
  scope event. Nothing in this thread reopens them.
