---
proposal: per-state-verb-vocabulary.md
decision: modify
revised_at: 2026-07-26T17:26:19Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accept the vocabulary, with one door rule corrected before it lands. The proposal is the maintainer-decided output of a completed brainstorm and closes a real gap: this repository's contracts are cited BY livespec-console-beads-fabro as owning the per-state valid-verb vocabulary, which was never authored, so no consumer could suppress a verb without inventing a vocabulary it does not own. As filed, however, the proposal was self-contradictory and false about two shipped paths: it blessed reject (rework|regroom) on the acceptance lane while also asserting that active is entered ONLY by a journaled dispatch, and it never stated where a rework return lands. Verified at source 2026-07-26: _drive_valves.py sets target_status = 'active' if reject_kind == 'rework', and _dispatcher_acceptance_rework.py writes status='active' under the acceptance-auto-rework disposition. Ratifying the door rule as written would have put a clause in the contract that two shipped code paths already violate. The defect was found by the livespec-orchestrator-beads-fabro dispatch-claim-liveness supervisor session on peer review and handed back before ratification.

## Modifications

1. The active-entry door rule now names the rework returns: 'active is entered ONLY by a journaled dispatch - factory dispatch or driver-dispatch - OR by a rework return from acceptance, which is either the reject:rework valve or the Dispatcher's own acceptance-auto-rework disposition.' Both returns are journaled, so the one-journaled-owner intent is preserved rather than weakened; the correction restores fidelity to the decided intent, which was to remove UNJOURNALED duplicate doors, not to deny journaled ones.
2. The reject clause now states where each kind lands: reject:rework returns the item to active, reject:regroom returns it to backlog. The proposal was silent on this.
3. Per this specification's own Intent-preservation rule, the section cites its design record (the console repo's verb-vocabulary-brainstorm.md and the filing draft) and carries its rationale, which the filed proposal body did not do in the spec text itself.
4. Wording bound to console-side file/line citations was generalized to the behavior being specified, since this is the orchestrator's contract and must not depend on a consumer's line numbers.
Everything else lands as proposed: the per-lane verb table, the removal of the three unjournaled duplicate doors, the dial-window rule, and driver-dispatch scoped to the host-only-refused set with its no-widening-without-a-claim-mechanism constraint.

## Resulting Changes

- contracts.md
