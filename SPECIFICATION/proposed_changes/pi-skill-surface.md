---
topic: pi-skill-surface
author: claude-fable-5-bootstrap-pi-driver-orch
created_at: 2026-08-15T15:46:05Z
---

## Proposal: Expose the orchestrator operation surface to pi as flat livespec-orchestrator-beads-fabro-<op> skills

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Add the pi coding agent as a third per-runtime binding layer for this
plugin's operation surface, at parity with the existing Codex surface
and over the SAME wrapper CLIs and prose artifacts (nothing is
duplicated for pi). The proposal specifies the packaging (a root
`package.json` pi manifest naming a nested
`.claude-plugin/.pi-plugin/skills/` bindings tree, mirroring the Codex
nesting), the concrete flat skill names
(`livespec-orchestrator-beads-fabro-<op>`, since pi skill names admit no
colon namespacing), the mapping rule (derived from the operations
shipped under `.claude-plugin/skills/`, never a restated enumeration),
the thin-binding obligations mirroring the Codex clauses (wrapper
dispatch for thin-transport ops, full prose reads for heavyweight ops,
one shared plugin-root resolver, no pi extension of its own), and the
trust-gate and non-interactive caveat BY CITATION to livespec core
rather than by restatement. It also sweeps the four existing sentences
that name Claude Code and Codex as the complete supported-runtime set,
rewriting each runtime-neutrally so ratifying the pi surface leaves
nothing behind contradicting it.

### Motivation

livespec core ratified (v208) that core is distributed to pi as a
resource-less git package and that the pi Driver `livespec-driver-pi`
exposes core's eight spec-side operations as flat `livespec-<operation>`
pi skills, while explicitly delegating the orchestrator-side mapping:
core's `SPECIFICATION/non-functional-requirements.md` §"pi dogfooding
contracts" states that the detailed pi mapping for orchestrator-plugin
commands is owned by each orchestrator plugin's own spec. This
repository has no such mapping today.

The gap is a real asymmetry, not a formality. This plugin already ships
its operation surface to TWO runtimes — Claude Code bindings under
`.claude-plugin/skills/` and Codex bindings under
`.claude-plugin/.codex-plugin/skills/` — both thin over the same
`scripts/bin/` wrappers and `prose/` artifacts, and both governed by
`constraints.md` §"Skill orchestration constraints" and a structural
gate (`dev-tooling/checks/codex_plugin_structure.py`) that enforces the
thinness. An operator working from pi has no surface at all: none of the
orchestrator's operations are reachable, even though core's own
operations are, so a pi session can drive the spec side of the
lifecycle and not the implementation side.

Two pi-specific facts make this a spec question rather than a purely
mechanical port. First, pi's skill namespace is flat — names admit no
colon — so the `/plugin:operation` form both existing runtimes rely on
has no pi expression, and the namespace must be carried by a name
prefix whose exact spelling is a contract consumers depend on. Second,
pi's project-trust gate makes a non-interactive invocation silently
resolve nothing in an untrusted project, which turns "the surface is
installed" and "the surface actually loads" into two separate claims —
the same distinction the Codex clauses already draw between
model-visible loading and human discoverability.

### Proposed Changes

Two files change, in two kinds of edit. The pi surface itself is ADDED
as one new section plus one new bullet. Four existing sentences that
enumerate this plugin's supported agent runtimes as exactly "Claude Code
and Codex" are additionally REPLACED with runtime-neutral phrasing —
without that sweep, ratifying the new section would leave four
statements silently contradicting it, and each would have to be found
again the next time a runtime is added. Nothing is deleted.

### 1. `SPECIFICATION/contracts.md` — new section

Insert the following new `## ` section immediately BEFORE the existing
line:

```
## Interactive dialogue ownership (orchestrator-side)
```

The inserted section, verbatim:

