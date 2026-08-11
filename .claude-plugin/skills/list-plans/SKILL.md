---
name: list-plans
description: List unarchived plans from the repo's plan/ store. Required thin-transport surface per livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md. Invoke as `/livespec-orchestrator-beads-fabro:list-plans [--json] [--project-root <path>]`.
allowed-tools: Bash
---

# list-plans

Thin-transport pass-through. All behavior lives in
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/list_plans.py`.

## Invocation

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/list_plans.py" "$@"
```

Supported flags:

- `--json` — emit `{"plans": ["<topic>", ...]}`
- `--project-root <path>` — override the repo root whose `plan/` store is enumerated

## When to use

- The needs-attention surface needs the current unarchived plan topics.
- A caller needs a read-only inventory of direct child directories under `plan/`, excluding `plan/archive/`.
