---
topic: typed-repo-integration-contract
author: janitor-argv-declared-resolution
created_at: 2026-08-30T08:27:25Z
spec_commitments:
  impl_followups:
    - id_hint: integration-contract-schema
      description: |
        Define the versioned RepoIntegrationContract schema (one machine-readable schema file in the package, with a matching kw_only dataclass) enumerating EVERY integration point the orchestrator requires of a governed repository: check-suite per venue (host janitor / in-sandbox gate), bootstrap recipe, master-CI pipeline, core provisioning (repo + ref), prepare toolchain premises, default branch. Commands are argv arrays. Replace the three hand-rolled per-key resolvers (janitor_bootstrap, master_ci, janitor.check_suite) plus the compat.pinned/core_repo reads with ONE generic schema-driven resolver returning the Declared | FleetDefault | Defective sum type. Existing committed key names and their absent/default/defective semantics are preserved verbatim so no adopter config migrates.
    - id_hint: resolved-contract-projection
      description: |
        Resolve the contract ONCE at plan-build time on the host into a frozen, journaled ResolvedIntegrationContract carried on the DispatchPlan, and PROJECT it into every seam — the host janitor argv, the fabro --input pairs, prompt variables, and prepare-step parameters. No seam re-derives an integration value from config or a literal; a consumer that must handle Defective is forced to by the type. Re-home the in-flight declared-core-provisioning behavior (compat.pinned refuse-on-defect, compat.core_repo) onto this resolver rather than re-landing it as a fourth per-key resolver.
    - id_hint: typed-workflow-inputs-seam-check
      description: |
        Declare every implement-work-item workflow input with a type and default in the workflow payload, template the in-sandbox janitor gate and the implementation_diff default-branch range from those inputs, and add a CI check asserting the set of inputs.* tokens in the workflow, the set the Dispatcher renders from the ResolvedIntegrationContract, and the schema's projectable fields are identical — and that every token sits in a position fabro renders. This absorbs the in-sandbox janitor gate, node-prompt tool-wrapper, and workflow.fabro default-branch parts of declared-sandbox-toolchain; workflow-payload edits remain an ATTENDED route per the factory-sandbox credential constraints.
    - id_hint: adopter-member-fixtures
      description: |
        Commit two governed-repository fixtures under the integration test tier: a fleet-member fixture carrying the fleet toolchain, and an ADOPTER fixture with zero fleet tooling (no mise, no justfile recipes, no lefthook, no livespec_dev_tooling). Every dispatch-path seam test (preflight, plan build, contract resolution, input rendering, workflow validation, with the sandbox stubbed) runs parametrized over BOTH fixtures, so members-and-adopters-identical is a failing test rather than prose.
    - id_hint: fleet-toolchain-literal-ban
      description: |
        Add a justfile check-no-fleet-toolchain-literals gate (AST/text, in the check aggregate) that fails when a fleet-toolchain literal — mise, just recipe names, lefthook, livespec_dev_tooling, livespec-step-timer, or a bare default-branch name — appears anywhere in the dispatcher package or workflow payload outside the single fleet-defaults module the schema names, so a new hardcoded premise cannot be reintroduced.
    - id_hint: schema-validation-pass
      description: |
        Realize the v090 up-front integration-contract validation pass and contract versioning AS schema validation: at first dispatch (and on plugin-build or declaration change) validate the repository's declaration against the contract schema version the executing build requires, and refuse pre-dispatch with every Defective point enumerated in one message. No hand-maintained checklist of keys exists; the pass is derived from the schema. This absorbs dispatch-integration-validation-pass.
  supersedes:
    - dispatch-integration-validation-pass
    - declared-sandbox-toolchain
---

## Proposal: Typed repository integration contract: single schema, generic resolver, resolve-once-project-everywhere

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

Replace the per-key declared-resolution pattern (v074 master_ci, v087 janitor_bootstrap, v090 janitor.check_suite and core provisioning — each a hand-rolled resolver) with ONE versioned, machine-readable RepoIntegrationContract schema that enumerates every integration point the orchestrator requires of a governed repository, ONE generic resolver returning a Declared | FleetDefault | Defective sum type, and a resolve-once-on-the-host, project-everywhere discipline. Existing key names and semantics are preserved; what changes is that the contract becomes a typed API object with a single source of truth instead of an ambient set of assumptions scattered across Python tuples, workflow script strings, prompt prose and prepare shell.

