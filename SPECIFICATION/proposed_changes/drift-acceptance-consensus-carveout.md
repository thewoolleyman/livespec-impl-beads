---
topic: drift-acceptance-consensus-carveout
author: claude-opus-5
created_at: 2026-08-04T12:09:52Z
---

## Proposal: Carve drift acceptance out of the human-gated-BY-DESIGN enumeration, consensus tier only

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Amend contracts.md section 'Every needs-human escalation still reaches a human' so that drift acceptance MAY be owned by the consensus tier when the governed repo has opted in via livespec core's `spec_governance.drift_acceptance_mode`, while every other floor in that section — the truly-unresolvable ban, the `needs-human` auto-resolve ban, spec-change slices, regroom/backlog bounces, `human-only` acceptance, and 'no release with zero verification' — remains verbatim.

### Motivation

livespec core's Increment 3 (repo `thewoolleyman/livespec`, epic livespec-jvdvx4, work item livespec-jvdvx4.5) ships `spec_governance.drift_acceptance_mode` (`human | consensus`, safe default `human`, opt-in, never `delegated`), which permits consensus-tier acceptance of drift-origin proposals. This section currently ENUMERATES drift acceptance among decisions that are human-gated BY DESIGN and MUST stay escalated. Those two cannot both stand.

This was nearly missed. The sibling `livespec-overseer` thread re-framed its own Phase D item away from 'a THREE-REPO reversal' on the reading that this section states a FLOOR over policy settings rather than a ban, so below the floor it is exactly config. That reading is correct in general and wrong for drift specifically: drift acceptance is one of the items the floor ENUMERATES, not something below it. Verified by reading this file directly rather than quoting it from a work item's description, which is how the original mis-framing arose. Filed from the livespec repo thread `plan/spec-side-autonomy/` as `bd-ib-qek6` in this tenant.

### Proposed Changes

In `SPECIFICATION/contracts.md`, section 'Every needs-human escalation still reaches a human', the following exact text (hard-wrapped as it appears in the file) MUST be replaced:

A decision that
is human-gated BY DESIGN — drift acceptance, a spec-change slice, a regroom /
backlog bounce, or a `human-only` acceptance — MUST stay escalated even when
the Dispatcher is fully confident.

It MUST be replaced by:

A decision that
is human-gated BY DESIGN — a spec-change slice, a regroom / backlog bounce, or
a `human-only` acceptance — MUST stay escalated even when the Dispatcher is
fully confident. Drift acceptance is human-gated by the same default and MUST
stay escalated unless the governed repo has opted in to the consensus tier
through livespec core's `spec_governance.drift_acceptance_mode`; under that
opt-in the consensus tier MAY own a drift acceptance, and only on unanimous
cross-vendor evidence that is present, fresh and conforming. No other setting,
and no `delegated` value, MAY accept drift, and the Dispatcher itself MUST NOT
accept a drift-origin proposal under any setting.

Every other sentence in that section MUST remain byte-identical. In particular the opening ban ('No policy setting MAY auto-dispose a truly-unresolvable decision'), the `blocked_reason: needs-human` auto-resolve ban, the 'no release with zero verification' floor requiring at least one AI pass per acceptance, and the ban on the Dispatcher creating net-new work-items MUST all survive unchanged. The carve-out MUST be narrow: it admits the consensus tier for DRIFT ACCEPTANCE ONLY and MUST NOT be read to widen any other enumerated class.

This amendment and livespec core's `livespec-jvdvx4.5` MUST agree, and neither MUST ratify on the assumption that the other already did.
