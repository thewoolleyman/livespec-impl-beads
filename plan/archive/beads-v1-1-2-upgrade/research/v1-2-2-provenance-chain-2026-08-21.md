# The v1.2.2 provenance chain, measured end to end

**Date:** 2026-08-21
**Item:** `bd-ib-3kolea.4`, exit criterion 2
**Status:** criterion 2 DISCHARGED, by a stronger chain than the criterion asked for
**Nothing was installed.** Every artifact below was verified in a scratch
directory. No tenant was contacted; no host path was written.

## Why this note exists

`bd-ib-3kolea.4` criterion 2 asks to re-verify v1.2.2 provenance "the same way
`qualification.md` did for v1.1.2 — upstream `checksums.txt`, tarball SHA-256,
extracted-binary SHA-256, the SPDX artifact, and the version probe."

Following that recipe literally turns up two things worth recording: one leg of
it **does not do what its name suggests**, and a **stronger instrument exists
that the v1.1.2 qualification did not use**.

## The five legs, as asked

| Leg | Result |
|---|---|
| upstream `checksums.txt` | obtained; 8 artifacts; itself sha256 `25507c2d3ac43d17a1e7dc6ea25141b0354300cebf3f3f549b7ba3d266ee4f69` |
| tarball SHA-256 | `8140098a51d3b81d5548d1c5e6db1a2d9930e5d141efe2a4bff7d079c4d321e8` — **matches `checksums.txt`** |
| extracted-binary SHA-256 | `54fc0e0581ce4c5487a5b242f0a4f34af1ef09cf056e164a1af63a6ec7aa1e0e` — see the caveat below |
| SPDX artifact | obtained, sha256 `117f89c22d3562029521b67f1bfcfa7a173513a8cd2c63edf09541dae5d60197` — **attests nothing about either artifact**; see below |
| version probe | reports exactly `1.2.2 (6c124203e: HEAD@6c124203e771)` |

Release metadata: tag `v1.2.2`, published `2026-08-15T03:59:10Z`,
`isPrerelease: false`. Asset sizes match those recorded on the item on
2026-08-20: tarball 49,107,375 bytes, SPDX 1,145,995 bytes, checksums 780 bytes.

**Caveat on the binary hash.** `checksums.txt` covers **tarballs only**. No
upstream artifact attests the extracted binary's hash, so
`54fc0e05…` is a pin *we* establish by measurement, exactly as
`6d767629…` was for v1.1.2 — it is not an upstream claim we are checking.

## The SPDX artifact does NOT attest artifact integrity

This is the leg whose name misleads, and it would be easy for a future reader to
assume the SBOM cross-checks the binary. It does not.

`beads-v1.2.2.spdx.json` is a **syft `dir:` scan of the source tree**
(`"documentNamespace": "https://anchore.com/syft/dir/…"`, creator
`Tool: syft-1.42.3`, created `2026-08-15T04:08:07Z`). Measured against the
document:

- the tarball sha256 appears **nowhere** in the file
- the binary sha256 appears **nowhere** in the file
- **0 of its 515 packages carry a `checksums` field**
- no package name contains `tar.gz`; the entries are build-time dependencies
  (`DeterminateSystems/determinate-nix-action`, workflow files, and so on)

So the SPDX is **dependency provenance, not artifact integrity**. It is worth
keeping for supply-chain review of what went *into* the build; it contributes
nothing to "is this the binary upstream published". Recording that so the next
reader does not count it as a second integrity check. It is one check plus an
SBOM, not two checks.

## The stronger instrument: a verified SLSA provenance attestation

The v1.1.2 qualification rooted trust in `checksums.txt`, which is an
**unsigned text file served from the same release page as the artifact it
describes** — an attacker who can replace one can replace the other.

v1.2.2 carries a Sigstore-backed **SLSA v1 provenance attestation**, which
closes that gap. Verified with `gh attestation verify … --repo gastownhall/beads`:

| Field | Value |
|---|---|
| `predicateType` | `https://slsa.dev/provenance/v1` |
| `buildType` | `https://actions.github.io/buildtypes/workflow/v1` |
| workflow | `.github/workflows/release.yml` at `refs/tags/v1.2.2` |
| `sourceRepositoryURI` | `https://github.com/gastownhall/beads` |
| `sourceRepositoryDigest` | `6c124203e771433a3550c348771a5b5e27fd3c21` |
| certificate issuer | `https://token.actions.githubusercontent.com` |
| run | `actions/runs/31862568799/attempts/1` |

Three cross-checks, all passing:

1. The attestation's subject digest for `beads_1.2.2_linux_amd64.tar.gz`
   **equals the tarball we measured** (`8140098a…`).
2. `checksums.txt` agrees with the attestation on **all 8 shared artifacts**
   (symmetric difference 0). The unsigned file is corroborated by the signed one
   rather than trusted on its own.
3. **The attested source commit equals the commit the executable itself
   prints.** The attestation binds `6c124203e771433a3550c348771a5b5e27fd3c21`;
   the extracted binary self-reports `HEAD@6c124203e771`. Build provenance and
   binary self-report agree, so the artifact is tied to a specific reviewable
   commit and not merely to a hash.

### The verifier was controlled, because exit 0 with no output is not evidence

`gh attestation verify` returned **exit 0 and zero bytes on both streams** for
the real tarball. That is indistinguishable, on its face, from a no-op. A
negative control settles it: verifying a file that cannot possibly be attested
returns **exit 1 with `HTTP 404: Not Found`**. The instrument discriminates, so
the silent exit 0 is a genuine pass. (Per AGENTS.md "Verification discipline":
a control proving an instrument *functions* is separate from one proving it is
*pointed correctly* — the 404 arm establishes aim.)

## What this settles, and what it does not

**SETTLES.** The v1.2.2 Linux amd64 artifact we would install is the one
upstream's tagged release workflow built from commit `6c124203e771…`, confirmed
by a signed attestation, an unsigned checksum file that agrees with it, and the
binary's own self-report. Criterion 2 is discharged.

**DOES NOT SETTLE.** Provenance is not behaviour. That the artifact is
authentically upstream's says nothing about whether it behaves identically to
v1.1.2 on our surface — that is **criterion 3**, which needs the Enemy Unit Test
harness (`bd-ib-3kolea.3`) and remains parked on the unruled EUT scope question.
Upstream's "it is the v1.1.2 code under a higher version number" claim is still
an upstream claim.

## Pins recorded for the eventual cutover, so it is not re-derived

When the retarget is actually performed — gated behind `bd-ib-3kolea.2` and
criterion 3, **not** by this note — these are the values:

```
BD_VERSION=1.2.2
BD_TARBALL_SHA256=8140098a51d3b81d5548d1c5e6db1a2d9930e5d141efe2a4bff7d079c4d321e8
BD_BINARY_SHA256=54fc0e0581ce4c5487a5b242f0a4f34af1ef09cf056e164a1af63a6ec7aa1e0e
BD_SPDX_SHA256=117f89c22d3562029521b67f1bfcfa7a173513a8cd2c63edf09541dae5d60197
expected version string: 1.2.2 (6c124203e: HEAD@6c124203e771)
```

Recording these is **not** the cutover and does not change any pin in the tree.
The live pins stay at v1.1.2 until `bd-ib-3kolea.2`'s final gate passes.
