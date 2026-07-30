# Why the client-side dispatch cap goes, and what replaces it

Durable reasoning for `plan/retire-host-dispatch-cap/`. Everything here was
MEASURED on 2026-07-30 unless labelled otherwise. Where an earlier belief was
falsified, the falsification is kept rather than the belief — several of the
wrong turns in this area were caused by confident claims that nobody had
checked.

## 1. There are two limits, at two layers, and only one of them is real

| Layer | Limit | Value | Enforced by |
|---|---|---|---|
| Factory | `server.scheduler.max_concurrent_runs` | 5 (raised to 10, 2026-07-30) | the fabro server daemon — the process that owns runs |
| Client | `host_dispatch_cap` | 2 (4 in one repo) | short-lived dispatcher processes |

The fabro server is a long-running daemon — measured `pid 3616318` on
`127.0.0.1:32276`, up 267 h. It is machine-level: not owned by any repo, not
started by the Dispatcher, not under systemd. Its concurrency limit lives in
`~/.fabro/settings.toml` under `[server.scheduler]`, which is host-scoped
configuration for a host-scoped value.

## 2. The client cap never reaches the factory

`resolve_host_dispatch_cap` is called at exactly two sites
(`_dispatcher_run_commands.py:166`, `_dispatcher_loop_command.py:164`), both
feeding `claim_dispatch_admission_mutex(cap=…)`. The value is used inside the
dispatcher process and discarded. It is absent from the `fabro run` argv —
observed live:

```
fabro run /tmp/fabro-run-config-overseer-4xfmez.3.toml --goal-file … \
  --input review_fix_visit_cap=4 \
  --input merge_on_review_cap_outcome=__merge_on_review_cap_disabled__
```

`review_fix_cap` crosses the boundary. `host_dispatch_cap` does not. It is a
client-side pre-check, not a factory setting.

## 3. The gauge cannot tell repos apart, so the cap starves rather than shares

`_parse_in_flight_run_ids` filters only on status kind. It never reads
`source_directory` or `repo_origin_url`, both of which are present in the same
`fabro ps` JSON. So every repo's threshold is applied to a count that includes
every other repo's runs.

Measured, with `livespec-overseer` at 4 and everyone else at 2:

```
HOST-WIDE in-flight: 3   (all 3 from livespec-overseer)
orchestrator repo: cap 2 vs host-wide 3 -> REFUSED
overseer repo    : cap 4 vs host-wide 3 -> admitted
```

The orchestrator repo was refused with **zero runs of its own** in flight.

The dynamic is worse than unfairness. A repo admits while the host count is
below its own number, so overseer had admission windows at 0/1/2/3 and the
orchestrator only at 0/1 — and every time the host drained toward 1, overseer
refilled it and shut the window again. The lower-capped repo is locked out of a
band it can never enter, permanently, even when it asks first.

`contracts.md` concedes the model in its own words: *"the host is bounded at 2
only while every dispatching repo commits (or defaults to) 2."* That is an
honor system, and it held only while nobody used the knob. The first real use
of the knob broke it the same day.

## 4. What fabro does instead, and why it is better

From fabro's documented run lifecycle and changelog:

> Additional start-requested runs wait as `runnable` before moving to
> `starting` … a background scheduler promotes `runnable` runs to `running` in
> **FIFO order**, up to the concurrency limit.

Three properties the client cap does not have: it **queues instead of
refusing**, it is **FIFO across all repos** (so first-come genuinely means
first-served), and it is enforced by the process that actually knows what is
running.

Observed in production before we understood it — a queued run:

```
01KYRRQTY9MER3  runnable  age=5.6m  wall=0.0m  overseer-4xfmez.4
```

## 5. The mechanism was built for a problem that does not exist

The cap descends from `bd-ib-sd8o`, filed after a concurrent dispatch appeared
to cause a `bwrap: No permissions to create new namespace` failure. Its own
diagnosis leg, `bd-ib-tyxzhv`, falsified that:

- the bwrap `EPERM` is a **host sysctl constant**
  (`kernel.apparmor_restrict_unprivileged_userns=1` +
  `…_unconfined=1`, kernel 6.17.0-40), reproduced in a **single** container
  under every security configuration — *"concurrency was temporal
  coincidence"*;
- the `--network host` port-collision premise was **false**: `allow_all` maps
  to the docker bridge, so sandboxes already hold per-run network namespaces
  and *"the host-netns port/namespace collision class does not exist in the
  current engine."*

`contracts.md` nonetheless calls 2 "the empirically verified safe level", which
overstates that evidence: 2 was the level *exercised*, never a level at which 3
was shown to fail. No contended host resource was ever found.

## 6. History — the number only ever went up

| Era | Limit | Mechanism |
|---|---|---|
| before 2026-07-23 | none mechanically | prose "sequential mandate" doctrine only |
| 2026-07-23 → 07-24 | 1 | interim binary admission mutex (`bd-ib-sd8o` deliverable c) |
| 2026-07-24 → 07-30 | 2 | counting cap, spec v047, `a84182e` |
| 2026-07-30 | 4, one repo | `2c7465b` (to be reverted) |

`DEFAULT_HOST_DISPATCH_CAP` was introduced in a single commit and its value
never changed. The key has never appeared in any repo's `.livespec.jsonc` in
its entire life except the 2026-07-30 override.

**Correcting a claim made mid-investigation:** it was stated that before the cap
there was "no mechanical limit" and that observed peaks of 5 showed unbounded
concurrency. That was wrong. `max_concurrent_runs` was 5 the whole time, which
is exactly why measured peaks reached 5 and never 6. The 2026-07-24 change did
not introduce a limit; it introduced a *second, lower* one.

## 7. Resource evidence

The machine is not the constraint and never was. Per running sandbox: **under
one core** (measured 74.66% and 4.48% of a single core) and **~300 MiB** RSS. A
run is dominated by network wait on LLM inference. Against 18 cores and 56 GB
available, memory permits ~180 sandboxes. Host load (~31, 1.7× oversubscribed)
comes from the interactive session fleet, not from sandboxes.

The real ceilings are elsewhere: the shared Anthropic credential, and
same-repo merge/rebase contention — which is what `wip_cap` bounds.

## 8. One open question, deliberately not blocking

Do PARKED fabro runs occupy a scheduler slot? livespec's gauge explicitly
excluded them (`_TERMINAL_OR_PARKED_KINDS` includes `blocked`) on the reasoning
that parked runs never block work. One observation suggests fabro may disagree:
at a moment when 3 runs were `running` and 2 were `blocked` — totalling exactly
`max_concurrent_runs` — a 6th sat `runnable` for 5.6 minutes.

That is a single uncontrolled observation, not a finding. It does not affect
the decision to delete (the client cap's exclusion of parked runs was never
what governed the scheduler), but it does affect what operators should expect
once the scheduler is the only authority. Worth confirming; not worth blocking
on.
