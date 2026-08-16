---
topic: fabro-factory-host-provisioning
author: claude-fabro-on-hp
created_at: 2026-08-16T21:01:56Z
---

## Proposal: Fabro factory host web-console dual reachability

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Every Fabro factory server in the fleet MUST have its web console reachable both from the host's own loopback address and from other machines via the host's externally-resolvable network name, codifying the reachability contract that Fabro's built-in canonical-host redirect already provides so future factory-host bring-up verifies both paths instead of re-discovering the mechanism by hand.

### Motivation

Standing up a second factory host (the fabro-on-hp track) surfaced that Fabro's canonical-host middleware pins the web console's browser-facing routes to exactly one configured origin (server.web.url): a raw request to the loopback address with a mismatched Host header receives a 308 redirect to that origin rather than a 200, which looks like a defect until a client that follows redirects (any real browser, or curl -L) is used. Separately, /health and every /api/* route bypass the redirect entirely and always respond directly on loopback. None of this was documented, so it had to be reverse-engineered from Fabro's source during bring-up, and would have to be re-derived again for every future factory host without a spec anchor naming the expected shape.

### Proposed Changes

In SPECIFICATION/constraints.md, add a new section (a sibling to "Fabro runtime constraints", scoped to factory HOST PROVISIONING rather than which Fabro BUILD is pinned) stating: every Fabro factory server the fleet operates MUST set its `server.web.url` (or equivalent canonical-origin setting) to the host's externally-resolvable network name, so that machines other than the host itself can reach the web console over that name. The web console MUST also remain reachable when accessed via the host's own loopback address; a client that follows the resulting redirect to the canonical origin, or that hits a route the server exempts from redirection (e.g. a health-check or API endpoint), MUST reach the running service without further configuration. Bringing up a new factory host MUST verify both reachability paths — loopback (redirect-and-follow, plus any bypassed health/API route) and the external network name (direct) — before the host is considered ready to accept dispatches. This section MUST NOT name any specific hostname, tailnet, or domain; per-host values are operational data recorded in the project's own work-item tracker, never in this specification.

## Proposal: New factory host credential sourcing reuses the fleet's existing channel

### Target specification files

- SPECIFICATION/constraints.md

### Summary

A newly provisioned Fabro factory host's secrets (its GitHub integration credential, and any other fleet-shared secret the factory server needs) MUST be sourced through the same project-configured credential-wrapper mechanism the project already uses for every other secret consumer, and MUST reuse the fleet's existing GitHub App installation rather than provisioning a new one, so the credential-sourcing pattern does not have to be re-derived by hand for each additional host.

### Motivation

Provisioning hp-xubuntu required inspecting an existing factory host's live configuration and credential-wrapper installation by hand to work out where its GitHub App credential actually came from, then manually replicating that channel onto the new host — a repo-agnostic pattern with no spec anchor describing the expected shape, so each future factory host would otherwise re-derive it from scratch (or worse, drift onto an ad hoc channel per host).

### Proposed Changes

In the same new section proposed above (SPECIFICATION/constraints.md, factory host provisioning), add: a newly provisioned Fabro factory host MUST source every fleet-shared secret it needs (at minimum, its GitHub integration credential) through the project's already-configured `credential_wrapper` mechanism, rather than through a bespoke or manually-copied channel invented for that one host. Where the fleet already operates under a single GitHub App installation, a new factory host MUST reuse that installation's credential rather than registering a separate App, unless an operator explicitly decides otherwise for that host (a decision that, like all per-host data, belongs in a ledger work-item, never in this specification). This constraint governs the CHANNEL a factory host's secrets travel through, not any specific secret value, host name, or credential-wrapper installation, all of which remain per-deployment operational data.
