# Root cause — needs-attention advertises an approve valve that drive refuses

Written 2026-07-26. Every claim below was verified against `origin/master`
on that date; each carries its evidence inline.

## The symptom, observed

`needs-attention` lists, at `[high]` priority:

```
- `valve:approve:bd-ib-wuotqm` [high] Approve pending work-item bd-ib-wuotqm: ...
  - Handoff: `python3 .../bin/drive.py --repo . --action approve:bd-ib-wuotqm --json`
```

Running that exact handoff command returns:

```json
{
  "action_id": "approve:bd-ib-wuotqm",
  "domain_error": "invalid-source-state",
  "kind": "human-valve",
  "status": "failed",
  "summary": "approve requires an effective-manual pending-approval item."
}
```

One surface advertises an action at high priority and hands the operator a
copy-pasteable command; the other refuses that command **by construction**.
This is not a transient state race — on this repo the approve valve can
NEVER succeed for ANY item (see "Why it is total, not intermittent").

## The two halves, verbatim

**The advertiser** — `.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_needs_attention_work_items.py:77-86`. It
branches on stored status ALONE and never consults admission policy:

```python
if status == "pending-approval":
    lanes.append(
        _valve(
            verb="approve",
            work_item=item_id,
            summary=f"Approve pending work-item {item_id}: {title}",
            project_root=project_root,
            action_id=f"approve:{item_id}",
        )
    )
```

**The guard** — `.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_drive_valves.py:141-152`. It demands the
effective policy be `manual`:

```python
def _approve_item(
    *, repo: Path, config: StoreConfig, item: WorkItem, action_id: str
) -> dict[str, Any]:
    if item.status != "pending-approval":
        return invalid_source_state(aid=action_id, item=item, expected="pending-approval")
    if effective_admission_policy(item=item, cwd=repo) != "manual":
        return valve_refusal(
            aid=action_id,
            wid=item.id,
            err="invalid-source-state",
            msg="approve requires an effective-manual pending-approval item.",
        )
```

The advertiser's predicate is a strict superset of the guard's. Every item
in the difference is advertised and then refused.

## Why it is TOTAL on this repo, not intermittent

`.livespec.jsonc:93` commits `"auto_approve_ready": true`. With no per-item
`admission_policy` label, `effective_admission_policy` resolves to `auto`
for every item, so the guard's `!= "manual"` is true for every item and the
valve refuses ALL of them. The advertised action is unreachable here in
100% of cases, not in an edge case.

Verified 2026-07-26: `resolve_auto_approve_ready(cwd=.)` returns `True`.

## Root cause — an incomplete call-site sweep, and why the method was blind

The guard was introduced by **`952d874` "fix: honor global auto approval in
valves"** (PR #839, 2026-07-20, release 0.45.14), a Fabro dark-factory
dispatch under work-item `bd-ib-24j5uy.4` ("D1").

D1's own record contains its analysis method — a table headed
**"Three call sites; TWO are wrong"**:

| Call site | Passes `cwd`? | Path |
|---|---|---|
| `intake_dor.py:142` | YES | capture-time intake — CORRECT |
| `_drive_valves.py:143` | NO | manual approve valve — WRONG |
| `_dispatcher_valves.py:191` | NO | the dispatcher loop — WRONG |

D1 correctly fixed both wrong sites. Its defect is what the table does not
contain.

**`_needs_attention_work_items.py` is absent from that inventory because it
never calls `effective_admission_policy` at all.** D1's method was an
enumeration of that function's CALLERS. A surface that decides whether to
ADVERTISE the valve without ever consulting the policy cannot appear in a
caller-based sweep. The method was structurally incapable of finding it.

Still true on master 2026-07-26 — the advertiser is not among the callers.

**CORRECTION (2026-07-26, found by this thread's own cold-open review).** An
earlier draft of this file asserted "exactly two callers" on the strength of
this grep:

```
intake_dor.py:158:        if effective_admission_policy(item=item, cwd=repo_root) == _AUTO_ADMISSION:
_drive_valves.py:146:    if effective_admission_policy(item=item, cwd=repo) != "manual":
```

That was WRONG, and wrong in exactly the way this file is about. There is a
THIRD live call site, invisible to a grep for the function name:
`_dispatcher_valves.py:165` takes the predicate as an INJECTED SEAM defaulting
to it —

```python
admission_policy: Callable[..., str] = effective_admission_policy,
```

— and invokes it at `:195` under the local parameter name:

```python
if admission_policy(item=item, cwd=cwd) != _AUTO_ADMISSION:
```

A grep for `effective_admission_policy(` cannot see that call. This is D1's
own failure mode reproduced by the document diagnosing it, and it strengthens
rather than weakens the thesis: **name-based sweeps of this predicate are
unreliable in both directions** — they miss injected seams that DO call it,
and they cannot see advertisers that SHOULD call it but do not. Only a check
that binds advertiser to enforcer behaviorally is trustworthy.

**The generalizable lesson.** D1 tightened a GUARD without tightening the
matching ADVERTISER. Whenever a predicate that gates an action changes, every
surface that *offers* that action must be re-derived against the same
predicate. A caller sweep of the predicate function finds the enforcers; it
cannot find the offerers, because an offerer's bug is precisely that it does
not call the predicate. The fix must not repeat this: it needs a check that
binds advertiser and enforcer together, not another one-sided edit.

## Telemetry — the run was already flagged as non-converged

Honeycomb was UNAVAILABLE for this investigation (see
`observability-gap.md`). The local dispatch journal
(`tmp/fabro-dispatch-journal.jsonl`) carried the D1 trace:

| stage | value |
|---|---|
| `ledger-admit` | 2026-07-20T16:17:40Z, assignee `fabro` |
| `dispatch-id` | `619d4a9fbfa74527be32f9d2cb11685c` |
| `fabro-run` | exit 0, 2026-07-20T16:46:21Z |
| `review-gate-telemetry` | run `01KY053B971WKTCS98TN62C4Z0`, verdict `approve`, `review_hit_cap: false` |
| **`calibration`** | **`converged: false`, `fix_loop_count: 4`**, `dispatch_context_size: 7734` |

The calibration record shows the run took FOUR fix loops and was recorded
as **not converged**, then shipped on an `approve` review verdict. A
non-converged run landing a partial call-site sweep is exactly the shape of
this defect, and the signal was already in the journal at the time. Nothing
consumed it.

That is worth a separate question for the maintainer: a `converged: false`
calibration is currently recorded and ignored. Whether it SHOULD gate a
merge is out of scope for this thread, but it is the second-order finding
here and is deliberately not being silently dropped.

## What is NOT the cause

Ruled out explicitly so a future reader does not re-litigate:

- **`b06dbc6` "fix: extract drive human valve actions"** (2026-07-11) only
  MOVED the valve code out of `drive.py` into `_drive_valves.py`. It did
  not introduce the policy predicate.
- **`b4e926d` (qiqz6b Part B, 2026-07-22)** touched
  `_needs_attention_work_items.py`, but only to thread
  `sibling_status_lookup` for cross-repo dependency resolution. Unrelated
  to admission policy.
- **The `dispatch-claim-liveness` track is NOT responsible.** Its only
  product changes are `a869253` and `acf061c`, which together touch exactly
  one product file (`_dispatcher_dispatch_lock.py`) plus its tests. That
  session independently confirmed the guard already existed at `dfed51b`,
  before its track landed anything. Its analysis was correct in full and is
  the reason this thread exists.
