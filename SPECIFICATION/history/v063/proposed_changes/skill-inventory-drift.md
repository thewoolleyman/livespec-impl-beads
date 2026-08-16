---
topic: skill-inventory-drift
author: claude-fable-5-bootstrap-pi-driver-orch
created_at: 2026-08-16T01:09:10Z
---

## Proposal: Repair the skill-surface inventory drift: derive the inventory, stop restating counts, and specify needs-attention

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/README.md
- SPECIFICATION/constraints.md

### Summary

The shipped Claude skill set has twelve operations, but contracts.md §"The skill surface" enumerates a six + one + four inventory that omits the shipped needs-attention skill, and the counts are repeated in three ### headings, the consent-discipline paragraph, SPECIFICATION/README.md, and the repo README. This change makes the inventory DERIVED (the operations shipped under .claude-plugin/skills/, classed by the chapter's class sections), drops every restated count, and adds the missing needs-attention thin-transport subsection with its CLI surface and its peers-with-drive semantics. No H2 heading changes.

### Motivation

Pre-existing drift noted (and deliberately not inherited) by the pi-skill-surface proposal ratified as v062: its pi mapping derives one pi skill per Claude binding under .claude-plugin/skills/ — twelve today — while this section's restated totals say eleven and never mention needs-attention, which shipped as a first-class read/awareness surface (peers with drive, coupled only by the action-id grammar, per the Operator-skill section). The repo README further claims a ten-skill surface citing a livespec-core section name that no longer exists. Tracked as bd-ib-4twg; part of the bootstrap-pi-driver plan (repo livespec epic livespec-g5h5ff). The repair follows the clause-lockstep discipline: delete counts a reader can re-derive from the enumeration or the shipped tree, so the inventory cannot silently fall out of lockstep again.

### Proposed Changes

Edits across three spec files; every replace-target exists verbatim and exactly once in its live file. Three edits retitle `###` headings and one inserts a `####` subsection — no `## ` H2 is added, changed, or removed, and this repo's tests/heading-coverage.json keys off `## ` headings only, so NO heading-coverage co-edit is required.

**Edit 1 — `SPECIFICATION/contracts.md`, three heading retitles (counts dropped).** Replace `### Heavyweight authored skills (6)` with `### Heavyweight authored skills`; replace `### Operator skill (1)` with `### Operator skill`; replace `### Thin-transport skills (4)` with `### Thin-transport skills`. A count in a heading is a hand-maintained projection over the section's own content — exactly the projection that drifted when `needs-attention` shipped.

**Edit 2 — `SPECIFICATION/contracts.md`, the authoritative-inventory sentence.** Replace exactly:

```
The six heavyweight ops are
`capture-impl-gaps`, `capture-spec-drift`, `capture-work-item`,
`implement`, `groom`, and `plan` — this enumeration (six heavyweight +
one operator + four thin-transport) is the ONE authoritative skill
inventory; other sections and files reference it rather than restating
counts.
```

with:

```
The heavyweight ops are
`capture-impl-gaps`, `capture-spec-drift`, `capture-work-item`,
`implement`, `groom`, and `plan`. The authoritative skill inventory is
the set of operations shipped under `.claude-plugin/skills/`, each
classed by one of this chapter's three class sections; other sections
and files reference the classes and the shipped set rather than
restating counts or totals.
```

**Edit 3 — `SPECIFICATION/contracts.md`, the consent-discipline count.** Replace exactly:

```
dialogue is orchestrator-owned: this plugin's six heavyweight
front-ends —
```

with:

```
dialogue is orchestrator-owned: this plugin's heavyweight
front-ends —
```

(The six-name enumeration immediately after it is unchanged and remains the definition of the governed set.)

**Edit 4 — `SPECIFICATION/contracts.md`, new `#### needs-attention` subsection.** At the end of the thin-transport section, replace exactly:

```
pass-through over the Spec Reader's output and the gap-rule enumeration.

## pi skill surface
```

with:

```
pass-through over the Spec Reader's output and the gap-rule enumeration.

#### `needs-attention`

CLI surface: `needs-attention [--project-root <path>] [--repo-name <name>] [--work-items-path <path>] [--json]`.

The read/awareness surface: it composes the spec, implementation,
human-valve, plan, and hygiene gather primitives into an operator
attention list — Markdown by default for operator reading, `--json` for
the machine envelope — as a thin pass-through over
`.claude-plugin/scripts/bin/needs_attention.py` and the shared
`commands/needs_attention.py` implementation. Its operator semantics
are the peer contract stated under §"Operator skill": `needs-attention`
and `drive` are peers coupled ONLY by the shared action-id grammar —
`needs-attention` composes and emits action-ids, executes nothing, and
creates no work-items.

## pi skill surface
```

**Edit 5 — `SPECIFICATION/README.md`, the required-documentation bullet.** Replace exactly:

```
- The plugin's skill surface (six heavyweight authored skills:
  capture-impl-gaps, capture-spec-drift, capture-work-item, implement,
  groom, plan;
  one operator skill: drive; four thin-transport skills:
  detect-impl-gaps, list-plans, list-work-items, next — per `contracts.md`
  §"The skill surface")
```

with:

```
- The plugin's skill surface (heavyweight authored skills:
  capture-impl-gaps, capture-spec-drift, capture-work-item, implement,
  groom, plan;
  the operator skill: drive; thin-transport skills:
  detect-impl-gaps, list-plans, list-work-items, needs-attention, next —
  per `contracts.md` §"The skill surface")
```

**Edit 6 — `SPECIFICATION/contracts.md`, three dangling §-citations of the retitled heading.** Edit 1 retitles `### Heavyweight authored skills (6)` to `### Heavyweight authored skills`; three existing citations of the old title become dangling unless rewritten in the same change.

6a. Replace exactly:

```
bindings read (per §"Heavyweight authored skills (6)").
```

with:

```
bindings read (per §"Heavyweight authored skills").
```

6b. Replace exactly:

```
authored skill (per §"Heavyweight authored skills (6)"), so
```

with:

```
authored skill (per §"Heavyweight authored skills"), so
```

6c. Replace exactly (the citation wraps across two lines in the live file):

```
`plan` is the SIXTH heavyweight authored skill (§"Heavyweight authored
skills (6)"), so its orchestration follows the same shared
```

with:

```
`plan` is the SIXTH heavyweight authored skill (§"Heavyweight authored
skills"), so its orchestration follows the same shared
```

**Edit 7 — `SPECIFICATION/contracts.md`, §"Out-of-scope surfaces" thin-transport enumeration.** `needs-attention` is genuinely query-only (verified: its implementation reads only from the work-items store and writes nothing but stdout) and belongs inside this consent-exemption clause, not outside it. Replace exactly:

```
The four thin-transport skills (`list-work-items`, `next`,
`detect-impl-gaps`, `list-plans`) are query-only by contract (per
`constraints.md` §"Forbidden patterns") and never write to the
store; the consent discipline does not apply to them.
```

with:

```
The thin-transport skills (`list-work-items`, `next`,
`detect-impl-gaps`, `list-plans`, `needs-attention`) are query-only by
contract (per `constraints.md` §"Forbidden patterns") and never write to the
store; the consent discipline does not apply to them.
```

**Edit 8 — `SPECIFICATION/constraints.md`, the thin-transport zero-orchestration bullet.** Replace exactly:

```
- Thin-transport skills (list-work-items, next, detect-impl-gaps,
  list-plans) carry ZERO orchestration in SKILL.md beyond a
  one-line invocation of the wrapper script. All logic lives in
```

with:

```
- Thin-transport skills (list-work-items, next, detect-impl-gaps,
  list-plans, needs-attention) carry ZERO orchestration in SKILL.md beyond a
  one-line invocation of the wrapper script. All logic lives in
```

**Ratification ride-alongs (same PR, outside resulting_files), in the repo-root README.md:** line 8's citation of livespec core's section "Implementation-plugin contract — the 10-skill surface" and the matching See-also entry near the bottom cite a core spec section that NO LONGER EXISTS under that name (verified against livespec origin/master 2026-08-16) — rewrite both to cite this repo's own `SPECIFICATION/contracts.md` §"The skill surface"; and the "## Skill surface" section's "eleven skills — six heavyweight authored skills, one operator skill, and four thin-transport machine-query surfaces" sentence is rewritten count-free with `needs-attention` added to its bullet list if missing.