### Motivation

The maintainer's architecture ruling (2026-08-30): the adopter-coupling class recurs because the orchestrator↔governed-repo contract is not an API — it is not clear, strongly typed, or hardened. This session measured the mechanism directly. Blast radius is the product of three multipliers: truth DISTRIBUTED across six places (a Python tuple, a workflow script= string, workflow.toml prepare shell, five prompt files, a second hardcoded core-ref default, and a compat.pinned reader with different silent semantics); STRINGLY-TYPED commands the orchestrator cannot inspect (the host and sandbox check-suites drifted to different literals because nothing types them as one concept, and whether fabro renders inputs inside script= is unknowable without a production dispatch); and LATE, SILENT failure (runtime, in a remote sandbox, after an irreversible merge, every absent key sliding to a fleet default). v090 and its six followups are symptom-shaped: they add one key and copy the resolver per key — the in-flight declared-core-provisioning PR #2018 now conflicts in four files with its two sibling per-key resolvers, which is the pattern demonstrating itself. The right fix is architectural, so it is ratified here rather than accreted key by key.

### Proposed Changes

Add a new subsection '### Repository integration contract' to SPECIFICATION/contracts.md immediately after '### Dispatch preflight and post-merge step discipline', with the corresponding scenarios in scenarios.md (co-editing tests/heading-coverage.json for the new H2/H3s). Clauses:

(1) ONE SCHEMA. The set of integration points the orchestrator requires of a governed repository MUST be enumerated by a single versioned, machine-readable RepoIntegrationContract schema shipped in the plugin payload. Every integration point named anywhere in this specification — check-suite per venue (host janitor and in-sandbox gate), bootstrap recipe, master-CI pipeline, core provisioning repository and ref, prepare-toolchain premises, default branch — MUST be a field of that schema; an integration point that is not a schema field is not a requirement the orchestrator may impose. Commands MUST be typed as argv arrays, never shell strings. Where a point legitimately differs by venue, the venue MUST be an explicit schema dimension, never two divergent literals.

(2) ONE RESOLVER, NO SILENT PATH. Every integration point MUST be read through one generic, schema-driven resolver whose result is the sum type Declared(value) | FleetDefault(value) | Defective(key, reason). Only a truly ABSENT key resolves to FleetDefault; a present-but-unusable key resolves to Defective; no code path may substitute a default for a Defective. Existing committed key names (dispatcher.master_ci, dispatcher.janitor_bootstrap.recipe, dispatcher.janitor.check_suite, compat.pinned, compat.core_repo) and their ratified absent/default/defective semantics are PRESERVED as schema fields, so no adopter declaration migrates; the per-key resolver modules are retired in favor of the generic one.

(3) RESOLVE ONCE, PROJECT EVERYWHERE. The Dispatcher MUST resolve the contract exactly once per dispatch, on the host, at plan-build time, into a frozen ResolvedIntegrationContract that is journaled with the dispatch record and carried on the dispatch plan. Every seam — the host janitor argv, the fabro run inputs, prompt variables, prepare-step parameters — MUST be a PROJECTION of that resolved object. No seam may re-derive an integration value from configuration or from a literal at a later point; the sandbox receives values and never resolves. (This generalizes the already-ratified rule that ACP adapters ride the plan because re-deriving at launch is how the record and the run come to disagree.)

(4) TYPED WORKFLOW INPUTS AND THE SEAM EQUIVALENCE CHECK. The implement-work-item workflow payload MUST declare every input it consumes with a type and a default. The set of inputs.* tokens the workflow references, the set of inputs the Dispatcher renders from the ResolvedIntegrationContract, and the schema's projectable fields MUST be identical, and every token MUST sit in a position the engine renders; a CI check MUST enforce this equivalence so a templating question is answered statically rather than by a production dispatch.

(5) CONTRACT VERSION = SCHEMA VERSION. The v090 up-front validation pass and contract-versioning obligations are REALIZED as schema validation: the executing plugin build names the contract schema version it requires; at first dispatch, and on plugin-build or declaration change, the repository's declaration is validated against it and every Defective point is enumerated in one pre-dispatch refusal (exit 3, journaled). No hand-maintained list of keys exists anywhere; adding an integration point means adding a schema field, and the validation pass, the seam check, and the fixtures below pick it up without further edits.

