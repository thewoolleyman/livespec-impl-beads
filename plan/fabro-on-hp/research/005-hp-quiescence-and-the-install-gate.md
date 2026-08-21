# fabro-on-hp — what "quiesce the factory host" actually costs

**Written 2026-08-21.** `bd-ib-l3nptz.14` was one command from done for four
days. The command took ten minutes to run and about five hours to become
*runnable*, and none of that delay was the install. This note records why, so
the next person who needs a factory host quiet does not rediscover it — and
they will need one, because `.10` step (4) and `.11` step (5) both stop a
`fabro` server.

It supersedes nothing in `001`–`004`.

## The gate is stricter than "the machine is busy"

`services/fabro-server/install.sh:68-74` (`require_quiet_server`) refuses when:

```bash
running="$(... "${FABRO_BIN}" --json ps)"
if [[ "$(jq 'length' <<<"${running}")" -ne 0 ]]; then
    echo "ERROR: Fabro has active runs; refusing to interrupt them" >&2
```

`jq 'length'` over `fabro --json ps`. **That count does not distinguish a run
doing work from a run parked on a human gate.** Measured with the installer's
own expression on 2026-08-21:

```
fabro --json ps | jq 'length'  ->  2
statuses: {"kind":"running"}
           {"kind":"blocked","blocked_reason":"human_input_required"}
```

A `human_input_required` run does not time out and does not self-clear — it
persists **by design** until a person answers it. So the precondition is not
"hp is idle"; it is "hp is idle *and* nobody is waiting on a question". The
first is a load property and the second is not.

**Consequence, measured.** 90 polls at 45s intervals, 13:02:03Z–14:09:50Z: the
run count never fell below 2 (39 polls at 3, 51 at 2) while hp's load average
was **1.36**. An idle 16-core machine, uninstallable for 67 minutes. Holding
the `livespec-console-beads-fabro` dispatcher — ordered by the maintainer at
12:33Z — drained console's runs to zero and did not help, because no amount of
dispatcher holding clears a parked gate. The install became possible only after
a human removed the parked run.

### Do not "fix" this by narrowing the guard

The obvious shortcut is counting only `status.kind == "running"`. It was
considered and refused. The guard is fail-closed protection against
interrupting work; a blocked run still holds its sandbox and its workspace, and
restarting under it may destroy recoverable state. Narrowing it is a real
safety decision about the installer, not a workaround to reach for while trying
to land an unrelated item. If it is ever wanted, it earns its own reviewed PR.

## The arrival process is not forecastable, in either direction

Once the gate cleared, the remaining question was when hp would next read zero.
**Three predictions were made and all three were wrong**, which is the useful
part of this note.

1. A forecast built from hp's own history — overseer run durations (median
   20.9m, mean 25.4m, n=15) and post-hold inter-arrival gaps (64m and 17m, mean
   40m) — predicted a window at **14:32–14:40Z**. Arrivals closed it before it
   opened.
2. The same session then stated flatly that the armed watcher would "expire
   without firing". It fired **33 minutes before its horizon**.
3. Two independent seats concluded a chance zero would not occur at all while
   the overseer tenant dispatched uncoordinated. One occurred within half an
   hour.

### Why the historical model could not work

It was wrong **in kind, not in parameter** — no better estimate would have
rescued it. Two runs (`01M0JBMMKJDJ`, `01M0JBMXZK7J`) started in the **same
second**, an event a fitted inter-arrival process assigns essentially zero
probability. These are batch submissions, not a stream.

The falsifier was already in the data: the pre-hold **minimum gap was 2.7
minutes**. It was read past.

A gap-fitted rate is also structurally blind to two things no amount of hp-side
history reveals:

- **how much work is queued** — the overseer tenant's ready set was 33 items
  (7 P1) and not draining that day;
- **how many independent actors can start more** — **at least four** sessions
  in that repo dispatch to hp on their own initiative, so no single dial, not
  even its foreman's, turns arrivals off.

One message to the tenant that *owns* the arrivals answered both, and inverted
the recommendation. Ask the owner before modelling the queue.

### The trap that made the bad model persuasive

The post-hold gaps really did stretch to a 40m mean. That number was real; the
causal reading attached to it — "the hold is slowing the arrival process" — was
not. It was a sampling artifact of a bursty hand-driven queue. This is the
shape the fleet's verification discipline already warns about: **the number
survives every check you run on the number**, because the error is in the
inference, not the measurement.

## What actually worked

An **armed watcher**, not a forecast. A loop that polls every 45s and, at the
first zero, places the rendered `settings.toml` and runs the installer *in the
same breath*:

- A human loop measures, then acts seconds later; hp accepts arrivals
  continuously, so the hand-timed version has a race the automated one does not.
- If a run starts between the measurement and the install, `require_quiet_server`
  refuses and nothing happens. **The guard is the backstop** — which is exactly
  why it must not be narrowed.
- It re-reads `fabro ps` inside the same ssh immediately before mutating, so the
  gate is satisfied on a fresh reading rather than on the poll that triggered it.

It fired at iteration 54, **14:56:26Z**, after an approach of 3 → 2 → 1 → 1 → 0
across 14:53:23Z–14:56:26Z, and discharged `.14`, `.15` and `bd-ib-wdns6b` in
one restart. Its justification was that nobody could forecast this — which is
the reasoning to keep, rather than any of the three forecasts.

## Checklist for the next host-quiescing operation

1. Read `fabro --json ps | jq 'length'` — the installer's own expression, not
   the table.
2. If any entry is `blocked`, find its owner and get the gate answered or the
   run removed. Dispatcher holds will not touch it.
3. Ask the tenant that owns the arrivals what its queue depth is and how many
   sessions dispatch. Do not infer it from arrival history.
4. Arm a watcher rather than predicting a window; let the guard be the backstop.
5. Stage everything first — a restart is one shot, so place `settings.toml`
   before the install so a single restart carries every change.
