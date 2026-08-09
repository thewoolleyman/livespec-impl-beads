---
topic: planning-lane-realization-core-v197-v198
author: claude-fable-5
created_at: 2026-08-09T00:00:00Z
---

## Proposal: Realize livespec core v197/v198 Planning Lane redesign

### Target specification files

- SPECIFICATION/README.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

Update this orchestrator's Planning Lane realization to conform to
livespec core v197/v198: a plan has a slim write-once git store
(`plan/<slug>/research/` plus exactly one write-once epic anchor), while
mutable handoff persistence moves to append-only, per-entry, attributed,
timestamped plan-epic ledger comments. A scoping event must cut known
requirements from research prose into requirement-carrier children before
the plan epic takes implementation children. Archive requires both no
undisposed children and an independent adversarial completeness review
that attests every requirement, including deferred requirements, has a
ledger carrier.

The revision also performs the vocabulary migration from "plan thread" to
"plan" in live spec prose, including the thin-transport primitive rename
from `list-plan-threads` to `list-plans`.

### Motivation

livespec core v197 redesigned the Planning Lane around ledger-held
planning state after the planning-lane redesign records in repo
`thewoolleyman/livespec`, especially
`plan/archive/planning-lane-redesign/research/maintainer-rulings.md`,
`brainstorm.md`, and `bd-long-prose-spike.md`. Core v198 restored the
explicit no-shadow-ledger statement in the same Planning Lane guidance.
This repository currently still realizes the older design: live
`handoff.md`, optional `supervisor-handoff.md`, plan-thread vocabulary,
and a `list-plan-threads` thin-transport surface. That is now
specification drift against the core contract this reference
orchestrator is expected to dogfood.

### Proposed Changes

Apply this as a proposal only. Ratification is explicitly out of scope
for this slice. The later revise payload MUST re-derive all target text
from the then-current `origin/master`; the line references below identify
the current drift sites on this branch, not immutable patch anchors.

**A. Skill inventory and README vocabulary.** In `SPECIFICATION/README.md`
§"Required content", replace the thin-transport inventory entry
`list-plan-threads` with `list-plans`. The inventory should continue to
say there are four thin-transport skills unless ratification has changed
that count for another reason.

**B. Thin-transport skill name and contract.** In
`SPECIFICATION/contracts.md` under §"Thin-transport skills", rename the
H4 subsection `#### list-plan-threads` to `#### list-plans` (currently
near line 389). Rename the CLI surface from
`list-plan-threads [--json] [--project-root <path>]` to
`list-plans [--json] [--project-root <path>]`. The operation MUST emit
the complete set of open, unarchived plans, not "plan threads".

The renamed contract MUST keep the read-only directory-enumeration
discipline: exactly one entry per direct child directory of `plan/`
except `plan/archive/`, in ascending lexicographic slug order; no ledger
consultation; no file-content scan; no mutation; missing or empty `plan/`
yields an empty result with exit 0. Its JSON shape SHOULD become
`{"plans": ["alpha-topic", "beta-topic"]}` so the schema vocabulary
matches the operation name. Any backwards-compatibility alias for the old
command is implementation policy and MUST NOT keep old vocabulary in
normative spec prose after this revision.

**C. Planning Lane realization store model.** In
`SPECIFICATION/contracts.md` §"Planning Lane realization", replace
`plan/<topic>/` / "thread store" prose with `plan/<slug>/` / "plan
store" prose. The plan store MUST contain only write-once research inputs
under `plan/<slug>/research/` and exactly one write-once metadata anchor
written at plan open. The anchor names the ledger epic id and MUST NOT be
updated to mirror children, statuses, handoffs, readiness, or archive
state. The ratified text MUST state that plans created after ratification
do not create live `handoff.md`, `supervisor-handoff.md`, mutable status
files, or any other mutable planning-state document in git.

Migration of pre-existing live `handoff.md` content MUST preserve it as
write-once historical evidence under `plan/<slug>/research/` and MUST NOT
delete it from the git tip. If migration relocates any plan path, the
same change or an explicitly linked work-item MUST update every
fleet-spec design-record citation naming the pre-relocation path.

**D. Ledger-held handoff persistence.** Replace the current
`plan/<topic>/handoff.md` self-sufficiency model with ledger-held handoff
entries. Handoff persistence MUST be append-only, per-entry,
individually attributed, and timestamped. In this Beads/Dolt reference
realization, those entries are comments on the plan epic, using the
ledger's comment/timeline read path as the authoritative resume source.
Each entry carries only non-derivable content such as rationale,
warnings, abandoned attempts, and pointers. Derivable state, including
children, statuses, PR state, merge state, and readiness, is queried
fresh from the ledger and git at resume time.

The no-shadow-ledger statement from core v198 MUST be realized in this
section: checklist items in planning artifacts are session-local steps or
pointers to real ledger ids, never a parallel work queue that shadows the
ledger.

**E. Scoping event before implementation children.** Add the scoping
contract to `SPECIFICATION/contracts.md` §"Planning Lane realization":
before a plan epic takes implementation children, a scoping event MUST
cut every known requirement from research prose into requirement-carrier
children under the epic, including deliberately deferred requirements.
A requirement MUST NOT exist only in prose after that point. Deferral is
ledger state on the requirement-carrier child: an explicit `deferred`
disposition where supported, otherwise a sanctioned label/state applied
only through the admission valve, never hand-edited.

**F. Two seams.** Replace the current read-only "prompt -> ledger" seam
description with the core v197 seam model. The plan surface appends and
reads plan-epic ledger handoff entries, reads ledger children to resume
work, and routes ripe work through the orchestrator's sanctioned
capture/admission surfaces. It MUST NOT write directly to
orchestrator-private storage outside those ledger-entry and
capture/admission surfaces.

