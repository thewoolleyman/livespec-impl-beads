---
topic: journal-invoker-attribution
author: claude-fable-5
created_at: 2026-08-25T11:38:54Z
---

## Proposal: Generalize v051 door attribution: a journal invoker input with a resolution order and a committed tightening dial

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Generalizes the per-valve actor attribution spec v051 already ratified (the door rules' one-journaled-owner guarantee and the `reject:rework` valve's durable attributed record, shipped as `bd-ib-ktxb`) to the WHOLE dispatch-journal append path, and designs the identity-propagation surface reviewer fable's finding 5 showed the matrix omitted: a uniform invoker-identity INPUT on every published state-changing CLI (`--invoker <id>` flag, `LIVESPEC_INVOKER` environment variable) with a defined resolution order (flag > environment > a derived fallback that is explicitly MARKED unattributed rather than trusted), an `invoker` + `invoker_source` field pair stamped once by the journal append layer and inherited by every writer, and a committed, deliberately NOT-API-configurable `dispatcher.require_invoker` setting (default `false`) whose `true` posture refuses a state-changing invocation whose identity resolved only by fallback — BEFORE any mutation, as a precondition error. Day one nothing breaks (fallback marks, never refuses); a repo tightens by committing the key. Adds Scenarios 72-73.

### Motivation

Filed from the `homelab-loop-hardening-orchestrator` plan thread (ledger epic `bd-ib-ujihbw`), executing the Phase 2 charge of homelab's `steady-state-loop-hardening` program: the section-06 filing bound by that program's research/007 (finding fable 5 of this repository's commissioned adversarial reviews, homelab PR #1027, refined by the console review's c-fable 3). Every claim below was RE-VERIFIED against this repository's primary sources on 2026-08-25.

THE VERIFIED GAP. `commands/_dispatcher_io.py::JournalFile.append` stamps `{"at": <utc>}` plus the caller's record — no invoker identity anywhere in the append path, and no identity input exists on any published CLI surface. After homelab's first-day incident (that program's research/001/002 section 06), nobody — the foreman seat included — could establish from the journal who had started a key session or ordered a state-changing act.

THE RATIFIED PRIOR ART THIS GENERALIZES (never reinvents). Spec v051's §"Door rules — every transition has exactly one journaled owner" already requires every lifecycle transition to be attributable in the journal, and specifically that "the `reject:rework` valve MUST write a durable journal record" — shipped as `bd-ib-ktxb` (closed, PR #1048). The `drive` valve contract already states the journal "records the actor" for the guarded valves, and the host-route door "journals the actor and a driver-session". What v051 ratified PER DOOR, this proposal ratifies for the append path as a whole — citing it, exactly as finding fable 5 directs. (The ratified door-rules text still carries two STALE sentences claiming the reject:rework valve writes no journal record; their refresh is a co-edit of the sibling `acceptance-rework-state-machine` proposal, which ratifies first.) `bd-ib-gbu3k6` (backlog) holds the adjacent operator-facing ownership-attribution gap for concurrent dispatch and is not closed by this proposal.

WHY AN INPUT WITH A RESOLUTION ORDER, NOT A BARE FIELD REQUIREMENT. The matrix's original ask ("the journal append path requires an invoker identity field and refuses the write without one") fails closed against every existing caller on day one, and — worse — without a defined propagation surface every writer self-reports whatever it likes: attribution-by-honor-system, the same prose-shaped trust the program exists to retire. The consumers that must stamp identities (`foreman-act`, the console's command adapters) act THROUGH the published dispatcher/drive CLIs, so the identity must enter as a CLI-surface input with a defined precedence, and the append layer must record WHERE the identity came from (`invoker_source`), so a fallback-derived identity can never masquerade as an asserted one. The console review (c-fable 3) confirms the consumer side: the console currently stamps the constant `"operator"` and its action port passes no identity — its leg (resolve a real principal, forward it on every invocation) files in the console's own charge; this proposal defines the producer-side input it will call.

