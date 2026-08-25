# 006 — Child triage readiness, and the discipline that governs it

Written while the thread's recorded next action — factory-dispatch
`bd-ib-ujihbw.1` — sat awaiting maintainer authorization. Everything below is a
read-only measurement or a recorded decision; no lifecycle state was moved.

## Correction to research/005

Research/005 closed by listing two follow-up candidates as "not filed by this
note". They have since been FILED, and that line is superseded:

- **`bd-ib-ohv3`** — Unattended plan resume is defeated by the credential
  wrapper's env scrub.
- **`bd-ib-rfgr`** — A non-convergence backlog bounce reaches no attention
  surface.

Both are freeform items in this repo's own tenant, deliberately NOT children of
this plan epic: neither implements a ratified v079 clause and neither belongs to
the Phase 2 charge. The epic's child count is unchanged at 16.

The second was verified before filing rather than filed on inference.
`commands/_needs_attention_untriaged_backlog.py` filters on `status == backlog
AND not triaged`, and its own docstring states that a backlog item "is admitted
by no dispatch surface and, before this lane, was reported by none either" — so
that lane is the only one composing backlog items. A bounced item was
necessarily triaged before it was ever dispatched, so it carries
`intake:triaged`, the lane filters it out, and nothing else picks it up.

## The triage discipline for this epic's children

**Never bulk-flip the children from `backlog` to `ready`. Triage each item
individually through the actual intake path, as its dependency edges unblock and
its turn comes.**

This is not conservatism for its own sake. All 16 children of this epic — the
eleven the earlier ratifications cut and the five v079 cut — were filed with raw
`bd create`, which does NOT run the intake Definition-of-Ready checklist. None
of them carries `intake:triaged`. A blanket status flip would therefore launder
sixteen items past a gate none has passed, which is precisely the
Definition-of-Ready-bypass pattern tracked as `livespec/livespec-h95t`.

Note the shape of the near-miss, because it is the useful part: the filing route
that produced these items is the same route that would make a bulk flip look
harmless. The items are well-formed — they carry titles, descriptions, and
line-per-assertion acceptance criteria — so nothing about reading one of them
reveals that it never met a gate. Only the absent `intake:triaged` marker does,
and that is an absence, which is the thing this repo's own catalogue warns reads
as nothing at all.

## Definition-of-Ready pre-evaluation: `bd-ib-ujihbw.1`

Measured 2026-08-25 against `contracts.md` §"The four maintainer touchpoints" →
the six intake gates. Recorded so the eventual triage is evidence-backed rather
than re-derived.

| Gate | Verdict | Evidence |
| --- | --- | --- |
| Exactly one coherent "done" | PASSES | One self-contained unit: a read-only projection plus its test. No dedicated `## Scenario`, so it qualifies under the gate's second arm — the standing gates fully define done, gate-verified. Not epic-shaped. |
| Acceptance autonomously verifiable | PASSES | Every criterion is machine-checkable: the journal is byte-identical across two calls, the classification matches the existing entry point, a test fails if the projection is swapped for the mutating one. No human judgement call. |
| Autonomy tier assigned | PASSES | Not a spec change — v079 is already ratified — so it is implementation and factory-dispatchable. `factory_safety` is absent from the record, which under the store's `omitempty` convention means null, i.e. factory-safe. |
| Dependencies linked | PASSES | Zero blockers. See the measurement note below. |
| Repo target named | PASSES | One slice, one ledger: this repository's own `.claude-plugin/scripts/`. |
| Above the size floor | **HUMAN JUDGEMENT** | The contract states the floor "is human judgement until slice-size calibration yields a value". This gate is not autonomously decidable. |

**Five of six gates pass mechanically; the sixth is by contract a human call.**
That is worth stating plainly, because it means a complete Definition-of-Ready
evaluation of this item cannot be finished without the maintainer — the gate the
routing depends on is the one the specification declines to automate.

### The dependency measurement, and the trap it walks into

