# Track 2: honest gap detector and check-anchored closure

Worker thread for homelab plan `pre-foreman-livespec-hardening`, Track 2
(homelab epic `hl-sqedvd`, coordinator session `homelab-rewrite`). Seeded
verbatim from
`/data/projects/homelab/plan/pre-foreman-livespec-hardening/research/008-track-2-seed.md`.

## Scope: two gates, this repo only

**Gate 1** (findings F1, F2, F5 in homelab's `001-findings-and-gates.md`).
`SPECIFICATION/contracts.md` sections `detect-impl-gaps` (~line 571) and
`capture-impl-gaps` (~line 53) promise a spec->impl comparison ("Detect
spec -> impl gaps") and then specify a spec-only MUST/SHOULD enumeration
and forbid in-skill detection logic. The ratified contract contradicts
itself. Resolution: either rename the operation to what it does (a clause
enumerator that surfaces untracked clauses) or specify the implementation
read it promises -- this repo decides which (homelab's `003` section
6.1). Also document `--since-version`'s real semantics: files whose
content differs since vN, every live MUST/SHOULD in them -- not "clauses
added since vN".

Exit proof: the contradiction is gone from the ratified contract
(proposal -> revise -> history/vNNN). Negative control: a gap-capture run
against a tree containing a demonstrably honored rule either no longer
reports that rule as a gap, or the operation's ratified text no longer
claims it would.

**Gate 3** (findings F3, F4). `implement`'s gap-tied closure gate
("closure REQUIRES re-running capture-impl-gaps in dry-run mode and
confirming the gap_id is no longer detected"; contracts.md ~lines 165 and
839) is unsatisfiable because detection is spec-only, so it is bypassed,
and rewards editing spec text instead of implementing. Replace it:
closure of a gap-tied item requires (a) the check path recorded ON THE
WORK ITEM passes AND its negative control fails; (b) if that check file
was modified on the item's branch, the drift gate is FORCED -- a targeted
`capture-spec-drift --for-work-item <id>` -- and closure is refused until
a propose-change exists. Anchor to the check path, never to `gap_id`
(F4: `gap_id` hashes a hard-wrapped source line; reflow re-keys it).

Exit proof, each demonstrated in a test: an item whose recorded check
FAILS is refused closure; one whose check passes and whose control fails
CLOSES; one whose check was modified on its branch is refused until a
propose-change exists. Negative control is the refusal cases.

## Do / do not

DO: measure the real detector against a real spec tree before touching
prose (homelab's `/data/projects/homelab/SPECIFICATION`, read-only);
file only this thread; implement in-session where the contract allows,
dispatch only if required; keep every change generic-not-local (nothing
homelab-shaped: no homelab paths, no `SPECIFICATION/checks/` concept);
ratify through this repo's own revise contract; cut a release whose ref
is greater than `f8cedb484f0e` (the pin homelab consumes); verify every
"merged"/"released" claim on the forge before reporting it.

DO NOT: add `capture-spec-drift` to the closure path as a survey
(homelab `003` section 2.2); anchor closure on `gap_id` (homelab `003`
section 3.1); build a `SPECIFICATION/checks/` concept; sweep the repo or
touch any item outside this thread (the standing one-track narrowing on
`bd-ib-1mjt` and every other plan in `plan/` are out of scope); design
for hypotheticals or for stale ratified text; redesign beyond the two
gates; park on a picker.

## Read-first chain

- `/data/projects/homelab/plan/pre-foreman-livespec-hardening/research/001-findings-and-gates.md`
  (F1-F5, "Gate 1", "Gate 3")
- `.../003-reasoning-and-rejected-alternatives.md` (2.2, 3.1, 3.2)
- `.../006-rescope-gate-0-only-orchestrator-next.md`
- `.../007-operating-model-one-worker-per-track.md` (2, 4, 5, 6)
- `.../008-track-2-seed.md`

## Finish line

Release tag/ref greater than `f8cedb484f0e`, reported to `homelab-rewrite`
in one line, handoff written on this epic, children closed with evidence,
then exit.
