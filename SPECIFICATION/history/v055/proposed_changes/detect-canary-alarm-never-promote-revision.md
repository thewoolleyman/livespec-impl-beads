---
proposal: detect-canary-alarm-never-promote.md
decision: accept
revised_at: 2026-08-02T22:36:08Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

ACCEPTED as filed, unmodified. Ratifies bd-ib-4zif.3 on the maintainer's 2026-08-02/03 ruling: DETECT, CANARY, ALARM — NEVER PROMOTE. The Dispatcher detects a newer provisioned payload, canaries it on the host that will run it, and alarms; a passing canary surfaces that a restart is due, a failing canary keeps last-known-good and alarms fail-closed. It never writes code.

WHY v054 COULD NOT STAND. v054 required that a candidate 'MUST NOT become the running version until a CANARY of that candidate has passed', presuming an in-process promote that the SAME revision's release-pinned execution makes impossible: the execution root is an immutable installed payload with no .git, so there is nothing to write into, and a running process cannot re-point itself mid-run.

A RATIFIED-SPEC VIOLATION IS ALSO CLOSED, and it was not a judgment call. v054 contracts.md:1121-1123 forbids treating the presence of a writable orchestrator checkout as a reason to behave differently; _dispatcher_self_update.py:262 branched on exactly that predicate and returned before the canary at :271. Measured: the installed payload has no .git, so the guard was always false on the mandated path — the canary was UNREACHABLE in the execution mode v054 mandates and reachable only in the mode it forbids. v054 ratified a canary requirement whose sole reachable path it simultaneously outlawed; this pass makes the requirement satisfiable and states the prohibition at the point of use.

THE CANARY IS NOT WEAKENED. Its scope, host, interpreter, packaged layout, side-effect-freedom and fail-closed alarm carry over verbatim in substance. Only the consequence of a PASS changes.

REJECTED ALTERNATIVES, recorded so they are not re-litigated: (1) retire the layer and move the canary to provisioning time — loses the 'actual artifact, actual host, before it takes over' property that is the canary's entire value; (2) an external supervisor that re-points execution — would actually solve bd-ib-97v4 but is a much larger change needing its own design pass.

THIS DOES NOT SOLVE bd-ib-97v4. The human-typed /reload-plugins cost for a session that goes stale mid-work is EXACTLY UNCHANGED — neither improved nor worsened. The maintainer chose this option knowing that. bd-ib-97v4 remains OPEN and unaddressed by this work; it was raised to P1 on separate evidence.

NO heading-coverage co-edit: the map is H2-keyed, and this pass changes only a nested Scenario: line inside Scenario 54's gherkin block. Verified — the H2 text is unchanged and its single entry stands.

Intent-preservation gate: CLEAR. The amended promotion sentence cites no design record; the self-containment and identical-consumption commitments beside it are untouched.

SELECTIVE PASS. Only this proposal is processed. set-workflow-scope-override-spec-coverage.md is deliberately LEFT PENDING — it belongs to the plan/factory-hardening thread.

## Resulting Changes

- contracts.md
- scenarios.md
