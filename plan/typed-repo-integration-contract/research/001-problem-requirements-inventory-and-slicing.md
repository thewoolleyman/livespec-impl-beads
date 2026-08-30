# 001 — The typed repository integration contract: problem, ratified requirements, code inventory, and proposed slicing

This is the opening research note of the `typed-repo-integration-contract` plan. It records why the plan exists, what specification revision v092 requires, where the contract's truth lives in the code today, how this plan relates to the plan it supersedes, and a proposed cut of the work into children. It files nothing; the children are proposed here and filed only after the maintainer reviews the cut.

Notation used in this note: `R<n>` names a requirement carrier (a ratified obligation this plan must deliver); `D<n>` names an explicit deferral; `file:line` cites a location on `origin/master` at commit `accff5ef` (release 0.109.0) on 2026-08-30; "ATTENDED" marks a child that must be hand-built through worktree, pull request and merge because it edits the factory workflow payload, which a factory run may not amend (constraints.md, the no-self-amending rule); "SAFE" marks a child the dark factory may build.

## 1. The architecture problem and the maintainer's ruling

Provenance: the ruling was made by the maintainer on 2026-08-30 in the Claude Code session named `janitor-argv-declared-resolution` (project `livespec-orchestrator-beads-fabro`, session UUID `905f2e54-1125-459d-9324-46de405dd1bd`), and ratified the same day as specification history version v092 (`SPECIFICATION/history/v092/`, proposal `typed-repo-integration-contract.md`, decision `modify`, independent ratification review verdict NO BLOCKERS).

The ruling, in the maintainer's words: the adopter-coupling defect class recurs "because our APIs suck. Because they are not clear and strongly typed and hardened. That is the root cause of why we do not know whether adopters will break or not." The instruction was to fix the class "mechanically and forever through good architecture and good API design principles", and not to be distracted by per-instance patches.

The mechanism, as measured in that session and in `plan/janitor-argv-declared-resolution/research/002-coupling-sweep-and-fail-fast-contract.md`: the blast radius of any change to what the orchestrator expects of a governed repository is the product of three multipliers.

1. Truth is DISTRIBUTED. The same integration fact (for example "the check suite to run after merge") lived in a Python tuple, in a `script=` string inside the workflow payload, in prepare-step shell in `workflow.toml`, in prose in five prompt files, in a second hardcoded core-ref default, and in a `compat.pinned` reader with its own silent semantics. Section 3 below lists the current locations.
2. Values are STRINGLY TYPED. Commands were shell strings the orchestrator could not inspect, so the host and sandbox check suites drifted to different literals, and whether the engine renders an `inputs.*` token inside a `script=` position was unknowable without a production dispatch.
3. Failure is LATE and SILENT. Resolution happened at runtime, in a remote sandbox, after an irreversible merge, and every absent key slid to a fleet default.

