# capture-work-item

Harness-neutral driving prose for the `capture-work-item` operation,
per `SPECIFICATION/constraints.md` §"Skill orchestration constraints":
this artifact is the plugin-owned LLM-facing half of the operation —
the consent flow, the multi-step dialogue, the
`livespec_orchestrator_beads_fabro.*` package calls, and the JSON /
handoff semantics. Each per-runtime SKILL.md is a THIN binding that
resolves the plugin root, reads this prose in full, and maps its
harness-neutral vocabulary (the `<plugin-root>` token, the
"ask the user" / "read the file" / "write the file" verbs, the named
sibling operations) to that runtime's tools. Nothing in this file
names a specific agent runtime's tools or command namespace.

The freeform direct-filing operation. Use this for bugs, refactors,
tactical tasks, and anything else that doesn't trace back to a spec
rule. For spec-traceable items, use the `capture-impl-gaps` operation
instead.

## Pre-requisites

- The work-items store (the resolved beads tenant connection) is
  reachable.
- `livespec_orchestrator_beads_fabro` package on import path.

## Flow

### Step 1 — Gather inputs

Ask the user (one question at a time):

1. **Title** — one-line summary.
2. **Description** — multi-line free-form (markdown permitted).
3. **Type** — one of `bug`, `feature`, `task`, `chore`, `epic`.
Optional follow-ups (skip-confirmable):

- **Acceptance criteria** — the gradeable assertions the item is judged
  against; string or null (default null). Author them to the rules in
  "Writing acceptance criteria" below BEFORE filing.
- **Assignee** — string or null (default null).
- **Depends-on** — comma-separated work-item ids (the tenant's
  configured `<prefix>-XXXXXX` form); empty list permitted.
- **Plan parent** — when the caller is filing this as a child of a
  plan epic, the plan epic id; otherwise null. This is distinct from
  `depends_on`: plan-child linkage is a beads parent-child relation, not
  a blocker edge.
