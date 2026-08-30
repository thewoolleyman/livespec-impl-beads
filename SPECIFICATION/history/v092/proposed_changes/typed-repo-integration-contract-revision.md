---
proposal: typed-repo-integration-contract.md
decision: modify
revised_at: 2026-08-30T08:48:45Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: janitor-argv-declared-resolution
---

## Decision and Rationale

Ratifies the maintainer's 2026-08-30 architecture ruling: the orchestrator<->governed-repo contract becomes a typed API — one versioned RepoIntegrationContract schema, one generic Declared|FleetDefault|Defective resolver, resolve-once-on-host projection, typed workflow inputs with a CI seam-equivalence check, and contract version = schema version — with existing key names and per-key clause semantics preserved and only the per-key mechanism superseded. The companion constraints make members-and-adopters-identical mechanically enforced via adopter+member fixtures and a fleet-toolchain literal ban. Each new MUST is paired with Scenarios 100-102. Independent sonnet ratification review returned NO BLOCKERS over the exact resulting bytes.

## Modifications

Supersession corrected relative to the proposal front-matter, which lists only dispatch-integration-validation-pass and declared-sandbox-toolchain: the ratified text additionally SUPERSEDES the unmerged declared-core-provisioning followup (its behavior is re-homed onto the generic resolver by resolved-contract-projection) and records the merged declared-janitor-check-suite as MIGRATED rather than superseded. Independent review also required: the Factory-sandbox toolchain disposition clause explicitly superseded (no-op arm as an explicit FleetDefault value); clause (5) scoped so a schema field realizes an already-ratified obligation and never bypasses the closed-set rule; and Scenario 100 extended with the reverse seam direction, the non-rendered-position token, and prompt/prepare-step projections. A third review round required per-field optionality in the resolver rule: the schema declares per field whether a fleet default exists, so an absent REQUIRED field (compat.pinned, which admits no safe default) resolves to Defective naming the absence rather than to a substituted moving tip.

## Resulting Changes

- constraints.md
- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-30T08:47:44Z
verdict: NO BLOCKERS
proposal_stem: typed-repo-integration-contract
content_digest: 42936f4180e3cd2c8f4abdfac955a75dae6a1d42715b2789450814d2586c5095