Revision v090 and its six follow-ups were symptom-shaped: each added one committed key and copied a resolver for it. The third such resolver (declared-core-provisioning, PR #2018) conflicted in four files with its two siblings, which is the pattern demonstrating itself. v092 is the architectural answer.

## 2. Requirement carriers from v092

Each carrier cites the ratified clause. Contract clauses are in `SPECIFICATION/contracts.md` §"Repository integration contract" (line 3006 at `accff5ef`); constraint clauses are in `SPECIFICATION/constraints.md` §"Governed-repository integration constraints" (line 637); scenarios are in `SPECIFICATION/scenarios.md`.

- R1 — ONE SCHEMA. One versioned, machine-readable `RepoIntegrationContract` schema, shipped in the plugin payload, enumerates every integration point the orchestrator requires of a governed repository: check suite per venue (host janitor and in-sandbox gate), bootstrap recipe, master-CI pipeline, core-provisioning repository and ref, prepare-toolchain premises, default branch. Commands are argv arrays. Venue is an explicit schema dimension. An integration point that is not a schema field is not a requirement the orchestrator may impose. (contracts.md clause 1; proposal `id_hint: integration-contract-schema`.)
- R2 — ONE RESOLVER, NO SILENT PATH, PER-FIELD OPTIONALITY. Every point is read through one generic schema-driven resolver returning the sum type `Declared(value) | FleetDefault(value) | Defective(key, reason)`. Only an ABSENT key with a declared fleet default resolves to `FleetDefault`; a present-but-unusable key resolves to `Defective`; the schema declares per field whether a fleet default exists, so an absent REQUIRED field (`compat.pinned`, which admits no safe default) resolves to `Defective` naming the absence, never to a substituted moving tip. Existing key names and their ratified semantics (`dispatcher.master_ci`, `dispatcher.janitor_bootstrap.recipe`, `dispatcher.janitor.check_suite`, `compat.pinned`, `compat.core_repo`) are preserved as schema fields; the per-key resolver modules are retired. (contracts.md clause 2; revision "third review round".)
- R3 — RESOLVE ONCE, PROJECT EVERYWHERE. The Dispatcher resolves the contract exactly once per dispatch, on the host, at plan-build time, into a frozen `ResolvedIntegrationContract` that is journaled and carried on the `DispatchPlan`. The host janitor argv, the fabro run inputs, prompt variables and prepare-step parameters are all projections of that object; the sandbox receives values and never resolves. The in-flight declared-core-provisioning behavior is re-homed onto this resolver. (contracts.md clause 3; `id_hint: resolved-contract-projection`.)
- R4 — TYPED WORKFLOW INPUTS AND THE SEAM-EQUIVALENCE CHECK. The implement-work-item workflow declares every input with a type and default; the in-sandbox janitor gate and the implementation-diff default-branch range are templated from those inputs; a CI check asserts that the set of `inputs.*` tokens in the workflow, the set the Dispatcher renders from the resolved contract, and the schema's projectable fields are identical, in both directions, and that every token sits in a position the engine renders. (contracts.md clause 4; Scenario 100 including its reverse-direction and non-rendered-position extensions; `id_hint: typed-workflow-inputs-seam-check`.)
- R5 — CONTRACT VERSION = SCHEMA VERSION. The executing plugin build names the schema version it requires; at first dispatch and on plugin-build or declaration change, the declaration is validated against it and every `Defective` point is enumerated in ONE pre-dispatch refusal (exit 3, journaled); no hand-maintained key list exists; an already-admitted item is not stranded. This realizes the v090 validation-pass and contract-versioning obligations. (contracts.md clause 5; Scenario 101; `id_hint: schema-validation-pass`.)
- R6 — SUPERSESSION BOOKKEEPING. The per-key MECHANISM clauses remain ratified as field semantics; the Factory-sandbox toolchain disposition clause is superseded with its no-op arm expressed as an explicit `FleetDefault` value; the members-and-adopters-identical audit gains its closing row. (contracts.md clause 6; revision "Modifications".)
- R7 — ADOPTER AND MEMBER FIXTURES. The integration test tier carries a fleet-member fixture and an ADOPTER fixture with zero fleet tooling (no mise, no fleet just recipes, no lefthook, no `livespec_dev_tooling`); every dispatch-path seam test (preflight, plan build, contract resolution, input rendering, workflow validation, sandbox stubbed) is parametrized over both and passes on both. (constraints.md bullet "Adopter and member fixtures"; Scenario 102; `id_hint: adopter-member-fixtures`.)
- R8 — FLEET-TOOLCHAIN LITERAL BAN. A `check-no-fleet-toolchain-literals` gate in the check aggregate (just check, pre-push, CI) fails on any fleet-toolchain literal (`mise`, a fleet just recipe name, `lefthook`, `livespec_dev_tooling`, `livespec-step-timer`, a bare default-branch name used as a ref) in the dispatcher package or workflow payload outside the single fleet-defaults module the schema designates. (constraints.md bullet "Fleet-toolchain literal ban"; Scenario 102; `id_hint: fleet-toolchain-literal-ban`.)

## 3. Where the contract's truth lives in the code today

All paths are under `.claude-plugin/` unless stated; `commands/` abbreviates `scripts/livespec_orchestrator_beads_fabro/commands/`.

- Per-key resolver modules to be retired into R2: `commands/_dispatcher_master_ci_pipeline.py`, `_dispatcher_master_ci_lookups.py`, `_dispatcher_master_ci_preflight.py`, `_dispatcher_master_ci_refusals.py` (master-CI), `_dispatcher_janitor_bootstrap_recipe.py` and `_dispatcher_step_janitor_bootstrap.py` (bootstrap recipe), `_dispatcher_janitor_check_suite.py` (check suite; consumed at `_dispatcher_plan_build.py:124`), `_dispatcher_janitor_core_provisioning.py` (core provisioning; fleet default `FLEET_JANITOR_CORE_REPO_URL` at line 66, the `pinned: "master"` bootstrap state at line 22).
- Plan-build seam: `commands/_dispatcher_plan_build.py` (imports the check-suite resolver at lines 13-14 and renders the janitor argv at line 124); `commands/_dispatcher_plan.py` (`DispatchPlan.janitor_core_repo_url` field at line 65 with its fleet default at line 106).
- Host janitor venue: `commands/_dispatcher_janitor_venue.py` (imports the master-CI lookups at line 48 and the bootstrap argv at line 52; provisions core at lines 182-214).
- Workflow payload, `.fabro/workflows/implement-work-item/workflow.fabro`: the implementation-diff dead-implementer check hardcodes `origin/master...HEAD` at line 114; the in-sandbox janitor gate hardcodes `mise exec -- just check-no-workflow-edits check` at line 126; the ACP adapter inputs `inputs.implement_adapter`, `fix_adapter`, `pr_adapter`, `review_adapter`, `disposition_adapter`, `review_fix_adapter` are rendered at lines 95-222; the comment at line 347 records the current understanding of which positions the engine renders.
- Prepare steps, `.fabro/workflows/implement-work-item/workflow.toml`: `livespec-step-timer` wrappers and fleet toolchain at lines 306 (fetch-unshallow), 349 (mise install), 352 (uv sync), 355 (lefthook install), 371 (commit-refuse install via `livespec_dev_tooling`), 386 (sandboxExempt), 399 and 409 (verification checks via `livespec_dev_tooling.checks`).
- Prompt prose that names the fleet toolchain or `origin/master`: `.fabro/workflows/implement-work-item/prompts/implement.md`, `fix.md`, `review.md`, `review-fix.md`, `pr.md`.
- Committed declaration surface read by the resolvers: `.livespec.jsonc` keys `dispatcher.master_ci`, `dispatcher.janitor_bootstrap.recipe`, `dispatcher.janitor.check_suite`, `compat.pinned`, `compat.core_repo`, read through `commands/_config.py`.

The `_DEFAULT_JANITOR` tuple named by the v090-era research no longer exists by that name on master; its role passed to `_dispatcher_janitor_check_suite.py` when `bd-ib-vdpnx3` landed.

## 4. Relationship to plan `bd-ib-6pshji` (janitor-argv-declared-resolution)

That plan delivered the v090 per-key contract and is the plan this one supersedes. Per the v092 revision file:

- `bd-ib-vdpnx3` (declared janitor check-suite) — merged; recorded as MIGRATED. Its key becomes a schema field; nothing is reverted.
- `bd-ib-qx4wmo` (declared core provisioning) — merged on 2026-08-30 as PR #2040 (`f246498c`) after the original PR #2018 conflicted; recorded as SUPERSEDED with its behavior re-homed onto the generic resolver by R3. It stands as a valid interim; R2/R3 absorb it rather than revert it.
- `bd-ib-f7qkne` (dispatch-integration-validation-pass) — SUPERSEDED by R5. At the time of writing it is completing a factory run (`01M1992VB221`) that was dispatched before the supersession was visible on that plan's timeline. Its outcome is to be evaluated against v092 when it lands: if its validation pass is a hand-maintained key list, it is interim code that R5 replaces; the maintainer chose to let the run complete rather than reap it. This note assumes nothing about that outcome.
- `bd-ib-2kpo7r` (declared-sandbox-toolchain, ATTENDED, not started) — SUPERSEDED by R4 (in-sandbox gate, prompt wrappers, workflow default-branch range) and by R7/R8 (prepare toolchain premises). It should be closed under the old epic with a rationale pointing here.
- `bd-ib-swwj5x` and `bd-ib-f3uuqm` — merged conformance and venue work; unaffected.

Winding down `bd-ib-6pshji` (disposing its superseded children and archiving) is that plan's own next action, not this plan's.

## 5. Proposed slicing (proposed only; nothing filed)

Layer 0 — schema and resolver (SAFE, dispatchable now):
- C1 `integration-contract-schema` (R1, R2): the versioned schema file plus kw_only dataclass, the generic resolver with the sum type and per-field optionality, and retirement of the four per-key resolver modules behind it, preserving every key name and semantics. Carries R6's field-semantics reading.

Layer 1 — depends on C1:
- C2 `resolved-contract-projection` (R3): resolve once at plan build into a journaled `ResolvedIntegrationContract` on `DispatchPlan`; project to the host janitor argv, fabro `--input` pairs, prompt variables and prepare parameters; re-home core provisioning onto it. SAFE.
- C3 `schema-validation-pass` (R5): pre-dispatch validation against the build's schema version, one enumerated refusal, no key list. SAFE. Depends on C1; its refusal wording depends on C2's journaled shape, so it follows C2.
- C4 `fleet-toolchain-literal-ban` (R8): the `check-no-fleet-toolchain-literals` gate. SAFE for the dispatcher-package scope; depends on C1 naming the single fleet-defaults module. The workflow-payload scope of the gate can only go green after C5, so the gate lands with the payload scope allow-listed until C5 merges (see D2).

Layer 2 — depends on C2:
- C5 `typed-workflow-inputs-seam-check` (R4): typed inputs in `workflow.fabro`, gate and diff range templated from them, prompt wrappers projected, and the seam-equivalence CI check. ATTENDED, because it edits `.claude-plugin/.fabro/workflows/`. The CI check itself is SAFE and could be split out if the maintainer prefers, but the check cannot pass before the payload edit, so they are proposed as one attended child.
- C6 `adopter-member-fixtures` (R7): the two fixtures and parametrization of every seam test over both. SAFE. Depends on C2 (the seams must be projections before an adopter fixture can pass them) and on C5 for the workflow-validation seam.

The critical path is C1 → C2 → C5 → C6; C3 and C4 hang off C1/C2 in parallel.

## 6. Explicit deferrals

- D1 — Migrating any adopter's committed declaration. Deferred because v092 preserves every key name and semantics (R2), so no migration is required; reconsidered only if C1 discovers a key whose ratified semantics cannot be expressed as a schema field, in which case it routes to `propose-change`.
- D2 — Extending the literal ban to prompt prose. The ban (R8) covers the dispatcher package and workflow payload; prompt `.md` files are covered by projection (R4) rather than by the gate. Reconsidered at C5, when the prompt wrappers become projections and the residual literal set is measurable.
- D3 — Upstream fabro changes (typed input declarations beyond what the pinned 0.254.0 fork renders). Deferred because the fork pin is normative (constraints.md §"Fabro runtime constraints"); C5 must work within what the pinned engine renders, and the seam check exists precisely to make that knowable. Reconsidered if C5 finds a required position the engine cannot render, which routes to the fabro fork branch, not to this plan.
- D4 — Disposing `bd-ib-6pshji`'s superseded children. Owned by that plan's wind-down, not by this plan (Section 4).
