---
topic: janitor-argv-declared-resolution
author: janitor-argv-declared-resolution
created_at: 2026-08-30T02:47:41Z
spec_commitments:
  impl_followups:
    - id_hint: declared-janitor-check-suite
      description: |
        Add a committed declaration surface for the janitor's check-suite invocation covering BOTH the host post-merge janitor argv (_DEFAULT_JANITOR in _dispatcher_fabro_argv.py) and the in-sandbox janitor hard-gate node (workflow.fabro:123-127), read through dispatcher_block(cwd=) with the same in-presence / absent-only-fallback / present-but-defective-refuses semantics as dispatcher.master_ci and dispatcher.janitor_bootstrap. A declared value runs VERBATIM (no mise-exec wrapper imposed); the fleet default applies only when the key is truly absent. Subordinate or retire the per-invocation --janitor CLI override so committed policy is not overridden by an uncommitted per-invocation argv.
    - id_hint: declared-core-provisioning
      description: |
        Give livespec-core provisioning the same declared-resolution + refuse-on-defect shape: the janitor-core repo URL gains a declaration surface (today _DEFAULT_JANITOR_CORE_REPO_URL is hardwired with no override), and the ref stops defaulting to a moving master. Route compat.pinned (or its successor key) through the dispatcher_block refuse-on-defect pattern instead of the current silent raw-config default, and remove the second hardcoded _DEFAULT_JANITOR_CORE_REF='master' default in _dispatcher_plan_build.py:27,98.
    - id_hint: declared-sandbox-toolchain
      description: |
        Disposition every factory-sandbox prepare premise as declared-and-validated OR ratified-as-no-op explicitly, abolishing silent degradation: the mise/.mise.toml prepare (workflow.toml:349), the lefthook Red-Green-Replay gates (workflow.toml:13-17,355,371,399; workflow.fabro:8-9), the fleet Python-package prepare steps (livespec_dev_tooling.install_commit_refuse_hooks and ...checks.primary_checkout_commit_refuse_hook_installed) plus the livespec-step-timer binary prefix, and the node-prompt tool wrappers (mise exec -- git / mise exec -- just check across implement.md, fix.md, review.md, review-fix.md, pr.md).
    - id_hint: dispatch-integration-validation-pass
      description: |
        Implement the single up-front all-points validation pass: at first dispatcher invocation against a repo (re-run when the plugin build or the declaration changes), check every declared-or-defaulted integration expectation against the repo and refuse pre-dispatch (exit 3) with the COMPLETE enumerated unmet list in one message, before any dispatch, merge, or factory run. Version the contract so a plugin upgrade that ADDS expectations fails the validation pass fast with the new points named, never stranding a mid-pipeline item on an expectation that did not exist when the dispatch was admitted.
    - id_hint: janitor-venue-merged-tip
      description: |
        Change the post-merge/reconcile janitor venue to a clean checkout of the target default-branch tip CONTAINING the merge (resolved per the ratified Default-branch-resolution rule), not the item's historical merge sha, so a post-merge environment fix clears historical items while the venue still proves the merge is present. Applies to janitor_worktree_add_argv / janitor_reconcile_checkout_path and the reconcile-merged path.
    - id_hint: default-branch-conformance-workflow-guard
      description: |
        Conformance fix against the already-ratified Default-branch-resolution clause (not a new rule): replace the hardcoded origin/master...HEAD ranges in _dispatcher_workflow_guard.py:41-51 and workflow.fabro:114 (implementation_diff dead-implementer check) with the dynamically resolved target default branch, so a non-master adopter is neither falsely refused at the workflow-drift guard nor given a false dead-implementer sentinel.
---

## Proposal: Adopter-neutral integration: one committed declaration surface plus an up-front all-points validation pass

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

