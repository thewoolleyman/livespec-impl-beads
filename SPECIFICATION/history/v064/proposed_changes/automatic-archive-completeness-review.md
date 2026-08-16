---
topic: automatic-archive-completeness-review
author: gpt-5.6-codex
created_at: 2026-08-16T07:26:33Z
---

## Proposal: Automatic completeness-review dispatch at the plan archive gate

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

The plan operation currently requires completeness-review evidence but does not produce it, leaving mechanically complete plans stranded until a human notices and commissions a review. The archive gate must become self-driving while preserving its independent-review and no-premature-archive safeguards.

### Motivation

Two independently observed plans were blocked only because the operation silently required evidence it did not spawn. The current repository example, multi-factory-support, was manually resolved and archived before this change, so the behavior needs a controlled live exercise rather than reliance on that historical plan.

### Proposed Changes

In contracts.md Archive on completion, add that when a plan operation resumes or drives an archive attempt whose mechanical child-disposition leg passes but whose ledger timeline lacks a valid independent completeness-review evidence reference, the operation MUST commission a fresh independent adversarial completeness reviewer. The reviewer MUST have had no role in that plan’s implementation, MUST compare all plan research including explicit deferrals against the complete child set, MUST spot-check closure evidence against the forge, and MUST record its result durably. The plan MUST remain unarchived until valid evidence exists; a reviewer’s self-attestation, missing durable reference, or failure to attest complete carrier coverage MUST NOT satisfy the completeness leg. Add Scenario 55 in scenarios.md covering the all-children-disposed/no-evidence trigger, fresh independent reviewer, durable evidence, and archive only after a successful attestation. The resulting revision MUST add Scenario 55 to tests/heading-coverage.json with an integration-tier test binding or a non-empty TODO reason.
