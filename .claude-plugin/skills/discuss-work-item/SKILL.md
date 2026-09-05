---
name: discuss-work-item
description: Open an interactive stand-by session over one work item or plan — assemble its context through the `context` primitive, answer questions, draft research, record maintainer rulings as plan scope events, and drive a lifecycle action only on explicit instruction. Invoke as `/livespec-orchestrator-beads-fabro:discuss-work-item <plan_slug | work_item_id>`.
allowed-tools: Bash, Read, Grep, Glob, Write
---

# discuss-work-item — Claude Code binding

This file is the thin Claude Code binding for the `discuss-work-item`
operation of the **livespec-orchestrator-beads-fabro** plugin. The
complete harness-neutral driving prose — the subject resolution, the
context-envelope assembly through the `context` primitive, the
envelope-alone resume, the stand-by turns, the consented scope-event
write, and the explicit-instruction gate on every lifecycle drive — is
the plugin's own artifact at
`${CLAUDE_PLUGIN_ROOT}/prose/discuss-work-item.md`. Read that prose file
in full, then execute it end-to-end, binding its harness-neutral
vocabulary to this runtime per `## Runtime bindings` below.

```bash
cat "${CLAUDE_PLUGIN_ROOT}/prose/discuss-work-item.md"
```

This binding adds NO operation behavior of its own; all orchestration
lives in the prose.

## Runtime bindings

- **`<plugin-root>`** — the live `${CLAUDE_PLUGIN_ROOT}` token in this
  Claude Code skill. Any `python3 "<plugin-root>/scripts/bin/<x>.py"`
  invocation in the prose runs via the Bash tool with
  `<plugin-root>` → `${CLAUDE_PLUGIN_ROOT}`.
- **"ask the user" / "confirm with the user" / "obtain consent" /
  "surface" / "narrate" / "stand by and ask"** — conversational turns in
  this session (the AskUserQuestion tool or plain narration, as
  appropriate; ask one question at a time).
- **"read `<file>`"** — the Read tool. **"write `<file>`"** — the Write
  tool. **Enumerate `plan/` directories** — the Glob tool.
  **Python snippets** — run via the Bash tool against the bundled
  `livespec_orchestrator_beads_fabro` package (the wrappers
  self-bootstrap the import path).
- **"assemble the context envelope" / "invoke the `context`
  primitive"** — the
  `/livespec-orchestrator-beads-fabro:context` skill in this plugin, or
  its wrapper `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/context.py"`
  run via the Bash tool with `--json`.
- **"record a scope event" / "read the timeline" / "append a handoff" /
  "set the next action"** — call the package primitives in
  `livespec_orchestrator_beads_fabro.commands.plan` from a Python
  snippet, using the project root and resolved store config.
- **"the `drive` operation"** — the
  `/livespec-orchestrator-beads-fabro:drive` skill in this plugin (the
  one lifecycle-action seam; invoke it only on an explicit maintainer
  instruction).
- **"the `list-work-items` / `next` operation"** — the
  `/livespec-orchestrator-beads-fabro:list-work-items` and
  `/livespec-orchestrator-beads-fabro:next` skills in this plugin (the
  read-only status surface).
- **"the `capture-work-item` operation"** — the
  `/livespec-orchestrator-beads-fabro:capture-work-item` skill in this
  plugin (the ripe-work filing seam).
- **"the `doctor` / `propose-change` operation"** — the cross-boundary
  `/livespec:doctor` and `/livespec:propose-change` skills of the
  **livespec** plugin.