Extend the already-ratified declaration-over-assumed-tooling pattern (v074 dispatcher.master_ci, v087 dispatcher.janitor_bootstrap) to the WHOLE class of governed-repo integration premises, and add the fail-fast up-front validation the current per-instance discovery lacks. contracts.md §'Self-contained plugin dispatch' ratifies that fleet members and adopters consume the orchestrator IDENTICALLY, yet the dispatch / janitor / factory-sandbox path still hardwires fleet-tooling premises (mise; specific just recipe names; lefthook; the livespec_dev_tooling package and livespec-step-timer binary; livespec CORE cloned at a moving master). Each has been discovered one broken dispatch at a time. This amendment names one committed declaration surface for the remaining integration points and one validation pass that refuses pre-dispatch with the complete enumerated unmet list, so no integration premise can silently degrade or strand an item post-merge.

### Motivation

homelab (an adopter that does not import livespec-dev-tooling) dispatched its first clean hardened run on 2026-08-29; the factory produced a real merge (PR homelab#1045), then the run FAILED at janitor-post-merge because homelab's justfile has no install-worktree-pack recipe — stranding the merged item active and failing every further dispatch identically. This was the SECOND adopter-premise instance (the first, janitor-bootstrap, was fixed by v087). A coupling sweep from the adopter side then located six instances (I1-I6), and an in-repo re-verification at HEAD 65f34d62 confirmed all six and found four more (N1-N4). The maintainer's directive (2026-08-29) is to make the adopter contract EXPLICIT and FAIL-FAST like a programmatic API version check, and to finish the audit in-repo so this is the LAST instance of the class rather than the second of N. The same implicit contract today fails at three different times: pre-dispatch refusal (the good model), post-merge stranding (after the irreversible merge), and silent degradation (nothing refuses; behavior just differs for adopters) — the taxonomy IS the defect.

### Proposed Changes

Amend §'Dispatch preflight and post-merge step discipline' in SPECIFICATION/contracts.md and add the corresponding Given/When/Then scenarios to SPECIFICATION/scenarios.md (co-editing tests/heading-coverage.json for any new H2, per the revise co-edit discipline). The clauses to add:

(R1) ONE COMMITTED DECLARATION SURFACE. Extend the dispatcher.* committed-configuration-only class (§'Control surface and audit') with the remaining governed-repo integration points, each read through the shared dispatcher_block(cwd=) helper and each carrying the EXACT v074/v087 semantics: a declared value runs VERBATIM (the orchestrator MUST NOT impose its own `mise exec --` or other tool wrapper on a declared command); the fleet default convention applies ONLY when the key is truly ABSENT (presence tested with `in`, so a JSON null is a present-but-nothing declaration that REFUSES rather than sliding onto the convention); a present-but-unusable declaration is a DEFECT whose refusal names the key and states which resolution (declared or default) was attempted, never a silent slide. The points, each verified present at HEAD:
  - the janitor CHECK-SUITE INVOCATION, covering both the host post-merge janitor argv (_dispatcher_fabro_argv.py:58-66 `_DEFAULT_JANITOR`; only override today is the per-invocation --janitor flag, which MUST be subordinated to committed policy) and the in-sandbox janitor hard-gate node (workflow.fabro:123-127, `mise exec -- just check-no-workflow-edits check`);
  - CORE PROVISIONING: the janitor-core repo URL (_DEFAULT_JANITOR_CORE_REPO_URL, hardwired with no override today) and ref, whose default MUST stop being the moving `master` and whose resolution MUST use the refuse-on-defect pattern (today compat.pinned reads raw config and silently defaults; a second hardcoded default sits in _dispatcher_plan_build.py:27,98);
  - the FACTORY-SANDBOX TOOLCHAIN premises: mise / .mise.toml prepare (workflow.toml:349), the lefthook Red-Green-Replay gates (workflow.toml:13-17,355,371,399), the fleet Python-package prepare steps (livespec_dev_tooling.install_commit_refuse_hooks, ...checks.primary_checkout_commit_refuse_hook_installed) and the livespec-step-timer binary prefix, and the node-prompt tool wrappers (`mise exec -- git ...` / `mise exec -- just check` across implement.md, fix.md, review.md, review-fix.md, pr.md).

(R2) ONE UP-FRONT ALL-POINTS VALIDATION PASS. Generalize the existing single-integration-point pre-dispatch re-verification into a validation pass that runs at the first dispatcher invocation against a repository (and re-runs when the plugin build or the declaration changes), checks EVERY declared-or-defaulted expectation against the repository, and — when any are unmet — refuses the dispatch (exit 3, journaled) with the COMPLETE ENUMERATED list of unmet points in ONE message, BEFORE any dispatch, merge, or factory run. No per-instance discovery, no post-merge stranding, no silent degrade: each expectation is met, declared-and-met, or a named refusal item.

(R3) VERSION THE CONTRACT. A plugin upgrade that ADDS expectations MUST fail the validation pass fast with the new points named, and MUST NOT strand a mid-pipeline item on an expectation that did not exist when its dispatch was admitted — the cross-dispatch-persistence guarantee generalized to the whole set.

(R4) ABOLISH SILENT DEGRADES. Every instance above becomes either declared-and-validated or ratified-as-no-op EXPLICITLY. The only sanctioned silent no-op remains the ratified fleet-manifest sibling-clone projection.

(Audit-list completion) Extend the 'Members-and-adopters-identical audit of the step and preflight set' list with a row for each point above so the closed step/preflight set's disposition is COMPLETE; the set stays closed and any future step carries its own members-and-adopters disposition at ratification.

Required scenarios (Given/When/Then in scenarios.md): (positive) an adopter repo with a complete declaration passes the validation pass and dispatches with zero fleet-tooling present, its declared janitor argv running verbatim; (discriminating) removing one declared integration point fails the validation pass pre-dispatch naming exactly that point, and the dispatch never reaches merge or post-merge; (present-but-defective) a key present as JSON null or naming an unparseable command REFUSES naming the key, never sliding onto the fleet default; (control) a fleet-member repo with no declarations runs today's defaults unchanged and passes the validation pass; (versioning) a plugin upgrade that adds an expectation fails the validation pass fast for a repo that has not yet declared it, rather than stranding an in-flight item. NON-GOAL, stated so scope stays bounded: this amendment does not itself re-file the per-instance patches; it is one contract amendment for the class, realized by the declared impl-followups.

## Proposal: Post-merge and reconcile janitor venue is the merged default-branch tip, not the item's historical merge sha

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

The post-merge and reconcile janitor venue MUST be a clean checkout of the target default-branch TIP CONTAINING the merge (resolved per the ratified Default-branch-resolution rule), not the item's historical merge sha. Pinning the venue to the historical merge sha makes a janitor-environment fix that lands AFTER an item's merge unable to ever clear that item, producing a deterministic reconcile deadlock whose only in-band exit today is a one-off --janitor override.

### Motivation

Measured on homelab (I7, 2026-08-29): hl-cid234 merged as 16fe3ac (PR homelab#1045); the install-worktree-pack recipe that would let the janitor pass landed one commit later as 918c6cf (PR homelab#1066). Two reconcile attempts (12:11:47Z and 13:29:56Z, the second AFTER pull-primary fast-forwarded the primary checkout to 918c6cf) BOTH ran janitor-checkout-add at 16fe3ac and failed identically on a recipe that cannot exist at that sha. This is a deterministic deadlock, not a transient failure: a post-merge environment fix can never reach an item whose venue is pinned to a sha from before the fix existed.

### Proposed Changes

Add a clause to §'Dispatch preflight and post-merge step discipline' (and a paired scenario in scenarios.md, co-editing tests/heading-coverage.json for any new H2): the post-merge janitor and the reconcile-merged janitor MUST provision their fresh checkout at the target repository's DEFAULT-BRANCH TIP that contains the item's merge — resolved via the ratified §'Self-contained plugin dispatch' → 'Default-branch resolution' rule — NOT at the item's historical merge sha. This lets a post-merge environment fix (a newly provided recipe, a repaired toolchain declaration) clear historical items on the next reconcile, while the venue still proves the item's merge is present (the tip contains it). If sha-pinning is deliberately retained anywhere for reproducibility, the contract MUST state explicitly how a post-merge environment fix ever clears an earlier item without a manual --janitor override. Required scenarios: (deadlock-cleared) an item merged before a janitor-environment fix landed is cleared by a reconcile run whose venue is the post-fix default-branch tip; (merge-present) the venue provisioning refuses or flags if the resolved tip does NOT contain the item's merge, so the venue still proves merge presence.
