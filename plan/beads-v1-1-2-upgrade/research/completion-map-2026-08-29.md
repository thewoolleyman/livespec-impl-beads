# Completion map: what remains before bd-ib-3kolea can archive

**Date:** 2026-08-29
**Thread:** `plan/beads-v1-1-2-upgrade/`
**Epic:** `bd-ib-3kolea` (backlog)

Built by auditing every undisposed child through the union child-enumeration
primitive (`client.children` + `undisposed_plan_child_ids`), re-verifying dated
premises against the forge and the current-master acceptance matcher rather than
trusting the ledger text. The qualification side of the epic is discharged
(`bd-ib-3kolea.4` closed, criterion 3 proven behaviourally by the 2026-08-29
isolated-server migration-delta run); what remains is five children plus the
cutover phase.

## The five undisposed children, by disposition class

| Child | P | State | Class | Blocker to closing |
|---|---|---|---|---|
| `bd-ib-1atn` | 1 | backlog | **dispatchable now** | Archive-gating O4 secret-scan fix. Factory-safe (one shell wrapper + beside-tests). Criteria made matcher-safe 2026-08-29 (see below); dispatch-ready on maintainer nod. |
| `bd-ib-3kolea.3` | 0 | backlog | **dispatchable (large)** | Enemy Unit Test harness (a BeadsPort). Factory-safe; the house pattern it is told to follow is now merged/readable. Substantial; not required for criterion 3 (that is discharged) but a standalone deliverable. |
| `bd-ib-3kolea.2` | 0 | backlog | **must run LAST** | FINAL PRE-CUTOVER GATE: sandbox-test the targeted release against the livespec API surface. Maintainer-directed to run after every other item is done; gates the cutover. |
| `bd-ib-ao3j` | 2 | backlog | **authorization-gated** | Attended isolated migration-and-restore rehearsal. Host-mutating, ATTENDED. Has NO acceptance criteria, so the shipped pre-dispatch empty-criteria guard (`pre_dispatch_criteria_refusal`, exit 5) would refuse it: it needs criteria authored AND a foreground attended window. |
| `bd-ib-092q` | 3 | backlog | **authorization-gated** | `dolt_remote` credential/network/partial-fetch probe against a REAL remote. Outward-facing (network egress); the foreman split it out precisely so it gets its own authorization on its own grounds. |

## What is dispatchable without a maintainer decision, and what is not

- **Factory-safe, ready:** `bd-ib-1atn` (criteria now clean), `bd-ib-3kolea.3`
  (large). Both are in-repo pure work. Under the standing "prefer factory
  dispatch for factory-safe work" rule these are the drain candidates — but each
  is a P0/P1 the maintainer has approved per-dispatch so far, so they wait on a
  nod rather than autonomous dispatch.
- **Authorization-gated (do NOT start unprompted):** `bd-ib-ao3j` (attended +
  host-mutating), `bd-ib-092q` (outward-facing network), and the cutover phase
  itself (install/pin/migrate every clone and the shared multi-tenant server,
  with the v1.2.1 schema-v65 landmine live). These are genuine
  maintainer/values/irreversible calls.
- **Sequenced last:** `bd-ib-3kolea.2` runs only after the other four close.

## The bd-ib-1atn criteria fix (recorded here because it changes the drain order)

Its criterion 2 was a three-arm control written as a prose header plus three
sub-arm lines. The 2026-08-23 rider warned that line would be RUBBER-STAMPED by
the acceptance matcher (passing on the single term "test"). That rider is now
**outdated**: `bd-ib-5z0g` (PR #1787, diff arm now needs ≥2 terms) and
`bd-ib-zodd` (PR #1982, telemetry arm now needs verification-term dominance)
both landed after it. Re-judged against the current master matcher, the prose
header and the "arm (c) fails today…" line now FAIL both arms — the risk
inverted from a false PASS to a false REWORK, on the item that gates this epic's
archive. The rider's "do not edit — preserve the specimen" reason is void
(`bd-ib-5z0g` shipped its control fixtures). The prose was moved out and the
three arms preserved as self-contained gradeable assertions; all seven criteria
now pass the current matcher against a representative diff. Full account on the
item's ledger.

## Path to archive

1. Close `bd-ib-1atn` (dispatch the fix) and `bd-ib-3kolea.3` (dispatch the
   harness) — both factory-safe.
2. Obtain authorization for, then run, `bd-ib-ao3j` (attended rehearsal, after
   authoring its criteria so the empty-criteria guard admits it) and `bd-ib-092q`
   (outward-facing remote probe), OR transfer either to a follow-up plan if it is
   descoped.
3. Run `bd-ib-3kolea.2` LAST as the final pre-cutover gate.
4. Authorize and scope the cutover phase (its own implementation children).
5. Archive only after every child is closed AND an independent completeness
   review attests full requirement-carrier coverage (Step-5 gates).

## Deferrals recorded

The cutover execution, `bd-ib-ao3j`, and `bd-ib-092q` are deferred pending
explicit maintainer authorization — host-mutation and outward-facing egress
respectively — and are NOT admitted for autonomous work. They remain the
epic's requirement carriers; deferral is where they will be reconsidered, not a
descope.
