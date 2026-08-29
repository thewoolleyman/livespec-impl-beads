# SPIKE bd-ib-bdcmok.1 — fabro retention surface, and what vps is actually holding

Measured 2026-08-22 by the `factory-host-storage-reclamation` session. READ-ONLY:
nothing was pruned, deleted, or reconfigured on either host. Every prune
invocation below was a DRY RUN (`fabro system prune` defaults to dry-run; `--yes`
was never passed).

Companion to `incident-2026-08-22-and-prior-art.md`, which covers the hp incident.
This note answers the two questions that gate `bd-ib-bdcmok.2`, `.3` and `.4`.

**Headline: both answers came back different from what the plan assumed, and the
second one is different in kind.** fabro DOES ship a prune command the plan
recorded as absent — and it is worth ~0.1 GB. vps is at 84% for reasons that have
nothing to do with containers or fabro: 250 GB of accumulated git worktrees, which
no mechanism this plan had scoped would touch.

---

## Q1 — Does fabro expose native retention/TTL configuration?

**Two-part answer. A retention COMMAND exists and the plan's prior art says it does
not. A retention CONFIG does not exist, on the pinned build or on a build 56 minor
versions newer.**

### Q1a — `fabro system prune` EXISTS on the pinned build

Measured against the pinned host binary, `fabro 0.254.0 (8de6611 2026-07-30)`:

    $ ~/.fabro/bin/fabro system --help
    Commands:
      info    Show server runtime information
      prune   Delete old workflow runs
      df      Show disk usage
      events  Stream run events from the server
      repair  Inspect and repair durable server data

`fabro system prune` takes `--older-than <DURATION>` (default 24h when no explicit
filter is set), `--before <YYYY-MM-DD>`, `--workflow <substring>`,
`--label <K=V>` (repeatable, AND semantics), and `--orphans` (directories with no
matching durable run). It is **dry-run by default**; `--yes` is required to delete.

**It accepts `--server`, so it prunes a REMOTE factory.** So does `fabro system df`.
Both were exercised against hp from vps in this spike and returned in seconds. This
is a significant design input for `bd-ib-bdcmok.2`: the fabro layer needs no host
login, no per-host unit, and no bespoke reaper — one scheduled caller with a
`--server` list reaches every factory.

**This disconfirms a recorded claim in `bd-ib-il35`**, which states that
`fabro --help` and `fabro server --help` show no prune/gc subcommand and that
`fabro rm` removing runs by id is the only route. `fabro rm` is not the only route.
The reason the earlier scan missed it is worth recording, because it is the
"instrument that cannot return a hit" trap from `AGENTS.md` in its purest form:
`fabro --help` DOES list the parent command, but as

    system      System maintenance commands

That line contains neither "prune" nor "gc" nor "retention". A keyword scan of the
top-level help — the natural way to answer "is there a prune subcommand" — cannot
match it, and returns a clean, plausible, wrong negative. The discriminating move
is to expand every subcommand's own help, not to grep the index.

### Q1b — No declarative retention/TTL CONFIG exists

Checked four surfaces; all negative:

1. **Effective settings.** `fabro settings --json` dumped and walked
   programmatically over every key at every depth for
   `reten|ttl|prune|gc|expir|cleanup|max_age|age|keep|purge`. The only hits were
   substring false positives (`agent` contains "age", `storage` contains "age").
   The `server.server` block is `listen, api, web, auth, sandbox, storage,
   artifacts, slatedb, scheduler, logging, integrations` — no retention member.
2. **On-disk TOML.** `~/.fabro/settings.toml` plus all five
   `~/.fabro/environments/*.toml`: no retention-ish key in any of them.
3. **Server surface.** `fabro server --help` exposes only
   `start|stop|restart|status` — no retention option.
4. **Source, at a build far newer than the pin.** `/data/projects/fabro` is at
   `v0.310.0-nightly.2-1-g3b3781888`. A search of `lib/` and `apps/` for
   `retention|auto_prune|prune_after|max_age|gc_interval` across `*.rs` and
   `*.toml`, excluding tests, returns only: a comment in a Bedrock provider
   catalog, a demo-fixture string, HTTP cookie `max_age` values, and
   `LOG_RETENTION_DAYS: u32 = 7` in the CLI's own **log** rotation
   (`fabro-cli/src/logging.rs` — CLI logs, not run storage). Nothing for run
   storage. A search for `system_prune|SystemPrune` outside tests finds no
   server-side scheduler wiring: prune is a manual command with no timer behind it.

