---
topic: detect-canary-alarm-never-promote
author: claude-opus-5
created_at: 2026-08-02T22:08:49Z
---

## Proposal: Replace in-process self-update promotion with detect, canary, alarm

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Replace in-process self-update promotion with DETECT, CANARY, ALARM. The Dispatcher detects that a newer released payload is provisioned, canaries that payload on the host that will run it, and then ALARMS — a passing canary surfaces that a restart is due; a failing canary keeps the last-known-good running and alarms fail-closed. It never modifies, promotes into, or re-points its own execution artifact. The canary contract itself is unchanged and unweakened; only what happens AFTER a passing canary changes. Scenario 54's promotion scenario is amended to match. This does NOT solve bd-ib-97v4.

### Motivation

Maintainer ruling 2026-08-02/03, on ledger epic bd-ib-4zif slice .3.

WHY v054 CANNOT STAND AS WRITTEN. v054 says "A candidate release MUST NOT become the running version until a CANARY of that candidate has passed", which presumes an in-process promote. Under the same revision's release-pinned execution that promote is IMPOSSIBLE: the execution root is an immutable installed payload with no `.git`, so there is nothing to write into, and a running process cannot re-point itself at a different payload mid-run. The clause is not wrong about the canary; it is wrong about what follows a passing one.

A RATIFIED-SPEC VIOLATION IS ALSO IN SCOPE, and it is not a judgment call. v054 states (contracts.md:1121-1123) that the Dispatcher "MUST NOT treat the presence of a writable orchestrator checkout as a reason to behave differently". The implementation branches on exactly that: `_dispatcher_self_update.py:262` guards on `is_writable_orchestrator_checkout` and returns before the canary when it is false. Verified 2026-08-03 against origin/master: the clause is present as quoted and the guard is present at :262.

MEASURED CONSEQUENCE. The installed payload has no `.git`, so that guard is always false on the v054-mandated path and the function returns at :270 BEFORE the canary at :271. The canary is therefore unreachable in the execution mode v054 mandates, and reachable ONLY in the mode v054 forbids. v054 ratified a canary requirement whose sole reachable path it simultaneously outlawed. This proposal makes the requirement satisfiable.

REJECTED ALTERNATIVES, recorded so they are not re-litigated. (1) RETIRE the layer from the dispatcher and move the canary to provisioning time — rejected because it moves the canary off the dispatch path and loses the "actual artifact, actual host, before it takes over" property, which is the canary's entire value. (2) An EXTERNAL SUPERVISOR that re-points execution — rejected for now: it would actually solve bd-ib-97v4, but it is a much larger change needing its own design pass.

THIS DOES NOT SOLVE bd-ib-97v4, and the proposal must not be read as though it does. bd-ib-97v4 records that the dispatcher's staleness gate compares the executing build against the newest release while its prescribed remedy cannot move the executing build from inside a running session — only a human-typed `/reload-plugins` or a restart re-points a live session. That cost is EXACTLY UNCHANGED here, neither improved nor worsened. The maintainer chose this option knowing that. bd-ib-97v4 remains OPEN and unaddressed by this work.

SCOPE. The canary contract is unchanged: candidate artifact itself, on the host that will run it, same interpreter and packaged layout, import graph + argument parsing + check pipeline, side-effect-free, fail-closed on failure. Nothing here reduces what the canary does or when it runs. No change to the release pipeline, release-please, the workflows, or the plugin-cache path.

### Proposed Changes

Anchors verified byte-exact against `origin/master` (`73f225d`) on 2026-08-03;
each quoted block matches exactly once.

---

### (A) `contracts.md` — replace the promotion paragraph with detect / canary / alarm

Replace verbatim:

> A candidate release MUST NOT become the running version until a CANARY of
> that candidate has passed. The canary MUST execute the CANDIDATE ARTIFACT
> ITSELF, on the host that will run it, using the same interpreter and the
> same packaged layout it will run under, and it MUST exercise at minimum
> the candidate's import graph, its argument parsing, and its check
> pipeline end-to-end. It MUST remain side-effect-free: no real ledger, no
> engine run, no network. A PASSING canary is the only thing that MAY
> promote a candidate. A FAILING canary MUST keep the last-known-good
> running release AND MUST alarm a human; it MUST NOT promote, and it MUST
> NOT be downgraded to a warning or skipped.

