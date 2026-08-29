---
topic: dispatcher-staleness-gate-comparand
author: dispatcher-staleness-gate-comparand
created_at: 2026-08-29T11:55:18Z
---

## Proposal: Dispatch-admission plugin-currency surfaces staleness, never blocks; only a deliberate release floor refuses

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Re-base the dispatch-admission plugin-currency gate so it MUST NOT refuse dispatch merely because the executing operator-provisioned build predates the instantaneous latest release: running the provisioned payload is already ratified as legitimate, so ambient release-staleness MUST be SURFACED (the already-ratified canary restart-due, plus a new non-blocking needs-attention dispatcher-currency-staleness fact naming how far the provisioned build lags the latest release) rather than enforced by blocking dispatch. The ONLY blocking form the gate MAY carry is a deliberate operator-configured `dispatcher.minimum_release` floor, refused fail-closed when the executing release is below it. This removes an impl-stricter-than-spec condition: the shipped `_dispatcher_staleness_gate.py` hard-refuses (exit 3) whenever the executing build head does not equal the live `refs/heads/release` head probed at dispatch time, a blocking form that appears nowhere in SPECIFICATION.

### Motivation

On 2026-08-29 an adopter (homelab) dispatch was hard-refused (blocking, exit 3, journaled `dispatcher-staleness-refused`) because a release (v0.96.1, build ba30bc662f07) was published 83 minutes into an attended session that had been current at start (v0.96.0). No factory run occurred, and the only remedy is a full session restart, because plugin bindings resolve only at session start while the gate probes the moving `release` head at dispatch time. Any release published between session start and dispatch bricks every live session's dispatch until each restarts; on a multi-release day attended dispatch windows shrink toward zero. The shipped gate is STRICTER than the ratified self-update contract, which states that a host-side dispatch runs the last RELEASE the operator has provisioned, that the running process is never moved onto a newer candidate, and that 'detecting, canarying, and alarming is the whole of the Dispatcher's self-update responsibility.' The literal refusal string 'predates latest release' appears nowhere in SPECIFICATION, the ratified 'staleness' vocabulary is the SURFACED (non-blocking) detection-coverage facts, and the only restart-due scenario is the canary one (Scenario 54). The blocking gate entered through the fix lane (33bf8d5d, 2026-07-24, no spec citation) and has already needed two corrective fixes for adjacent over-blocking (ad715ea3, 96ce547e / bd-ib-n7ce4n), which is evidence the comparand, not the implementation, is the problem. Provenance and full measurement: plan/dispatcher-staleness-gate-comparand/research/001-staleness-gate-incident-and-ratified-divergence.md, re-verified against HEAD e094a3e4. Co-edit note (outside the spec target): adding a `## Scenario` to scenarios.md requires an accompanying entry in `tests/heading-coverage.json` per this repo's revise co-edit discipline; the revise pass that accepts this proposal MUST make that co-edit atomically. The four in-flight `spec/*` branches surveyed at authoring time (adopter-neutral-janitor-bootstrap, codex-config-shell-quoting, factory-spend-expiry-clause, repair-snyquw6-reference) touch adjacent contracts.md areas only and none edits the self-update section or Scenario 54; this proposal ALIGNS with all four.

### Proposed Changes

Amend `SPECIFICATION/contracts.md` in the section beginning **"Self-update triggers on a version comparison, and every promotion is canaried"** and add a companion `SPECIFICATION/scenarios.md` scenario, as follows.

### contracts.md — bound the gate's blocking authority

Add a clause to the self-update section:

> **The dispatch-admission path MUST NOT block on ambient release-staleness.** The plugin-currency check that runs before a dispatch is admitted MUST NOT refuse dispatch, and MUST NOT return a blocking exit code, on the sole ground that a newer RELEASE exists than the executing operator-provisioned build. Running the operator-provisioned payload is legitimate per this section; the comparand for any blocking decision MUST be the operator-provisioned payload, NOT the instantaneous latest-release head probed at dispatch time. When the executing build cannot be proven to predate anything the operator deliberately required, the check MUST proceed. A release published after a session starts MUST NOT brick that session's dispatch; freshness pressure is carried by surfacing (below), not by refusal.

> **Ambient staleness is surfaced, not enforced.** When the executing operator-provisioned dispatcher build lags the latest available release, the needs-attention snapshot MUST carry a non-blocking dispatcher-currency-staleness fact stating how far the provisioned build is behind (in released versions and/or elapsed time) and naming the restart-and-update remedy, modeled on the detection-coverage staleness facts in the "Detection coverage records and staleness facts" subsection. This fact is a surfaced TRIGGER; it MUST NOT itself refuse or gate a dispatch, and it composes with the already-ratified passing-canary "restart is due" surfacing rather than replacing it.

> **The sole blocking currency form is a deliberate operator floor.** The gate MAY refuse dispatch fail-closed (exit 3, journaled) if and only if the operator has committed a `dispatcher.minimum_release` floor in this repo's `.livespec.jsonc` AND the executing release is below that floor. Absent that key the gate has no blocking authority over currency. `dispatcher.minimum_release` (optional; when present, a released-version identifier) is a human-chosen safety floor for a release known to be safety-critical, never an ambient latest-release comparison. When the floor cannot be evaluated because the executing or available release is unobservable, the gate MUST record that it could not determine currency (distinct from recording that the floor was satisfied) and MUST proceed rather than fail open into a false refusal or a silenced pass.

### scenarios.md — the behavior

Add a `## Scenario` (numbered per the file's sequence) with, at minimum:

```gherkin
Feature: Dispatch admission surfaces plugin-currency staleness rather than blocking on it,
  so a release published mid-session never bricks a live session's dispatch

  Scenario: A release published after session start does not refuse a dispatch from the provisioned build
    Given a session whose executing dispatcher build was the latest release when the session started
    And a newer release is published before the session dispatches
    And no `dispatcher.minimum_release` floor is configured
    When the Dispatcher admits a ready work-item
    Then the dispatch is not refused on plugin-currency grounds
    And no blocking `dispatcher-staleness-refused` record is journaled
    And a non-blocking dispatcher-currency-staleness fact surfaces that the provisioned build lags the latest release

  Scenario: A deliberate release floor refuses a below-floor dispatch fail-closed
    Given a committed `dispatcher.minimum_release` floor
    And an executing release below that floor
    When the Dispatcher admits a ready work-item
    Then the dispatch is refused fail-closed with an actionable diagnostic naming the floor

  Scenario: Unobservable currency is recorded as undetermined and does not refuse
    Given the executing or available release cannot be determined
    When the plugin-currency check runs at dispatch admission
    Then it records that currency could not be determined
    And it does not refuse the dispatch on currency grounds
```

The implementation that follows this revision MUST remove the ambient `refs/heads/release`-head refusal from `_dispatcher_staleness_gate.py`, retaining the identity-first exemptions and re-basing any blocking decision onto the `dispatcher.minimum_release` floor, with the lag surfaced through the needs-attention composer. The revise pass MUST add the corresponding `tests/heading-coverage.json` entry for the new scenario heading.
