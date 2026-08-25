---
proposal: needs-attention-completeness.md
decision: modify
revised_at: 2026-08-25T15:50:32Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Ratified with modifications after both commissioned adversarial review legs (claude and codex) were triaged into plan research/005 and every accepted disposition was applied to the proposal bytes in a separate merged change (PR #1856), then a third defect was caught by the independent ratification reviewer and fixed here. The three Blockers are resolved at the source rather than papered over: the duplicated stale-claim fact is dropped because host-only:stranded-dispatch already composes that population under its own owner; the blanket release handoff that would have re-queued merged work is gone, with an explicit prohibition retained; and the mandate to consume the accounting directly is replaced by a required side-effect-free projection, because the shipped entry point appends a journal record on every call and the thin-transport surfaces are query-only by contract. Codex's unique finding - that the ratified envelope has no structured payload - forced the representation to flat items with their own stable ids, which is what makes the clause implementable without a runtime field change. Capacity is split into an unconditional single-authority rule and a narrowly triggered actionable-residue fact, so the section closes the section 03 re-derivation incident without turning the attention list into a dashboard. The wait set is closed over six enumerated waits - adding the two ratified ones the filing had omitted, host routing and provider exhaustion - plus a forward-registration rule, replacing a universal MUST that could not be checked. Scenarios 83-85 carry concrete counts and negative controls in place of the two vacuous assertions.

## Modifications

Three departures from the proposal's section 1 blockquote, all mechanical and none re-litigating a content decision. (1) Two dangling section citations the proposal carried were expanded to the headings that actually exist: 'Dispatcher admission' became 'Dispatcher admission, WIP cap, and post-merge acceptance', and 'Grooming' became 'Grooming and slice-size calibration'. Both were authored wrong in the proposal and were caught by the independent ratification reviewer; a self-check missed them because it matched headings by substring rather than exactly, so it could not have returned the other answer. (2) The capacity single-authority heading label was shortened from '(normative, unconditional)' to '(unconditional)' - the normativity is carried by the MUST/MUST NOT body text, so the label was redundant. (3) 'PREREQUISITE for the attention fact below' was corrected to 'PREREQUISITE for the capacity fact below', naming the fact it actually governs. The scenarios were split from the proposal's single fenced block into one gherkin fence per scenario heading, matching scenarios.md's established convention; their content is unchanged.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-25T15:49:45Z
verdict: NO BLOCKERS
proposal_stem: needs-attention-completeness
content_digest: 2689055723c0999e93237f1b4a5ba3d04f0bc16064c23ccec081f5a84865e4bc