(6) SUPERSESSION. This subsection supersedes the per-key MECHANISM described by 'Master-CI pipeline resolution', 'Janitor-bootstrap recipe resolution', 'Janitor check-suite resolution' and 'Janitor-core provisioning resolution' — those clauses remain ratified as the SEMANTICS of the corresponding schema fields and are read as such; and it absorbs the 'Up-front integration-contract validation pass' and 'Contract versioning' clauses as (5). The 'Members-and-adopters-identical audit' list gains one closing row: every step and preflight is dispositioned identically by construction because every integration point is a schema field validated against the adopter fixture (see the constraints amendment filed alongside).

Required scenarios (Given/When/Then): (resolve-once) a dispatch resolves the contract once at plan-build, journals it, and the host janitor argv and the in-sandbox gate input render the SAME check-suite value from that object; (no-silent-path) a present-but-unusable key resolves to Defective and no seam receives a default for it; (seam-equivalence) a workflow token with no matching rendered input, or a rendered input with no workflow token, fails the CI seam check; (schema-versioned refusal) an executing build requiring a newer contract version than a repository declares refuses pre-dispatch enumerating every Defective point in one message, and an already-admitted item is not stranded. NON-GOAL: no new committed key is introduced and no existing key is renamed.

## Proposal: Members-and-adopters-identical is a failing test: adopter fixture and fleet-toolchain literal ban

### Target specification files

- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

Make the members-and-adopters-identical principle mechanically enforced rather than prose: two committed governed-repository fixtures (a fleet member, and an ADOPTER with zero fleet tooling) over which every dispatch-path seam test is parametrized in the integration tier, plus a check-aggregate gate that bans fleet-toolchain literals outside the single fleet-defaults module the contract schema names.

### Motivation

Every instance in this class (v087 janitor-bootstrap, the six v090 instances, and the four found in-repo at HEAD 65f34d62) was discovered by an adopter breaking in production, because there is no adopter in the test suite: the principle lives in contracts.md and is enforced by homelab. An adopter fixture converts the principle into a test that a new hardcoded premise cannot pass, and a literal ban makes the premise un-authorable in the first place — the 'forever' half of the fix. This repo already enforces comparable rules mechanically (check-no-workflow-edits, check-no-fleet-pat-dispatch-surface, check-no-direct-tool-invocation), so the gate follows an established convention rather than inventing one.

### Proposed Changes

Add two constraints to SPECIFICATION/constraints.md under a new '## Governed-repository integration constraints' heading (or, if the maintainer prefers fewer H2s at revise time, as bullets under '## Forbidden patterns'), with paired scenarios in scenarios.md:

(a) ADOPTER AND MEMBER FIXTURES. The integration test tier MUST carry two committed governed-repository fixtures: a fleet-member fixture carrying the fleet toolchain, and an adopter fixture carrying NO fleet tooling — no mise, no justfile recipes named by the fleet convention, no lefthook, no livespec_dev_tooling. Every test of a dispatch-path seam — preflight, plan build, contract resolution, input rendering, workflow validation, with the sandbox stubbed — MUST be parametrized over both fixtures and MUST pass on both. A seam test that runs against the member fixture only is non-conforming. The adopter fixture MUST declare its integration points through the contract schema and nothing else, so that any orchestrator behavior that depends on an undeclared fleet premise fails the adopter leg.

(b) FLEET-TOOLCHAIN LITERAL BAN. A fleet-toolchain literal — mise, a fleet just recipe name, lefthook, livespec_dev_tooling, livespec-step-timer, or a bare default-branch name such as master or main used as a ref — MUST NOT appear in the dispatcher package or the workflow payload outside the single fleet-defaults module the RepoIntegrationContract schema designates. A check-aggregate gate (check-no-fleet-toolchain-literals, run by just check, pre-push and CI) MUST fail on any such literal, so a new hardcoded premise cannot be reintroduced by a later change.

Required scenarios: (adopter-passes) the adopter fixture with a complete contract declaration passes every dispatch-path seam test with zero fleet tooling present; (member-unchanged) the member fixture passes the same tests on fleet defaults; (literal-reintroduced) a change that adds a fleet-toolchain literal outside the fleet-defaults module fails check-no-fleet-toolchain-literals and the adopter-fixture leg.
