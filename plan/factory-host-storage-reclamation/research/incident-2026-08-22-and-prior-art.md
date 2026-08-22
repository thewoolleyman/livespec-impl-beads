# Factory host storage reclamation — incident of 2026-08-22 and prior art

Initial research note. Written by the `fix-hp-disk-space` session, which held the
P0 and performed the mitigation described below. Every figure here was measured
by that session directly over `ssh root@hp-xubuntu` unless attributed otherwise.

## 1. What happened

`hp-xubuntu` — this repo's DEFAULT factory (`dispatcher.default_factory: hp`) —
filled its root filesystem to **zero bytes available**. Dispatches routed there
died at stage `fabro-run` before any agent work began.

Measured 2026-08-22, before mitigation:

    /dev/sda1   458G size   435G used   0 available   100%

The presenting symptom was NOT a disk alarm. It was per-item dispatch failure:

    could not create run
    ╰─▶ Failed to persist run state: I/O error: creating run directory
        /home/cwoolley/.fabro/storage/scratch/<date>-<run-id>:
        No space left on device (os error 28)

`drive.py` exit 1, dispatcher exit 1, no fabro run created, and a phantom claim
left behind on the item. Nothing in that envelope names a HOST condition, so it
reads as a fault in the work-item.

## 2. Root cause — and why two sessions missed it

**The consumer was the containerd image store.** Docker 29 on this host uses the
CONTAINERD image store, so images live under `/var/lib/containerd`, NOT under
`/var/lib/docker`.

This is what made it hard to find, and both investigating sessions hit it from
opposite directions:

- `livespec-overseer-foreman` measured `du -xsh /var/lib/docker` = **12M** and
  eliminated Docker. That measurement was CORRECT. It was still a false negative
  for the question being asked, because the Docker root dir genuinely holds
  almost nothing on this host while the images Docker manages sit elsewhere.
- This session measured `du -sh /var/lib/docker` = **4.3G** (crossing mounts) and
  reached the same wrong conclusion. `docker system df` HUNG rather than
  answering. `du /var/lib/containerd` timed out at 280s.

What finally identified it was a **per-subtree walk**: `/var/*` first, then
`/var/lib/*`. Every sibling returned in milliseconds; `containerd` alone never
returned. **The absence of a result WAS the result.** That is the generalizable
technique here — when a whole-tree `du` times out, do not retry it with a longer
timeout; bisect it, and treat the subtree that never returns as the finding.

The store held **28 sandbox images**, tags `python-agent-*` and
`python-rust-agent-*`, versions v1.19.0 through v1.32.0, accumulated over roughly
two weeks. `docker image prune -a -f` reclaimed approximately **390G**:

    after prune:  /dev/sda1  458G size   33G used   402G available   8%

Nothing had ever pruned them, and nothing watched the disk.

## 3. Prior art — and two claims it makes that this incident disconfirms

A ledger scan (all statuses, 665 items) found two directly-governing items.
Both were read in full, including comments.

### `bd-ib-il35` — "Research and implement garbage collection for fabro factory host local state" (backlog, P2, filed 2026-08-17)

