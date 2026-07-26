# handoff — valve-advertisement-mismatch

Opened 2026-07-26. This is the single resumption point for this thread.

**Repo root for every path and command in this file:**
`/data/projects/livespec-orchestrator-beads-fabro`. All repo-relative paths
below are relative to that root, and every command block assumes you have
`cd`'d there first.

## Read-first chain

Read in this order before acting:

1. `plan/valve-advertisement-mismatch/research/root-cause.md` — the defect,
   the verbatim code on both sides, the provenance, and why the originating
   fix's method could not have found it. Includes a CORRECTION notice about
   this thread's own earlier caller-count error; read it, it is the point.
2. `plan/valve-advertisement-mismatch/research/prior-work-and-collisions.md`
   — the closed/archived originating track, what is already filed (do not
   duplicate), and TWO live collisions against the same contract paragraph.
3. `plan/valve-advertisement-mismatch/research/observability-gap.md` — an
   unrelated infrastructure finding discovered here; NOT this thread's work.

## Status — read it, do not trust this file

Ledger ids, cited read-only. Compose current status before acting:

```bash
cd /data/projects/livespec-orchestrator-beads-fabro
/usr/local/bin/with-livespec-env.sh -- python3 \
  .claude-plugin/scripts/bin/list_work_items.py --json
```

| id | role |
|---|---|
| `bd-ib-dohu2g` | this thread's epic anchor (`backlog`) |
| `bd-ib-h57nx4` | the fix (`ready`; child of the anchor via `parent-child`) |

Related, **not** owned by this thread — read before designing, do not
duplicate: `bd-ib-4m5f` (`next` vs Dispatcher candidate-SET divergence),
`bd-ib-kn63nm` (`append_work_item` hardcodes `--type blocks`; hit live while
filing this thread — the epic edge had to be added by hand as
`parent-child`).

## In one sentence

`needs-attention` advertises `valve:approve:<id>` at `[high]` for every
`pending-approval` item, and `drive` refuses that exact command on this repo
100% of the time, because the advertiser branches on stored status alone
while the enforcer requires an effective-`manual` admission policy and
`.livespec.jsonc:93` commits `auto_approve_ready: true`.

## Next action — dispatch the fix

`bd-ib-h57nx4` is `ready`, and its `factory_safety` field is null, which is
what makes it factory-safe (a null field means no host-only constraint;
`is_host_only_item` returns False). Dispatch it:

```bash
cd /data/projects/livespec-orchestrator-beads-fabro
/usr/local/bin/with-livespec-env.sh -- python3 \
  .claude-plugin/scripts/bin/dispatcher.py dispatch \
  --repo /data/projects/livespec-orchestrator-beads-fabro --item bd-ib-h57nx4
```

**Do NOT hand-build it in session.**

Do **not** try to `groom` `bd-ib-h57nx4` first: `groom` is `backlog`-only
(`SPECIFICATION/contracts.md` §"Grooming", and the operation raises
`GroomTargetNotBacklogError`), and this item is `ready`. It was already
sized as one coherent slice at intake. If a dispatch comes back
non-convergent and the item is bounced to `backlog`, groom is then available
and each re-cut slice is dispatched the same way.

## The contract is also wrong — but read this before amending it

`per-state-verb-vocabulary` **ratified as v050** (`27980bb`,
2026-07-26T17:26:19Z) while this thread was being written.
`SPECIFICATION/contracts.md` §"Door rules" now says:

> The move from `pending-approval` to `ready` is REMOVED: it is an
> unjournaled duplicate of the `approve` valve, so the ledger cannot
> attribute the transition.

**Exactly one half of that is wrong, and it is NOT the half you might
expect.**

- **"Unjournaled" is CORRECT.** Do not contest it. The `journal: {...}`
  object returned by `drive --action move:<id>:ready` is a RESPONSE PAYLOAD
  field built by `_drive_valve_result.py:29`, not a durable write.
  `_drive_valves.py` references no `JournalFile`; the dispatch journal holds
  zero `human-valve-*` records. An earlier draft of this thread claimed
  otherwise and was wrong.
- **"Duplicate" is FALSE.** The approve valve refuses every item on this
  repo, so the move is not a duplicate of it — it is the only on-demand
  operator door from `pending-approval` to `ready`.

So the amendment case, if one is made, is *"removing this door leaves the
operator no working on-demand door"* — never *"the move journals"*.

**A second proposal is already pending against this same paragraph:**
`SPECIFICATION/proposed_changes/rework-return-door-attribution.md` (filed
2026-07-26T17:42:47Z), narrowing the adjacent `active`-entry clause. Before
filing anything here, check whether it has ratified and re-derive your
verbatim anchor if so.

**Recommended sequencing: fix the code FIRST.** Landing `bd-ib-h57nx4` makes
`approve` a genuinely working door, which may reduce this to a small wording
fix or remove the need entirely. Re-read the clause after the fix lands and
decide then. Rationale in
`research/prior-work-and-collisions.md` §"Consequence for this thread".

If an amendment is filed, tell the `console-happy-path-mvp-supervisor`
session (`livespec-console-beads-fabro`), which authored the v050 proposal.

## Open questions for the groom — do not assume

- **Do the sibling valves have the same defect?** `accept`, `reject`, and
  `resolve-blocked` are advertised by the same function. Whether their
  enforcers carry preconditions the advertiser also ignores was NOT
  investigated. Check before scoping — the answer decides whether the fix is
  one predicate or a general advertiser/enforcer binding.
- **What should the advertiser show for an auto-policy `pending-approval`
  item?** Emitting nothing trades a broken action for an invisible item. See
  `bd-ib-h57nx4`'s Deliverable section.
- **Does one fix subsume `bd-ib-4m5f`?** Same theme, different defect. If
  yes, say so explicitly rather than filing overlapping work.
- **Should a `converged: false` calibration gate a merge?** The originating
  D1 run recorded `converged: false, fix_loop_count: 4` and shipped anyway.
  Out of scope here; raised in `root-cause.md` so it is not lost.

## Definition of done for this thread

- `bd-ib-h57nx4` closed with a verifier that would go RED against today's
  code (not one that passes on arrival).
- The v050 door-rule clause re-read after the fix lands, and either amended
  via `/livespec:propose-change` (and ratified) or explicitly recorded here
  as no-longer-needing amendment.
- The epic `bd-ib-dohu2g` closed, and this directory moved to
  `plan/archive/valve-advertisement-mismatch/`.
