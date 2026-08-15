---
topic: supervisor-author-literal
author: claude-code
created_at: 2026-08-15T07:55:00Z
---

## Proposal: Reserve a deterministic supervisor-author literal for plan handoff entries

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Ratify a reserved, deterministically-computed `author` literal —
`f"{topic}-supervisor"` — for plan-epic handoff entries written by the
plan's supervisor role, so a downstream consumer can tell "does this
plan have a supervisor-authored entry" with a plain string-equality
scan instead of prose/LLM parsing. State explicitly that the check
reads the body-parsed `author:` field, never `bd`'s own `--actor`/`-a`
audit-trail field.

### Motivation

`commands/plan.py`'s `append_handoff(*, author: str, ...)` accepts a
free-text `author` supplied by the caller. Real entries today carry
values identifying WHO typed them (`codex`, `thewoolleyman` — runtime/
user identity), not WHICH ROLE they spoke for, so a worker entry and a
supervisor entry from the same runtime are indistinguishable. The one
existing precedent for doing this correctly is already in the same
file: `archive_thread` hardcodes `author="plan-archive"` at its one
call site — the caller cannot override it. This proposal generalizes
that precedent to the supervisor role, because two consumers now need a
deterministic "supervisor defined" discriminator over a plan-epic
timeline: `livespec-overseer`'s foreman check (work-item
`overseer-4bbnit`) and `livespec-overseer`'s `supervise-plan` binder,
which today only says an entry is "attributed to the plan's supervisor
entity" without ever stating the literal it must match.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Ledger-held handoff persistence",
after the existing paragraph ending "...never a parallel work queue
that shadows the ledger.", insert a new paragraph:

```
A plan's SUPERVISOR role — the entity coordinating the plan across
worker-session restarts, distinct from the worker session itself — MUST
be attributable by a deterministic literal, not free text, mirroring an
archive entry's own attribution: an archive entry's body-parsed
`author:` field is the reserved literal `plan-archive`, computed by the
archiving primitive and never caller-supplied. Generalizing that same
rule, when a handoff entry is authored on the supervisor's behalf, the
ledger comment's body-parsed `author:` field MUST be exactly
`<slug>-supervisor`, where `<slug>` is the plan's slug — likewise
computed by the entry-writing primitive itself, never accepted as a
caller-supplied string. A "does this plan have a supervisor"
discriminator MUST scan the timeline for a body-parsed `author:` field
matching this literal — a plain string-equality check, never prose or
LLM interpretation of entry content. This check reads the body-parsed
`author:` field ONLY. It MUST NOT read Beads' own `--actor`/`-a`
audit-trail field: that field is a separate, independently-settable
identity layer (e.g. a human runtime acting on the supervisor's behalf
carries its own `--actor` while the comment body still names the role),
and the two are permitted to diverge. Every free-text `author` a worker
session supplies through the general handoff primitive is unaffected by
this reservation; only the archive and supervisor literals are reserved.
Design record: repo `thewoolleyman/livespec-orchestrator-beads-fabro`,
work-item `bd-ib-8stn`, filed 2026-08-15; independently corroborated the
same date by repo `thewoolleyman/livespec-overseer`, work-item
`overseer-4bbnit`.
```

No heading is added, changed, or removed.