**Answer, stated plainly as the item asks:** on the pinned 0.254.0 build there is
**no native retention or TTL configuration** for `storage/scratch` or
`storage/objects/artifacts`, and **a v0.310 nightly does not add one either**. So
the deferred modernization (`bd-ib-6qu`) would not supply this, and D3's contingency
("if no retention surface exists, the answer is a bespoke external reaper") is
half-right: **a scheduler is still required, but the reaper itself must NOT be
bespoke — it should invoke `fabro system prune --server <factory>`.**

#### Q1c — And it barely matters, which is the more important finding

Dry runs, both factories, 2026-08-22:

| host | `fabro system df` runs | logs | db & artifacts | `prune --older-than 7d` dry run |
|---|---|---|---|---|
| vps | 2195 runs, 121.5 MB (99% reclaimable) | 129.0 MB | 179.3 MB | **618 runs, 103.9 MB freed** |
| hp  | 296 runs, 52.6 MB (99% reclaimable) | 2.0 KB | 167.7 MB | **No matching runs to prune** |

The entire fabro storage layer is ~430 MB on vps and ~220 MB on hp. Pruning seven
days of it on the fuller host reclaims **103.9 MB against a 568 GB usage figure —
0.018%.**

This **extends the incident note's §3 finding from hp to vps**: `bd-ib-gr9f` reasons
that "fabro run state persists per run" and that "a host serving several repos at
this fleet's dispatch rate will fill". Measured on both factories, it does not.
Fabro is the reporter of ENOSPC, never the consumer. **A retention horizon derived
from the `fabro dump` recovery window — which `bd-ib-gr9f` makes its central design
constraint and which requirement carrier R4 inherits — governs a layer that is three
orders of magnitude too small to matter.** R4 should be narrowed accordingly: the
`fabro dump` window is real and should still bound the fabro prune horizon, but it
is a correctness constraint on a trivial layer, not a sizing constraint on the
problem.

---

## Q2 — What is vps actually holding?

### Q2a — First: this session was already ON vps

`ssh root@vps` returns `Permission denied (publickey)`, as do
`thewoolleyman@`, `ubuntu@` and `cwoolley@`. That is not an access problem. This
repo's primary checkout runs on the vps host itself:

    $ hostname
    vmi3006760
    $ tailscale status --json | .Self
    HostName: vmi3006760   DNSName: vps.perch-rudd.ts.net.   IP: 100.89.189.118

`tailscale status` lists the local node first, and its row (`vps`) carries no
connection descriptor — which reads exactly like an idle peer. A successor
measuring vps should measure locally. hp is the remote one
(`ssh root@hp-xubuntu`, which works).

### Q2b — Root filesystem

    /dev/sda1   678G size   568G used   110G available   84%     (vps, 2026-08-22)
    /dev/sda1   458G size    34G used   401G available    8%     (hp,  same day)

hp is healthy because the unmanaged hotfix is holding. **vps has no reclamation
mechanism of any kind** — verified directly: no `docker-prune` or `disk-guard`
unit files in `/etc/systemd/system/`, no matching entry in `systemctl
list-timers --all` (the only cleanup timer is stock `systemd-tmpfiles-clean`), no
root crontab entry, and nothing in `/etc/cron.d` or `/etc/cron.daily` beyond
distro defaults. The same query on hp returns `disk-guard.timer` (every 15m) and
`docker-prune.timer` (daily). **The hotfix's single-host scope is now measured, not
assumed.**

Note for `bd-ib-bdcmok.2`: vps carries `/usr/local/sbin/vps-restic-backup`,
`arq-vps-root-snapshot` and `arq-vps-docker-volume-snapshot`. Any reclamation
placed here must not race the backup window.

### Q2c — The hp diagnosis does NOT transfer

| | hp-xubuntu | vps |
|---|---|---|
| Docker version | 29 | **28.2.2** |
| Image store | **containerd** (`/var/lib/containerd`) | **overlay2** (`/var/lib/docker`) |
| `docker system df` | **hangs** | **returns in seconds** |

