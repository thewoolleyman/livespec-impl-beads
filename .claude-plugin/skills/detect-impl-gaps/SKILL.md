---
name: detect-impl-gaps
description: Enumerate the ratified spec's MUST/SHOULD clauses mechanically via the Spec Reader and emit the current gap-id set as JSON. This is a spec-clause enumerator, not a spec→impl comparator — it never reads implementation state, so a returned gap-id means the clause is not yet tracked by a work-item, never that it is missing from the implementation. Required thin-transport surface per livespec/SPECIFICATION/contracts.md. Pure read-and-emit pass-through — never mutates the work-items store, never prompts the user. Invoke as `/livespec-orchestrator-beads-fabro:detect-impl-gaps [--spec-target <path>] [--project-root <path>] [--json] [--since-version <vN>]`.
allowed-tools: Bash
---

# detect-impl-gaps

Thin-transport pass-through. All behavior lives in
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/detect_impl_gaps.py`.

## Invocation

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/detect_impl_gaps.py" "$@"
```

Supported flags:

- `--spec-target <path>` — path to the spec tree (default:
  `SPECIFICATION/` under `--project-root`).
- `--project-root <path>` — project root (default: current working
  directory).
- `--json` — emit `{"gap_ids": [...]}` JSON instead of
  human-readable lines.
- `--since-version <vN>` (optional, default unset) — restrict the
  scan to spec files whose content differs between the historical
  version `<vN>` and the live spec. Accepts either `v<N>` (e.g.
  `v082`) or a bare positive integer (e.g. `82`). For each such
  file, only MUST / SHOULD clauses present in the LIVE version are
  surfaced — clauses removed by the diff are not gaps (they were
  spec content that no longer exists). When omitted, the skill
  scans every file in the live spec (pre-flag behavior, unchanged).

Validation of `--since-version`:

- The value MUST resolve to a positive integer. Non-integer or
  non-positive input exits `2` with a usage error written to
  stderr.
- The version directory `<spec-root>/history/v<padded-N>/` MUST
  exist. Missing version exits `3` with a
  `SpecVersionNotFoundError` message naming the expected path.
- When `<vN>` equals the live spec's latest cut version AND the
  live tree matches that snapshot byte-for-byte, the diff is empty
  and the skill emits an empty gap-id set.

## When to use

- Doctor's `gap-tracking-one-to-one` and `no-stale-gap-tied`
  invariants subprocess `detect-impl-gaps --json` to enumerate the
  current gap-id set against the work-items JSONL store.
- The heavyweight `capture-impl-gaps` sibling invokes
  `detect-impl-gaps --json` as its detection step before walking
  the user through per-gap consent.
- The heavyweight `implement` skill does NOT invoke this skill at
  gap-tied closure. Per `prose/implement.md` Step 5a, closure is
  anchored to the CHECK PATH recorded on the work-item's own metadata
  (`gap_check_path`) — an executable check that must pass and whose
  `--negative-control` arm must fail — and never to `gap_id`, which
  hashes a hard-wrapped source line and re-keys on reflow, so it cannot
  anchor a closure that must survive the clause being reworded.

## Properties

- **Non-mutating.** No JSONL writes, no spec modifications, no
  user prompts.
- **Pure function of spec state.** Same spec text yields the same
  gap-id set; gap-id derivation hashes
  `<spec-file>\x1f<heading-path>\x1f<rule-text>`.
- **Excludes `proposed_changes/`** via the Spec Reader's exclusion
  contract — only ratified canonical content surfaces.
- **No LLM in the detection path.** Pattern-matching of
  MUST / MUST NOT / SHOULD / SHOULD NOT keywords (uppercase only)
  outside fenced code blocks is deterministic.
