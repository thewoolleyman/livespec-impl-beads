---
name: livespec-orchestrator-beads-fabro-discuss-work-item
description: "Open an interactive stand-by session over one work item or plan: assemble its context through the context read primitive, answer questions, draft research, and record maintainer rulings as plan scope events. Use when the user wants to discuss, review, or resume a work item or plan. Mutating: it writes consented scope events, and it drives a lifecycle action only on explicit instruction."
allowed-tools: bash read write edit
---

# livespec-orchestrator-beads-fabro-discuss-work-item — pi binding

This file is the thin pi binding of the `discuss-work-item` operation of
the **livespec-orchestrator-beads-fabro** plugin, per this repository's
`SPECIFICATION/contracts.md` (the pi skill surface contract). It carries
pi-runtime mechanics ONLY. The complete harness-neutral driving prose is
the plugin's shared artifact at `prose/discuss-work-item.md`, the same
artifact the Claude and Codex bindings read.

Order of work, every time:

1. Resolve `$PLUGIN_ROOT` (next section).
2. Read `$PLUGIN_ROOT/prose/discuss-work-item.md` **completely** with the
   `read` tool.
3. Execute that prose end-to-end, binding its harness-neutral vocabulary
   to this runtime via the Runtime bindings section below.

Never paraphrase, summarize, or act on a partial read of the prose, and
never restate its steps here — the prose owns the behavior, this file
owns the wiring.

pi's skill namespace is flat — a skill name admits no colon — so this
plugin's namespace is carried by the unabbreviated
`livespec-orchestrator-beads-fabro-` name prefix rather than by the
`/livespec-orchestrator-beads-fabro:discuss-work-item` form the Claude
and Codex surfaces use. Keep the full prefix: sibling fleet repos ship an
operation of the same short name, and shortening it collides with them.

## Resolving the plugin root (`$PLUGIN_ROOT`)

The ordered algorithm is realized ONCE, by this package's
`lib/resolve-plugin-root.sh`, and MUST NOT be restated inline here.
Twelve independently-maintained inline copies of a resolution rule are
kept in agreement only by copying, and that is exactly how one
positional defect came to live in every binding of a sibling Driver at
once.

`<skill-dir>` below is the directory holding THIS `SKILL.md` — you read
this file from disk, so you know its absolute path; the resolver sits
two levels up, beside the bindings tree.

```bash
PLUGIN_ROOT="$(bash "<skill-dir>/../../lib/resolve-plugin-root.sh" .)" || exit 1
echo "$PLUGIN_ROOT"
```

The resolver searches, in order: the `LIVESPEC_ORCH_PLUGIN_ROOT`
override; the governed project's own plugin directory when that checkout
IS this plugin (dogfooding); the project-scope pi package clone under
`.pi/git/github.com/thewoolleyman/livespec-orchestrator-beads-fabro/`; and the user-scope clone
under `~/.pi/agent/git/github.com/thewoolleyman/livespec-orchestrator-beads-fabro/`.

On failure the resolver writes its own diagnostic to stderr and exits 1.
STOP and surface that diagnostic verbatim. Do not improvise a path, and
do not run an install command the diagnostic did not ask for — under a
non-interactive pi run (`-p`, `--mode json`, `--mode rpc`) a failure is
frequently pi's project-trust gate silently ignoring project packages
rather than a missing install.

## Runtime bindings

- **"ask the user" / "confirm with the user" / "obtain consent" /
  "stand by and ask"** — conversational turns in this pi session. pi has
  no structured-picker tool, so ask in plain prose, state the options
  explicitly, and WAIT for the user's reply before proceeding. Every
  store write this operation performs on the user's behalf is consented
  before it executes, per this repository's `SPECIFICATION/contracts.md`
  (the store-write consent discipline); a missing picker is never
  grounds to skip the turn, and it is never grounds to treat an
  ambiguous request as an explicit instruction to drive.
- **"read `<file>`" / "list `<dir>`"** — the `read` tool, or the `bash`
  tool for shell work.
- **"assemble the context envelope" / "invoke the `context`
  primitive"** — the `bash` tool, invoking the context wrapper with
  `--json` and the resolved subject:

```bash
python3 "$PLUGIN_ROOT/scripts/bin/context.py" --json "$@"
```

- **"invoke the `<name>` wrapper"** — the `bash` tool, invoking
  `python3 "$PLUGIN_ROOT/scripts/bin/<name>.py"` with explicit argv.
- **"record a scope event" / "read the timeline" / "append a handoff" /
  "set the next action"** — call the package primitives in
  `livespec_orchestrator_beads_fabro.commands.plan` from a Python
  snippet run through the `bash` tool, using the project root and
  resolved store config.
- **"invoke the sibling `<operation>` skill"** — this runtime exposes it
  as the pi skill `livespec-orchestrator-beads-fabro-<operation>`; drive that skill rather than
  reimplementing its behavior. The `drive` sibling is the one
  lifecycle-action seam, and it runs only on an explicit maintainer
  instruction.
- **"hand off to a livespec core operation"** — core's operations reach
  pi through the livespec pi Driver as the skill
  `livespec-<operation>`. This plugin never binds core's prose or CLIs
  itself; `doctor` and `propose-change` are reached that way.
- **"surface the captured stdout" / "present the JSON verbatim"** —
  plain narration in this session, without re-interpretation or
  re-summarization.
