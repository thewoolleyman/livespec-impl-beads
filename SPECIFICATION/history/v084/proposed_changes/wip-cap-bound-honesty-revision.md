---
proposal: wip-cap-bound-honesty.md
decision: modify
revised_at: 2026-08-28T23:43:19Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: fabro-factory-underutilization
---

## Decision and Rationale

The clause it removes is knowingly false in two independent ways, both measured. The absoluteness falsehood is bd-ib-aabn's, filed on the maintainer's 2026-07-30 instruction under the ruling that the code is correct and the contract incomplete, adopted here unchanged. Rewriting once rather than twice is correct for the stated reason. Modified to settle the checkout-versus-tenant scope question per the rider's recommended option (a), and to repair four further residual falsehoods plus one biconditional-completeness defect found by two independent adversarial reviewers checking the ratified text against the real dispatcher code, not the proposal's claims about it. Independent ratification review sessions: ratify3-naming, ratify3-bound (both sonnet, both NO BLOCKERS on the final bytes), preceded by ratify2-naming/ratify2-bound and ratify-naming-collision/ratify-bound-honesty (fable, superseded once the configured reviewer model was found to be sonnet; their findings drove the fixes verified here).

## Modifications

Accepted substantively as written, with the scope question its own later rider raises settled per the rider's OWN recommended resolution (a): the bound is stated TENANT-scoped, the host-observation prohibition is kept, and the current checkout-scoped implementation is recorded as a known divergence -- filed and named as bd-ib-snyquw.6 in the ratified text, not left implicit. The separability point -- tenant-wide claim counting requires bookkeeping, not host observation -- is stated explicitly.

Label agreement with the sibling: PER-REPO CLAIM CAP.

Scenario numbering: wip-cap-naming-collision accepted first (57), these land at 58/59 -- verified against final scenarios.md (no collision, 57-59 never issued in any committed revision) rather than trusted from the proposal's stale "max 56" measurement.

REPAIRED, beyond this proposal's own text, across two revise rounds: the same false formula appeared unrepaired in three other places in contracts.md (one added by an unrelated revise pass during the week this proposal sat pending) and once more in scenarios.md's Scenario 66 Given clause. A further defect -- the counted-claims biconditional's "when, and only when" not accounting for lock-less rework-pending rows, which the shipped predicate excludes unconditionally even under an unreadable journal (`_dispatcher_claim_reclaim.py`, rework-pending branch precedes the journal-readability branch) -- was found by independent review verifying the ratified text against the real code rather than against the proposal's own claims, and fixed by scoping term 2 to exclude that class, cross-referencing §"Rework-pending re-dispatch" and Scenario 66's third sub-scenario.

Both proposals' appends to §"Host concurrency belongs to the Fabro scheduler" were taken.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-28T23:43:13Z
verdict: NO BLOCKERS
proposal_stem: wip-cap-bound-honesty
content_digest: 85ffda84212e5cb92f8f86cdbddeaa7b5520ace06c7b56d1d2fa3b92686b0773