`bd-ib-ujihbw.1` reports `dependency_count: 1`, and a reader who stops there
concludes the item is blocked. It is not. Its single dependency row is:

```
{'depends_on_id': 'bd-ib-ujihbw', 'type': 'parent-child'}
```

One row, and it is the `parent-child` edge to the plan epic — not a blocker.
`.1` carries no `blocks` edge at all, which is exactly why it is the unblocked
prerequisite gating `.2`. This is the heterogeneous-`dependencies`-array trap
this repo already catalogues, met in the wild: the array mixes six edge types
and the majority of rows fleet-wide are not blockers, so a count is not a
blocker count.

### Where a passing item actually lands

Not in `ready`. The contract routes a Definition-of-Ready-passing item to
`pending-approval` first, and `.livespec.jsonc` sets
`dispatcher.auto_approve_ready: true`, so the effective `admission_policy` is
`auto` and the item is approved on into `ready` with no human step. The full
transition for `.1` is therefore:

```
backlog -> pending-approval -> (auto-approve) -> ready -> dispatch
```

A direct `backlog -> ready` move is not the sanctioned path and would skip the
routing the checklist exists to perform.

## What remains owed

- The release plan for the ratified v071-v079 surface, owed to homelab's
  steady-state-loop-hardening session once the first implementation children
  merge. None have merged, so it is not yet due.
- The remaining fifteen children triage per item as their edges unblock, never
  as a batch.

## Release identity for the ratified v071-v079 surface

Measured 2026-08-25, and it settles the release plan owed to homelab's
steady-state-loop-hardening session. Recorded here because it corrects a
mis-pin risk that would otherwise be discovered only by a consumer missing a
whole section.

**The spec surface and the implementation surface release separately.** The
obligation was framed as owed "when the first children merge", but the ratified
SPEC is already fully released; the children's IMPLEMENTATION will land in later
tags. Homelab can pin and consume the Phase 2 spec surface today without waiting
for a single child.

**The pin is `v0.72.10`.** Each version's history snapshot was located by the
commit that introduced it, then `git tag --contains` was run against that commit
— the instrument this repo's own Rule 1 prescribes for "was this released", and
one with no wrong-answer failure mode:

| Spec version | First release tag containing it |
| --- | --- |
| v071 | v0.72.2 |
| v072 | v0.72.3 |
| v073 | v0.72.4 |
| v074 | v0.72.5 |
| v075 | v0.72.6 |
| v076 | v0.72.7 |
| v077 | v0.72.8 |
| v078 | v0.72.9 |
| v079 | **v0.72.10** |

Every tag carries a PREFIX of the arc, never the whole of it. `v0.72.10` is the
first and only tag containing all nine. It is a real published release, neither
draft nor prerelease, published 2026-08-25T15:56:07Z.

### The mis-pin this prevents

Homelab has recorded that `v0.72.4`-`v0.72.9` exist as spec-carrying releases.
That is true, and every one of those tags does carry spec — which is exactly what
makes it dangerous. `v0.72.9` carries v071 through v078 and **not** v079, so a
consumer pinning it as "the Phase 2 surface" silently loses the entire
`### Orchestrator-owned attention facts` section: all three fact families and
Scenarios 83-85. Nothing in that release announces that it is partial.

Confirmed by CONTENT rather than by tag arithmetic, because a tag list is not a
content check:

```
git show v0.72.10:SPECIFICATION/contracts.md | grep -c '^### Orchestrator-owned attention facts$'   -> 1
git show v0.72.9:SPECIFICATION/contracts.md  | grep -c '^### Orchestrator-owned attention facts$'   -> 0
```

### What consumption evidence should pin

TWO identities, not one:

1. **The spec surface** — `v0.72.10` or later. Available now.
2. **The implementation surface** — a later tag, cut by release-please once the
   implementation children merge. Does not yet exist.

Grading consumption against a single identity conflates them, and the spec
identity is the one available today.
