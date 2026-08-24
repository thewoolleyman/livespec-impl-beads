---
topic: check-anchored-gap-tied-closure
author: honest-gap-detector-and-check-anchored-closure
created_at: 2026-08-24T06:07:04Z
---

## Proposal: check-anchored-gap-tied-closure

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

The implement operation's gap-tied closure gate currently requires re-running detect-impl-gaps and confirming the gap_id is no longer detected. Because detection is spec-only (a gap_id disappears only when spec TEXT changes), this gate is unsatisfiable in practice and creates pressure to edit spec text to close an item instead of implementing it. gap_id is also unsound as a closure anchor: it hashes a hard-wrapped source line, so reflowing a paragraph with zero semantic change re-keys it. This proposal replaces the gate with closure anchored to a CHECK PATH recorded on the work-item's own metadata: closure requires the recorded check to pass AND its negative control to fail; if the check file was modified since the baseline recorded when it was cited, closure is refused until a targeted drift review produces a propose-change.

### Motivation

Findings F3 and F4 from homelab's pre-foreman-livespec-hardening plan. F3: hl-eoay6m is done, origin gap-tied, and its gap_id is STILL detected in the live spec at closure time -- the closure rule verified nothing, and its canary run edited SPECIFICATION/contracts.md and SPECIFICATION/hosts/example-host.md directly, which the closure mechanism itself rewards. F4: the rich detector output for one measured gap-id is truncated mid-sentence at a hard-wrapped source line, proving gap_id keys on wrap position, not clause identity. The corrected mechanism -- check passes, negative control fails, drift forced on check modification -- is implemented and tested in this repo's livespec_orchestrator_beads_fabro.commands._gap_closure module (16 tests, 100% coverage, merged PR #1819). This proposal brings the ratified contract and the implement operation's own prose into agreement with that implementation. Per homelab research 003 section 2.2, this deliberately does NOT add capture-spec-drift as a whole-tree survey to the closure path -- only a targeted --for-work-item mode is in scope, reusing drift's existing propose-change handoff. Per homelab research 003 section 3.1, closure deliberately never anchors on gap_id.

### Proposed Changes

Two files change, prose-only -- no CLI surface, flag, or exit-code change; no new detection mechanism, only a closure-gate replacement already backed by a merged, tested package primitive.

```diff
diff --git a/SPECIFICATION/contracts.md b/SPECIFICATION/contracts.md
index 01b0e815..18f3af88 100644
--- a/SPECIFICATION/contracts.md
+++ b/SPECIFICATION/contracts.md
@@ -116,6 +116,21 @@ plus every work-item captured on or after the most-recently-cut spec
 version. The flag scopes only the ledger-intent source; the impl → spec
 heuristic is unaffected.
 
+`capture-spec-drift` MUST also accept an optional `--for-work-item <id>`
+flag selecting a TARGETED mode instead of the whole-tree survey above.
+`implement`'s gap-tied closure gate (§"`implement`" → "gap-tied
+completion") invokes this mode when a gap-tied work-item's recorded
+check file was modified since the baseline blob hash recorded when it
+was cited. In this mode the skill MUST NOT run the whole-tree survey
+above; it presents exactly ONE candidate — framed from the diff
+between the check file's current content and its recorded baseline —
+asking whether the spec clause the check settles needs to change to
+match. On consent it reuses the SAME cross-boundary propose-change
+handoff as the whole-tree mode. On the resulting proposed-change
+landing, the caller records its canonical topic onto the work-item
+(`gap_drift_propose_change` metadata), which is what the closure gate
+checks before allowing closure to proceed.
+
 #### `capture-work-item`
 
 Freeform direct filing of a work-item. The user supplies title,
@@ -152,8 +167,22 @@ update` sets the `resolution:<enum>` label, and — for resolutions that
 imply a canonical-branch merge — the full `AuditRecord` is written into
 the issue's `metadata` JSON column. No second record is appended.
 
-- **gap-tied completion** — invoke `detect-impl-gaps --json`; confirm
-  the `gap_id` is NO LONGER in the returned gap-id set; close with
+- **gap-tied completion** — closure is anchored to a CHECK PATH recorded
+  on the work-item's own metadata (`gap_check_path`), never to `gap_id`
+  (a `gap_id` hashes a hard-wrapped source line and re-keys on reflow,
+  so it cannot anchor a closure that must survive the clause being
+  edited). The check path is recorded the first time it is cited for
+  this work-item — at latest, `implement` MUST ask the user which
+  executable check settles the clause and record it (with its current
+  blob hash as the closure-drift baseline) before evaluating closure at
+  all, if no check has been recorded yet; a work-item reaching closure
+  with no recorded check path is refused. Closure requires BOTH legs
+  once a check is recorded: the recorded check passes, AND
+  its negative control fails (a passing check with no failing control
+  proves nothing). If the check file was modified since the baseline
+  recorded when it was cited, closure is refused until a targeted
+  `capture-spec-drift --for-work-item <id>` run produces a
+  propose-change covering the modification. Close with
   `resolution: completed` and an `AuditRecord`
   (`verification_timestamp`, `commits`, `files_changed`, `merge_sha`,
   optional `pr_number`) in `metadata`.
@@ -172,8 +201,8 @@ governs the Dispatcher's machine-driven dispositions only (§"Dispatcher
 admission, WIP cap, and post-merge acceptance", §"Dispatcher policy
 settings"); a human-driven `implement` closure
 does NOT transit `acceptance` — the operator's own verification (the
-gap-tied re-detection, the Red → Green evidence) is the closure's
-verification consent.
+gap-tied check-path verification, the Red → Green evidence) is the
+closure's verification consent.
 
 ### Operator skill
 
