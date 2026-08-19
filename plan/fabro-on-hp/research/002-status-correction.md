# fabro-on-hp — status correction to `001-initial-research.md`

**Written 2026-08-19.** Read this note BEFORE acting on anything in
`001-initial-research.md`. That document is preserved unedited as the
historical record of what was known on 2026-08-16, but two of its
sections now assert conditions that no longer hold, and both of them
read as authoritative to a cold-open successor.

## Correction 1 — "Blocker #1: no shell access to hp-xubuntu" is RESOLVED

`001` §"What is NOT yet known / blocks immediate execution" says shell
access to hp-xubuntu did not exist and that "nothing past this point can
be verified or executed remotely". That was true on 2026-08-16. It is
false now: hp-xubuntu was provisioned, and the fabro server on it is
live, healthy, and actively serving dispatches.

Measured 2026-08-19, using the repo's own readiness gate
(`/data/projects/vps-info/services/fabro-server/fabro-server-verify-web`,
pointed with its `FABRO_BASE_URL` / `FABRO_CANONICAL_HOST` overrides)
rather than a hand-rolled probe:

| Factory | Endpoint | Result |
|---|---|---|
| hp | `https://hp-xubuntu.perch-rudd.ts.net:32276` | exit 0 — READY |
| vps | `http://127.0.0.1:32276` (reference) | exit 0 — READY |

That gate is stricter than reachability: it requires `/runs` **and** the
unauthenticated `/login` shell to load, **and** the embedded SPA
JavaScript asset to fetch. Tailscale ping to hp: 63ms, direct.

### Shell access to hp works — use the `cwoolley` account

`tailscale ssh cwoolley@hp-xubuntu` **works** and is the way in.
Verified 2026-08-19:

```bash
tailscale ssh cwoolley@hp-xubuntu 'fabro --version'
# fabro 0.254.0 (8de6611 2026-08-16)
```

`001` §"Blocker #1" says both `ssh` and `tailscale ssh` failed. That was
true on 2026-08-16, and it is the section a successor reads first — but
the scope event recorded on the epic that same day already noted, in its
*third deferral*, that "Tailscale SSH already provides working access via
the cwoolley account". Two records of one thread disagreed; the more
recent and more specific one was right.

**The operative detail is the account.** Probes that use the default
user fail; `cwoolley@` succeeds. Re-test a recorded blocker before
honouring it.

hp is also *serving*, not merely up — `fabro ps` against it listed two
live `ImplementWorkItem` runs from this repo on the same date. The host
fabro binary is `0.254.0 (8de6611 2026-07-30)`, exactly the pin
`SPECIFICATION/constraints.md` requires.

**Probe warning, because the wrong probe is easy to write.** A bare
`curl https://<host>:32276/runs` returns **HTTP 404 from a healthy
server**, because fabro 404s a request lacking `Accept: text/html` and
the canonical `Host` header. Two identical 404s against hp *and* the
known-good vps reference mean the probe is wrong, not that both
factories are down. Use the shipped verifier.

## Correction 2 — "Scope not yet cut" is STALE

`001` §"Scope not yet cut" says no scope event has been recorded. One
was recorded on the plan epic `bd-ib-l3nptz` on 2026-08-18, and
implementation children were admitted under it. Read the epic timeline,
not this section, for the current scope.

## Where the live state actually lives

Status for this thread is **ledger-held**, never mirrored into these
research files. `001` is 2026-08-16 reasoning; this note corrects two of
its claims and nothing more. For what is true right now, read the
`bd-ib-l3nptz` handoff timeline oldest-first, then the open children.

As of this note the remaining work is children `.10` (homelab), `.11`
(dolt-server) and `.12` (openbrain + resume) — App retirements, each
gated first on a maintainer-only 1Password Environment credential
switch. Each child carries a pre-computed execution package. Two
caveats there are load-bearing and are recorded on the children
themselves: `.11` cannot be run in the step order its description
lists (its identity verifier fails closed against the shared App, on an
actively-used dispatch path, so it needs an atomic cutover), and `.12`
needs an openbrain **spec revision** because that repo's ratified
`constraints.md` says the factory publishes *exclusively* as the old
App.
