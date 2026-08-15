---
name: livespec-orchestrator-beads-fabro-next
description: Rank the most-ripe implementation-side action from the beads-backed work-items store. Use when the user asks what to work on next on the implementation side, or as a primitive a loop driver composes. Read-only and deterministic — no LLM in the ranking path.
allowed-tools: bash
---

# livespec-orchestrator-beads-fabro-next — pi binding

This file is the thin pi binding of the `next` operation of the
**livespec-orchestrator-beads-fabro** plugin, per
`SPECIFICATION/contracts.md` §"pi skill surface". It carries pi-runtime
mechanics ONLY. The behavior lives in the plugin's reference wrapper
`scripts/bin/next.py`; this binding resolves the plugin root and
dispatches to it, adding no operation behavior of its own.

pi's skill namespace is flat — a skill name admits no colon — so this
plugin's namespace is carried by the unabbreviated `livespec-orchestrator-beads-fabro-` name
prefix rather than by the `/livespec-orchestrator-beads-fabro:next` form the Claude and Codex
surfaces use. The operation, its flags, and its output are identical
across all three runtimes.

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

## Invocation

```bash
python3 "$PLUGIN_ROOT/scripts/bin/next.py" "$@"
```

The supported flags are the wrapper's own; pass through whatever the
user supplied and let the wrapper validate them. A usage error exits 2
and a precondition failure exits 3 — surface either verbatim rather than
retrying with guessed arguments.

## Output

Surface the wrapper's stdout verbatim. Do NOT re-interpret,
re-summarize, or re-rank it: every listing, ranking, filtering, and
formatting decision belongs to the wrapper, which is the same code the
Claude and Codex surfaces call.
