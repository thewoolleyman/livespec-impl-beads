---
topic: honest-detector-contract
author: honest-gap-detector-and-check-anchored-closure
created_at: 2026-08-24T04:24:17Z
---

## Proposal: honest-detector-contract

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

SPECIFICATION/contracts.md's `capture-impl-gaps` and `detect-impl-gaps` sections, and scenarios.md's Scenario 1, promise or imply a spec→impl comparison that the mechanism never performs. Measured against a real spec tree (homelab's SPECIFICATION, 2026-08-24): two rules independently verified as honored by their implementation (installation scoped to selected repositories; force-push and admin-enforcement blocked) are still reported as gaps, because detect-impl-gaps enumerates MUST/SHOULD clauses from spec TEXT alone and never reads implementation state. This proposal makes the ratified contract state that plainly: `detect-impl-gaps` is a spec-clause enumerator, not a spec→impl comparator, and a returned gap-id means "clause not yet tracked by a work-item", not "clause verified absent from the implementation". It also documents `--since-version`'s real semantics explicitly for callers: it scopes the scan to files whose content differs since vN and then surfaces EVERY live MUST/SHOULD clause in those files, not merely the clauses added since vN — so a caller (the revise post-step included) must not read its output as a diff of new clauses.

### Motivation

Two independently-verified findings from homelab's pre-foreman-livespec-hardening research (2026-08-23/24): F1 (a gap-capture run against a tree containing demonstrably-honored rules still reports them as gaps — re-measured against homelab's live SPECIFICATION on 2026-08-24 with the same two rules reproducing) and F2 (contracts.md's own text contradicts itself: `capture-impl-gaps`'s opening line promises "Detect spec → impl gaps" while its mechanism clause forbids any detection logic beyond the spec-only enumerator and `detect-impl-gaps` itself states plainly "it reads the spec tree, never the work-items store"). F5: `--since-version` does not mean "clauses added since vN"; it was measured to return 61 gaps for `--since-version v003` because it re-surfaces every live clause in every file that changed, not just new clauses — any caller including revise's own post-step (`Step 13`) that assumes otherwise will overcount. A ratified contract that promises a comparison its own forbidding clause prevents it from performing produces exactly the confusion measured: 44 untracked clauses were nearly bulk-consented because the operation's name and opening sentence implied a verified absence rather than an unverified spec-text hit.

### Proposed Changes

Two files change, prose-only — no CLI surface, flag, exit code, or wire-format contract changes; no new MUST/SHOULD clause is introduced (the fix removes a self-contradiction and adds accurate framing/naming-note prose to existing sections).

```diff
--- a/SPECIFICATION/contracts.md
+++ b/SPECIFICATION/contracts.md
@@ -53,7 +53,14 @@
 #### `capture-impl-gaps`
 
-Detect spec → impl gaps by invoking the sibling
+Surface untracked spec clauses as candidate work-items by invoking the
+sibling
 `/livespec-orchestrator-beads-fabro:detect-impl-gaps --json` thin-transport skill (no
 in-skill duplication of the detection logic; both this skill and doctor
-consume the same canonical surface). The returned gap-ids are presented
+consume the same canonical surface).
+
+**Naming note.** Despite the `-impl-gaps` name, this operation performs
+NO spec↔impl comparison. `detect-impl-gaps` (below) enumerates ratified
+MUST/SHOULD clauses from spec TEXT alone and never reads implementation
+state, so a clause it surfaces may already be fully implemented. A
+returned gap-id means "this clause is not yet tracked by a work-item",
+never "this clause is verified absent from the implementation" — that
+comparison, when one exists, is a per-clause human judgement or a cited
+executable check, not this operation's mechanism.
+
+The returned gap-ids are presented
 to the user one at a time; on consent, a new work-item is created in the
 tenant DB via `bd create` carrying the `origin:gap-tied` and
 `gap-id:<stable-id>` labels. Detection state is in-memory and discarded
@@ -574,10 +581,15 @@
 CLI surface: `detect-impl-gaps [--spec-target <path>]
 [--project-root <path>] [--since-version <vN>] [--json]`. No `--filter`
 flag — the skill emits the complete current gap-id set.
 
+**Naming note.** This is a spec-clause enumerator, not a spec→impl
+comparator — despite the `-impl-gaps` name, it never reads
+implementation state (see the `capture-impl-gaps` naming note above,
+which this section's own mechanics substantiate).
+
 The skill reads the live Specification via the Spec Reader, enumerates
 every MUST/SHOULD rule per the gap-rule enumeration contract (per the
 upstream Spec Reader required-capability surface, capability 1), and
 computes a stable `gap_id` per detected rule. Gap-id derivation is a
 pure function of rule text + canonical heading path; the same rule text
 always yields the same gap-id across runs. This skill is
 substrate-agnostic — it reads the spec tree, never the work-items store.
@@ -589,7 +601,12 @@
 For each such file, only MUST / SHOULD clauses present in the live version
 are considered (clauses removed by the diff are not gaps — they were
 spec content that no longer exists).
 
+**Caller caution.** This is NOT "clauses added since `<vN>`" — a file
+that changed for any reason resurfaces EVERY live MUST/SHOULD clause it
+contains, including clauses that predate `<vN>` and were untouched by
+the edit. A caller (the `revise` operation's Step 13 post-step included)
+MUST NOT read this flag's output as a diff of newly-introduced clauses.
+
 Validation:
 
 - The value MUST be a positive integer. Non-integer / negative input
   exits `2` with a usage error.

--- a/SPECIFICATION/scenarios.md
+++ b/SPECIFICATION/scenarios.md
@@ -20,8 +20,8 @@
   When the user invokes `/livespec-orchestrator-beads-fabro:capture-impl-gaps`
   Then the skill loads the rule set via the Spec Reader
-  And walks each rule against the impl
-  And surfaces uncaptured gaps one at a time
+  And enumerates every MUST/SHOULD rule from spec text alone (no read of the impl)
+  And surfaces every rule not yet tracked by a work-item, one at a time
   When the user consents to file a gap
   Then the skill creates a beads issue via the 2-step append carrying the `origin:gap-tied` label
```