So the incident note's central measurement trap — "the bytes are under
`/var/lib/containerd`, and a correct small reading of `/var/lib/docker` falsely
exonerates Docker" — **is an hp-specific artifact of Docker 29's containerd store,
and is false on vps.** Requirement carrier R1's wording ("reclaims the containerd
image store on every factory host") describes a store that exists on one of the two
hosts. R1 needs restating in store-agnostic terms.

The trap that DOES generalise, and that bit this spike too: `du` run as an
unprivileged user **silently skips** `/var/lib/docker` (mode `drwx--x---`, root).
`du -xd1 -h /var/lib` as `ubuntu` returns `460M` with no `docker` row and no error.
Measure the container store under `sudo`.

### Q2d — Docker on vps, measured

    $ docker system df
    TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
    Images             10        7   6.885GB   3.727GB (54%)
    Containers         19        1   32.7GB    32.7GB (100%)
    Local Volumes       0        0   0B        0B
    Build Cache         1        0   0B        0B

**`bd-ib-il35`'s vps figure of 116.8 GB of containers at 99% reclaimable, measured
2026-08-17, is now 32.7 GB.** Its accompanying claim that "nothing has reclaimed it
since" is therefore disconfirmed as stated — something reduced it, and this spike
did NOT establish what (no prune timer, no cron entry, no root crontab). Candidates
not investigated: manual operator action, or container removal by whatever creates
them. Flagging rather than guessing.

The item's direction was still right: **32.7 GB of stopped containers is 100%
reclaimable and nothing is scheduled to reclaim it.** It is simply not the reason
vps is at 84%.

### Q2e — The actual consumer on vps: 250 GB of git worktrees

Bisected per subtree, treating a non-returning subtree as the finding:

    /home/ubuntu/.worktrees   250G     <- dominant
    /data/projects            122G      (of which /data/projects/fabro/target = 98G)
    /tmp                       23G      (of which /tmp/claude-1000 = 16G, agent scratchpads)
    /srv                       19G      (entirely /srv/arq-vps-root-snapshot, a backup)
    /nix                      9.1G
    /usr                      8.7G
    /var                      8.6G      (+ /var/lib/docker, root-only; see Q2d)
    /home/ubuntu/.fabro       1.3G
    /opt                      890M
    /boot                     243M

Two of those are worth calling out separately from the worktree finding, because a
reclamation mechanism must not touch either blindly: `/srv` is 19 GB of backup
snapshot, and `/tmp/claude-1000` is 16 GB of live agent scratchpad directories —
this session is writing into one of them right now.

`~/.worktrees` holds **542 worktree directories**, oldest dated 2026-06-24 (two
months) and newest today. Per repo:

    livespec-console-beads-fabro   113G
    fabro                          102G
    livespec-overseer               17G
    livespec                       9.0G
    livespec-orchestrator-beads-fabro  3.5G
    livespec-dev-tooling            2.8G
    openbrain                       2.1G

The bytes are per-worktree **build artifact trees**, not source:

    /data/projects/fabro/target                        98G
    ~/.worktrees/fabro/factory-integration             71G
    ~/.worktrees/fabro/otlp-span-export                25G
    ~/.worktrees/fabro/instrument-v0254               7.3G
    ~/.worktrees/livespec-console-beads-fabro/docs      16G

Two fabro build trees alone — `/data/projects/fabro/target` at 98 GB and the
`factory-integration` worktree at 71 GB — account for **169 GB, ~30% of everything
used on this disk**, and are a direct cost of the repo's own "build the pinned fork"
instruction.

The worktrees are also not being cleaned up as the mutation protocol requires. The
first pass at this counted directories under one repo's worktree root and reported
"16 orphans in this repo alone", then called the rule violated "at fleet scale".
That was an extrapolation from a population of one, which this repo's verification
discipline does not permit, so it was replaced with a measurement.

**Fleet-wide, measured 2026-08-22T03:57:41Z** by the defining property of a
worktree — a `.git` entry — rather than by counting directories, and compared
against what every clone under `/data/projects` actually registers:

    worktrees on disk under ~/.worktrees      575
    registered by a clone in /data/projects   505
    clones scanned                             42
    ORPHANS (on disk, registered by nothing)   70   = 6.4 GB

    by repo:  livespec-overseer 35 | livespec-orchestrator-beads-fabro 17
              livespec-console-beads-fabro 14 | livespec-dev-tooling 2

