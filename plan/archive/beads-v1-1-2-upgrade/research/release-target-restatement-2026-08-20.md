# Release-target restatement — v1.1.2 is superseded by v1.2.2

**Measured:** 2026-08-20. **Supersedes in part:**
[`qualification.md`](qualification.md), whose evidence date is 2026-07-30 and
whose conclusion named v1.1.2 as the candidate to qualify. That conclusion was
correct on its date and is no longer current.

**Ledger item:** `bd-ib-3kolea.4` (P1) carries the decision and its exit
criteria. This note is the evidence behind it.

## Why this was checked now rather than at the gate

`bd-ib-3kolea.2` requires re-resolving the latest targeted release **at gate
time**. Nobody had re-checked upstream in the three weeks since
`qualification.md` was written, and the gate is the last item in the epic — so
a stale target would have been discovered at the most expensive possible
moment. This is the standing hazard that a written instruction can outlive the
condition that made it correct, in exactly the document a successor trusts
instead of re-checking.

## Upstream release state

| Tag | Published | Kind |
|---|---|---|
| **v1.2.2** | 2026-08-15 | **stable — current latest** |
| v1.2.2-rc.1 | 2026-08-15 | prerelease |
| v1.2.1 | 2026-08-11 | prerelease — see the landmine |
| v1.1.2 | 2026-07-26 | stable — the previous target |

Prior-art scan before filing: zero of this tenant's 590 items (`--status all`)
mentioned v1.2.x.

## v1.2.2 is a recovery release, so the qualification work survives

Per the v1.2.2 release notes: v1.2.0 and v1.2.1 were *"published by accident on
2026-08-11 without release testing"*, and **v1.2.2 re-releases the tested 1.1
line — "it is the v1.1.2 code under a higher version number"**. The 1.2.x-only
features (work leases, events journal, sync federation, HTTP API server,
provenance events) are explicitly **not** in it.

If that holds, everything `qualification.md` established carries over
unchanged: the adapter-facing command surface, the JSON envelope shapes, and
migrations 0050–0053 landing at schema **v53**. The rehearsal package
(`bd-ib-8azd`, merged) and the attended rehearsal (`bd-ib-ao3j`) are not
wasted.

**This is upstream's claim, not a verified fact, and it must not be carried
forward as one.** The two binaries cannot be hash-identical, because the
version string is embedded — so a hash comparison cannot settle it either way.
The honest check is behavioural: run the Enemy Unit Test harness
(`bd-ib-3kolea.3`) against v1.1.2 and v1.2.2 and assert an **empty delta**. A
non-empty delta falsifies the premise of the retarget.

## The v1.2.1 landmine, and why it is worse for this fleet

Running the v1.2.1 binary **even once** migrates the database schema from v53
to v65. Every v1.1.2 / v1.2.2 binary then stops with:

```
schema version mismatch: database is at v65, binary knows up to v53 (12 migrations ahead)
```

Upstream's recovery guidance assumes a **local single-clone database**. This
family runs a **shared multi-tenant Dolt server**, so one v1.2.1 invocation
against a shared tenant strands that tenant for *every* client in the family.
There are 14 live tenants. The blast radius is fleet-wide, not per-clone.

Recorded so they are not rediscovered under pressure:

- **Recommended recovery:** roll the schema cursor v65 → v53 with one
  `dolt sql` command. Guide: `docs/RECOVERY-1.2.1.md` at tag v1.2.2.
- **Stopgap:** `BD_IGNORE_SCHEMA_SKEW=1 bd <command>`, described upstream as
  verified-safe for this schema range.
- **Ordering matters:** upgrade every machine and clone to v1.2.2 **before**
  recovering — a leftover v1.2.1 binary silently re-migrates the database.

**v1.2.1 is still downloadable.** It is marked prerelease, not withdrawn, so
this is a live hazard rather than a historical one.

## Exposure: LOW, measured family-wide

Scope searched: the tracked trees of **twelve** repositories under
`/data/projects` — `livespec`, `livespec-runtime`, the three drivers,
`livespec-console-beads-fabro`, `livespec-overseer`, `livespec-dev-tooling`,
`livespec-orchestrator-git-jsonl`, `dolt-server`, `vps-info`, `homelab`, and
this repo — for `releases/latest`, `beads@latest`, `bd@latest`,
`include-prereleases`, and `--prerelease`.

**Zero of them resolve a beads version dynamically.** Two repos
(`livespec-overseer`, `livespec-dev-tooling`) contain latest-resolvers, but
filtering those hits for `beads` / `gastownhall` / `bd` returns nothing — they
target other tooling. The raw counts alone would have been misleading here; the
discriminating check was what each resolver actually points at.

Also confirmed:

- Every beads reference in this repo is explicitly version-pinned, e.g.
  `VERSION="1.1.2"` in `bd-guard/test/run-v1-1-2-candidate-tests.sh`.
- No `mise` declaration of `bd` in any family repo checked, consistent with the
  standing prohibition.
- The host still runs v1.0.5 at `/usr/local/bin/bd-real`, hash re-measured
  2026-08-19 and matching its 2026-07-30 pin.
- `go install …@latest` is safe: v1.2.2's `go.mod` **retracts** v1.2.1, v1.2.0,
  and v1.1.1, so it resolves to v1.2.2.

The residual risk is therefore **human, not mechanical** — someone
hand-installing "the latest beads" including prereleases, or following
third-party instructions. That is why `bd-ib-3kolea.4` carries an exit
criterion to write an explicit *never install v1.2.0 or v1.2.1* prohibition
wherever the pin is recorded, with the schema-v65 reason stated, so a future
reader cannot "helpfully" bump to a version that merely looks newer.

## Published pins for v1.2.2 (upstream values, NOT yet verified)

Assets confirmed present 2026-08-20:
`beads_1.2.2_linux_amd64.tar.gz` (49,107,375 bytes), `checksums.txt`,
`beads-v1.2.2.spdx.json`.

Published tarball checksum, fetched from the release's own `checksums.txt`:

```
8140098a51d3b81d5548d1c5e6db1a2d9930e5d141efe2a4bff7d079c4d321e8  beads_1.2.2_linux_amd64.tar.gz
```

**This is what upstream publishes.** It has not been verified against a
downloaded artifact, and the extracted-binary and SPDX hashes have not been
measured at all. `bd-ib-3kolea.4` criterion 2 requires reproducing
`qualification.md`'s full chain. Recording the published value here only turns
that verification into a comparison rather than a discovery.

## What still needs deciding

`bd-ib-3kolea.4` is `ready` but carries `admission:manual`, inherited from the
epic. It also inherited `factory-safety:mutates-host-machinery`, which is
inaccurate for its content — deciding a retarget and verifying published
provenance mutates no host binary, tenant, or image. **That label has not been
changed**: relabeling a safety class to make an item dispatchable is
guard-loosening, and must not be done unilaterally even when the inherited
label is over-strict. The maintainer should rule on it.
