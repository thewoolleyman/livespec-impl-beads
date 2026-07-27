---
proposal: reconcile-merged-dispatch-lock.md
decision: modify
revised_at: 2026-07-27T19:17:23Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted in substance and modified in one clause. The substance is not speculative: every requirement it states is already SHIPPED — the `--force` flag, all four lock fields (work_item_id, pid, started_at_epoch, dispatch_id), the distinct `janitor-reconcile-<work-item-id>` checkout path, the default-branch `--base` filter and the ambiguous-PR refusal — while the ratified paragraph it replaces still mandates a dispatch-heartbeat read that `_dispatcher_reconcile_merged.py` no longer performs at all. Ratifying closes live spec-to-code drift rather than opening new work. Its 'a red janitor ... MUST leave the item `active`' clause was re-checked against the ratified v050 door rules rather than the pre-v050 analysis, and it is honored literally by the shipped S3 slice (bd-ib-pme57n, PR #1014), which narrows the WIP-cap arithmetic and leaves the row's status untouched; post-v050 that is the only coherent option, since bare operator moves into `active` were removed from every lane.

## Modifications

One sentence changed. The proposal's closing enumeration — '`acceptance`, `done`, and `pending-approval` remain forbidden `move` targets' — is byte-identical to the ratified text it replaces, and v050 made that list incomplete by removing bare operator moves into `active` from every lane. The enumeration now reads '`acceptance`, `done`, `pending-approval`, and `active`'. The proposal did not introduce the gap; it inherited one v050 created, and per SPECIFICATION/spec.md §'Intent preservation' a revise pass is the sanctioned place to resolve a conflict between ratified statements. No behavior changes: the door was already closed by v050, the sentence merely failed to say so.

## Resulting Changes

- contracts.md