**G. Two-leg archive gate and total archival.** Rework
`SPECIFICATION/contracts.md` §"Archive on epic close" so archive requires
both legs: no undisposed children, and an independent adversarial
completeness review of the research prose against the epic's children
attesting every requirement, including deferred requirements, has a carrier. A
`plan/<slug>/` record is active if and only if its ledger epic is open.

Keep the total-archival invariant in plan vocabulary: archival relocates
the whole `plan/<slug>/` record to `plan/archive/<slug>/` with no live
path residue, and no committed tree may contain the same slug at both
paths. Closing with something unresolved still has only two sanctioned
dispositions: leave the epic open and the plan unarchived, or transfer
all blockers to another non-archived plan or work-item before archival.

**H. Cross-references and query-only lists.** Replace every live spec
cross-reference to `list-plan-threads` with `list-plans`, including:

- `SPECIFICATION/contracts.md` §"`next`" scope asymmetry, where the
  read/awareness surface composes human-valve lanes via `list-work-items`
  and plans via `list-plans`.
- `SPECIFICATION/contracts.md` §"Out-of-scope surfaces", where the
  query-only thin-transport set names `list-plans`.
- `SPECIFICATION/constraints.md` §"Skill orchestration constraints",
  where the zero-orchestration thin-transport set names `list-plans`.

**I. Scenario 41 rename and content.** In `SPECIFICATION/scenarios.md`,
rename H2 `## Scenario 41 — standalone analysis lands in a plan thread,
not a root research tree` (currently near line 919) to plan vocabulary.
The revised scenario MUST say standalone analysis lands in the plan
store, normally as write-once research under `plan/<slug>/research/`, and
no root `research/` path is created. It MUST NOT teach live
`handoff.md`, supervisor handoff files, or mutable plan-state files as
valid plan-store contents.

**J. Scenario 42 rename and content.** In `SPECIFICATION/scenarios.md`,
rename H2 `## Scenario 42 — list-plan-threads enumerates unarchived plan
threads` (currently near line 934) to
`## Scenario 42 — list-plans enumerates unarchived plans`. Rename the
Feature and When lines to `list-plans`. The JSON assertion SHOULD become
`plans is exactly ["alpha-topic", "beta-topic"]`. The scenario MUST keep
the unarchived-visible / archived-invisible split, lexicographic order,
missing-plan zero result, and read-only guarantee.

**K. Heading-coverage co-edit.** Because items I and J rename two H2
headings, the ratifying revise payload MUST include
`tests/heading-coverage.json` in the same `resulting_files[]` set. The
entries for Scenario 41 and Scenario 42 MUST be re-derived from the
ratified headings. Any `TODO` entry for Scenario 41 or Scenario 42 MUST
carry a reason that names this proposal, names the implementation
follow-up, and explicitly acknowledges the integration tier using one of
the literal tier keywords `tier`, `integration`, `e2e`, `consumer`, or
`pyramid`; alternatively, map the heading to a test id under an
integration-tier prefix such as `tests.integration`. Scenario 42 MUST NOT
keep a stale test id that still names `list_plan_threads` unless the
implementation test has already been renamed or an alias test explicitly
covers the new `list-plans` contract.

**L. Vocabulary sweep.** Re-enumerate the live spec vocabulary sweep at
ratification time with a search equivalent to:

```bash
grep -RIn "plan-thread\\|plan thread\\|planning thread\\|plan threads\\|list-plan-threads\\|plan/<topic>/handoff.md\\|plan/<topic>/supervisor-handoff.md" SPECIFICATION/*.md
```

As of this proposal's branch, the live-spec sweep includes at least these
drift sites and their nearby sections:

- `SPECIFICATION/README.md` Required content: thin-transport inventory.
- `SPECIFICATION/constraints.md` Skill orchestration constraints:
  zero-orchestration thin-transport set.
- `SPECIFICATION/contracts.md` top-level skill surface summary: Planning
  Lane references to thread store, handoff self-sufficiency, and
  archive-on-close.
- `SPECIFICATION/contracts.md` `#### list-plan-threads`: heading, CLI
  surface, prose, JSON key, and human-output derivation.
- `SPECIFICATION/contracts.md` §"`next`": awareness composition via
  `list-plan-threads`.
- `SPECIFICATION/contracts.md` §"Out-of-scope surfaces": query-only
  thin-transport set.
- `SPECIFICATION/contracts.md` §"Planning Lane realization": front-end
  create/resume language, `plan/<topic>/` store definition,
  `handoff.md`, `supervisor-handoff.md`, seams, self-sufficiency gate,
  archive-on-close, unresolved-close dispositions, and restraint budget.
- `SPECIFICATION/scenarios.md` Scenario 41 H2 and scenario body.
- `SPECIFICATION/scenarios.md` Scenario 42 H2, Feature, Given, When,
  Then, JSON key, and missing-plan wording.

Frozen `SPECIFICATION/history/` content is not rewritten by this
proposal. Live prose may quote old terms only as exact replacement
targets inside this proposal or its revision rationale.

**M. Implementation follow-ups.** Ratifying this proposal creates
implementation work for the reference orchestrator: rename or alias the
thin-transport command surface to `list-plans`, update wrapper scripts
and bindings, migrate plan creation away from live git handoff files,
append/read plan-epic ledger comments for handoffs, enforce the scoping
event before implementation children, enforce the two-leg archive gate,
and migrate any live plan records. Those implementation items MUST be
filed through the work-item ledger after ratification. They are not part
of this proposal-authoring slice.