with:

> The Dispatcher MUST NOT modify, promote into, or re-point its own execution
> artifact. It never writes code, and no passing check causes it to begin
> running a different payload than the one it started under. The executing
> payload changes only when the process is restarted against a newly
> provisioned one.
>
> When a newer released payload is provisioned, the Dispatcher MUST canary it
> before that payload is treated as usable. The canary MUST execute the
> CANDIDATE ARTIFACT ITSELF, on the host that will run it, using the same
> interpreter and the same packaged layout it will run under, and it MUST
> exercise at minimum the candidate's import graph, its argument parsing, and
> its check pipeline end-to-end. It MUST remain side-effect-free: no real
> ledger, no engine run, no network.
>
> A PASSING canary MUST surface that a RESTART IS DUE — the newer payload is
> validated and will take effect on the next start. A FAILING canary MUST keep
> the last-known-good payload running AND MUST alarm a human; it MUST NOT be
> downgraded to a warning or skipped, and it MUST NOT cause the candidate to be
> treated as usable.
>
> Neither outcome moves the running process onto the candidate. Detecting,
> canarying, and alarming is the whole of the Dispatcher's self-update
> responsibility.

Three things this preserves and one it changes. The canary's scope, host,
interpreter, layout, side-effect-freedom and fail-closed alarm are carried over
verbatim in substance. What changes is only the consequence of a PASS: an alarm
that a restart is due, rather than an in-process promote that the execution model
makes impossible.

### (B) `contracts.md` — state that the writable-checkout branch is not permitted here

Append to the block inserted in (A):

> This restates, for the self-update path specifically, the rule above that the
> Dispatcher MUST NOT treat the presence of a writable orchestrator checkout as a
> reason to behave differently. Self-update MUST NOT branch on whether its
> execution root is a writable checkout: under release-pinned execution it never
> is, and a branch that skips the canary when it is not is prohibited.

This is deliberately explicit rather than left to inference from the general
clause. The implementation currently carries exactly that branch, and it is the
reason the canary is unreachable; naming it in the section that governs
self-update makes the violation checkable at the point of use.

### (C) `scenarios.md` — amend Scenario 54's promotion scenario

Replace verbatim:

>   Scenario: A newer release is canaried before it is promoted
>     Given a running release and a newer available release
>     When the Dispatcher evaluates whether to update itself
>     Then it compares the running release against the available release
>     And it validates the newer release with a canary before promoting it
>     And a failing canary keeps the running release and surfaces the failure to a human

with:

>   Scenario: A newer provisioned payload is canaried and alarmed, never promoted
>     Given a running release and a newer provisioned released payload
>     When the Dispatcher evaluates whether a newer payload is available
>     Then it compares the running release against the provisioned release
>     And it validates the newer payload with a canary on this host
>     And a passing canary surfaces that a restart is due
>     And a failing canary keeps the last-known-good payload running and alarms a human
>     And in neither case does the Dispatcher modify or re-point its own execution artifact

The other two scenarios under `## Scenario 54` are unchanged: the
unreleased-working-tree-edit scenario and the undeterminable-release scenario
both still hold.

### (D) `tests/heading-coverage.json` — NO co-edit required

The map is H2-keyed and this proposal changes no `## ` heading: `## Scenario 54 —
Host-side dispatch runs a released payload, never the working tree` keeps its
text, and only a nested `Scenario:` line inside its gherkin block changes.
Verified: the map holds 90 entries and one for that H2. Stating this explicitly
so the revise pass does not add a spurious entry or conclude the co-edit was
forgotten.

---

### Explicitly NOT changed

- The canary's scope, host, interpreter, packaged-layout, side-effect-freedom
  and fail-closed properties. This proposal preserves them; it changes only what
  a PASS causes.
- Release-pinned execution, the no-escape-hatch clause, and the operator
  consequence paragraph — all of v054 outside the promotion paragraph.
- The release pipeline, `release-please`, and `.github/workflows/`.
- The plugin-cache path.
- **bd-ib-97v4 is NOT addressed.** The human-typed `/reload-plugins` cost for a
  session that goes stale mid-work is exactly as it was. Nothing here shortens
  it, and nothing here should be read as having shortened it.
