# Observability gap found while investigating this defect

Written 2026-07-26. Incidental to the valve defect but discovered by it,
and recorded here so it is not lost. It is NOT in this thread's scope to
fix — see "Routing" at the bottom.

## Honeycomb MCP is registered but cannot launch

The maintainer asked for this investigation to use Honeycomb observability.
It was unavailable. `claude mcp list` reports:

```
plugin:honeycomb:honeycomb: /home/ubuntu/.worktrees/vps-info/hc-dualrun/services/honeycomb-mcp/honeycomb-mcp.sh
  - ✘ Failed to connect — ENOENT: no such file or directory,
    posix_spawn '/home/ubuntu/.worktrees/vps-info/hc-dualrun/services/honeycomb-mcp/honeycomb-mcp.sh'
```

The registration points at a launcher **inside a git worktree**
(`~/.worktrees/vps-info/hc-dualrun/`) that no longer exists. A routine
worktree cleanup silently removed the fleet's Honeycomb access; the
registration survived the thing it points at.

Also checked: no `~/.config/honeycomb`, and no `HONEYCOMB_*` variable in
the session environment — so there is no fallback path to the API either.

**Impact.** Any session asked to investigate via Honeycomb will fail the
same way, and the failure mode is quiet — the tools simply are not in the
tool list, which reads as "Honeycomb wasn't relevant" rather than
"Honeycomb is broken." This investigation only caught it because the
maintainer named Honeycomb explicitly.

**The generalizable point** matches this thread's own theme: a reference
pointing into a worktree outlives the worktree. Same class as a handoff
citing an uncommitted path, which the `plan` operation's self-sufficiency
gate (`no dangling reference`) exists to prevent.

## What was used instead

The local dispatch journal, `tmp/fabro-dispatch-journal.jsonl` (3527
records), which carried the full D1 trace including the
`converged: false / fix_loop_count: 4` calibration record quoted in
`root-cause.md`. It was sufficient for this investigation.

Note this is a LOCAL, host-only artifact under `tmp/`. It is not fleet
observability: it exists only on this host, is not queryable across repos,
and has no retention guarantee. Relying on it is a workaround, not a
replacement for Honeycomb.

## Routing

Deliberately NOT filed as a child of this thread's epic — it is
infrastructure, unrelated to the valve defect, and would muddy this
thread's acceptance. It is recorded here because it was discovered here and
would otherwise be lost.

Two candidate homes, for the maintainer to choose:

1. A standalone freeform work-item in the `bd-ib` ledger (it affects this
   repo's investigations), or
2. The `vps-info` repo that owns the `hc-dualrun` service, which is where
   the launcher path actually belongs.

The second is more likely correct — the fix is either to repoint the
registration at a non-worktree path or to reinstall the service — but the
`vps-info` repo was not inspected during this investigation, so that is a
recommendation, not a finding.
