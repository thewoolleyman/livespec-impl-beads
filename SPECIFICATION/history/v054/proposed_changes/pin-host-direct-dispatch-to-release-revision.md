---
proposal: pin-host-direct-dispatch-to-release.md
decision: accept
revised_at: 2026-08-02T18:15:23Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

ACCEPTED as filed, unmodified. Ratifies bd-ib-4zif.1 (epic bd-ib-4zif) on the maintainer's 2026-08-02 ruling: the orchestrator has standardized releases, so a dispatcher version should only be usable once past semantic-commit versioning, the CI gates, and the release cut. Comparing git SHAs and merged file lists against a local checkout is therefore the wrong question; the running RELEASE against the proposed RELEASE is the right one.

WHAT THIS RETIRES, stated precisely. This is NOT a drift correction. This section already ratified self-containment and identical consumption ("Fleet members and adopters therefore consume the orchestrator IDENTICALLY"), but it never mentioned releases, versions, or tags, and its degradation clause plainly CONTEMPLATED checkout-presupposing behaviors ACTING when a writable checkout is present — requiring them to no-op when one is ABSENT presupposes exactly that. The current host-direct mode was therefore ACCOMMODATED by ratified text, not forbidden by it. This pass RETIRES that accommodation. The load-bearing argument is the identical-consumption sentence: a fleet member running from a source tree and an adopter running from the installed payload are not consuming the same product, which is precisely what that sentence says they do.

THE TRIGGER IS RETIRED; THE CANARY IS NOT — and the canary is stated MORE strongly here than in the text it replaces. It MUST execute the candidate artifact itself, on the host that will run it, under the same interpreter and packaged layout, exercising import graph, argument parsing and check pipeline, side-effect-free; only a PASSING canary may promote; a FAILING canary MUST keep last-known-good AND alarm a human and MUST NOT be downgraded to a warning or skipped. Justification, scope searched = all of .github/ plus the justfile: `ledger-check` appears in ZERO CI gates; the one gate line executing dispatcher.py (justfile:742) runs a DIFFERENT subcommand from the repo layout rather than a staged candidate; and acceptance-live-golden-master.yml is workflow_dispatch-only, needs a privileged DinD host, and is referenced by nothing. CI never runs the candidate binary and never exercises the packaged payload layout, so the canary covers a dimension nothing else does. An earlier draft justified retiring it as superseded by the release pipeline; that was false and was corrected before filing. The separate CI gap is tracked as bd-ib-6gwk and is NOT part of this change.

NO ESCAPE HATCH, per the maintainer's explicit 2026-08-02 ruling. The ratified text says release pinning is the single execution mode and that no override, environment variable, or flag re-enables a checkout-dependent one. Any opt-in local-checkout mode would reintroduce the exact execution path being retired and keep the two-products problem alive in dormant form; going through merge and release takes minutes and is the repo's worktree-PR-merge discipline anyway.

Intent-preservation gate: CLEAR. The retired clause is descriptive of a degraded branch, not a design record, and it cites none. The self-containment and identical-consumption commitments it sits beside are strengthened rather than departed from.

Behavior/scenario discipline: the change introduces BCP14 clauses about observable behavior, so Scenario 54 is added (no existing scenario covered self-contained dispatch, self-update, or the canary) and tests/heading-coverage.json gains its entry in this same pass.

SELECTIVE PASS. Only this proposal is processed. set-workflow-scope-override-spec-coverage.md is deliberately LEFT PENDING: it belongs to the plan/factory-hardening thread and is not this thread's to accept or reject.

## Resulting Changes

- contracts.md
- scenarios.md
- ../tests/heading-coverage.json