`AGENTS.md` says "Do not leave orphaned worktrees" and treats leaving dirty state
as a failure of the workflow. Seventy orphans across four of forty-two clones is a
real and ongoing violation of it — but it is a **compliance** finding, not a
capacity one, and conflating the two would size the fix against the wrong
population.

**That is the correction that matters for `bd-ib-bdcmok.6`'s design.** The 70
orphans hold **6.4 GB** of the **244 GB** under `~/.worktrees` — **2.6%**.
Reclaiming every orphaned worktree on the fleet, perfectly, would move vps from
110 GB free to about 116 GB. **The capacity problem is build artifacts inside
LIVE, REGISTERED worktrees — roughly 238 GB of it — which is the harder and more
dangerous target, because those worktrees have owners.** Orphan removal is the
safe, secondary, compliance leg.

Two figures in this note also moved between measurements taken about forty minutes
apart (`~/.worktrees` 250 GB → 244 GB; this repo 48 directories → 44). That is live
churn from other sessions creating and removing worktrees, not measurement error.
Treat every figure here as point-in-time.

**This is a third accumulation layer the plan had not scoped**, and no mechanism
under consideration reaches it: `docker image prune` does not, `docker container
prune` does not, `fabro system prune` does not, and the hp hotfix's `disk-guard.sh`
does not. A reclamation plan that ships R1 exactly as written would leave vps at
84% and still falling.

---

## What this changes for the plan

1. **R1 must be restated store-agnostically** and must cover BOTH Docker layouts
   (containerd on Docker 29 / hp; overlay2 on Docker 28 / vps), and must cover
   **stopped containers**, which are the 100%-reclaimable layer on vps, not just
   images, which are the layer on hp.
2. **A new requirement carrier is owed** for build-artifact / worktree reclamation.
   It is the dominant consumer on vps by an order of magnitude and no other carrier
   touches it. **It must be aimed primarily at build artifacts inside LIVE,
   REGISTERED worktrees**, which are ~238 GB of the 244 GB. The 70 fleet-wide
   orphaned worktrees are a genuine protocol-compliance failure and should also be
   addressed, but they are 6.4 GB — 2.6% — so they cannot be the design's centre of
   gravity without sizing it against the wrong population.
3. **R4's horizon question is answered for the fabro layer and is nearly moot
   there.** `fabro system prune --older-than <dump window>` is the mechanism; the
   layer is ~430 MB. The horizons that actually matter are image re-pull cost
   (hp/containerd) and build-cache rebuild cost (the worktree layer) — the latter a
   constraint nobody has stated yet.
4. **The mechanism question (`bd-ib-il35` Q2, plan Q6) is partly settled.** The
   fabro layer needs no per-host anything: one scheduled caller with `--server`
   reaches every factory. The Docker and worktree layers are unavoidably host-local
   and still need the `fabro-hosts` unit-template route.
5. **vps is the urgent host, not hp.** hp sits at 8% behind a live hotfix; vps sits
   at 84% behind nothing. Whatever ships first should ship to vps.

## Method note

Two instruments in this spike returned confident wrong negatives before a control
caught them, both matching the `AGENTS.md` catalogue:

- A `grep` for retention across the fabro source targeted `crates/` — a directory
  that **does not exist** in this repo (the layout is `lib/`, `apps/`). It returned
  empty, with exit 0, and read as "no retention support anywhere". The positive
  control that caught it: grep for `"Delete old workflow runs"`, a string that MUST
  be present, which also returned empty from `crates/` and returned three hits from
  the repo root.
- `du` as an unprivileged user returned `460M` for `/var/lib` with no `docker` row,
  silently omitting a root-only subtree. No error, no warning.

A third instrument was replaced before it produced a wrong answer, and the
replacement is reusable. Counting orphaned worktrees by comparing
`ls ~/.worktrees/<repo> | wc -l` against `git worktree list | wc -l` is wrong twice
over: the numerator counts directories rather than worktrees (a branch name
containing a slash nests one a level deeper, and a stray non-worktree directory
inflates it), and the denominator includes the primary checkout, which is not under
`~/.worktrees` at all. Enumerate instead by the defining property — a `.git` entry —
and difference against the registered set of every clone:

    find ~/.worktrees -mindepth 1 -name .git -printf '%h\n' | sort -u
    git -C <clone> worktree list --porcelain | awk '/^worktree /{print substr($0,10)}'

The first method gave 16 for this repo; the second gives 17, and generalises to the
whole fleet without an extrapolation.
