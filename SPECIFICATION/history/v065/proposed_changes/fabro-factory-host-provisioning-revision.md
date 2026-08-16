---
proposal: fabro-factory-host-provisioning.md
decision: modify
revised_at: 2026-08-16T21:11:55Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fabro-on-hp
---

## Decision and Rationale

Both proposals are sound, additive, non-conflicting requirements about factory-host provisioning (web-console dual reachability; new-host credential sourcing reuses the fleet channel). Independent ratification review of the original draft found two structural blockers (no deciding command named, matching the file preamble requirement every sibling section satisfies; and a term collision reusing credential_wrapper for an unrelated concern). Modified to add Verification subsections and remove the term collision; a second independent review of the corrected bytes returned NO BLOCKERS.

## Modifications

Added Verification subsections naming the deciding command for each rule (matching every sibling section in this file, per the file's own preamble requirement), and removed the reuse of the already-defined contracts.md term 'credential_wrapper' -- replaced with generic prose ('the SAME project-configured secret-injection mechanism') so the new factory-host provisioning concern does not collide with the narrower, established per-dispatch-target sandbox-credential-injection meaning of that term. Both fixes per independent ratification review findings.

## Resulting Changes

- constraints.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: claude-sonnet-5
reviewer_identity: claude-sonnet-5
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-16T21:10:55Z
verdict: NO BLOCKERS
proposal_stem: fabro-factory-host-provisioning
content_digest: eccc69cb919ae528f010c9f9f9e40536490a80aa9fdf0941f3467cf4e3a06dfe