- **Spec-commitment-hint** — string `id_hint` or null (default null).
  Supplied via `--spec-commitment-hint <id_hint>` when the work-item
  is being filed in response to a spec-side
  `spec_commitments.impl_followups[].id_hint` declaration (per livespec
  `SPECIFICATION/contracts.md` §"Implementation-plugin contract — the
  10-skill surface" → "Work-item `spec_commitment_hint` field"). When
  supplied, the resulting record's `spec_commitment_hint` MUST equal
  the verbatim `id_hint`; when omitted, the field defaults to `null`
  (the freeform case). This is the surface livespec's
  `unresolved-spec-commitment` doctor invariant queries via
  `list-work-items --json` to verify each declared spec→impl
  commitment maps to a filed work-item.

#### Writing acceptance criteria

The acceptance pass grades the criteria field one gradeable ASSERTION at a
time, as standalone claims. `criteria_lines` segments the field by CONTENT,
never by line width: only a blank line, a list marker, or a header starts a
block, and each block is then split into sentences. A flush-left line with
no marker CONTINUES the block above it. Filers MUST therefore write **one
bulleted assertion per criterion, ending in a period**:

- **One `- ` bullet per assertion, each a complete sentence with a
  terminal period.** The marker starts the block and the period ends the
  sentence, so the assertion is graded on its own however the text is
  later reflowed. Plain flush-left lines with no marker and no period
  collapse into ONE assertion (measured 2026-08-31: nine such lines
  parsed as one; the same nine as bullets parsed as nine).
- **Wrapping is safe inside a bullet.** A continuation line, indented or
  not, joins the sentence it belongs to; what must not happen is two
  assertions sharing one sentence.
- **Keep rationale, provenance and explanation out of the field.** They
  belong in the description or a ledger comment; in the criteria field
  they become sentences that are graded as assertions.
- **No negative criteria.** The judge passes a criterion on literal
  merged-diff vocabulary, and "no file contains X" has none to offer.

Apply this AT FILING TIME. Acceptance grades the criteria SNAPSHOT taken
at dispatch time, not the live ledger row, so a post-dispatch reflow of
the criteria is inert against the run already in flight: rewriting the
field after dispatch cannot rescue that dispatch, and the failure only
surfaces after the work has merged. Filing conforming criteria here is
the whole mitigation.

### Step 2 — Confirm and file

Show the user the assembled record and ask "file?". On `yes`, append:

```python
from livespec_orchestrator_beads_fabro._ids import new_work_item_id
from livespec_orchestrator_beads_fabro._beads_client import EDGE_PARENT_CHILD, make_beads_client
from livespec_orchestrator_beads_fabro.commands._config import resolve_store_config
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import WorkItem
from livespec_runtime.work_items.rank import key_between
from datetime import datetime, timezone
from pathlib import Path

config = resolve_store_config(cwd=Path.cwd(), work_items_arg=None)
rank = key_between(a=None, b=None)
item = WorkItem(
    # The id-prefix is the tenant's server-stored bd create-prefix
    # (config.prefix), DECOUPLED from the tenant DB name — so the id
    # carries config.prefix, not a hardcoded `li-`.
    id=new_work_item_id(prefix=config.prefix),
    type=type_,
    status="backlog",
    title=title,
    description=description,
    origin="freeform",
    gap_id=None,
    rank=rank,
    assignee=assignee,
    depends_on=tuple(depends_on),
    captured_at=datetime.now(tz=timezone.utc).isoformat(),
    resolution=None,
    reason=None,
    audit=None,
    superseded_by=None,
    spec_commitment_hint=spec_commitment_hint,  # str | None; None for freeform.
    # One `- ` bullet per assertion, each ending in a period, per "Writing acceptance criteria".
    acceptance_criteria=acceptance_criteria,  # str | None; None when unsupplied.
)
append_work_item(path=config, item=item)
if plan_parent_id is not None:
    make_beads_client(config=config).add_dependency(
        from_id=item.id,
        to_id=plan_parent_id,
        edge_type=EDGE_PARENT_CHILD,
    )
```

Print the assigned id back to the user.

Then resolve and DISPLAY the item's effective-criteria parse, through the one
public primitive every gate uses — never by re-reading the criteria field or
the description by hand
(`SPECIFICATION/contracts.md` §"Effective acceptance criteria"):

```python
from livespec_orchestrator_beads_fabro.commands._dispatcher_effective_criteria import (
    effective_criteria,
)

criteria_advice = effective_criteria(item=item).parse_display()
```

Show the user `criteria_advice` — it names the gradeable-assertion count and
the resolved source (`criteria-field` or `description-exit-criteria`). This is
ADVICE, never a refusal: capture MUST NOT refuse on an empty parse, because
filing stays consent-gated and criteria may legitimately arrive at groom time.
Say plainly what an empty parse costs, though: an item whose effective
`acceptance_policy` is `ai-only` or `ai-then-human` and whose effective
criteria parse to zero gradeable assertions is refused entry to `ready` by the
`approve` valve, and refused at dispatch with exit code `5` — the remedy is to
author criteria (here, or later via groom or edit), or to set the item's
`acceptance_policy` to `human-only` where machine grading is genuinely
inapplicable.

### Step 3 — Run the intake Definition-of-Ready checklist

Every capture front-end MUST run the intake Definition-of-Ready
checklist at capture and route the filed item into its lifecycle state
(SPECIFICATION/scenarios.md "Scenario 8 — Intake Definition-of-Ready
triage"; contracts.md §"Gap-detectable behavior clauses"). The gate
logic is the ONE shared `livespec_orchestrator_beads_fabro.intake_dor`
primitive — never re-derive the gates in prose here.

Resolve the six gates from the inputs you already gathered plus a short
confirmation dialogue (one question at a time; many gates are already
answerable from Step 1):

- `single_coherent_done` — does the item describe exactly ONE coherent
  "done"? (more than one means an epic routed to `backlog`)
- `autonomously_verifiable` — can the acceptance be checked WITHOUT a
  human judgement call?
- `autonomy_tiered` — does the item carry an explicit autonomy tier?
- `dependency_linked` — are its blockers linked (the `depends_on` set),
  or does it genuinely have none?
- `repo_targeted` — does it name the repo it lands in?
- `above_floor` — is it above the size floor (worth a discrete
  dispatch)?

Then route the just-filed item:

```python
from livespec_orchestrator_beads_fabro.intake_dor import (
    DefinitionOfReadyChecklist,
    apply_intake_dor,
)

verdict = apply_intake_dor(
    path=config,
    item_id=item.id,
    checklist=DefinitionOfReadyChecklist(
        single_coherent_done=single_coherent_done,
        autonomously_verifiable=autonomously_verifiable,
        autonomy_tiered=autonomy_tiered,
        dependency_linked=dependency_linked,
        repo_targeted=repo_targeted,
        above_floor=above_floor,
    ),
)
# verdict is one of "pending-approval" / "ready" / "backlog" / "blocked".
```

Narrate the verdict to the user:

- `pending-approval` — DoR-passing and waiting for the admission valve.
- `ready` — DoR-passing and approved onward because the effective
  `admission_policy` is `auto` and no dependency edge blocks dispatch.
- `backlog` — epic-shaped and waiting for decomposition.
- `blocked` — not autonomously verifiable or missing a dispatch facet;
  carries `blocked_reason: needs-human` and MUST NOT be filed `ready`.

If the item has unresolved blockers, make sure the dependency edges are
linked in `depends_on`; linked blockers derive the dependency lane and
MUST NOT be bypassed by direct `ready` routing.

If the item is part of a plan thread, make sure the plan epic is linked
through `plan_parent_id` / `parent_id`, not `depends_on`. Task children
cannot block epics on the live beads server, and the plan archive gate
enumerates parent-child children when refusing archive for undisposed
work.

## Important properties

- **`origin: freeform`** — never `gap-tied`. Use the `capture-impl-gaps`
  operation for gap-traceable items.
- **`gap_id: null`** — REQUIRED. The schema check fires on any
  non-null value combined with `origin: freeform`.
- **Closure path** — closed via the `implement` operation's freeform
  fix path (a user-supplied `--reason` with no re-detection step).

## What this operation does NOT do

- Does NOT close work-items. Use the `implement` operation.
- Does NOT detect gaps. Use the `capture-impl-gaps` operation.
- Does NOT auto-set `assignee` or `depends_on`. User supplies both.