```markdown
## pi skill surface

The plugin's operation surface is ALSO exposed to the pi coding agent
(`@earendil-works/pi-coding-agent`) as a third per-runtime binding layer
over the SAME artifacts the Claude Code and Codex surfaces bind: the
wrapper CLIs under `.claude-plugin/scripts/bin/` and the harness-neutral
prose under `.claude-plugin/prose/`. livespec core owns the pi packaging
model for CORE's own operations and delegates this one: core's
`SPECIFICATION/non-functional-requirements.md` §"pi dogfooding
contracts" states that the detailed pi mapping for orchestrator-plugin
commands is owned by each orchestrator plugin's own spec. This section
is that mapping.

**Packaging.** The pi surface ships from THIS repository as a pi package
per pi's documented package model: a `pi` manifest block in a
`package.json` at the repository root, carrying the `pi-package` keyword
for gallery discoverability. The manifest declares exactly one resource
kind — `skills` — naming a NESTED bindings tree at
`.claude-plugin/.pi-plugin/skills/`, the pi sibling of the Codex
bindings' `.claude-plugin/.codex-plugin/skills/`. The nesting enforces
the same single-artifact discipline the Codex surface already follows:
the payload (`scripts/`, `prose/`, and the Claude bindings under
`skills/`) has exactly ONE home under `.claude-plugin/`, and each
runtime's bindings sit beside it rather than duplicating it. No prose
file, wrapper, schema, or template is duplicated for pi. A consumer
installs this repository as a pi git package — `pi install
git:github.com/thewoolleyman/livespec-orchestrator-beads-fabro@release
-l`, the same moving `release` channel the Claude and Codex
marketplaces track — and the resulting clone carries the payload the
bindings resolve.

**Skill names.** pi's skill namespace is FLAT. A pi skill name admits
only lowercase letters, digits, and hyphens (1–64 characters, no
leading or trailing hyphen, no consecutive hyphens), so the
colon-qualified `/livespec-orchestrator-beads-fabro:<op>` form the
Claude and Codex surfaces use cannot be expressed. The namespace is
therefore carried by a name PREFIX, exactly as core's pi Driver carries
`/livespec:<op>` as the pi skill name `livespec-<operation>`. Each of
this plugin's operations is exposed to pi as the skill named
`livespec-orchestrator-beads-fabro-<op>`: the plugin's own name,
UNABBREVIATED, followed by the operation name it carries on every other
runtime. Abbreviating the prefix is forbidden — two fleet repositories
end in the same `-beads-fabro` suffix, so a shortened prefix would name
an ambiguous surface.

The mapping is DERIVED, not enumerated: the pi surface exposes one skill
per operation this plugin ships as a Claude binding under
`.claude-plugin/skills/`, no more and no fewer, so an operation added or
retired there changes the pi surface in the same act rather than through
a separately-maintained list that can silently fall behind. Every name
this rule produces fits pi's 64-character limit; an operation name long
enough to breach that limit MUST be resolved through a propose-change
cycle here, never by silently abbreviating the plugin prefix. Each
binding's directory name under `.claude-plugin/.pi-plugin/skills/` MUST
equal its frontmatter `name`: pi tolerates a mismatch — observed on pi
v0.84.1, anchored because it is a claim about an external project no
gate here watches, and to be re-verified on any pi major-version bump —
the Agent Skills standard does not, and the tolerance is not a licence
to diverge.

**Thin-binding obligations.** Every pi binding carries pi-runtime
mechanics ONLY, under the same thinness discipline the Codex bindings
carry (`constraints.md` §"Skill orchestration constraints"). A pi
`SKILL.md` MUST NOT copy a Claude-specific or Codex-specific SKILL.md
body. Concretely:

- A thin-transport operation's pi binding resolves the plugin root and
  invokes that operation's `scripts/bin/<op>.py` wrapper. Ranking,
  listing, filtering, and output formatting stay in the wrapper; the
  binding surfaces the wrapper's stdout without re-interpretation.
- A heavyweight operation's pi binding reads its shared
  `.claude-plugin/prose/<op>.md` artifact COMPLETELY and executes it,
  binding the prose's harness-neutral vocabulary to pi's tools. It MUST
  NOT restate, summarize, or act on a partial read of that prose. The
  store-write consent discipline (§"Store-write consent discipline")
  binds it unchanged: pi has no structured-picker tool — an absence
  observed on pi v0.84.1, anchored for the same reason and to be
  re-verified on any pi major-version bump — so a consent turn is asked
  in plain prose, with the options stated explicitly, and answered
  before the write executes. Should a future pi release add a picker,
  using it is permitted, and only through a propose-change cycle here.
- The operator surface `drive` is a thin binding over `drive.py`, with
  the selected action executed by the shared CLI, and it composes and
  ranks nothing.
- Plugin-root resolution is realized ONCE, by a single shared resolver
  script in the pi bindings tree that every binding invokes; the ordered
  algorithm MUST NOT be restated inline in a SKILL.md. The sibling repo
  `thewoolleyman/livespec-driver-claude` carried its core-root
  resolution rule as one inline copy per operation binding, across all
  eight of the operations that Driver exposes; copies kept in agreement
  only by copying, so a single positional defect came to live in all
  eight bindings at once. The resolver's search order is: the
  `LIVESPEC_ORCH_PLUGIN_ROOT` explicit override; the governed project's
  own `.claude-plugin/` when that checkout IS this plugin (dogfooding);
  the project-scope pi clone under
  `.pi/git/github.com/thewoolleyman/livespec-orchestrator-beads-fabro/`;
  then the user-scope clone under the pi user-scope git root. A
  candidate counts as resolved ONLY when it actually carries the payload
  (`scripts/bin/`), so a half-fetched clone fails loudly instead of
  resolving to a path whose every subsequent read fails separately. On
  exhaustion the resolver MUST emit an install diagnostic naming every
  candidate it searched, and the binding MUST surface that diagnostic
  verbatim and stop rather than improvising a path.
- The pi package declares NO `extensions`. The sanctioned pi footgun
  guard is the pi DRIVER's, required of `livespec-driver-pi` by core's
  `SPECIFICATION/contracts.md` §"Driver-shipped hooks"; a second
  registration of the same `tool_call` handler from this package would
  double-guard the same tool calls without adding a control.

**Trust gate and the non-interactive caveat.** pi's project-trust
behavior is core's contract and is NOT restated here: per core's
`SPECIFICATION/contracts.md` §"Plugin distribution", pi package
enablement is project-scoped through a committed `.pi/settings.json`,
and a NON-INTERACTIVE pi invocation (`-p`, `--mode json`, `--mode rpc`)
silently ignores project-local settings and packages unless a trust
decision is pre-seeded. Any unattended pi drive of an operation from
this plugin MUST establish trust first, and a resolution failure under a
non-interactive run MUST be read as a possible trust gate before it is
read as a missing install. Mirroring the Codex claim discipline in
`constraints.md` §"Skill orchestration constraints", pi support is
CLAIMED only once the package registration is present AND a live pi
invocation drives one of this plugin's operations through it; the human
discoverability surface (pi's `/skill:<name>` command completion or the
startup skills listing) is verified SEPARATELY from model-visible skill
loading, because the two can diverge. A temporary local pi registration
used for testing is removed afterward unless the maintainer asks to
keep it.
```

