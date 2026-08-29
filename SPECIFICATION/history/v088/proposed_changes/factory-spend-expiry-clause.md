---
topic: factory-spend-expiry-clause
author: claude-opus-5
created_at: 2026-08-28T23:30:00Z
---

## Proposal: An exhaustion record's expiry must not be the provider's own claim

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Amends the third paragraph of §"Provider spend containment" — "Every exhaustion
record expires" — to REMOVE the sentence making the provider-stated reset instant
normative, replace it with a bounded default expiry that applies in every case,
and require that an exhaustion record be falsifiable by a dispatch outcome. Keeps
the requirement that every record expires, which is the control that makes this a
discrimination rule rather than an outage. Adds Scenario 92. Flags the
`tests/heading-coverage.json` co-edit the accepting revise pass must make for that
new heading.

### Motivation

The ratified text currently asserts as normative something this plan measured to
be FALSE, and the shipped admission gate silently disagrees with it.

The clause reads, today, at `SPECIFICATION/contracts.md`:

> Where the provider's own refusal states when the window resets, that instant is
> the expiry.

C4's admission gate never adopts that instant. That is DELIBERATE AND CORRECT.

THE MEASUREMENT, recorded in commit c7443663 (PR 1791) and in FOREMAN RULING 4 on
ledger epic bd-ib-yhbsd4. A Codex refusal named a reset roughly 95.9 HOURS in the
future. Measured against it on the same `hp` factory: run 01M0PZ4PRVVK started
NINE MINUTES AND TWENTY-FOUR SECONDS after the refusing run and SUCCEEDED, both its
Codex implement and pr nodes completing; run 01M0Q01QB15W succeeded with a full
twenty-one-minute implement on the same two pinned tiers; and a direct host probe
returned normally. The control that closes the obvious escape was run and is
decisive: it was the SAME ACCOUNT — `auth.json` mtime unchanged at
2026-08-14T10:27:41 and the `account_id` inside it unchanged — so no rotation
happened between the refusal and the successes. The provider's claim was wrong by
orders of magnitude, in the direction that MAXIMISES lost capacity.

A SECOND INSTANCE, measured 2026-08-28 and independent of the first. A dispatch of
work-item bd-ib-8nnu failed on 2026-08-23 carrying `You've hit your weekly limit ·
resets Aug 28, 12am (UTC)` with `errorKind: rate_limit` — a claim roughly five days
out. Whatever the true reset was, the pattern is the same shape as the first: a
refusal message is a PREDICTION the provider makes about its own future behaviour,
and it is not obliged to keep it.

WHY A WRONG NORMATIVE CLAUSE IS WORSE THAN AN UNSPECIFIED ONE. A future implementer
reading the specification would build the wrong thing, and a reviewer grading an
implementation against the specification would REJECT the correct code that ships
today. The divergence is currently invisible: nothing in either artifact announces
that they disagree, and the code's silence reads as conformance.

THE EXPIRY CONTROL ITSELF MUST SURVIVE. It is load-bearing for the containment
obligation — it is precisely what keeps provider containment a discrimination rule
rather than a standing outage — so the clause cannot simply be deleted. It must be
replaced by an expiry rule an implementation can honour.

### Proposed Changes

In `SPECIFICATION/contracts.md`, §"Provider spend containment", REPLACE the
paragraph beginning "**Every exhaustion record expires.**" with the following.

**Every exhaustion record expires.** An observed-exhaustion record MUST carry an
expiry instant and MUST NOT be permanent. A bounded default expiry applies in
EVERY case. Where the provider's own refusal states when its window resets, that
instant MUST NOT be adopted as the expiry, and MUST NOT extend an expiry beyond
the bounded default; it MAY be recorded on the exhaustion record as provenance,
clearly marked as a provider claim rather than as an observation. The Dispatcher
MUST admit normally once the record has expired, and MUST admit normally against
any provider for which it holds no unexpired record. A rule that refuses
unconditionally is not containment; it is an outage.

**An exhaustion record is falsifiable by a dispatch outcome.** A provider-stated
reset instant is a prediction, not a measurement, and has been measured wrong by
orders of magnitude in the direction that maximises lost capacity. Accordingly, a
SUCCESSFUL dispatch outcome against the same provider MUST expire any unexpired
exhaustion record the Dispatcher holds for that provider, whether or not the
recorded expiry instant has been reached. The observed-not-predicted rule above
governs the CREATION of the record; this rule governs its RETIREMENT, and the two
are the same principle applied at both ends.

### Scenario additions

Add to `SPECIFICATION/scenarios.md`:

## Scenario 92 — A provider's stated reset instant does not extend an exhaustion record's expiry

GIVEN a dispatch fails with a typed provider usage-limit condition
AND the provider's refusal states that its window resets 95 hours in the future
WHEN the Dispatcher mints the observed-exhaustion record
THEN the record's expiry is the bounded default and NOT the provider-stated instant
AND the provider-stated instant is recorded as a provider claim rather than as an observation
AND a successful dispatch against that same provider expires the record even though the recorded expiry has not been reached

### What this proposal deliberately does NOT do

It does NOT change any admission-gate code. The code is already correct; the
specification is what is wrong, and this proposal moves the specification to the
code rather than the reverse.

It does NOT set a numeric value for the bounded default. That value is an
implementation choice within the ratified bound and does not belong in the
contract.

It does NOT relax the requirement that every exhaustion record expires, nor the
observed-not-predicted rule governing how a record is created.

It does NOT touch the two dead-implementer paragraphs or the no-silent-containment
journaling obligation, which are separate requirements under the same section and
are carried by other work-items.

### Required co-edit

The accepting revise pass MUST add an entry to `tests/heading-coverage.json` for
the new H2 heading "Scenario 92 — A provider's stated reset instant does not extend
an exhaustion record's expiry", per the revise co-edit discipline. No existing H2
heading is added, renamed, or removed by the `contracts.md` half of this proposal.