ROLLOUT POSTURE, STATED EXPLICITLY (fable 5's requirement). The ratification release ships the flag, the environment variable, the fallback marking, and the `dispatcher.require_invoker` key with default `false`: no existing caller breaks, and every record becomes attributed or EXPLICITLY unattributed immediately. The tightening to hard refusal is config-owned per consuming repo (commit `require_invoker: true`), not release-staged: a repo tightens when its callers pass identities, and the refusal is a startup precondition (exit 3) so no mutation is half-performed. `require_invoker` is deliberately NOT API-configurable and has no per-item override — an attribution-integrity dial editable over the same surface it audits would be self-defeating — so the console Settings-surface lockstep is NOT triggered (the per-key declaration the program's early-deliverables rule requires is made here: committed-configuration-only).

ATTENTION/RUNTIME INDEPENDENCE. This filing touches no attention kind, no shared-runtime type, and no console code; it is one of the runtime-independent filings the plan's R4 sequencing allows to proceed ahead of the livespec-runtime attention-surface baseline.

### Proposed Changes

All changes use BCP14 normative language and land in `SPECIFICATION/contracts.md` and `SPECIFICATION/scenarios.md`. The accepting revise pass MUST co-edit `tests/heading-coverage.json` for the two new `## Scenario` H2 headings.

#### 1. `contracts.md` — new subsection `### Journal invoker attribution`, placed adjacent to the door rules of §"Work-item state semantics"

Full text:

