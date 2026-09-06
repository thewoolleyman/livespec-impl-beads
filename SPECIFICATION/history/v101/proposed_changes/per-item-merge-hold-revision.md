---
proposal: per-item-merge-hold.md
decision: accept
revised_at: 2026-09-06T17:41:50Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5 (pluggable-factory-workflow-configs)
---

## Decision and Rationale

The proposal lands as written. Its three target spec files and its tests/heading-coverage.json co-edit were applied edit-by-edit with each anchor asserted to match exactly once; every numbered edit resolved, including edit 7's conditional insertion anchor, which takes its '### The three rework caps' branch because v100 landed first. The proposal's own contingencies are all discharged on this tree: Scenario 118 is taken by v100 so the new scenario keeps its proposed number 119 with no renumbering, contracts.md's H2 heading set is byte-identical to HEAD as edit 9 asserts, the wip_cap sentence of edit 8 and the Merge-strategy resolution paragraph of edit 6 are untouched, and the heading-coverage co-edit adds exactly one owned entry while modifying zero existing entries, so no unowned-TODO release tier arms. Doctor static over the edited tree reports 20 pass, 2 skipped and 0 fail, with anchor-reference-resolution passing over the new cross-references. No modification was needed, so the decision is accept rather than modify.

## Resulting Changes

- contracts.md
- scenarios.md
- README.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T17:41:08Z
verdict: NO BLOCKERS
proposal_stem: per-item-merge-hold
content_digest: c14878aca7fe109b784064317def0c7bff462c725e89cb4891724490e3650fa2
