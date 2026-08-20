# Opening brief — factory-run-correlation-observability

Ledger anchor: **bd-ib-qfv9** (P1, `epic`, filed
2026-08-20T23:36:51Z, `metadata.plan_slug=factory-run-correlation-observability`).
This thread was routed by maintainer directive; the anchor already existed when
the thread was created, so no second epic was minted. `epic.md` names it.

This note is the write-once opening research capture. It carries the anchor's
own description and the filing seat's direction comment **verbatim**, so the
thread's founding statement is readable from the filesystem without a ledger
round-trip. Everything below the two rules is quoted, not paraphrased — later
notes in this directory may correct or supersede it, but must not edit it.

Read next, in this order:

1. `plan/archive/codex-factory-telemetry/research/observability-gap.md` — why
   the pipeline was Claude-Code-native, and how the correlation triple is
   projected into the sandbox.
2. `plan/otel-receiver-attr-verification/research/handoff.md` — the receiver's
   fail-closed attribute allowlist and its documented false-negative trap.
3. `plan/honeycomb-telemetry-followups/research/01-guard-and-provisioning-findings.md`
   — independent corroboration, from a repo module rather than from Honeycomb,
   that fabro spans carry no correlation ids.

---

## Anchor title

> factory-run-correlation-observability: a fabro run span carries no work-item, dispatch, run or factory identity, so 'which factory did this run land on' is unanswerable from Honeycomb and from the journal

---

## Anchor description (verbatim, bd-ib-qfv9)

Plan anchor for plan/factory-run-correlation-observability (livespec-orchestrator-beads-fabro).

GOAL: make it possible to answer, from Honeycomb alone, which factory and which sandbox a given fabro run executed on, and to join that run back to the dispatch and work-item that caused it. Today that question requires hand reconstruction from a local append-only journal, and for the factory it cannot be answered at all.

WHY NOW, and the incident that exposed it. On 2026-08-20 a publish-stage defect (bd-ib-veid) was narrowed with a control of two runs in livespec-overseer that OVERLAPPED in flight: overseer-5serwd dispatched 22:25:34Z blocked at publish 23:05:49Z, while overseer-hgq4wi.19 dispatched 22:32:20Z went green and merged pull request 1340 at 23:10:59Z. Same repo, same host, same plugin build, concurrent. That control eliminated repo layout, dispatcher build, time-varying credential expiry and any global outage in one stroke, leaving per-run or per-sandbox state as the only surviving hypothesis class. The NEXT question - did those two runs go to the same factory - is the discriminator between a routing bug and a per-sandbox bug, and it was UNANSWERABLE from telemetry or from the journal. That is the hole this plan closes.

MEASURED STATE, Honeycomb team thewoolleyweb, environment livespec, 2026-08-20T23:32Z, over a 24h window:

1. THE FABRO RUN SPAN IS ANONYMOUS. get_span_details on span name "run" in dataset "fabro" (98 sampled spans) returns SEVENTEEN attributes and every one of them is infrastructural: duration_ms, error, library.name, library.version, meta.signal_type, name, service.name, service.namespace, span.kind, span.num_events, span.num_links, status_code, trace ids, type, Sample Rate. There is NO work-item id, NO dispatch id, NO fabro run id, NO repo, NO factory, NO sandbox identity. The span records that a run took some milliseconds and whether it errored, and nothing about which run it was.

2. THERE IS NO JOIN KEY BETWEEN THE DISPATCHER AND FABRO DATASETS. A column search shows work.item.id present in claude-code, livespec-dispatcher and livespec-smoketest but ABSENT from fabro; livespec.dispatch.id present in claude-code and livespec-dispatcher but ABSENT from fabro; fabro.run_id present in fabro-sandbox and livespec-dispatcher but ABSENT from fabro, which carries only a bare unqualified run_id column. So the dataset where the work actually executes shares no correlation attribute with the dataset that dispatched it.

3. THE ENRICHER CANNOT FIX THIS FROM WHERE IT STANDS, BY DESIGN. commands/_otel_enrich.py maintains an in-memory join map KEYED ON work.item.id and its own docstring states the constraint plainly: it only learns from a span that carries work.item.id, and a span with no work.item.id and none learnable gets only what it brought. The fabro run spans bring nothing, so no amount of backfill reaches them. This is not a bug in the enricher; it is a missing key at the emitter.

4. NO FACTORY ATTRIBUTE EXISTS ANYWHERE IN THE ENVIRONMENT. A column search across all nine datasets for factory, route, host, server and sandbox terms returns no such column. The factory IS resolved and IS recorded - commands/_dispatcher_factory_ledger.py exposes resolve_dispatch_factory_target() and record_dispatch_factory(), and items carry a dispatch_factory value in ledger metadata - but that value never becomes telemetry.

