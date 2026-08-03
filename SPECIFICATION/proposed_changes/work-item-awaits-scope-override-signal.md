---
topic: work-item-awaits-scope-override-signal
author: plan/01-action-registry-and-invoker (livespec-console-beads-fabro)
created_at: 2026-08-03T00:45:44Z
---

## Proposal: publish a per-item "awaits scope override" signal on the work-item read surface

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The per-item read surface should carry an explicit signal saying that a work-item has
been refused for factory safety **by the declared-workflow-edit arm**, and therefore that
`set-workflow-scope-override:<id>:citation-only` is the remedy available for it.

Today that fact exists only inside the Dispatcher at dispatch time. A consumer cannot
learn it from any published field, so **no consumer can offer the remedy the refusal
message itself names.**

### Motivation — measured, not inferred

Filed on the maintainer's decision of 2026-08-03, recorded verbatim: *the orchestrator's
per-item read surface gains an explicit refusal / awaits-scope-override signal, written
when dispatch refuses, consumed by the console as data.* Two alternatives were considered
and REJECTED: retrofitting refusal-state onto `factory_safety`, and a point-fix widening
the negation regex.

Measured against plugin build `4e3e883a08b3` on 2026-08-03, on a real refused item
(`livespec-console-beads-fabro-ccycuk`):

1. **`is_host_only_item` refuses on three ORDERED arms** (`_dispatcher_host_only.py:43-49`):
   (1) `item.factory_safety is not None`; (2) allow when the raw label
   `workflow-scope-override:citation-only` is present; (3) `_declares_workflow_edit(item)`,
   a regex over title/description/reason.
2. **Arm 3 fires only when `factory_safety` is null**, because arm 1 returns first. So the
   two conditions are disjoint by construction.
3. **Nothing writes `factory_safety` on an arm-3 refusal.** Every occurrence under
   `scripts/livespec_orchestrator_beads_fabro/` is a read or a serialization of an
   already-set field; the only assignments (`store.py:134,170`) read it back FROM labels.
   The refusal is therefore computed and discarded.
4. On the measured item: `factory_safety` is `None`, the declared-edit regex MATCHES, the
   negation escape does NOT match, and the override label is absent. The item is refused
   and stays refused, with no published trace on its record.

**The span that triggers the refusal is the item's own PROHIBITION.** The matched text was
`… MUST NOT\ncreate or update any file under '.github/workflows/' …` — an edit verb within
80 characters of the path, inside a sentence forbidding the edit. The refusal message
advises adding "an inline negation declaration", but `_NEGATED_WORKFLOW_SCOPE` requires the
phrasing `no files? (under|in) .github/workflows/`; an item saying "any file" complies in
substance and fails on wording. That inverts the incentive: it rewards NOT writing the
constraint down.

**A consumer-visible inconsistency this already causes.** `_host_only_reasons`
(`_needs_attention_work_items.py:167-175`) has two arms — the item field when non-null,
else the DISPATCHER JOURNAL (`tmp/fabro-dispatch-journal.jsonl`), yielding the literal
`recorded-refusal`. So the Attention list DOES surface the refusal (from the journal) while
the work-item record does not (the field is null). A consumer rendering both shows the
refusal in one pane and cannot offer its remedy in the other. Both are correct given their
inputs; the inputs disagree.

### Proposed Changes

1. **Publish the signal on the per-item read surface.** Add a field — suggested
   `awaits_scope_override` (boolean), named for what a consumer must decide, not for the
   internal arm that set it — asserting that the item is currently refused by the
   declared-workflow-edit arm and that the recorded override is the applicable remedy.
   Specify it in contracts.md alongside the other published per-item fields.

2. **Specify it as DISTINCT from `factory_safety`, and say why.** The ordering guarantee is
   already stated in the sibling proposal
   `set-workflow-scope-override-spec-coverage.md` — `factory_safety` is checked FIRST, so
   the override "can never admit an intrinsically host-only item", pinned upstream by
   `test_workflow_scope_override_admits_citation_but_not_factory_safety`. **The published
   signal must inherit that disjointness**: an item with a non-null `factory_safety` is
   NOT awaiting a scope override, because the override cannot admit it. Conflating them
   would lead every consumer to offer the remedy exactly where it provably cannot work.

3. **Specify when it is written and when it clears** — set when a dispatch attempt is
   refused by that arm, cleared when the recorded override is applied or when the item's
   text no longer triggers the arm — so consumers can treat it as current rather than
   as a historical marker.

### Consumer half — ALREADY SHIPPED, deliberately inert

`livespec-console-beads-fabro` merged its half on 2026-08-03 (its PR #600): the availability
predicate for `set-workflow-scope-override` reads `awaits_scope_override` from the wire and
is **inert until this signal is published**, so the action is honestly reported unavailable
rather than advertised-and-dead. It is consumed AS DATA with no re-derivation of the arm-3
regex, per the consume-don't-re-derive rule. When this ships, no consumer predicate changes.

That work also removed a defect worth naming here because it argues for the field: the
console had been testing `factory_safety == "host-only-refused"` — a Dispatcher STAGE name,
**not** a member of the published `FactorySafety` vocabulary
(`needs-host-secrets` | `mutates-host-machinery` | `needs-privileged-host`). The arm could
never fire on real data, and ten tests covered it by inventing the value they then asserted
on. A consumer forced to guess at unpublished state produces exactly that class of bug;
publishing the signal is what removes the incentive to guess.

### Relationship to the pending sibling proposal

Adjacent, not overlapping. `set-workflow-scope-override-spec-coverage.md` (filed
2026-07-28 by `plan/factory-hardening`) specifies the VERB where it is already enforced.
This proposal adds the per-item SIGNAL that tells a consumer when to offer that verb.
Ratifying either alone leaves the other gap open, and this one is what unblocks a cockpit
operator.

### Evidence

Two measured comments on `livespec-console-beads-fabro-w7d` in the console tenant carry the
full measurements. The console-side blocking edge is wired as
`external:livespec-orchestrator-beads-fabro:work-item-awaits-scope-override-signal`.
