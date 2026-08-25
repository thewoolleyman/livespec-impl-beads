# 007 — Post-ratification hardening of the v079 children

A pre-dispatch pass run after v079 landed, while the thread's recorded next
action sat awaiting authorization. Everything here is a read-only measurement or
a ledger record; no lifecycle state was moved and no dispatch was made.

The point of the pass: v079's children will eventually be handed to the factory,
and the two things a dispatch cannot recover from — a poisoned goal render and
mis-shaped acceptance criteria — are both fixable now and unfixable mid-run. The
clause-coverage audit was added because a ratified clause with no owning child is
the exact gap class this program exists to close.

## 1. Dispatchability gate — all children clean

Ran the repo's prescribed template-opener check over the full assembled goal text
(title, description, acceptance criteria, notes, lessons, plus every ledger
comment) for each new child and for every item that received a rider below.

| Item | Result | Goal text |
| --- | --- | --- |
| `bd-ib-ujihbw.1` | clean | 3,554 chars |
| `bd-ib-ujihbw.2` | clean | 4,657 chars |
| `bd-ib-ujihbw.3` | clean | 1,554 chars |
| `bd-ib-ujihbw.4` | clean | 4,174 chars |
| `bd-ib-ujihbw.5` | clean | 2,145 chars |
| `bd-ib-ujihbw.6` | clean | — |
| `bd-ib-mrsply` | clean | 4,311 chars |

The gate was re-run **after** each rider was added, not only before. A comment is
part of the goal render, and a comment is append-only — a poisoned one cannot be
repaired, only escaped by filing a clean successor item.

## 2. Acceptance-criteria shape

The evaluator grades each line as a checkable claim, so a wrapped sentence is
graded as two broken claims. Verified as STORED rather than as drafted:

| Item | Lines | Longest | Blank-line wrapped | Unterminated lines |
| --- | --- | --- | --- | --- |
| `.1` | 6 | 154 | no | 0 |
| `.2` | 11 | 155 | no | 0 |
| `.3` | 6 | 125 | no | 0 |
| `.4` | 9 | 137 | no | 0 |
| `.5` | 11 | 127 | no | 0 |
| `.6` | 7 | 137 | no | 0 |

## 3. Riders added — binding scope that the descriptions do not carry

### `bd-ib-mrsply` — exposure, not merely exclusion

The sharpest finding of the pass. v079 requires that when the rework class is
materialized "the ACCOUNTING MUST EXPOSE it and the snapshot MUST CONSUME THAT
VERDICT", and forbids re-deriving it from the raw label. But `bd-ib-mrsply`'s
fourth criterion only requires that the accounting *classifies* a marked row as
"excluded from the capacity count and not recorded as an abandoned claim".

Classification, exclusion and non-recording are not exposure. An implementation
can satisfy all eight of that item's criteria with

```python
if item.rework_pending:
    continue
```

which excludes the row and writes no abandoned record — and exposes nothing.
`bd-ib-mrsply` would close green while v079's clause stays unimplementable,
because `bd-ib-ujihbw.2` must consume the verdict and may not re-derive it. A
downstream item blocked on a class that was already "delivered" is expensive to
diagnose, which is why the rider went on now rather than at dispatch.

The rider adds the missing criterion: `ActiveClaimAccounting` must expose the
rework rows as their own readable member, alongside the existing
`live_lock_active_ids`, `green_terminal_active_ids` and
`journal_unreadable_active_ids`.

Note the same exclusion-without-exposure shape already exists for rows journaled
no-outcome-since-ledger-admit or terminal-outcome-non-green. That was finding 7
of the v079 review (research/005) and is explicitly NOT in `bd-ib-mrsply`'s
scope; the rider names it only so an implementer recognises the pattern instead
of reproducing it.

### `bd-ib-ujihbw.2` and `.4` — the repo-keyed silent-drop exposure

Both emit ids whose final component is the repository name, and **v079 is the
first contract here to make repo-name-keyed ids normative**, so this exposure is
new and appears in neither item's description. The runtime id validator rejects a
purely decimal component, and the shipped composer drops an invalid id silently —
so a numerically-named checkout loses the fact with no error, which is the
absence-reads-as-resolution direction the machine envelope forbids.

The rider deliberately does NOT add a dependency edge and explicitly forbids a
local workaround: no fallback id, no sanitising the repo name, no catching the
validation failure locally. Each of those re-manufactures the absence that
`bd-ib-r4erae` exists to make loud. `r4erae`'s ratified criteria already cover
the general case, so the remedy is to let it land, not to route around it.

## 4. Clause-coverage audit — one gap, now filed

Every v079 clause was checked against all sixteen children for an owner.

| Clause | Owner |
| --- | --- |
| Capacity single authority; residue fact | `.2` |
| Side-effect-free projection prerequisite | `.1` |
| Accounting's exposed classes; rework ordering | `bd-ib-mrsply` (via rider) |
| Ready-work aging; clock; age-unknowable; in-flight | `.4` |
| Durable ready-dwell instant prerequisite | `.3` |
| Wait completeness; parked-acceptance arity | `.5` |
| `ready_aging_threshold_hours`; API-configurable declaration | `.4` |
| Scenario 83-85 bindings | `bd-ib-w3if5j` |
| **The ownership boundary** | **none — now `.6`** |

The ownership boundary was the only clause no child mentioned: "the orchestrator
MUST NOT read overseer or foreman surfaces, and MUST NOT emit an item whose
derivation required one".

**It is satisfied today, which is exactly why it needed a child.** Grepping the
whole composition — `commands/needs_attention.py` and every
`commands/_needs_attention*.py` — for `overseer` or `foreman` returns zero. The
single package-wide match is a docstring line in `commands/_plan_timeline.py`,
which is the plan lane, is prose rather than a surface read, and is outside the
snapshot composition the clause binds.

A constraint satisfied only by construction is one refactor away from silent
violation with nothing in the suite failing. `bd-ib-ujihbw.6` adds the regression
guard, including the negative control that proves the guard actually fires. The
epic now carries **17** children.

## Still awaiting maintainer decision

Neither of these was self-resolved:

1. Whether the unrescinded stand-down on this repo (`bd-ib-1mjt`,
   2026-08-23T07:33:25Z) binds a track created 2026-08-25. Recorded as an
   authorization tension in a plain comment on `bd-ib-ujihbw`.
2. Authorization to triage `bd-ib-ujihbw.1` through intake and dispatch it.
