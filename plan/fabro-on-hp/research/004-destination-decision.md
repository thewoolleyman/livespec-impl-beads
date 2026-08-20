# fabro-on-hp — the `.14` destination decision, and the move

**Written 2026-08-20.** This note records the decision that `bd-ib-l3nptz.14`
had been waiting on since it was filed, the reasoning that produced it, and
what was verified across the move. It supersedes nothing in `001`–`003`; it
closes the question those notes deliberately left open.

## The decision

The parameterized `fabro-server` provisioning artifacts live in a **new
fleet-scoped repository**, `thewoolleyman/fabro-hosts` (private), at
`services/fabro-server/`. `vps-info/services/fabro-server/` was **removed**, not
copied, in `vps-info` PR #50.

## Why not the two options the item named

`.14`'s description framed this as a two-way choice: "vps-info is named for the
vps host, so either it gains a per-host layout or a sibling host repo is
created." Both were considered and both were rejected, for reasons that only
became visible once `vps-info`'s own charter was read rather than assumed.

**`vps-info`'s README already documents a per-host convention**, and it argues
*for* the sibling repo:

> **Why a separate repo** — Mirrors the existing per-host pattern:
> `openclaw-info` for the macmini, `tsvmtunnel` for the Mac↔VM tunnel. The
> tailnet itself (ACL policy, machine inventory) lives in `tailscale-admin`.
> Per-host service config lives here.

**And that convention structurally cannot hold these artifacts.** The set is
*one* `fabro-server.service.in` plus a six-line `hosts/<host>.env` per host,
deliberately shared across `vps` and `hp`. A per-host repo can only hold a
*copy* of the template — which recreates the exact divergence `.14` exists to
end. Two instances of that divergence were already filed (`bd-ib-l3nptz.15`,
`bd-ib-wdns6b`), and both were invisible until someone diffed the live hosts.
So following the documented convention would have defeated the item's purpose.

Re-chartering `vps-info` as multi-host was the low-friction option — no new
repo, and every existing reference already pointed there. It was rejected
because the repo name asserts a single host it would no longer describe, and
its stated per-host rationale would have had to be rewritten to mean its
opposite.

## Why a fleet repo is the right third category

The workspace already has this category and already has a name for it.
`tailscale-admin` is **fleet-scoped, not host-scoped**: it holds what spans
machines (ACL policy, machine inventory) while each host repo holds its own
services. A cross-host *service definition* is that same shape, and no existing
repo covered it.

So the split is now principled rather than incidental:

| Scope | Repo | Holds |
|---|---|---|
| One host's own services | `vps-info`, `openclaw-info` | That host's service config |
| One service, many hosts | **`fabro-hosts`** | The shared template + per-host values |
| The tailnet itself | `tailscale-admin` | ACL policy, machine inventory, serve mappings |

`vps-info`'s "Why a separate repo" section now records that distinction
explicitly, so the next multi-host service does not have to rediscover it.

## What was verified, and when

The artifacts' recorded verification was **re-run rather than quoted**, before
the move and again from the new location — because a claim with a timestamp is
not a fact, and because a test suite that silently depends on its directory
would pass in one place and lie in the other.

| Check | Before move | From `fabro-hosts` |
|---|---|---|
| `install.test.sh` | 6/6 | 6/6 |
| `check-settings.test.sh` | 8/8 (1 honest skip: `hp`'s home is on another machine) | 8/8 |
| `shellcheck`, all five scripts | clean | clean |
| Rendered `vps` unit vs the committed one | one substantive line | — |

**One recorded claim needed sharpening, and measuring is what found it.**
`.14`'s comment said rendering for `vps` "adds only `FABRO_CANONICAL_HOST`"
against the committed unit. The raw `diff` shows **more than that** — three
comment blocks as well. Stripping comments and blanks shows the substantive
difference is exactly the one line claimed:

```text
12d11
< Environment=FABRO_CANONICAL_HOST=vps.perch-rudd.ts.net:32276
```

So the claim holds, but only under a qualifier it did not state. The extra
lines are explanatory prose the template adds and the hand-written units
lacked — an improvement, not a divergence. Recorded because the unqualified
form would have looked *false* to the next person who ran the obvious command,
and "the claim was true if you strip comments" is exactly the kind of thing
that gets discovered mid-incident rather than mid-review.

The shared verifier was also confirmed byte-identical to `vps-info`'s committed
copy before the move, which is what makes "the fork is gone" a fact about the
files rather than an inference from the script's behaviour.

## What this does not do

It does not install anything. `install.sh` still has never been run end-to-end
from this artifact set, so its `require_inputs` path onward and its
supersede-the-old-drop-in step remain unexercised; `.14`'s acceptance requires
one real run on `hp`. It does not choose `bd-ib-wdns6b`'s concurrency number —
`hosts/hp-xubuntu.settings.expected` still records the observed `5`, not a
chosen value. And it does not capture the `tailscale serve` mappings, which
belong to `tailscale-admin` and are still absent for `hp`.
