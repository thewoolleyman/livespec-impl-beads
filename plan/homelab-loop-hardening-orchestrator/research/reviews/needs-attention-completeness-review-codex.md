# Adversarial review of needs-attention-completeness — reviewer codex

## Executive verdict

Not ready to ratify as-is. The strongest defect is that the proposed “wait completeness” contract claims to cover every orchestrator-owned wait while omitting several waits the ratified specification already requires to remain surfaced, plus the factory-headroom wait introduced by another pending proposal.

## Findings

### 1. Confirmed — Axes 1 and 2: the exhaustive wait inventory is not exhaustive

**Cited sections:** [needs-attention-completeness.md, “Wait completeness”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:42); [contracts.md, “Dispatcher grooming behavior”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md:1152); [contracts.md, “Admission valve”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md:2197); [contracts.md, “Provider spend containment”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md:2604); [factory-headroom-preflight.md, “Refusal effect”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/factory-headroom-preflight.md:121).

**Defect:** The proposal says “Every wait state the orchestrator itself creates MUST compose,” but its four-entry inventory omits orchestrator-created states that existing or pending contracts require to stay surfaced.

**Evidence:**

- The proposal enumerates only capacity deferral, NEEDS_ATTENTION acceptance, `blocked`/`needs-human`, and manual `pending-approval`.
- The ratified spec also requires:
  - a non-converging dispatch bounced to `backlog` to be surfaced;
  - a factory-unsafe `ready` item to be surfaced for host routing;
  - a provider-exhaustion refusal to leave the item `ready` and “surfaced through the needs-attention awareness surface.”
- If the sibling factory-headroom proposal is ratified, its refusal likewise leaves the item `ready` until recovery and requires an actionable refusal naming the alternate-factory route.
- Negative search scope: I searched the full 80-line proposal for `provider-exhaustion`, `non-convergence`, `backlog bounce`, `storage headroom`, `headroom refusal`, `host-only`, and `awaits-scope-override`; none occurs.

The cited R1 research lists the same four populations, but that does not reconcile its broad “every wait” wording with the larger ratified population.

**Suggested fix:** Either narrow the normative claim to a precisely named “R1 four-population inventory” and reconcile that scope with every existing “MUST surface” clause, or define a genuinely extensible orchestrator-wait predicate and include at least provider exhaustion, host routing, non-convergence/regroom, and—if ratified—factory-headroom refusal. Add a rule requiring future refusal contracts that leave work parked to register their attention derivation and executable unblock.

### 2. Confirmed — Axes 4 and 5: “ready age” has no defined clock or durable source

**Cited sections:** [needs-attention-completeness.md, “Ready-work aging”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:41); [Scenario 84](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:64); [contracts.md, “Work-item beads-issue mapping”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md:3432); [store.py, `_record_to_work_item`](/data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec_orchestrator_beads_fabro/store.py:135); [vendored WorkItem](/data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/_vendor/livespec_runtime/work_items/types.py:177).

**Defect:** “Has waited past” the threshold can mean time since capture, time since the latest transition into `ready`, or time since eligibility became true. Those yield materially different facts, and only capture time currently exists.

**Evidence:**

- The proposal requires the “oldest age” of admission-eligible `ready` items but never defines the age’s origin.
- The ratified mapping defines only `captured_at`, mapped from beads `created_at`.
- The current `WorkItem` has `captured_at` but no `ready_since` or lifecycle-transition timestamp; `store.py` likewise materializes only `captured_at`.
- Negative search scope: across all four current ratified spec files and the complete `.claude-plugin/scripts/livespec_orchestrator_beads_fabro/` tree, I searched `ready_since`, `ready_at`, `ready_entered`, `entered_ready`, `status_changed`, `status_updated`, and `transition.*ready`. The only matches were transition prose; no durable age source exists.
- Scenario 84 has no negative control for an old item that only recently became `ready`, nor for an item that was long-ready but only recently became admission-eligible.

**Suggested fix:** Define the clock explicitly. If the intended measurement is time continuously admission-eligible in `ready`, specify a durable timestamp and reset rules for exit/re-entry and eligibility changes. Add controls distinguishing old capture/recent readiness, recent eligibility after a long dependency wait, exactly-at-threshold, and strictly-past-threshold.

### 3. Confirmed — Axes 1 and 4: the aggregate capacity “data” does not fit the ratified envelope as specified