### 2. `SPECIFICATION/contracts.md` — retire two two-runtime enumerations

Both edits below replace an existing enumeration that names Claude Code
and Codex as the complete set of supported runtimes. Each is rewritten
runtime-NEUTRALLY rather than extended to a three-item list: an
enumeration extended by hand is the same defect deferred by one runtime,
and the concrete per-runtime packaging is already owned by the sections
that define each surface.

**2a.** In §"The skill surface" → "Heavyweight authored skills (6)",
replace:

```
per-runtime SKILL.md bindings (one for Claude Code, one for Codex) that
resolve the plugin root, read `prose/<op>.md` in full, and map its
```

with:

```
per-runtime SKILL.md bindings — one per supported agent runtime — that
resolve the plugin root, read `prose/<op>.md` in full, and map its
```

**2b.** In §"Interactive dialogue ownership (orchestrator-side)",
replace:

```
and `groom` (per §"Store-write consent discipline"), usable from the
supported agent runtimes (Claude Code and Codex CLI). These front-ends
```

with:

```
and `groom` (per §"Store-write consent discipline"), usable from every
supported agent runtime. These front-ends
```

### 3. `SPECIFICATION/constraints.md` — new bullet in §"Skill orchestration constraints"

In `SPECIFICATION/constraints.md` §"Skill orchestration constraints",
insert the following new bullet immediately AFTER the existing bullet
that begins `- Codex support is REQUIRED as a first-class agent-runtime
consideration.` and ends `...before Codex support is claimed.`, and
immediately BEFORE the existing bullet that begins `- Heavyweight skills
that write to the work-items store MUST`:

