---
proposal: supervisor-handoff-hosted-artifact-in-the-thread-store.md
decision: accept
revised_at: 2026-07-25T00:08:28Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Maintainer-accepted 2026-07-25 via the plan-skill-supervisor-handoff session's per-proposal dialogue. Admits the reserved plan/<topic>/supervisor-handoff.md as a hosted, non-facet, non-handoff artifact the plan operation MUST NOT create, read, or validate, making the exception enumerated rather than an incidental non-match of the handoff*.md refusal glob — per the adopted design record livespec core plan/plan-skill-supervisor-handoff/design.md SECTION 11.3 and SECTION 4 item 2. Precondition met: independent adversarial review (separately-spawned Fable reviewer, 2026-07-24) returned NO-BLOCKERS on all five criteria and all three latent classes. Includes the proposal's named ratification co-edit: the mirroring third bullet in .claude-plugin/prose/plan.md SECTION 'The planning-thread store'. Sibling core amendment ratified as livespec v175 (livespec PR #1731).

## Resulting Changes

- contracts.md
- ../.claude-plugin/prose/plan.md