> ### Journal invoker attribution
>
> Every record the Dispatcher's journal append path writes MUST carry two fields stamped ONCE by the append layer and inherited by every writer above it: **`invoker`** (a non-empty opaque identity string) and **`invoker_source`** (exactly one of `flag`, `env`, `fallback`). Writers MUST NOT stamp these fields themselves; a record supplied with either field is refused by the append layer as a programming error, so the attribution cannot be forged one caller at a time. EVERY journal write MUST route through the append layer: writing the journal path directly is forbidden, the two shipped direct writers (the acceptance-rework disposition writer and the ledger-close status-normalization writer, which today bypass the layer and carry no timestamp) are migration obligations of this contract's implementation, and a mechanical control MUST prove no code appends to the journal path outside the layer — without this, the stamped-once guarantee governs only part of the journal, and the bypassed acceptance-rework record is the very provenance carrier the rework state machine designates.
>
> The identity enters on the published CLI surface and resolves in this order:
>
> 1. `--invoker <id>` on the invocation (`invoker_source: flag`) — accepted by every published state-changing entry point (`dispatcher.py` `loop` / `dispatch` / `reconcile-merged`, the `drive` operation's valve actions, and the `probe` subcommand once ratified — every later-ratified state-changing entry point inherits this input as a filing obligation of its own proposal).
> 2. Otherwise the `LIVESPEC_INVOKER` environment variable, when set and non-empty (`invoker_source: env`).
> 3. Otherwise the derived fallback `unattributed:<os-user>@<hostname>` (`invoker_source: fallback`). The fallback is a MARK, not an identity: it records that no caller asserted who acted.
>
> Identity strings are opaque to this contract; the RECOMMENDED convention is `<role>:<name>` (for example `human:<name>`, `session:<session-name>`, `foreman:<seat>`, `console:<principal>`), and callers acting on a human's explicit order SHOULD carry that human in the identity they assert. Where a ratified door already journals a door-specific actor field (the v051 valve records), that field remains; `invoker`/`invoker_source` is the uniform envelope-level attribution.
>
> **`dispatcher.require_invoker`** (boolean, committed `.livespec.jsonc`, default **`false`**) governs the fallback: when `true`, a published state-changing invocation whose identity would resolve by `fallback` MUST be refused at startup as a precondition error (exit `3`), naming the two accepted inputs — BEFORE any store mutation, journal write, or run creation, so no act is half-performed and no attribution gap is created by the refusal itself. When `false`, the fallback applies and the record is written marked `invoker_source: fallback`. This setting has NO per-item override (attribution is a property of the invocation, not the item) and is deliberately NOT API-configurable: it MUST NOT be editable through the console Settings surface or any remote API, because a dial that relaxes attribution MUST NOT be reachable over the surface whose acts it attributes. Read-only invocations (`--dry-run`, status reads) resolve and stamp identity identically when they journal, but are never refused on attribution grounds.

#### 2. `contracts.md` §"Dispatcher policy settings" — record the non-membership

Append one sentence to the section preamble:

> `dispatcher.require_invoker` (§"Journal invoker attribution") is a committed attribution-integrity dial, not a policy setting of this section: it has no per-item override and is deliberately not API-configurable.

And amend §"Control surface and audit", whose opening sentence today reads "Every setting MUST be settable via the orchestrator API" — a universal quantifier that would otherwise contradict this key (and the already-ratified `dispatcher.fabro_bin` / `dispatcher.codex_models` keys, which the shipped six-entry API-configurable manifest likewise omits). The amended opening scopes the quantifier and ratifies the existing practice:

> Every POLICY SETTING of §"Dispatcher policy settings" MUST be settable via the orchestrator API and, through it, the Control-Plane console. Keys ratified as COMMITTED-CONFIGURATION-ONLY (`dispatcher.require_invoker`; `dispatcher.fabro_bin` and `dispatcher.codex_models` by shipped precedent; any key a later ratification adds to this class) are deliberately outside the API-configurable key set, and the lockstep of §"API-configurable completeness" applies to the API-configurable set only.

And scope the `wip_cap` heading claim: §"`wip_cap` — the one setting with no per-item override"'s sentence describing it as "the ONE setting" gains "among this section's policy settings" (committed-configuration-only keys are not per-item properties either).

#### 3. `scenarios.md` — two new scenarios

```gherkin
## Scenario 72 — Every journal record carries a resolved invoker

Feature: Journal invoker attribution with a defined resolution order
  As an operator reconstructing an incident
  I want every journaled act to say who invoked it and how that identity was resolved
  So that attribution never depends on a writer's honor

Scenario: The flag wins over the environment
  Given a state-changing dispatcher invocation with --invoker set and LIVESPEC_INVOKER set
  When the invocation journals its records
  Then every record carries the flag identity with invoker_source flag

Scenario: The environment is used when no flag is passed
  Given a state-changing dispatcher invocation with only LIVESPEC_INVOKER set
  When the invocation journals its records
  Then every record carries that identity with invoker_source env

Scenario: An unasserted identity is marked, never trusted
  Given a state-changing dispatcher invocation with neither input set
  And dispatcher.require_invoker is false
  When the invocation journals its records
  Then every record carries the derived fallback identity with invoker_source fallback

Scenario: The append layer is the only writer and refuses forged fields
  Given a caller supplying a record that already carries an invoker or invoker_source field
  When the record reaches the append layer
  Then the append is refused as a programming error
  And a mechanical control proves no code appends to the journal path outside the layer

## Scenario 73 — The tightened posture refuses before it mutates

Feature: require_invoker refuses unattributed state-changing invocations at startup
  As a maintainer tightening attribution
  I want an unattributed invocation refused before any mutation
  So that the refusal itself never creates a half-performed act or an attribution gap

Scenario: A fallback-only invocation is refused as a precondition error
  Given dispatcher.require_invoker is true in the committed configuration
  And a state-changing dispatcher invocation with neither --invoker nor LIVESPEC_INVOKER
  When the invocation starts
  Then it is refused with the precondition exit code before any store mutation, journal write, or run creation
  And the refusal names the two accepted identity inputs

Scenario: The dial is not in this repo's API-configurable key manifest
  Given the orchestrator's API-configurable key manifest
  When its key set is read
  Then dispatcher.require_invoker is not among the keys
  And changing it requires a committed configuration change
```

#### 4. Revise-time co-edits

The accepting revise pass MUST add `tests/heading-coverage.json` entries for `## Scenario 72` and `## Scenario 73`. This proposal does not close `bd-ib-gbu3k6` (operator-facing concurrent-dispatch ownership attribution); the consumer legs (foreman-act, console principal forwarding) file in their owning repositories' charges and consume the input defined here.
