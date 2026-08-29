---
topic: repair-stale-snyquw6-reference
author: fabro-factory-underutilization
created_at: 2026-08-29T01:01:57Z
---

## Proposal: repair-stale-snyquw6-tracked-defect-reference

### Target specification files

- contracts.md

### Summary

The Per-repo WIP cap section's paragraph on tenant-scoping describes a per-checkout counting divergence as an open, tracked gap citing bd-ib-snyquw.6, but that item closed via PR #1969 which tenant-scoped the live-dispatch-lock counted-claim term. The paragraph is rewritten to state what the implementation now does, precisely, without overclaiming that every branch of the predicate is tenant-scoped.

### Motivation

Ratified 2026-08-28 as v084 (PR #1964), the paragraph reads: "the shipped predicate at the time of this revision computes claims from paths under the invoking `--repo` checkout only ... That divergence is KNOWN, tracked as `bd-ib-snyquw.6`". bd-ib-snyquw.6 closed roughly an hour later via PR #1969 (merge sha fe10bf36), which added a tenant-checkout registry (`_dispatcher_tenant_checkouts.py`) that the live-dispatch-lock branch of `claimed_active_accounting` now consults, so a claim held live by any checkout of the tenant is visible from every checkout's admission check. An independent completeness reviewer, commissioned to verify the wip-cap-accounting-honesty plan was safe to archive, found the ratified text stale about the very defect it names as its own closing item -- exactly the failure mode this plan's own thesis (the spec must describe what is actually bounded) exists to prevent. Verified directly against `_dispatcher_claim_reclaim.py` and `_dispatcher_tenant_checkouts.py` before drafting this proposal: the journal-unreadable term and its dependents (green-terminal reclamation, abandoned-claim detection) remain per-checkout by design -- each checkout still reads only its own dispatch journal -- so the fix closes the specific N-checkouts-admit-N-times-wip_cap divergence bd-ib-snyquw.6 measured, and the corrected text says so precisely rather than claiming every branch is now tenant-scoped.

### Proposed Changes

### Amend §"Per-repo WIP cap" — update the tenant-scoping paragraph

REMOVE the paragraph beginning "The counted-claim bound is TENANT-scoped" (the one citing `bd-ib-snyquw.6` as an open, tracked divergence) and REPLACE it with:

> The counted-claim bound is TENANT-scoped: it MUST count claims across every
> checkout of this repository (worktrees, janitor checkouts, and fresh clones
> alike), not only the invoking process's own checkout. A checkout holding a
> live dispatch lock (term 1 above) registers itself, keyed by the tenant its
> committed `.livespec.jsonc` declares, so a claim held live by ANY checkout of
> the tenant is visible from every checkout's own admission check — closing
> the specific divergence `bd-ib-snyquw.6` measured and tracked (two checkouts
> of one tenant reporting disjoint live-claim counts against the same ledger),
> where N checkouts could admit independently up to N × `wip_cap`. The
> journal-unreadable term (term 2) and the terminal-outcome classification it
> depends on (green-terminal reclamation, abandoned-claim detection) remain
> per-checkout by design — each checkout reads only its own dispatch journal —
> which does not reopen the over-admission divergence just closed: it biases
> toward counting MORE from a given checkout's own view, never fewer, matching
> term 2's existing fail-closed guarantee. Per-checkout counting REMAINS the
> implementation of term 2 and its dependents; tenant-scoping applies fully to
> term 1 and MUST NOT be read as extended to those by this section.

This is a status-of-implementation correction only. It does NOT alter the
TENANT-scoped REQUIREMENT itself (unchanged from v084), does NOT reopen or
weaken the host-observation prohibition in §"Host concurrency belongs to the
Fabro scheduler", and does NOT touch any Gherkin scenario — no scenarios.md
or tests/heading-coverage.json co-edit is required.
