---
proposal: wip-cap-naming-collision.md
decision: modify
revised_at: 2026-08-28T23:43:19Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: fabro-factory-underutilization
---

## Decision and Rationale

The measured 2026-08-22 misdiagnosis is real and the proposal's core judgement is right: the confusable moment is the act of READING a refusal or a config value, not the act of naming a key. Its explicit rejection of a rename is right and is recorded so it is not re-litigated. Modified to settle the shared label with the sibling proposal (both require this), to resolve the scope question its own later rider raised per that rider's own terms, and to repair six residual falsehoods found across two independent adversarial review rounds, none addressed by either pending proposal as filed. Independent ratification review sessions: ratify3-naming, ratify3-bound (both sonnet, both NO BLOCKERS on the final bytes), preceded by ratify2-naming/ratify2-bound and ratify-naming-collision/ratify-bound-honesty (fable, superseded once the configured reviewer model was found to be sonnet; their findings drove the fixes verified here).

## Modifications

Adopted PER-REPO CLAIM CAP in place of the mandated "per-repo LEDGER cap", as both proposals' Reconciliation sections prescribe verbatim ("Accepting either proposal WITHOUT settling the label MUST NOT happen").

SETTLED THE SCOPE QUESTION this proposal's own later rider raised ("The recommended label presumes a scope that is NOT yet settled"): the sibling proposal measured that the counted-claim bound is currently PER-CHECKOUT, not per-tenant. Adopted option (a) from the sibling's own analysis: state the bound as TENANT-scoped (matching the merge/rebase-contention rationale the cap exists for, per the 2026-07-30 bd-ib-aabn ruling) and record the current checkout-scoped implementation as a tracked divergence -- filed as bd-ib-snyquw.6, named explicitly in the ratified text -- rather than blessing the narrower behavior as a second sanctioned reading.

REPAIRED FIVE residual restatements of the exact falsehood this pass removes, found across two revise rounds and two independent adversarial reviewers, in text neither proposal itself touched: the loop-invocation "authority on how many items may be `active`" sentence; the admission-valve Capacity bullet's literal `count(active) < wip_cap`; the `0`-value clause's same formula; the Rework-pending re-dispatch section's "count of `active` items ... below `wip_cap`" (added by an unrelated revise pass while this proposal sat pending); and Scenario 66's Given clause carrying the same rework-capacity formula verbatim. A sixth defect -- the counted-claims biconditional's "when, and only when" omitting the rework-pending carve-out, falsifiable by a one-command measurement against `_dispatcher_claim_reclaim.py` -- was found by round-2 review and fixed by adding the carve-out as a scoped qualifier on term 2, preserving the code's actual branch order (live-lock, then rework-pending exclusion even under an unreadable journal, then journal-unreadable). Scenario 57's Feature line and Then steps use the adopted label.

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
proposal_stem: wip-cap-naming-collision
content_digest: 5dd0937a48c195297aa416d464460fcdf86215084666645a5934f33eda6e6373
