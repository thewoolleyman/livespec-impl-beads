# The next-action marker must LITERALLY begin `next action:`

Captured 2026-08-22 by the session resuming plan epic `bd-ib-2nq`. Recorded here
because this thread paid for it twice, silently, and nothing in the operation's
prose says the literal out loud.

## The trap

`plan`'s unattended resume takes the single recorded next action instead of
raising the which-action picker. Whether an entry records one is decided by
`recorded_next_actions` in
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_plan_timeline.py`:

```python
_NEXT_ACTION_MARKER = "next action"
_MARKER_ORNAMENTS = "-*# "
...
marker_line = line.strip().lstrip(_MARKER_ORNAMENTS).strip()
if not marker_line.lower().startswith(_NEXT_ACTION_MARKER):
    continue
_, separator, action = marker_line.partition(":")
if not separator or not action.strip():
    continue
```

So a line qualifies only if, after stripping leading `-`, `*`, `#` and spaces, it
STARTS WITH `next action` and carries non-empty text after a colon.

## Why it is easy to get wrong

A banner heading is the natural way to write this in a long handoff, and every
banner form fails:

- `== EXACTLY ONE NEXT ACTION ==` — starts with `=`, which is not an ornament,
  and does not start with the marker even after stripping. No colon either.
- `## Next action` — ornament `#` is stripped and the marker matches, but there
  is no colon, so it still records nothing.
- `**Next action:**` — `*` is stripped from the LEFT only; the line then begins
  `Next action:**`, which does match, and the action text survives. This one
  happens to work, which makes the failures harder to predict.

The failure is SILENT and it fails in the safe-looking direction: the entry is
written, reads perfectly to a human, appears on the timeline, and simply produces
`ask=True` with reason `newest handoff records 0 next actions, not exactly one`.
Nobody sees that reason unless an unattended resume actually fires.

## What it cost this thread

Two consecutive handoff entries on `bd-ib-2nq` — the 2026-08-22 grooming-pass
opening handoff, and this session's own first entry — both used banner headings
and both recorded ZERO next actions. Each was otherwise a complete, correct
handoff naming exactly one action in prose. A hands-off restart would have parked
on a picker nobody was present to answer, which is precisely the outcome the
unattended path exists to prevent.

## The rule

Write the marker as a plain line, at the left margin, in this shape:

```
next action: <the one action, in a single line>
```

Keep the surrounding banner if it helps a human reader — the parser scans every
line, so a `== EXACTLY ONE NEXT ACTION ==` heading followed by a
`next action: ...` line satisfies both audiences.

## Verify, do not assume

Read the entry back after appending it. This is a two-line check and it is the
only thing that distinguishes "recorded" from "looks recorded":

```python
entries = read_timeline(config=cfg, epic_id="bd-ib-2nq")
print(resume_directive(entries=entries, unattended=True))
```

`ask=False` with a populated `next_action` means the thread is genuinely
resumable hands-off. Anything else names its own reason.

Note that `resume_directive(..., unattended=False)` ALWAYS returns
`ask=True, reason="interactive resume"` by design — so checking it in attended
mode tells you nothing about whether your marker parsed. Pass `unattended=True`
for the check even from an attended session, or the control cannot fail.