**Cited sections:** [needs-attention-completeness.md, “Capacity facts”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:40); [contracts.md, “The needs-attention machine envelope”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md:752); [livespec-runtime contracts, `attention_item`](/data/projects/livespec-runtime/SPECIFICATION/contracts.md:395); [livespec-runtime contracts, `needs_attention`](/data/projects/livespec-runtime/SPECIFICATION/contracts.md:447).

**Defect:** One `hygiene:capacity:<repo>` item is required to carry a free-slot count and every holder with its reason “as data,” but the ratified wire shape provides no structured payload for those records.

**Evidence:**

- The proposal promises machine-consumable capacity truth and says every reporting surface must consume this composition or accounting directly.
- The v077 envelope allows exactly `id`, `kind`, `urgency`, one-line `summary`, `source_ref`, and one `handoff`.
- The ratified runtime v012 `HygieneScanFinding` likewise has only `type`, `resource`, `path`, `summary`, `command`, and urgency; it maps to the same flat item.
- Therefore an implementation must either hide an unbounded holder collection in human prose, invent an unspecified parser for `summary`, or add an unratified field. The first two do not satisfy a stable “composed as data” contract; the third contradicts the proposal’s “no runtime field is changed” statement.

**Suggested fix:** Choose one explicit representation:

- If this is human-readable only, define a deterministic one-line summary and stop calling it consumable structured data.
- If machines must consume holder records, define separate stable items such as `hygiene:capacity-hold:<work-item-id>` and precisely contract their summaries/reasons.
- If an aggregate structured payload is required, ratify that field in `livespec-runtime` first, as v077 requires.

### 4. Confirmed — Axis 2: the capacity fact conflicts with unresolved WIP scope and override semantics

**Cited sections:** [needs-attention-completeness.md, “Capacity facts”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:40); [wip-cap-bound-honesty.md, proposed counted-claim contract](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/wip-cap-bound-honesty.md:109); [wip-cap-bound-honesty.md, “The locality clause does not say WHICH local state”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/wip-cap-bound-honesty.md:234); [wip-cap-naming-collision.md, capacity-surface requirement](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/wip-cap-naming-collision.md:72); [wip-cap-naming-collision.md, unresolved label scope](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/wip-cap-naming-collision.md:157).

**Defect:** The proposal fixes the key as `hygiene:capacity:<repo>` and presents a generic free-slot count before the sibling proposals settle whether the bound is tenant- or checkout-scoped and despite one dispatch path bypassing it.

**Evidence:**

- `wip-cap-bound-honesty` requires the accepting revise pass to choose tenant scope or checkout scope; it expressly forbids leaving “this repository’s own” ambiguous.
- That sibling also says hand-picked `dispatch --item` bypasses `wip_cap`, so cap assertions must be scoped to enforcing paths.
- `wip-cap-naming-collision` requires every attention surface echoing the cap to use the final truthful label and explicitly says the label cannot be settled before the scope decision.
- The target proposal says only “free-slot count against `wip_cap`” and uses `<repo>` as the stable resource. It neither limits the fact to automatic/cap-enforcing admission nor disclaims the targeted override or Fabro’s separate scheduler ceiling.

**Suggested fix:** Sequence this proposal after the siblings’ scope resolution. Define the resource as the selected accounting scope identity, state that the count applies only to cap-enforcing paths, and require the final truthful capacity label plus the Fabro-scheduler disclaimer.

### 5. Confirmed — Axes 3 and 4: the claimed accounting verdict does not yet expose the ratified rework class

**Cited sections:** [needs-attention-completeness.md, “Composition with the ratified siblings”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:26); [contracts.md, “Rework-pending re-dispatch”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md:2293); [`ActiveClaimAccounting`](/data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_claim_reclaim.py:27); [`claimed_active_accounting`](/data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_claim_reclaim.py:46); [research/004, implementation children](/data/projects/livespec-orchestrator-beads-fabro/plan/homelab-loop-hardening-orchestrator/research/004-ratifications-and-children.md:54).

**Defect:** The proposal treats the v071 four-way accounting verdict as an available composition input, but the current implementation has no rework-pending field or classification.

**Evidence:**

- Ratified v071 correctly requires unlocked `rework:pending` items to be excluded from capacity and not recorded as abandoned.
- The current `ActiveClaimAccounting` contains only `active_count`, live-lock IDs, green-terminal IDs, and journal-unreadable IDs.
- For every unlocked item with a readable journal, the implementation appends an abandoned-claim record; it has no rework discriminator.
- The vendored `WorkItem` and `store.py` materializer contain no `rework_pending` field.
- Research/004 still lists “stamp + materialize rework:pending” and re-dispatch as implementation children, confirming the ratified contract has not landed in this code.
- Second-order consequence: Scenario 83 cannot pass through “composition only.” Re-reading the raw label in needs-attention would violate the proposal’s single-accounting-authority rule.