@@ -644,9 +673,10 @@ Consumers:
   upstream §"Cross-boundary handoffs" entry 5).
 - The heavyweight sibling `capture-impl-gaps` invokes this skill as its
   detection step before walking the user through per-gap consent.
-- The heavyweight `implement` skill invokes this skill at gap-tied
-  work-item closure to confirm the `gap_id` is no longer detected before
-  closing the record.
+- The heavyweight `implement` skill's gap-tied closure verification is
+  check-path-anchored (§"`implement`" → "gap-tied completion") and does
+  NOT invoke this skill at closure — a `gap_id` is unsound as a closure
+  anchor (it hashes a hard-wrapped source line and re-keys on reflow).
 
 The skill MUST NOT mutate any impl-side store; it MUST NOT write to the
 tenant DB; it MUST NOT prompt the user. It is a pure read-and-emit
@@ -857,7 +887,8 @@ three recognized forms:
   start of the operation that names the write the operation will
   perform. Example: `implement`'s resolution-path decision, which is
   the consent for the eventual closure write (gap-tied closures
-  additionally confirm the re-detection outcome before the close).
+  additionally require the recorded check to pass and its negative
+  control to fail before the close).
 
 ### Operation-class waiver
 
diff --git a/SPECIFICATION/scenarios.md b/SPECIFICATION/scenarios.md
index 49101167..3c6daab7 100644
--- a/SPECIFICATION/scenarios.md
+++ b/SPECIFICATION/scenarios.md
@@ -32,8 +32,8 @@ Scenario: A new MUST clause is detected, filed, implemented, and closed in place
   And surfaces the newly-filed gap-tied item as the recommendation (the top-ranked `ready` item — earliest `rank`)
   When the user invokes `/livespec-orchestrator-beads-fabro:implement` for that work-item
   Then the skill walks Red → Green → closure
-  And at closure re-runs `capture-impl-gaps` in dry-run mode
-  And confirms the `gap_id` is no longer detected
+  And at closure evaluates the recorded check-path (never `gap_id`)
+  And confirms the check passes and its negative control fails
   And closes the issue IN PLACE with `bd close --reason …`
   And `bd update` sets the `resolution:completed` label
   And the `AuditRecord` (`verification_timestamp`, `commits`, `files_changed`, `merge_sha`, optional `pr_number`) is written into the issue's `metadata` column

```
