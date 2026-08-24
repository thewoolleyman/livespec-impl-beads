# capture-spec-drift

Harness-neutral driving prose for the `capture-spec-drift` operation,
per `SPECIFICATION/constraints.md` §"Skill orchestration constraints":
this artifact is the plugin-owned LLM-facing half of the operation —
the consent flow, the multi-step dialogue, the
`livespec_orchestrator_beads_fabro.*` package calls, and the
cross-boundary propose-change handoff semantics. Each per-runtime
SKILL.md is a THIN binding that resolves the plugin root, reads this
prose in full, and maps its harness-neutral vocabulary (the
"ask the user" / "read the file" verbs, the propose-change operation
handoff) to that runtime's tools. Nothing in this file names a specific
agent runtime's tools or command namespace.

Asymmetric counterpart to `capture-impl-gaps`. Where impl-gap detection
is mechanical, drift detection is heuristic — the implementation may
have evolved beyond what the spec documents, in ways no static
pattern-match can flag. The operation drives an LLM-assisted comparison
between the canonical Specification (via the Spec Reader) and the
working impl tree, surfaces each candidate finding to the user, and
hands the confirmed findings off to the propose-change operation
via the cross-boundary handoff (red-edge handoff 1 per
livespec/SPECIFICATION/contracts.md §"Cross-boundary handoffs").

## Pre-requisites

- A `<spec-root>/` containing ratified spec content at the path
  declared in `.livespec.jsonc` (default: `SPECIFICATION/`).
- The consumer project's impl tree (the rest of the repo besides
  `<spec-root>/`).
- livespec installed and accessible — the propose-change cross-boundary
  handoff requires it.

## Flow

### Step 1 — Load the comparison baseline

Use the Spec Reader to load the current specification:

```python
from livespec_orchestrator_beads_fabro.spec_reader import read_current_specification
from pathlib import Path

snapshot = read_current_specification(spec_root=Path("SPECIFICATION"))
```

The snapshot is the "what the project says it does." The impl tree is
"what the project actually does." Drift is the delta.

### Step 2 — Survey the impl tree

Scan the consumer project's impl tree (excluding `<spec-root>/`,
`.venv/`, `_vendor/`, generated artifacts) for:

- Public API surfaces (function signatures, CLI flag declarations,
  config schema entries, REST/gRPC endpoint definitions, etc.).
- Behavior documented inline in code (docstrings, comments tagged
  `# spec:`, etc.).
- Tests that assert behavior visible to external consumers.

For each candidate, ask:

> Is this behavior reflected in the Specification? (yes / no / partial / skip)

- `yes` — no drift; move on.
- `no` — drift exists; behavior is not in the spec. Proceed to Step 3.
- `partial` — drift exists; spec captures some but not all of the
  behavior. Proceed to Step 3 with a "refinement" framing.
- `skip` — defer judgment.

### Step 3 — Per-finding propose-change handoff

For each `no` / `partial` finding:

1. Draft a one-sentence proposed-change framing the missing behavior.
2. Surface it to the user with the recommended action ("file a propose-change
   targeting `<spec-root>/`?").
3. On consent, invoke the propose-change operation as the cross-boundary
   handoff:

```bash
the propose-change operation --spec-target SPECIFICATION/ --topic <slug> --body <draft>
```

The proposed-change file lands under `<spec-root>/proposed_changes/`
awaiting a subsequent revise pass.

### Targeted mode — `--for-work-item <id>`

Gate 3's forced-drift closure path (`SPECIFICATION/contracts.md`
§"`implement`" → "gap-tied completion") invokes this operation in a
TARGETED mode instead of Step 1-2's whole-tree survey, when a gap-tied
work-item's recorded check file was modified since the baseline blob
hash recorded when it was cited. This mode reuses Step 3's
cross-boundary propose-change handoff; it does NOT duplicate it, and it
does NOT run Step 2's whole-tree survey — a whole-tree heuristic for one
already-known finding is the wrong shape and duplicates effort for a
single, already-mechanically-detected change.

1. Read the work-item's `gap_check_path` metadata (the check file that
   changed) and diff its current content against the recorded baseline
   blob (`git diff <baseline-blob-hash> -- <check-path>`, or an
   equivalent working-tree diff when the baseline blob object is
   unavailable locally).
2. Skip Step 2's whole-tree survey entirely. Present exactly ONE
   candidate to the user, framed from the diff itself: "the check
   `<check-path>` cited by `<item-id>` changed — does the spec clause it
   settles need to change to match?"
3. On consent, run Step 3's propose-change handoff exactly as in the
   whole-tree mode, targeting the spec clause the check settles.
4. On the resulting proposed-change file landing, record its canonical
   topic onto the work-item:

   ```python
   from livespec_orchestrator_beads_fabro.commands._gap_closure import record_drift_propose_change

   record_drift_propose_change(
       config=config,
       item_id=work_item_id,
       propose_change_topic=canonical_topic,
   )
   ```

   so `evaluate_gap_closure` (consumed by `implement`'s gap-tied closure
   step) stops refusing this item's closure on the drift leg.

### Step 4 — Summary

When all candidates are processed, print a summary:

- N impl behaviors surveyed
- M classified as drift, of which K were filed as propose-changes
- S skipped

## Important properties

- **LLM-assisted, user-in-the-loop** — every drift finding requires
  explicit user consent before a propose-change is filed. The operation
  does NOT auto-file.
- **Read-only on the impl tree** — the operation never modifies source
  code. Spec authorship happens through the propose-change operation,
  not here.
- **Spec-side write goes through the cross-boundary handoff** — this
  plugin never writes to `<spec-root>/proposed_changes/` directly. The
  handoff invocation is the surface contract.

## What this operation does NOT do

- Does NOT modify the impl tree.
- Does NOT modify the spec tree directly. Routes through
  the propose-change operation.
- Does NOT detect spec→impl gaps. That's the `capture-impl-gaps`
  operation.
- Does NOT auto-accept findings. User confirms every handoff.
