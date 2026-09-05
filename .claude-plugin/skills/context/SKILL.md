---
name: context
description: Assemble one work-item's or plan epic's full context envelope from the beads-backed store — record, comments, children, dependencies, next_action, research directory, and cited spec clauses. Required thin-transport surface per SPECIFICATION/contracts.md. Invoke as `/livespec-orchestrator-beads-fabro:context <plan_slug | work_item_id> [--json]`.
allowed-tools: Bash
---

# context

Thin-transport pass-through. All behavior lives in
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/context.py`.

## Invocation

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/context.py" "$@"
```

Supported flags:

- `<plan_slug | work_item_id>` — the required positional subject; a plan
  epic's `plan_slug` metadata or any work-item id
- `--json` — emit the context envelope as one JSON object
- `--project-root <path>` — override the default `Path.cwd()` project root
- `--work-items-path <path>` — override the resolved store connection

## When to use

- A session resumes a plan and needs its current facts without any chat
  history — the envelope is the whole read.
- The `discuss-work-item` skill assembles its subject through this
  primitive rather than a hand-rolled per-item read.
- The console chat pane reads this surface to open a work-item.

## What it is not

Query-only. It never mutates the work-items store, and an absent id or
`plan_slug` exits 3 naming the missing key rather than emitting an empty
envelope.
