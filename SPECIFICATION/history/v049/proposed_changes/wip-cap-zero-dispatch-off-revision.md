---
proposal: wip-cap-zero-dispatch-off.md
decision: accept
revised_at: 2026-07-26T09:04:32Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

ACCEPTED. The consumer's committed off-switch must mean what it says. The homelab adopter descoped factory dispatch and committed `dispatcher.wip_cap: 0` as its dispatch-off gate, governed by its own spec (homelab v005 §"Dispatch-off posture"), which names the committed value as a verifiable fact and explicitly defers its MEANING to this spec. This spec was silent on `wip_cap`'s value domain, and the shipped implementation treats 0 as out-of-domain in three places — so the committed off-switch silently resolves to a cap of 5, the exact inversion of the posture it encodes. Blessing 0 here makes the off-value documented, mechanically honored, and protected against a future `minimum: 1` tightening that would entrench the breakage as a documented constraint.

Scope discipline. The blessing is deliberately narrow: 0 is valid for `wip_cap` ONLY. v047's `host_dispatch_cap` gave this spec a second no-per-item-override integer ceiling, so the clause names it explicitly and carves it out with a reason — that key bounds a ceiling shared by every repo dispatching to the host, so a 0 there would switch dispatch off host-wide on one repo's say-so. The per-item-overridable caps stay positive integers, and `wip_cap` has no per-item override and no `clear` sentinel, so no sentinel ambiguity arises.

Intent-preservation gate: CLEAR, no contradiction to name. The load-bearing definition (§"`wip_cap` and `host_dispatch_cap` — the settings with no per-item override") cites repo `thewoolleyman/livespec`, `plan/archive/autonomous-mode/handoff.md` ("SESSION UPDATE — 2026-07-14 (cont. 12)" plus its CORRECTION / ADDENDUM). That record rules on PER-ITEM OVERRIDABILITY only ("Every dispatcher setting is per-item overridable EXCEPT `dispatcher.wip_cap`") and types the key as plain `int`, default `5` — it never constrains the value to positive. Blessing 0 is consistent with it, and §"`wip_cap` and `host_dispatch_cap`" is left untouched (including "Its value semantics are unchanged") because it defers to §"Per-repo WIP cap" as the authority this proposal amends in place.

Authoring discipline. Split (i) behavior ⇒ scenario is satisfied: the value-domain clause carries BCP14 MUSTs and is paired with a new Gherkin Scenario 50 plus the co-edited `tests/heading-coverage.json` link. Split (ii) placement: a user-observable wire-contract value domain belongs in contracts.md. Split (iii) cross-repo: the realization mechanism is this orchestrator's own, so it stays in this repo's SPECIFICATION/, not core.

Provenance and staleness. Filed 2026-07-23 by claude-fable-5 on behalf of the homelab adopter (which closed hl-5sm4fm on the principle "acceptance = filing, not landing", transferring accept/reject to this repo). Deliberately deferred by v046; carried with cross-proposal coordination notes by v047. All three collisions v047 predicted then materialized and were re-derived on 2026-07-26 before this pass: the edit (a) anchor (0 matches → 1), Scenario 49 → 50, and the renamed H3 citation.

Selective revise: `reconcile-merged-dispatch-lock` and `per-state-verb-vocabulary` belong to other threads and are deliberately left undecided this pass, per the v046 precedent.

IMPL DEBT, explicit and owed. This ratifies the contract, not the code. All three sites still contradict the new clause on master as of 2026-07-26: `_resolve_positive_int_setting` (`_dispatcher_policy_settings.py`) coerces a committed 0 to DEFAULT_WIP_CAP = 5; `wip_cap` is typed `positive_integer` in `_drive_config_schema.py`, refusing `set-config:wip_cap:0`; and `.claude-plugin/api-configurable-keys.json` publishes `positive_integer`. The post-revise gap-detection pass over v049 owes that work, and the Scenario 50 heading-coverage entry is filed as TODO for exactly that reason.

## Resulting Changes

- contracts.md
- scenarios.md
- ../tests/heading-coverage.json
