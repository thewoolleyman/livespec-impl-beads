# Post-repair independent adversarial review — livespec-orchestrator-beads-fabro v059

**This is the evidence artifact for `bd-ib-mrqoy2.8`.** It is the review that
actually covers the bytes v059's `content_digest` binds. Preserve it verbatim
beside the ratification record when correcting that record, per the
`review-v198-retroactive.md` precedent.

## Provenance

- **Reviewer:** separately-spawned Fable-model agent, read-only, not the author
  of the proposal and not the session that composed the payload.
- **Rounds:** three. Round 1 (proposal bytes at `40ce44e5`) → BLOCKERS FOUND,
  one, in section K's heading-coverage guidance. Round 2 (amended proposal at
  `9f3d053d`) → NO BLOCKERS. Round 3 (resulting bytes, pre-repair) → BLOCKERS
  FOUND, the unratified root-note allowance. Round 4, below (repaired resulting
  bytes at `814083af`) → content clean.
- **Bytes covered by this verdict:** `814083af`, which is byte-identical to
  what merged as `6fae8205` (verified: `contracts.md`, `scenarios.md`, and the
  `history/v059/` snapshot copies all share blob hashes across the two).
- **Digest it corresponds to:**
  `86c95993edc891b01ae715642075dae68a97b11d0bab7a6b6449dde0436162ac`
- **Delivered:** 2026-08-09, after the repair landed at `revised_at`
  2026-08-09T13:44:33Z. THIS IS THE POINT: the committed record's
  `reviewed_at` of 12:01:11Z predates the composition of these bytes, which is
  the defect `bd-ib-mrqoy2.8` exists to correct.

## Verdict on the spec content: NO BLOCKERS

**Q1 — all three repair sites fixed, no residue.** The parenthetical is gone
from the plan-store clause in BOTH live and snapshot (identical hunks), and the
clause now matches core's ratified bullet verbatim. Scenario 41's Then line
reads "under plan/t/research/" in both. Line 668 reads "a plan's ledger epic".
Residue hunt for the root-note IDEA in other phrasings — `sit directly`,
`directly in \`plan`, `directly under \`plan`, `note MAY`, `MAY sit`, `at the
plan root`, `top-level note`, `loose note`, case-insensitive — returned zero
hits across all five live spec files, with a positive control (the identical
`MAY sit directly` pattern finds 1 hit in the frozen `history/v058/contracts.md`
snapshot). Scenario-placement grep for `under plan/t/` not followed by
`research`: zero. The idea did not survive in any constructible phrasing.

**Q2 — nothing else moved.** `git diff 3b664b2f..814083af` is EXACTLY: the
three corrections applied identically to live and `history/v059/` copies (same
hunks, same blob transitions `16adad86`→`0b9730be` for both `contracts.md`
copies, `fe280394`→`c82a93a1` for both `scenarios.md` copies), plus the
revision record's `revised_at` (13:34:08→13:44:33Z), an appended REPAIRED
sentence in the rationale, and `content_digest` (`7a4db378`→`86c95993`).
`tests/heading-coverage.json`, `README.md`, and `constraints.md` were untouched
by the repair. No riders.

**Q3 — re-derived versus carried forward, split honestly.** RE-DERIVED on the
repaired tree: the banned-vocabulary sweep (the proposal's own L regex — zero,
exit 1); the word-boundary `\bthreads?\b` sweep (only `constraints.md:181`
"thread-parameter chokepoint", unrelated Codex-companion usage); live-vs-
snapshot identity for all four spec files (byte-identical); the plan-store
clause's verbatim match to core; and the residue hunt above. CARRIED FORWARD,
justified by the diff's exactness: the v057 tombstone-ban sentence-by-sentence
survival walk, the v056/v058 spot-checks, the hunk-by-hunk proposal mapping of
every `contracts.md` change, and heading-coverage direction-4 satisfaction —
all performed on bytes differing from `814083af` only by the three corrections,
none of which touch what those checks examined.

## What the reviewer tried to break and could not

The residue hunt in eight phrasings with a positive control; the re-derived
sweeps; the snapshot identity; the no-riders diff; and the digest provenance —
proving the proposal bytes' hash was unchanged (`2bf70ead…` identical at
`9f3d053d` and in the snapshot) is what established that the digest change came
from the RESULTING bytes, which is how the attestation defect surfaced.

## The attestation finding (now `bd-ib-mrqoy2.8` and `livespec-yrq4`)

The reviewer flagged that the committed `## Ratification Review` block pairs
`reviewed_at: 2026-08-09T12:01:11Z` with a digest spanning resulting bytes
composed at 13:44:33Z, and that core's contract treats it as ONE evidence block
whose digest binds verdict to content — so the split the supervisor's brief-19
instructed ("`reviewed_at` timestamps the proposal-bytes verdict") is not
permitted. It also noted, unprompted, that the SAME defect existed in the
pre-repair accept and that it had not flagged it in round 3 because the
supervisor's brief marked the attestation as already-verified — an honest
account of its own miss.