**Suggested fix:** Make completion of the v071 materialization/accounting child an explicit prerequisite. Extend `WorkItem` and `ActiveClaimAccounting` with the ratified rework class first, then consume that verdict without fallback re-derivation.

### 6. Confirmed — Axes 3, 4, and 5: acceptance composition cannot represent the promised valves unambiguously, and no scenario tests wait completeness

**Cited sections:** [needs-attention-completeness.md, “Wait completeness”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:42); [contracts.md, “The NEEDS_ATTENTION verdict”](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md:2794); [contracts.md, envelope handoff field](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md:771); [`human_valves`](/data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_needs_attention_work_items.py:74); [proposed scenarios](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:46).

**Defect:** A parked acceptance has three valid dispositions, but an attention item has one handoff, the proposal does not specify item cardinality or stable IDs, and the current implementation advertises only `accept`.

**Evidence:**

- The ratified verdict names `accept:<id>` and both `reject:<id>:rework|regroom`.
- The machine envelope permits exactly one `handoff` per attention item.
- Current `human_valves` emits one `accept` lane for every item in `acceptance`; it emits neither reject choice.
- The proposal says “the `accept`/`reject` valves” without stating whether this means three attention items, which IDs they use, or which handoff a single item should carry.
- Negative search scope: I read the complete `_needs_attention_work_items.py` and searched it for `reject`; there is no rejection branch. I also checked the complete proposed scenario block, lines 48–76: it contains only capacity and aging, so no scenario can falsify any wait-completeness requirement.

**Suggested fix:** Specify one independently actionable `valve` item per disposition, with exact stable IDs and action IDs, and add a scenario proving all three appear only for an eligible parked acceptance. Add another scenario exercising every declared wait class and a non-wait control.

### 7. Confirmed — Axis 5: Scenario 83 cannot falsify incorrect capacity arithmetic

**Cited sections:** [Scenario 83](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:49); [proposal’s accounting classes](/data/projects/livespec-orchestrator-beads-fabro/SPECIFICATION/proposed_changes/needs-attention-completeness.md:26).

**Defect:** “The free-slot count reflects the accounting’s verdict” is tautological without a configured cap or expected number, and the scenario omits the fail-closed journal-unreadable class.

**Evidence:**

- Scenario 83 supplies one live lock but no `wip_cap`, then asserts no numeric free-slot result.
- It includes green-terminal and rework exclusions, but not the journal-unreadable class that must count as a held slot.
- Negative search scope: within the complete scenario block at lines 48–76, `journal-unreadable`, `unreadable journal`, and `journal unreadable` have no matches; those terms appear only in the proposal prose.

An implementation that incorrectly treats unreadable journals as free or emits any arbitrary free-slot number could still satisfy the written scenario.

**Suggested fix:** Give the scenario a concrete cap and include live-lock, journal-unreadable, stale, and rework rows. Assert the exact held count, exact free count, reasons, exclusions, and distinct stable IDs. Add the negative control that an unreadable journal never increases free capacity.

## Unverified observations

The proposal’s factual assertion that foreman/overseer waits already publish as ledger state on owning plan epics was not independently checked against a separate overseer implementation repository. The requested orchestrator research supports it, but verifying the overseer’s ratified contract and plan-epic writer would establish deployed behavior rather than only internal consistency.

## What the proposal gets right

The `hygiene:<type>:<resource>` claim is correct: the ratified livespec-runtime baseline accepts three-part hygiene IDs and maps arbitrary `HygieneScanFinding.type` and `.resource` values to that form, so the proposed IDs themselves need no runtime grammar or kind change.

The R1 dependency direction is internally sound: the orchestrator remains unaware of overseer surfaces, while runtime owns the shared types and grammar and this repository owns derivation, thresholds, and handoffs. That matches both the cited research and v077’s ownership cut.

Scenarios 83–84 also follow the current ratified maximum of Scenario 82; the numbering is consistent.

Codex session ID: 01a03934-0fd5-7423-a699-ee5a0f11cb36
Resume in Codex: codex resume 01a03934-0fd5-7423-a699-ee5a0f11cb36
