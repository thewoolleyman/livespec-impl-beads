---
topic: context-and-discuss-work-item-surface
author: claude-opus-4-8
created_at: 2026-09-05T03:24:49Z
---

## Proposal: The `context` read-primitive surface

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

Contract a new query-only read primitive `context` in the list-work-items / needs-attention family: given a plan_slug or a work-item id it deterministically assembles one structured envelope of the item's full context.

### Motivation

Console decision D6 (ratified v095) names `context` as the deterministic loader that `discuss-work-item` (b2) and the console chat pane read to resume a plan without chat history. b1 delivered the typed next_action and the associated_work_item_id anchor that this loader reads; the surface itself is not yet contracted, so its impl (bd-ib-g4lj2w) has no spec commitment to trace to. This adds the surface clause and an exercising scenario, spec-first.

### Proposed Changes

Add a new surface clause under `contracts.md` §"The skill surface", as a sibling of `#### list-work-items` and `#### needs-attention`:

#### `context`

CLI surface: `context <plan_slug | work_item_id> [--json] [--work-items-path <path>] [--project-root <path>]`.

`context` is a query-only read primitive: it MUST NOT mutate the work-items store. Given a `plan_slug` (matching a plan epic's `plan_slug` metadata) OR a work-item id, it deterministically assembles one structured envelope for that item and, with `--json`, emits it as a single JSON object. The envelope MUST carry: the resolved epic or work-item record; its comments; its children (unioned across BOTH the dotted-id hierarchy and the `parent-child` dependency edge, per the child-enumeration contract, so neither linkage is dropped); its dependency edges; its typed `next_action`; the linked research directory path when an `associated_work_item_id` anchor resolves one; and the linked spec clauses it cites. Resolution is order-independent and side-effect-free: two invocations against an unchanged store MUST emit byte-identical envelopes. An absent id or plan_slug MUST fail with a not-found error naming the missing key, never an empty envelope. `--json` is the machine surface; `--project-root` and `--work-items-path` carry the same semantics as for `list-work-items`.

Add `## Scenario 114 — The context read primitive assembles a deterministic item-context envelope` to `scenarios.md`, exercising: `context --json` on an epic id emits an envelope populating epic, comments, children, dependencies, next_action, research, and spec fields; `context --json` on a child work-item id emits the same envelope shape; two invocations against an unchanged fixture tenant emit byte-identical envelopes; an unknown id fails with a not-found error naming the key. Co-edit `tests/heading-coverage.json` to add the new H2 (`test` MAY be `"TODO"` with a non-empty reason pending the b2.S2 exercising test bd-ib-g4lj2w).

## Proposal: The `discuss-work-item` interactive skill surface

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

Contract the interactive stand-by skill `discuss-work-item` over the `context` primitive: the maintainer day-to-day session and the console future chat pane, which stands by and drives only on explicit instruction.

### Motivation

D6 rules that resume context is what the discuss-work-item loader computes; this is the interactive surface the maintainer runs instead of the plan operation's ad-hoc mechanics. Its impl (bd-ib-kr334k) needs a contracted surface to trace to. Naming is constrained: it MUST NOT be `plan`, which collides with the Claude Code built-in on autocomplete.

### Proposed Changes

Add a surface clause under `contracts.md` §"The skill surface", after `#### context`:

#### `discuss-work-item`

CLI surface: `discuss-work-item <plan_slug | work_item_id> [--project-root <path>]`.

`discuss-work-item` is the interactive skill layered over the `context` primitive. It MUST assemble its subject's context through `context` (never a hand-rolled per-item read). It STANDS BY: it answers questions about the item, drafts research notes, and records maintainer rulings as plan scope events through the plan primitives, and it drives a lifecycle action ONLY on explicit maintainer instruction. It MUST resume a plan from the `context` envelope alone, without chat history. It MUST be registered under the name `discuss-work-item`; it MUST NOT be named `plan` (which collides with the Claude Code built-in on autocomplete). Plan mechanics that need no operation (epic creation, research-directory and anchor scaffolding, the archive move) MAY be offered by this skill; doctor reports what is missing.

Add `## Scenario 115 — discuss-work-item stands by over the context envelope and resumes without chat history` to `scenarios.md`, exercising: the skill assembles context through the `context` primitive; it resumes a plan from the envelope alone; it records a maintainer ruling as a scope event; it is registered under the name `discuss-work-item`. Co-edit `tests/heading-coverage.json` for the new H2 (`test` MAY be `"TODO"` with a reason pending b2.S3 bd-ib-kr334k).
