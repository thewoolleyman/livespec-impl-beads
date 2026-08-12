---
topic: out-of-band-edit-2026-08-12t00-53-03z
author: livespec-doctor
created_at: 2026-08-12T00:53:03Z
---

## Proposal: out-of-band-edit-2026-08-12t00-53-03z

doctor detected drift between HEAD-active spec content and the
HEAD-history-vN snapshot; this auto-backfill records the active
state as the new canonical version.

### Proposed Changes

```diff
--- history/vN/contracts.md
+++ active/contracts.md
@@ -1052,17 +1052,22 @@
 orchestrator-private storage outside those ledger-entry and
 capture/admission surfaces.
 
-### Archive on epic close
-
-A plan's lifecycle binds to its ledger epic: `plan/<slug>/` is active if
-and only if its epic is open, and archived to `plan/archive/<slug>/` if
-and only if the epic is closed (reopening the epic unarchives it);
-whatever closes the epic also archives the directory. Nothing is lost —
-the archived plan stays under `plan/archive/` and in git history. The
-mechanical backstops (`archived` matches `epic-closed`) are five-slot
-conformance concerns paired with Ledger-closure, whose always-on
-enforcement is realized by the Conformance Pattern, not by `plan`
-itself; this realization holds them behaviorally.
+### Archive on completion
+
+A plan's lifecycle binds to its ledger epic, but an epic's closed status
+is not by itself archive authority. `plan/<slug>/` remains active until
+the plan's work is genuinely complete: implemented, merged, and, where a
+release applies, shipped and verified. A status transition to closed can
+also mean regroomed out, superseded, or otherwise retired without
+completion, so whatever closes the epic MUST archive the directory only
+when that completion evidence exists. The one exception is an explicit
+handoff at archive time: every remaining piece of work MUST be
+transferred to named follow-up plan(s) or work-item(s), and the archive
+record MUST state those names exactly. Nothing is lost — the archived
+plan stays under `plan/archive/` and in git history. Mechanical
+enforcement of this corrected archive rule is tracked outside this repo
+in `livespec-dev-tooling-5asgvm` and the related converse-gap item
+`livespec-dev-tooling-q3emww`.
 
 Archive requires BOTH legs. First, the mechanical leg: a plan epic MUST
 NOT close or archive while any child requirement or implementation item
@@ -1084,8 +1089,8 @@
 remains — choose a new slug; or, if the new work genuinely continues the
 old plan, REOPEN ITS EPIC, which unarchives the record by moving it
 back. Moving an archived record back WITHOUT reopening its epic is
-forbidden: it produces an active `plan/<slug>/` whose epic is closed,
-contradicting the if-and-only-if binding this section states.
+forbidden: it produces an active `plan/<slug>/` whose epic remains
+closed, contradicting the lifecycle binding this section states.
 
 The mechanism belongs with the rule. Control-Plane consumers of this
 lane discover plans and test archival at DIRECTORY granularity, so
```