This is the correct parent for the durable work and it is **still open**. It
already scopes the problem to every factory host, names both accumulation layers
(Docker's cache and `~/.fabro/storage`), and asks the right research questions —
notably whether fabro exposes native retention config before a bespoke cleanup
script is assumed, and what is safe to reclaim without breaking an in-flight run.

Its measurements were taken on the **vps** host and reported
`docker system df` showing 116.8GB of containers at 99% reclaimable. **This
incident is the same defect class arriving on hp five days later, unfixed.**

One refinement this incident adds: the item frames the Docker layer through
`docker system df`. On hp that command HANGS when the store is large, and the
directory it implicates (`/var/lib/docker`) is not where the bytes are. Any
mechanism this plan builds must target the containerd store explicitly and must
not depend on `docker system df` returning.

### `bd-ib-gr9f` — "The fabro factory host (hp) intermittently has no room for a run directory" (backlog, P2, filed 2026-08-22)

Filed hours before this incident, by the maintainer, then **corrected by its own
author** in a comment at 01:28Z. Two claims in that correction are disconfirmed
by direct measurement, and both pushed in the direction of under-reacting:

1. **"The condition is INTERMITTENT and threshold-shaped, not a persistent
   outage"** and **"nothing needs reclaiming by hand right now."**
   *Disconfirmed.* Roughly an hour later the filesystem measured 435G used and
   **0 bytes available**, and clearing it required reclaiming ~390G by hand.
   The correction's evidence — a run completing successfully at 01:18Z — is real,
   but it is equally consistent with a few gigabytes transiently freeing at the
   margin while the 390G accumulation sat untouched underneath. A completed run
   proves the disk had room for ONE run directory at that instant; it does not
   prove the accumulation resolved. The original filing's instinct was right and
   the correction over-corrected.

2. **The implied consumer is `~/.fabro/storage`.** The item reasons at length
   that "fabro run state persists per run" and that "a host serving several repos
   at this fleet's dispatch rate will fill." *Disconfirmed as the cause.*
   `~/.fabro/storage` measured **219M** total (objects 163M, scratch 57M), and
   `~/fabro-dumps` 13M. Fabro was the REPORTER of the error, not the consumer of
   the space. A retention policy tuned to the `fabro dump` recovery window — which
   the item makes its central design constraint — would have reclaimed essentially
   nothing here.

Both corrections matter for THIS plan because `bd-ib-gr9f` is where a future
session would look first, and following its analysis would aim the fix at the
wrong subsystem.

What in `bd-ib-gr9f` **does** survive and remains owed work: no headroom
telemetry on either factory host; no dispatcher preflight refusal (the dispatcher
already refuses before sandbox launch for an exhausted credential and names the
condition — a factory with no room deserves the same); and the phantom claim left
behind by an ENOSPC dispatch failure.

## 4. Unmanaged hotfix currently live on hp-xubuntu

Incident mitigation was applied **directly to the host, outside any repo**. This
is deliberate scope for a P0 and is deliberately called out here because it is
now unmanaged state that this plan must formalize or replace. It exists on ONE
host, is in no repository, is covered by no test, and would be lost on a rebuild:

    /etc/systemd/system/docker-prune.service   + .timer
        daily, RandomizedDelaySec=30m, Persistent=true
        container prune until=24h; image prune -a until=72h; builder prune -a
    /etc/systemd/system/disk-guard.service     + .timer
        every 15m; if / available < 40G -> aggressive prune, journal vacuum,
        apt clean; logs "LOW DISK" at daemon.err via logger
    /usr/local/sbin/disk-guard.sh

Both are enabled and armed. `disk-guard` was executed once as a test and
correctly no-op'd at exit 0. Images held by a RUNNING container are never removed
by `docker image prune`, which is why the initial reclamation was safe to run
with eight dispatches live.

The `72h` and `40G` values were chosen under incident pressure against the
observed accumulation rate (~390G over ~2 weeks ≈ 28G/day, implying a steady
state near 84G at a 72h horizon). **They are not derived from the `fabro dump`
recovery window**, which is the constraint `bd-ib-gr9f` correctly identifies as
governing. Treat them as a stopgap, not as the answer.

## 5. Also provisioned during the incident

`/dev/sda` had **1396 GiB unallocated** — the root filesystem had only ever been
given 466 GiB of an 1863 GiB disk. A new `sda3` was created across that free
space, ext4, label `data`, mounted at `/data` via an fstab UUID entry. Per the
maintainer it is deliberately GENERIC — large storage for containers, LLM model
files, or anything else — and is not container-specific.

A separate external Toshiba USB disk was wiped by the maintainer during the
incident. It is unformatted and unused; the internal free space made it
unnecessary.

**Not yet done:** relocating the container store onto `/data`. That requires
stopping `docker` and `containerd`, which kills every in-flight run, so it is
gated on a factory-idle window. Owned by the `fix-hp-disk-space` session, which
is watching for that window.

## 6. Open questions for this plan

1. **Does fabro expose native retention/TTL config?** `bd-ib-il35` asks this and
   it is still unanswered. It determines whether the fabro-storage layer needs a
   bespoke reaper at all. Answer it before designing one.
2. **Where does the mechanism live?** A per-host systemd timer (what the hotfix
   is), versus a periodic step in the orchestrator's own dispatch loop mirroring
   the existing post-merge janitor machinery. `bd-ib-il35` poses this explicitly.
   A repo-owned mechanism is testable and reaches every host; a host-owned timer
   works when the orchestrator is not running.
3. **How does a host-level mechanism get DEPLOYED and stay deployed?** The
   `fabro-server` unit precedent is `thewoolleyman/fabro-hosts`
   (`services/fabro-server/`, one unit template plus a per-host env file, with an
   installer that refuses to apply one host's values on another). That repo is the
   natural home for a reclamation unit, and it already solved the two-host
   divergence problem this would otherwise reproduce.
4. **What is the correct retention horizon?** Must be derived from the `fabro
   dump` recovery window for run state, and separately from image re-pull cost for
   the containerd store. These are two different layers with two different
   horizons; the hotfix collapses them into one number.
5. **Is `vps` in the same state?** `bd-ib-il35` measured 116.8GB reclaimable there
   on 2026-08-17 and nothing has reclaimed it since. NOT re-measured by this
   session. Must be measured, not assumed.
6. **Preflight and telemetry**, per `bd-ib-gr9f`: a dispatcher refusal that names
   the condition instead of a failed run plus a phantom claim, and free-space
   telemetry on both factory hosts so this is observed rather than discovered.
7. **Does any of this require a specification change?** Free-space headroom as a
   dispatch precondition would sit alongside the existing fabro runtime
   constraints in `SPECIFICATION/constraints.md`; a telemetry obligation would sit
   in the non-functional requirements. To be determined before children are filed.

## 7. Method note

The prior-art scan that surfaced both governing items cost one ledger listing
over all statuses plus a keyword filter. `bd-ib-il35` had been open for five days
describing exactly this defect, on another host, with the research questions
already framed. Neither investigating session found it during the incident —
both went straight to measurement. The scan was run only when this thread was
opened, at which point the mitigation was already applied and one design decision
(the 72h/40G constants) had already been made without the constraint
`bd-ib-gr9f` supplies.