5. THE LOCAL JOURNAL HAS THE SAME HOLE. tmp/fabro-dispatch-journal.jsonl in livespec-overseer contains ZERO occurrences of dispatch_factory across the entire file, including on the dispatch-id stage entry that would be the natural place to record it.

RELATIONSHIP TO EXISTING WORK, checked before filing. bd-ib-98c (Codex-era factory telemetry) owns the EMITTER gap - the pipeline went dark for Codex-driven runs because it was Claude-Code-native. That gap is substantially addressed: fabro spans now land, emitted through library livespec.otel.enrich. THIS plan is the distinct downstream gap - the spans arrive and carry no identity. Do not fold this into bd-ib-98c and do not treat 98c's closure as covering it.

SCOPE BOUNDARY. This plan is about CORRELATION and ROUTE IDENTITY on telemetry that already flows. It is not a request for new datasets, not a sampling or cost change, and not a re-litigation of the emitter architecture.

---

## Direction comment (verbatim, thewoolleyman at 2026-08-20T23:38:48Z)

DIRECTION AND ACCEPTANCE SHAPE — from the filing seat. This is scaffolding, not a prescribed design; the grooming pass owns the cut.

THE ONE QUESTION THAT DEFINES DONE. A reader with only Honeycomb access, given two run identifiers, can determine whether those runs executed on the same factory and the same sandbox, and can join each back to its dispatch and work-item, WITHOUT reading a local journal file and without reconstructing from timestamps. Every criterion below is subordinate to that.

TWO CANDIDATE SEAMS, both already exist and neither is a new subsystem:

SEAM A - carry the join key into the fabro spans. The correlation triple is already projected into the sandbox as OTEL_RESOURCE_ATTRIBUTES by the dispatcher's overlay path (service.namespace, work.item.id, livespec.dispatch.id). The fabro-side emitter does not carry them onto its own spans. If the emitter picks up the same resource attributes, commands/_otel_enrich.py's existing join map starts working on fabro spans for free, because that map is keyed on exactly work.item.id. Preferred if it is reachable, since it fixes the general problem rather than one attribute.

SEAM B - emit the factory explicitly. commands/_dispatcher_factory_ledger.py already resolves and records the target through resolve_dispatch_factory_target() and record_dispatch_factory(). The resolved value needs to reach two places it does not reach today: the telemetry attributes, and the dispatch-id stage entry in tmp/fabro-dispatch-journal.jsonl. The journal half is small and independently valuable - it makes the reconstruction path work even when telemetry is degraded.

DO BOTH ONLY IF BOTH ARE CHEAP. If seam A lands the identity, seam B narrows to the factory attribute plus the journal field.

ACCEPTANCE SHAPE, as an enumerable checklist rather than prose (a 5,900-character prose acceptance was measured on 2026-08-20 to be split line-by-line by the evaluator and graded on continuation fragments):
1. A fabro run span carries the work-item id, and a query grouping fabro runs by work-item returns non-empty.
2. A fabro run span carries the factory it executed on, under a name that is stable and documented.
3. A fabro run span carries an identifier that joins to the dispatcher's own view of the same run.
4. The dispatch-id stage entry in the dispatch journal records the resolved factory.
5. A DISCRIMINATING CONTROL proves the new attributes reflect reality rather than a constant: two runs deliberately routed to DIFFERENT factories are shown to report different values. An attribute that is always present and always the same passes a presence check and answers nothing.
6. The 2026-08-20 question is re-run against real telemetry and answered: for two concurrent runs in one repo, whether they shared a factory.
7. Redaction is preserved - commands/_otel_scrub.py still governs anything added, and no credential, token or host secret is introduced as a span attribute.
8. Backfill is explicitly OUT of scope: historical spans stay anonymous, and the plan says so rather than implying the past becomes queryable.

CHEAPEST FIRST MEASUREMENT, before any code: establish whether the fabro emitter can see the resource attributes the overlay already projects. That single answer decides between seam A and seam B and should precede grooming.

PRIOR ART TO READ FIRST, so this is not re-derived: plan/archive/codex-factory-telemetry/research/observability-gap.md explains why the pipeline was Claude-Code-native and how the correlation triple is projected; bd-ib-98c is its anchor and owns the EMITTER gap, which is a different gap from this one; plan/otel-receiver-attr-verification and plan/honeycomb-telemetry-followups are adjacent live threads and should be checked for overlap before children are filed.

MEASUREMENT PROVENANCE. Everything in the description was taken from live Honeycomb through the honeycomb MCP surface on 2026-08-20T23:32Z against environment livespec over a 24h window, plus reads of the named modules in this repo. The span-attribute inventory is from get_span_details on span name "run" in dataset "fabro" at 98 sampled spans; the absence claims are from column searches across all nine datasets in the environment. Re-measure before trusting any of it as current - these are timestamped claims, and the whole point of this plan is that such claims should be checkable from telemetry instead.
