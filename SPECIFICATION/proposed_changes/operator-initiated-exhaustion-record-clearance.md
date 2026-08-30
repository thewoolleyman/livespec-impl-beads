---
topic: operator-initiated-exhaustion-record-clearance
author: claude-opus-5
created_at: 2026-08-30T13:45:05Z
---

## Proposal: Operator-initiated clearance of an observed exhaustion record

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

The exhaustion-record contract enumerates how a record retires and names two mechanisms: its bounded expiry elapses, or a successful dispatch falsifies it. A third route -- an operator-initiated clearance -- shipped in pull request 2046 with no specification commitment. This proposal ratifies that route: that it exists, that it retires by APPENDING rather than by rewriting or deleting the observation, that it demands a stated reason, and that it refuses an unattributed invocation unconditionally so it cannot degrade into a second automatic-expiry path. Adds one clause to contracts.md and Scenario 107 to scenarios.md.

### Motivation

This is a RETROACTIVE ratification. The behaviour already shipped: work-item
bd-ib-yhbsd4.4 merged as pull request 2046 on 2026-08-30, adding a
`clear-provider-exhaustion` Dispatcher subcommand that appends a
`provider-exhaustion-cleared` journal line which the admission scan reads as a retirement.

The specification does not know it exists. Measured three ways on 2026-08-30: the merged
work-item's ledger record carries `spec_id: null`; no scenario in this tree covers operator
clearance of an exhaustion record; and the literal `provider-exhaustion-cleared` appears
nowhere under SPECIFICATION.

The gap is SILENCE, not contradiction, and the distinction is deliberate. The existing
clause reading "The one signal the Dispatcher trusts is a dispatch outcome" sits in a
paragraph about whether a PROVIDER's claim about its own availability is authoritative; an
operator is not a provider, so the shipped behaviour does not violate it, and the shipped
behaviour positively satisfies the ratified requirement to admit normally against any
provider for which no unexpired record is held. What is missing is any specification
commitment at all for a new operator-facing valve, in a section that explicitly enumerates
retirement and names two routes.

The most load-bearing thing to ratify is the unattributed-invocation refusal. It is the only
property preventing the valve from degrading into a second automatic-expiry path, it was
deliberately placed outside the `dispatcher.require_invoker` dial, and it currently exists
solely as an implementation detail that no specification obliges a future refactor to
preserve.

This proposal is filed from plan factory-spend-containment (ledger epic bd-ib-yhbsd4), whose
requirement carriers R1 and R2 are themselves retroactive ratifications of behaviour that
shipped unspecified. Closing that plan while its own final child shipped unspecified would
recreate the debt the plan was opened to retire.

### Proposed Changes

Add one new clause to `SPECIFICATION/contracts.md`, immediately after the existing
**An exhaustion record is falsifiable by a dispatch outcome.** clause, and one new
`## Scenario 107` to `SPECIFICATION/scenarios.md`. Update `tests/heading-coverage.json`
in the same change per this repo's revise co-edit discipline, binding the new scenario
heading to the tests that already exercise the behaviour
(`tests/livespec_orchestrator_beads_fabro/commands/test_dispatcher_provider_exhaustion_clear.py`
and `..._clearance_scan.py`).

AMENDMENT TO THE NEIGHBOURING CLAUSE, and it is REQUIRED rather than optional. Adding a
third retirement route without touching **An exhaustion record is falsifiable by a dispatch
outcome.** would leave the ratified spec contradicting itself in two places, because that
clause currently asserts exclusivity in both a signal sense and a scope sense:

- "The one signal the Dispatcher trusts is a dispatch outcome" — after this change an
  operator clearance is a second trusted signal. Amend to scope the exclusivity to what it
  was actually written about, provider self-reports: "Of the signals a PROVIDER offers about
  its own availability, the Dispatcher trusts none; the one signal it trusts is a dispatch
  outcome."
- "this rule governs its RETIREMENT" — after this change that rule governs only the
  observation-driven half. Amend to "this rule governs retirement BY OBSERVATION; an
  operator-initiated clearance is governed by the clause below."

Both edits are narrowing clarifications: they preserve the clause's whole intent, which is
that a provider's own claim about its future availability is never authoritative, and they
remove only the accidental exclusivity over a route that clause was not written to consider.
Neither weakens the falsification rule, and a successful dispatch MUST still retire an
unexpired record immediately.

CLAUSE, proposed text:

**An operator may retire an exhaustion record early.** Bounded expiry and dispatch-outcome
falsification are not the only ways a record retires. An operator who KNOWS a provider is
available again -- they restarted a self-hosted model, freed the GPU, corrected a
configuration -- can reach neither: the bounded default is sized for a commercial
rate-limit cadence that need not apply, and the admission gate refuses the very dispatch
that would falsify the record, so dispatch-outcome falsification is reachable only by a
race with a dispatch already in flight. The Dispatcher therefore MUST offer an
operator-facing mechanism that retires an unexpired exhaustion record for a named provider
without waiting for its expiry and without requiring a dispatch to occur first, and MUST
admit normally against that provider immediately afterwards, exactly as if the record had
expired.

The mechanism MUST record the clearance by APPENDING to the audit journal. It MUST NOT
rewrite or delete the observation it retires: the observation and the override are two
separate durable facts, and a reader MUST be able to see both. The appended record MUST
carry the provider, the acting identity, the time, and a stated reason; a clearance
asserts a fact about the world that no observation supports, so the assertion MUST be
stated rather than inferred from the act, and an absent or blank reason MUST be refused.

The mechanism MUST NOT become a second automatic-expiry path. An invocation that asserts
no identity -- one resolving to the unattributed invoker mark -- MUST be refused
unconditionally, and that refusal MUST NOT be governed by whatever configuration dial
governs invoker attribution on the dispatch entry points, because a dial that can be
turned off is not a floor. An automated caller that DOES assert an identity is permitted:
the requirement is attribution, not humanity, and asserting an identity makes the act
explicit, journaled and attributable rather than silent. A clearance against a provider
holding no unexpired record MUST be refused before anything is written, so no record ever
asserts an override that never happened.

This clause does NOT relax **Every exhaustion record expires.** A cleared record is
retired, not made permanent, and the bounded-expiry obligation continues to govern every
record the Dispatcher mints.

SCENARIO, proposed text for `## Scenario 107 -- An operator retires an exhaustion record
before its expiry`:

  As a factory operator
  I want to clear an exhaustion record I know is stale
  So that a provider I have just restored is not held out for a wait sized for someone
  else's rate limit

  Scenario: An operator clearance retires the record and admission resumes
    Given an unexpired observed provider-exhaustion record against provider "codex"
    When the operator clears that provider's record with a stated reason and an asserted
      identity
    Then the clearance is appended to the audit journal carrying the provider, the acting
      identity, the time, and the reason
    And the original observation record remains readable in the journal
    And a dispatch against provider "codex" is admitted normally

  Scenario: A clearance asserting no identity is refused
    Given an unexpired observed provider-exhaustion record against provider "codex"
    When a clearance is attempted by an invocation that asserts no identity
    Then the clearance is refused
    And nothing is appended to the audit journal
    And the record continues to refuse admission for provider "codex"

  Scenario: A clearance with no stated reason is refused
    Given an unexpired observed provider-exhaustion record against provider "codex"
    When a clearance is attempted with a blank reason
    Then the clearance is refused
    And nothing is appended to the audit journal

  Scenario: A clearance against a provider holding no record is refused
    Given the Dispatcher holds no unexpired exhaustion record for provider "anthropic"
    When a clearance is attempted for provider "anthropic"
    Then the clearance is refused before anything is written

