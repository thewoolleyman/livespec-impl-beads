# 002 — Phase 2 filings and the decisions they carry

Written 2026-08-25 by the `homelab-loop-hardening-orchestrator` session,
same day as seeding (research/001). All eight propose-change filings the
charge binds are FILED as pending proposals under
`SPECIFICATION/proposed_changes/`; none is ratified — each awaits this
repo's propose-change → adversarial review → revise lifecycle, and two
carry an explicit revise gate on the livespec-runtime baseline. Every
filing re-verified its review claims against primary sources before
authoring (per research/007's instruction); the §§04/05 filing re-took
every measurement itself.

## The filing inventory

| Proposal (pending) | Charge obligation | PR |
|---|---|---|
| `acceptance-rework-state-machine.md` | ONE state-machine change (007 fable 3 / sol 6) — keep `acceptance → active`, make fix-forward executable via a ledger-held `rework:pending` marker; drain-before-ready selection; `dispatch --item` override; `reconcile-merged` refusal; counted-claims capacity; NO `lane_reason` extension | #1826 |
| `needs-attention-verdict.md` | §01 (007 fable 4 / sol 10) — third verdict + evidence rule; park-under-every-policy disposition table; ONE public effective-criteria primitive (native → metadata-merged → description "Exit criteria", per `bd-ib-1dbg`); walls at ready/pre-dispatch (new exit code 5); advise at capture; sequenced with `bd-ib-tfpdya` | #1827 |
| `journal-invoker-attribution.md` | §06 (007 fable 5; 009 c-fable 3) — `--invoker` flag + `LIVESPEC_INVOKER` env, flag > env > marked fallback; `invoker`/`invoker_source` stamped once by the append layer; committed NOT-API-configurable `dispatcher.require_invoker` (default false) refusing fallback-only invocations at startup; generalizes v051 / `bd-ib-ktxb` | #1828 |
| `loop-probe.md` | §12 (007 fable 7 / sol 3; 009 R3) — probe TAKES a pre-filed `--item`, never files; `.livespec-probe/` sanctioned path + cleanup; residue scoped to own ids and before/after delta; unavailability fails, never clears; fixture-creating variants on fake/disposable tenants only | #1829 |
| `dispatch-preflight-persistence.md` | §§04/05 restated from journal evidence (007 fable 2) — three-outcome step discipline ratified; degraded outcome persists into the NEXT dispatch's refusal with pre-dispatch re-verification clear; committed `dispatcher.step_waivers`; declared `dispatcher.master_ci` (default `CI`/`ci-green`), fail-closed kept | #1830 |
| `temporary-setting-restore.md` | §13 (007 sol 8) — the LEDGER route: owned restore work-item with gradeable criteria; deliberately NO generic schema, NO condition DSL, NO new key (console lockstep untouched) | #1831 |
| `needs-attention-envelope.md` | Envelope early deliverable (007 fable 6; 009 c-fable 5; 010 R4/rt-sol-2) — wire envelope ratified in the producing repo; per-item field stability + skip-and-surface tolerance posture; loud producer validation; additive evolution; executable-as-advertised with the `bd-ib-dohu2g` negative control; ownership cut recorded. REVISE-GATED on the runtime baseline | #1832 |
| `detector-coverage-records.md` | §15 (007 sol 2 / fable 9; 008 sol 1 + corrected premise) — tenant-backed attributed ATTEMPT + all-or-nothing COMPLETED records on a committed coverage anchor; gap staleness as Step 13's BACKSTOP (v081 coordinating epic cited); drift staleness on API-configurable `dispatcher.drift_capture_merge_threshold` (default 1); scoped read-only exception. REVISE-GATED on the runtime baseline | #1833 |

## Decisions recorded (so review re-litigates deliberately, not accidentally)

- **State-machine transition**: extend the bounded `active` fix-forward
  contract (sol 6's stated default). `ready`+marker rejected (re-enters
  approval identity); `blocked`/`needs-rework` rejected (external-
  impediment reservation; `lane_reason` is shared-runtime + console
  vocabulary — extending it reverses the R4 cut for no gain).
- **§13**: the ledger route, sanctioned by sol 8's own "if no general
  schema is justified" branch. One observed instance does not justify a
  cross-repo condition DSL.
- **Per-key API-configurability declarations** (009 c-fable 2, made per
  key at filing time): `require_invoker` NOT API-configurable (an
  attribution dial must not be editable over the surface it audits);
  `step_waivers` NOT (relaxes a safety refusal; committed diff only);
  `master_ci` NOT (repo topology description); `drift_capture_merge_threshold`
  **API-configurable** — the console Settings lockstep is deliberately
  triggered and its legs belong to the console charge.
- **Ownership cut** (rt-sol-2, recorded in the envelope filing):
  livespec-runtime owns attention item types, `kind` vocabulary,
  stable-ID grammar, validator, pure normalizer over injected facts;
  THIS repo owns fact derivations, persistence, thresholds, the CLI
  envelope, handoff commands. New fact classes prefer broad existing
  kinds + additive ID forms; grammar/kind changes ratify in the runtime
  first.
- **Runtime sequencing** (010 R4, confirmed by the runtime session's
  ack): "baseline ratified" means an ACCEPTED REVISE with a new history
  snapshot in `livespec-runtime` (epic
  `livespec-runtime/livespec-runtime-mqsxsu`, baseline PR
  thewoolleyman/livespec-runtime#606) — never the proposal's merge. The
  two gated filings' accepting revise must verify their citations
  against the ratified baseline text.

## What is deliberately NOT filed yet

The needs-attention COMPLETENESS facts themselves — matrix §03 (the
admission accounting's capacity verdict composed into the snapshot),
§10 (ready-work aging), §11 (every orchestrator-owned wait per 009 R1's
population split) — are the remaining fact-class package. They depend on
the ratified runtime baseline for ID forms and kind fit, and on the
envelope filing's substrate, so filing them before the baseline snapshot
exists would re-state R1 and defer every concrete decision. They file as
ONE further propose-change once the baseline is ratified.

Also not performed here: any ratification (revise), any implementation
child, any scope event — children are cut at revise time behind a scope
event, factory-first per this repo's standing rules.
