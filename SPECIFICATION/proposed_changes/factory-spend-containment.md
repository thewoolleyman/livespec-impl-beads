---
topic: factory-spend-containment
author: claude-opus-5
created_at: 2026-08-22T10:18:54Z
---

## Proposal: Spend containment is a factory obligation — no dispatch into an observed-exhausted provider window, and no cross-vendor burn on a dead implementer

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Adds two normative prohibitions to §"Dispatcher admission, WIP cap, and
post-merge acceptance", together with the observation rule that makes them
decidable and the journaling rule that keeps them visible:

1. The Dispatcher MUST NOT admit an item into a sandbox against a model provider
   whose usage or spend ceiling it has OBSERVED to be reached and whose reset it
   has no evidence of.
2. Once a run's implementer is known dead, the workflow MUST NOT continue
   spending a SECOND vendor's allowance evaluating its absent output.

The exhaustion signal MUST derive from a real dispatch outcome, never from
inspecting credential material, and MUST carry an expiry so that the rule is a
discrimination rule rather than a standing outage. Every containment refusal is
an auto-disposition and MUST be journaled under the existing audit obligation.

This states an obligation the factory does not currently carry. It does NOT
retroactively cover the two containment fixes already shipped (PR #1711 per-node
Codex model tiers, PR #1732 provider-limit permanence); those are separately
owned by `bd-ib-var6` and `bd-ib-qpuu`.

### Motivation

The maintainer holds ONE OpenAI Codex subscription against five Anthropic Claude
subscriptions, and the stated constraint on this work is that a second Codex
subscription is not to be bought. Containment is therefore a product obligation
of the factory, not a tuning preference — and today the specification does not
say so anywhere. Every measurement below was taken 2026-08-22 against the `hp`
factory and the `fabro` Honeycomb dataset, and is recorded in full in
`plan/factory-spend-containment/research/opening-research-2026-08-22.md`.

**The scale of the bleed.** Codex is 87% of all factory agent wall-time (89.0 of
102.8 agent-hours over seven days), and the rate is rising rather than flat: the
last 24 hours alone were 36.5 Codex agent-hours, roughly 2.9x the seven-day daily
average. Two independent instruments agree on how much of it is discarded. From
`run_turn` spans, 51.2 of 89.0 Codex agent-hours (57.5%) sit in runs that never
emitted `Workflow run completed`, of which 50.9 hours are the `implement` node
and only 0.13 reached `pr`. From `fabro ps -a` on the hp factory, 53 failed runs
consumed 118.2 of 216.8 run-hours (54.5%), averaging 2h14m each against 23m for
successes. The two routes agree within three points, which is what makes the
number usable rather than suggestive.

**FALSEHOOD OF OMISSION 1 — nothing forbids dispatching into a dead window.**
All 53 failed runs were inspected. Thirteen carried a diagnosable cause chain,
and ELEVEN of those thirteen were provider usage or spend refusals — 10 Codex,
1 Anthropic — consuming 21.1 of the 118.2 failed run-hours. The verbatim payload
of run `01M0DN6CTWPF`, at `causes[1]`:

    { "message": "You've hit your usage limit. Visit
                  https://chatgpt.com/codex/settings/usage to purchase more
                  credits or try again at Aug 20th, 2026 3:33 AM.",
      "codex_error_info": "usage_limit_exceeded" }

These arrive in BURSTS — three at 240m and three at 152m inside two ID-adjacent
windows — precisely because nothing stops the next dispatch from marching into
the same exhausted window. The absence of the rule is what makes one exhaustion
event cost many runs instead of one.

**FALSEHOOD OF OMISSION 2 — nothing stops a dead implementer from spending the
other vendor.** Recorded on `bd-ib-oj71` and independently corroborated: with the
implementer dead from its first turn, the workflow still cycles janitor, FOUR
Claude Opus review rounds, and a disposition round against a branch
byte-identical to `origin/master`, plus 16 empty process-stage commits. Codex
exhaustion therefore burns the Claude subscriptions too, and there is no circuit
breaker. The specification today contains no clause a reviewer could cite to call
that a defect.

**Why the spec and not just the code.** §"Dispatcher admission, WIP cap, and
post-merge acceptance" enumerates the admission valve's conditions exhaustively
— permission, capacity, assignee resolvable, factory-safe — and states that
eligibility IS that conjunction ("eligible = dependencies clear AND an assignee
is resolvable AND `factory_safety` is null"). An implementation that adds a fifth
refusal condition without amending that sentence would contradict the ratified
contract. `bd-ib-jtja` (C4, admission gate) and `bd-ib-vdpb` (C5, circuit
breaker) both carry a `blocks` edge on this proposal's work-item `bd-ib-nl97` for
exactly that reason: neither can land against a contract that says the valve has
four conditions.

**Why observation and not prediction.** The obvious implementation — read the
host's Codex `auth.json` and preflight the quota — is measured insufficient, and
this is a binding rider on `bd-ib-oj71` (2026-08-20T02:50). Host and sandbox
Codex credential state DIVERGE BY CONSTRUCTION: `project_codex_auth_snapshot`
replaces the refresh token with `CODEX_NON_ROTATABLE_REFRESH_SENTINEL` before the
sandbox ever sees it, so a host-side read describes a different credential than
the one that will be spent. Ratifying "observed, not predicted" prevents the
implementation from being rebuilt down that route.

**Why an expiry is load-bearing rather than a detail.** A refusal rule with no
reset condition is not containment; it is an outage that begins at the first
quota refusal and never ends. The provider's own refusal text carries the reset
instant (`try again at Aug 20th, 2026 3:33 AM` in the payload above), so the
expiry is available from the same observation that establishes the exhaustion.

### Proposed Changes

### Amend §"Admission valve (`ready → active`)" — add the fifth condition

Add one bullet to the existing condition list, after the `Factory-safe` bullet:

    - **Provider window not observed exhausted:** an item whose dispatch would
      run against a model provider for which the Dispatcher holds an unexpired
      OBSERVED exhaustion record is not admitted. See §"Provider spend
      containment" below. The item is NOT marked `blocked` on these grounds and
      MUST NOT be auto-disposed; it remains `ready` and is admitted on a
      subsequent pass once the record expires.

And amend the eligibility conjunction sentence in the same section so it stays
exhaustive. Replace:

    (eligible = dependencies clear AND an assignee is resolvable AND
    `factory_safety` is null — `admission_policy` plays no part at this valve)

with:

    (eligible = dependencies clear AND an assignee is resolvable AND
    `factory_safety` is null AND no unexpired observed provider-exhaustion
    record covers the provider the item would dispatch against —
    `admission_policy` plays no part at this valve)

### Add `SPECIFICATION/contracts.md` §"Provider spend containment"

Add as a new `###` subsection of §"Dispatcher admission, WIP cap, and post-merge
acceptance", placed immediately after §"Host concurrency belongs to the Fabro
scheduler":

    ### Provider spend containment

    The factory spends a metered, exhaustible allowance on every model provider
    it dispatches against, and those allowances are NOT interchangeable: the
    fleet holds a single OpenAI Codex subscription against several Anthropic
    subscriptions, so an hour of Codex allowance is the scarce resource and an
    hour spent producing nothing is not recoverable. Containment is therefore a
    stated obligation of the Dispatcher, not a tuning preference.

    **No dispatch into a known-exhausted window.** The Dispatcher MUST NOT launch
    a sandbox run against a model provider whose usage or spend ceiling it has
    already OBSERVED to be reached and for which it holds no evidence of a reset.
    The refusal is an admission-valve condition (§"Admission valve (`ready →
    active`)"), evaluated BEFORE any sandbox is launched.

    **No cross-vendor burn on a dead implementer.** Once a run's implementer node
    has terminated without producing any change to the worktree relative to the
    dispatch base, the workflow MUST NOT continue to spend a SECOND vendor's
    allowance evaluating its absent output. Review, review-fix, and disposition
    rounds against a tree byte-identical to the dispatch base MUST NOT be
    executed. The run is finalized with the implementer's own failure as its
    surfaced cause.

    **Observed, not predicted.** The exhaustion signal MUST derive from a real
    dispatch outcome — the typed provider-limit condition carried on a completed
    run's failure detail — and MUST NOT be derived by inspecting credential
    material. A host-side read of the provider's credential file is specifically
    insufficient and MUST NOT be used: host and sandbox credential state diverge
    by construction, because the worker credential projection (§"Worker
    credential projection") substitutes a non-rotatable sentinel for the refresh
    token before the sandbox receives it.

    **Every exhaustion record expires.** An observed-exhaustion record MUST carry
    an expiry instant and MUST NOT be permanent. Where the provider's own refusal
    states when the window resets, that instant is the expiry. Where it does not,
    a bounded default expiry applies. The Dispatcher MUST admit normally once the
    record has expired, and MUST admit normally against any provider for which it
    holds no unexpired record. A rule that refuses unconditionally is not
    containment; it is an outage.

    **No silent containment.** A refusal to admit on containment grounds, and a
    truncation of a run under the dead-implementer rule, are each
    auto-dispositions and MUST be journaled under §"Control surface and audit",
    carrying at minimum the work-item id, the governing condition, the provider
    and the observed record's expiry. Neither MAY be silent.

    **Relationship to the human-gate floor.** This section does NOT relax
    §"Every needs-human escalation still reaches a human". Refusing to dispatch
    is not auto-resolving an item: the item stays open, stays `ready`, and stays
    surfaced through the needs-attention awareness surface. No containment
    refusal MAY dispose of a `blocked_reason: needs-human` item.

### Amend §"Control surface and audit" — extend the auto-disposition enumeration

In the sentence beginning "Every auto-disposition a setting enables", replace the
parenthetical list:

    an auto-approve, an AI auto-accept, an AI-fail auto-rework, a ship-on-cap, a
    cap-exceeded escalation

with:

    an auto-approve, an AI auto-accept, an AI-fail auto-rework, a ship-on-cap, a
    cap-exceeded escalation, a provider-exhaustion admission refusal, a
    dead-implementer run truncation

### Add two scenarios to `SPECIFICATION/scenarios.md`

Numbered from 60, because the pending `wip-cap-naming-collision` and
`wip-cap-bound-honesty` proposals claim 57, 58 and 59.

    ## Scenario 60 — An observed provider exhaustion refuses admission, and expires

    Given the Dispatcher has observed a provider usage-limit refusal on a
      completed run against provider "codex"
    And that observation carries an expiry instant in the future
    When the Dispatcher evaluates the admission valve for a ready item that would
      dispatch against provider "codex"
    Then the item is not admitted
    And the item remains at status "ready" and is not marked "blocked"
    And the refusal is journaled with the work-item id, the governing condition,
      the provider and the expiry
    When the expiry instant has passed
    Then a subsequent Dispatcher pass admits the item normally

    ## Scenario 61 — A dead implementer does not spend the second vendor

    Given a factory run whose implementer node terminated without changing the
      worktree relative to the dispatch base
    When the workflow advances past the implementer node
    Then no review, review-fix, or disposition round is executed against that
      tree
    And the run is finalized carrying the implementer's own failure as its
      surfaced cause
    And the truncation is journaled with the work-item id and the governing
      condition

### Co-edit required at revise time

The accepting revise pass MUST add one `tests/heading-coverage.json` entry for
the new `## Provider spend containment` H3's parent H2 coverage as this repo's
map requires, and one entry per new `## Scenario` H2 in `scenarios.md`, per this
repo's revise co-edit discipline. The `test` value MAY be the literal `"TODO"`
with a non-empty `reason`.

### What this proposal deliberately does NOT do

It does NOT specify the mechanism by which the exhaustion record is stored or the
value of the bounded default expiry — those are implementation decisions owned by
`bd-ib-jtja`. It does NOT retroactively ratify the per-node Codex model tiers
shipped in PR #1711 (owned by `bd-ib-var6`) or the provider-limit permanence
shipped in PR #1732 (owned by `bd-ib-qpuu`). It does NOT shorten the escalate
gate window or tune `stall_timeout`, which the plan defers as D3 on the recorded
ordering constraint that shortening the window before preserve-by-reference lands
converts a visible stall into faster data loss. It does NOT raise `implement`
`max_retries` or its backoff, deferred as D4 behind the admission gate, because
retrying a misclassified quota refusal spends the exhausted allowance harder. It
does NOT touch the fabro-side classifier or the `CODEX_ACP_VERSION` pin, deferred
as D1 as outward-facing fork work. It does NOT introduce a host-level dispatch
concurrency ceiling and MUST NOT be read as licensing one — §"Host concurrency
belongs to the Fabro scheduler" is untouched, and a provider allowance is not a
host resource.

### Relationship to the pending sibling proposals (2026-08-22)

`wip-cap-naming-collision` and `wip-cap-bound-honesty` are both pending against
§"Dispatcher admission, WIP cap, and post-merge acceptance". They amend
§"Per-repo WIP cap" and §"Host concurrency belongs to the Fabro scheduler"; this
proposal amends §"Admission valve (`ready → active`)" and §"Control surface and
audit" and ADDS a sibling subsection, so the three do not collide textually. A
revise pass processing them independently via `--only-topic` MUST still confirm
the scenario numbering does not collide: this proposal takes 60 and 61 on the
assumption that both siblings land first.
