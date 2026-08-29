---
proposal: dry-run-not-picked-reasons.md
decision: accept
revised_at: 2026-08-29T00:08:51Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: fix-hp-disk-space
---

## Decision and Rationale

ACCEPT. Widens the Dispatcher's loop --dry-run obligation to report, per
ready-but-unpicked candidate, a single machine-stable exclusion reason drawn from a
closed set (WIP cap/budget, unsatisfied blocking dependency, --item filter exclusion).
Delivers the maintainer-commissioned second slice of the dry-run outcome-reporting work
(the picks half already ratified and shipped as bd-ib-omvia6, closed). Read-only-ness is
explicitly preserved; selection behavior is explicitly unchanged; the exclusion report is
explicitly required to accompany, not merge into, the existing selection output. Adds
Scenario 92, numbered as the next free integer above the current maximum (91) at
ratification time. One tests/heading-coverage.json entry added per this repo's revise
co-edit discipline, carrying a reason field that acknowledges the scenarios.md
integration/consumer-tier requirement (SPECIFICATION/constraints.md section "Heading
taxonomy" direction 4) and a work_item field (bd-ib-nt3cjv, freshly filed to own
implementing and testing this scenario) satisfying the TODO-ownership requirement
(SPECIFICATION/spec.md heading-coverage co-edit rule; enforced at commit time by
check-no-todo-registry's release tier, armed specifically because the staged changeset
authors a new TODO entry). Verified locally before this invocation:  and the full

::: just check-heading-coverage

::: just check-agents-ai-references-resolve

::: just check-claude-md-coverage

::: just check-handoff-dispatch-routing

::: just check-plan-anchor-declared

::: just check-vendor-manifest

::: just check-no-direct-tool-invocation

::: just check-check-tools

::: just check-no-todo-registry

All doc-only targets passed. (staged, replicating the real
pre-commit hook) both exit 0. Independently ratified NO BLOCKERS three times across
successive corrections; no functional content changed across any of the three passes,
only heading-coverage.json metadata (reason wording, then work_item ownership).

## Resulting Changes

- contracts.md
- scenarios.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-29T00:08:11Z
verdict: NO BLOCKERS
proposal_stem: dry-run-not-picked-reasons
content_digest: 0f1745ca4316006f6f34b238ababd34923a826e94bf6946e4b043e6cc28c77eb
