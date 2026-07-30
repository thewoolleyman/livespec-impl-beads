# Retire the client-side host dispatch cap — handoff

> Cold-open handoff. It assumes you have read nothing and remember nothing, and
> that you may be a different model than the session that wrote it. Everything
> load-bearing is either stated here or on the read-first chain in §2. Chat
> history is NOT a source of truth.

## 1. The goal, in the maintainer's words

> Just kill the tech debt that duplicates `max_concurrent_runs` (poorly) — that
> is the goal of this plan.

Nothing in this thread is exploratory. The design is settled (§3). Your job is
to route the filed work through the factory, not to redesign it.

## 2. Read-first chain

1. This file.
2. `plan/retire-host-dispatch-cap/research/why-the-client-gate-goes.md` — the
   measured evidence: the two-layer duplication, why the per-repo threshold over
   a host-wide count starves rather than shares, what fabro's scheduler does
   instead, and the falsified premise the mechanism was built on.

Ledger status is READ from the ledger, never from this file. Compose it with
`/livespec-orchestrator-beads-fabro:list-work-items` or `:next`. This handoff
deliberately carries no checkbox queue.

## 3. DECIDED — do not re-open, do not re-litigate

Each of these was settled by the maintainer on 2026-07-30. Re-opening any of
them is out of scope for this thread.

| Decision | Detail |
|---|---|
| Delete the client gate **entirely** | Not raise it, not make it per-repo-aware, not keep a thin pre-check. `DEFAULT_HOST_DISPATCH_CAP`, the `host_dispatch_cap` key, the two-gauge admission mutex, the slot files, the spec section, the scenarios, and the config-key registry entry all go. |
| `wip_cap` stays **exactly** as it is | Value 5, per-repo, `per_item_override: false`, and the `enforce_cap=False` bypass on `dispatch --item` is **kept**. The maintainer's reason: 5 bounds single-repo merge/rebase conflicts. **This is intentional. Do not "fix" the bypass and do not raise the number.** |
| A single repo therefore tops out at 5 concurrent runs | Even with the host at 10. Known and accepted — the remaining host capacity is reachable only when a second repo dispatches, and `dispatch --item` is the escape hatch. |
| Host throughput is fabro's job | `server.scheduler.max_concurrent_runs`, raised 5 → 10 in `~/.fabro/settings.toml` on 2026-07-30. **The config edit is already landed.** The server restart that applies it is owned by the maintainer in a separate session — it is NOT this thread's work and must not be attempted here. |
| No per-repo denominator is added | Counting only a repo's own runs would idle the machine whenever work concentrates in one repo. Explicitly rejected. |
| Thread and code live here | `livespec-orchestrator-beads-fabro`. This repo's `livespec-overseer` counterpart is one config revert, filed separately. |

## 4. Ledger anchors — ids only, status never copied

- Epic **`bd-ib-vmve`** — this thread's anchor.
  - **`bd-ib-vmve.1`** — spec: remove the `contracts.md` section and its four
    `scenarios.md` scenarios via `/livespec:propose-change` →
    `/livespec:revise`. No blockers. **Spec-change tier — design-human-gated,
    never auto-approved.**
  - **`bd-ib-vmve.2`** — delete the code, the config key, and the tests.
    **Blocked by `.1`** (edge recorded in the ledger): spec is ratified before
    product code.
  - **`bd-ib-rhap`** — SUPERSEDED, do not work as written. Held open only so the
    epic's history shows which question was retired. Close
    `no-longer-applicable` when `.2` lands.
  - **`bd-ib-r6o0`** — MOOTED (it polishes the section `.1` deletes). Close
    `no-longer-applicable` when `.1` lands.
- **`overseer-n11`** — filed in the **`livespec-overseer`** tenant, not this one:
  revert that repo's `host_dispatch_cap: 4` override (PR #305, `2c7465b`). Not
  blocking; landable any time. **Never implement it from this repo.**

## 5. Next action

**Route `bd-ib-vmve.1` through the spec lifecycle** — `/livespec:propose-change`
against this repo's `SPECIFICATION/`, then `/livespec:revise` to ratify. It is
spec-change tier, so a human accepts it; it is not auto-approved and it is not
factory-dispatched.

**Then dispatch `bd-ib-vmve.2` through the factory** once `.1` is ratified:

```
/livespec-orchestrator-beads-fabro:drive --action impl:bd-ib-vmve.2
```

The `drive` operation (action `impl:<id>`) or the Dispatcher drain is **THE**
implementation path for `.2`. Do **not** build it in-session with the
`implement` operation. If the item is not in the ready set, the sanctioned
admission act is the human valve `drive --action move:bd-ib-vmve.2:ready` —
surface it, never self-admit.

## 6. What "done" looks like

The Dispatcher performs no host-concurrency check at all. A dispatch attempted
while the machine is busy proceeds, and its run waits in fabro's scheduler as
`runnable` until promoted FIFO — instead of being refused with exit 3. `wip_cap`
is untouched and is the only concurrency control the Orchestrator still owns.

## 7. One open question — flagged, deliberately not blocking

Do PARKED fabro runs occupy a scheduler slot? livespec's deleted gauge excluded
them by design; one uncontrolled observation suggests fabro may not (3 `running`
+ 2 `blocked` = exactly `max_concurrent_runs`, with a 6th run sitting `runnable`
for 5.6 minutes). It does not affect the deletion — the client cap's exclusion
never governed the scheduler — but it changes what operators should expect once
the scheduler is the sole authority. Confirm opportunistically; do not block
`.1` or `.2` on it.

## 8. Hazards this thread already hit

- **`bd create --deps "blocked-by:<id>"` HANGS.** It is not a valid dependency
  type; the create never returns and never writes. Valid forms are
  `discovered-from:<id>` and `blocks:<id>`, or a bare id. Add edges after
  creation with `bd dep <blocker> --blocks <blocked>`.
- **`bd` writes to this tenant warn** `auto-backup failed: register backup
  remote: command denied to user 'livespec-orch-beads-fabro'@'%'`. The write
  still succeeds. Pre-existing, unrelated to this thread, and not yet filed.
