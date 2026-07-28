---
topic: set-workflow-scope-override-spec-coverage
author: plan/factory-hardening
created_at: 2026-07-28T22:14:19Z
---

## Proposal: Specify the set-workflow-scope-override operator verb

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The operator verb `set-workflow-scope-override:<id>:citation-only` is ENFORCED by `drive` today but has ZERO occurrences anywhere in SPECIFICATION/. It is absent from the per-lane valid-operator-verb sets and from every action-id enumeration. This proposal adds the missing specification coverage so the verb is specified where it is already enforced.

### Motivation

Measured 2026-07-28 by plan/factory-hardening: `grep -rn "workflow-scope-override" SPECIFICATION/*.md` returns 0 hits, while every sibling verb is specified — `set-admission` has 6 hits in contracts.md, `set-acceptance` 10, and each of the three cap verbs 3. That asymmetry is anomalous, not conventional.

It matters because contracts.md declares this vocabulary "OWNED here and consumed by console adopters", and livespec-console-beads-fabro defers per-item verb suppression to it explicitly. A console therefore cannot offer or suppress this verb while the enforcer accepts it in every lane. An operator's only route to discovering the verb today is the refusal message that names it.

The verb shipped through a full Red-Green-Replay dispatch (bd-ib-imzx24) with paired tests across five test files, a review node, and a green post-merge janitor, and no gate anywhere observed that it had no spec coverage — a repo-wide search finds no check asserting drive-verb/spec parity. Routed here on maintainer ruling because a spec change is human-gated; no SPECIFICATION/ file was edited directly.

Direction note for whoever reviews: this is the INVERSE of bd-ib-h57nx4 (advertised but not enforceable). A parity check written only in that direction would pass cleanly on today's tree and still miss this, so any mechanical check must be BIDIRECTIONAL. Tracked as evidence on epic bd-ib-dohu2g.

### Proposed Changes

Add `set-workflow-scope-override:<id>:citation-only` to contracts.md wherever its sibling policy verbs already appear, so the enforced surface and the specified surface agree:

1. **Per-lane valid operator verb sets** — add the verb to the lanes where `drive` actually accepts it, matching how `set-admission` and `set-acceptance` are listed. The enforcer accepts it in every lane today; the spec should state the intended lane set rather than describe the implementation by default.

2. **Action-id enumerations** — include it alongside the other `set-*` action ids so the enumeration is complete.

3. **A short dedicated subsection**, in the shape used by the sibling verbs, stating:
   - what it does: records a durable per-item override asserting that a work-item's mention of a `.github/workflows/` path is a CITATION, not a declaration of intent to edit, so the factory-safety admission heuristic admits it;
   - its value grammar: the single allowlisted value `citation-only`;
   - the ordering guarantee that makes it safe: `factory_safety` is checked FIRST, so the override can never admit an intrinsically host-only item (this ordering is already pinned by test_workflow_scope_override_admits_citation_but_not_factory_safety);
   - that it is an OPERATOR ASSERTION overriding a factory-boundary gate, and the alternative escape — an inline negation declaration in the item's own prose.

Rationale to cite: the vocabulary is owned by contracts.md and consumed by console adopters, so an enforced-but-unspecified verb breaks the consumer contract that section establishes.

Carry-forward worth ratifying alongside it: an item that adds a first-class OPERATOR VERB should carry a spec-coverage criterion in its acceptance, precisely because nothing mechanical enforces it today.
