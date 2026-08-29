---
proposal: factory-spend-expiry-clause.md
decision: modify
revised_at: 2026-08-29T10:05:07Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

The proposal correctly identifies that the ratified expiry clause made a provider-stated reset instant normative when the already-shipped admission-gate code correctly never adopts it, and that the measured falsification (a 95.9-hour claim contradicted by a success 9m24s later, same unrotated account) justifies amending the spec to match the code. Modified at the maintainer's explicit direction during ratification review: the original proposal wording assumed a provider always communicates availability timing in some window-reset shape and grounded the bounded-default-expiry requirement in resource-economics reasoning (a scarce metered allowance eventually replenishing). The maintainer correctly identified that this reasoning does not hold for a self-hosted or free model, which has no metered allowance to replenish, and asked for wording that makes no assumptions about whether or how any given provider signals its own availability. The landed text drops the provider-specific "window resets" framing, explicitly handles the case where no availability claim is offered at all, and grounds the bounded-expiry requirement in a liveness/no-permanent-lockout argument instead of a resource-economics one: whatever triggered an exhaustion record, correctly or by misclassification, holding it forever is a self-inflicted outage regardless of whether the provider is metered. A second independent reviewer confirmed this argument is sound and general, including against a stress-test case (a self-hosted model that is permanently gone: retry simply fails again cheaply, with no unbounded harm). Scenario 94 gained a third case (no availability claim offered at all) to test the generalization directly. One residual gap was identified and deliberately deferred rather than folded into this change: there is currently no operator-facing manual-clear mechanism for an exhaustion record, which matters most for self-hosted deployments the operator directly controls; the maintainer confirmed this should be filed as a separate follow-up rather than expanding this wording fix's scope.

## Modifications

Relative to the original proposal:

- Dropped the provider-specific "window resets" framing throughout; the clause
  no longer assumes any provider communicates availability timing at all, or
  that a timing claim (if offered) follows any particular shape.
- Removed the specific empirical justification ("measured wrong by orders of
  magnitude", tied to one observed Codex refusal) from the normative clause
  text. That evidence remains in this proposal's own Motivation section as the
  historical basis for the change; it no longer appears in the ratified rule
  itself.
- Replaced the resource-economics justification for the bounded-default
  expiry (an implicit assumption that a scarce metered allowance exists and
  eventually replenishes) with a liveness/no-permanent-lockout justification:
  a refusal that never expires is itself a self-inflicted outage, independent
  of whether the provider is metered.
- Added explicit coverage for "no availability claim offered at all" (not
  only "a claim was offered but is untrusted"), and stated the rule holds
  uniformly across a commercial vendor, a different account with that vendor,
  and a self-hosted or free model.
- Scenario 94 (renumbered from the proposal's "Scenario 92", since 92 and 93
  were claimed by unrelated revisions landed after the proposal was drafted)
  gained a third Given/When/Then case covering the no-claim-offered path,
  alongside the claim-offered-but-untrusted and successful-dispatch-retires-
  the-record cases.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-29T10:03:22Z
verdict: NO BLOCKERS
proposal_stem: factory-spend-expiry-clause
content_digest: aad9b7fa619652758cb05b578eeefbfda80706260bdb9a02f8c5ea05d6ca7147