```markdown
- pi support is REQUIRED as a first-class agent-runtime consideration on the same terms as Codex. pi adapters MUST be thin runtime bindings over the same wrapper CLIs, prose artifacts, beads tenant semantics, and consent rules as the Claude Code skills; they MUST NOT copy Claude-specific or Codex-specific `SKILL.md` bodies. Thin-transport behavior remains zero-orchestration under pi too: ranking, listing, and formatting logic stays in the wrapper scripts. The `drive` surface is likewise a thin runtime binding over `drive.py`, and plugin-root resolution is delegated to the ONE shared resolver script rather than restated inline per binding (per `contracts.md` §"pi skill surface"). pi skill names are flat — no colon namespacing exists — so the plugin namespace is carried by the unabbreviated `livespec-orchestrator-beads-fabro-` name prefix. Claude-only hooks are NOT assumed to run under pi; the sanctioned pi footgun-guard extension belongs to the pi Driver, and this plugin ships no pi extension of its own. The human pi discovery surface MUST be verified separately from model-visible skill loading, and pi support MUST NOT be claimed until a live pi invocation has driven one of this plugin's operations through the installed package.
```

### 4. `SPECIFICATION/constraints.md` — retire two more two-runtime enumerations

Both edits are in §"Skill orchestration constraints", in bullets that
predate this proposal, and both are rewritten runtime-neutrally for the
same reason as edit 2.

**4a.** In the heavyweight-skills bullet, replace:

```
utilities (record-formatting, schema validation); no dialogue logic is
  duplicated across the Claude and Codex bindings.
```

with:

```
utilities (record-formatting, schema validation); no dialogue logic is
  duplicated across the per-runtime bindings.
```

**4b.** In the operator-skill bullet, replace:

```
  in the shared `drive.py` wrapper and command module so Claude Code and
  Codex bindings call the same logic.
```

with:

```
  in the shared `drive.py` wrapper and command module so every
  per-runtime binding calls the same logic.
```

### Notes for the accepting revise

- **Heading-coverage co-edit.** This proposal adds exactly ONE `## `
  heading (`## pi skill surface` in `SPECIFICATION/contracts.md`) and
  changes or removes none. The accepting revise MUST therefore carry
  `tests/heading-coverage.json` in its `resulting_files[]` with a new
  entry for that heading (`spec_root: SPECIFICATION`, `spec_file:
  contracts.md`), alongside the two spec files. Without that co-edit the
  pre-commit `check-heading-coverage` gate fails.
- **Every replacement target was verified verbatim-unique.** Each of the
  four replaced passages in edits 2 and 4 was matched against the live
  file at the time this proposal was amended and occurs exactly once.
  The accepting revise SHOULD re-confirm that before applying them, since
  master moves between filing and ratification.
- **The Codex-specific bullet in §"Skill orchestration constraints" is
  deliberately left alone.** It states Codex-specific claim discipline
  (the Codex TUI picker rendering, Codex hook assumptions), not a
  supported-runtime enumeration, so neutralizing it would erase real
  content. The new pi bullet is its sibling rather than its replacement.
- **No count is introduced.** The pi mapping is stated as a derivation
  over the operations shipped under `.claude-plugin/skills/`, never as
  an enumeration or a total, so it cannot fall out of lockstep with the
  operation set the way a restated count would. This is deliberate: the
  existing §"The skill surface" inventory (six heavyweight, one
  operator, four thin-transport) does not account for the shipped
  `needs-attention` skill, a pre-existing drift this proposal neither
  inherits nor repairs. Repairing that inventory is separate work and
  should be filed on its own.
- **Implementation follows ratification.** The pi package files
  themselves (the root `package.json` manifest, the
  `.claude-plugin/.pi-plugin/skills/` bindings tree, the shared
  resolver, and a `check-pi-plugin-structure` structural gate modelled
  on the existing `dev-tooling/checks/codex_plugin_structure.py`) are
  drafted separately and MUST NOT merge before this proposal is
  ratified.
