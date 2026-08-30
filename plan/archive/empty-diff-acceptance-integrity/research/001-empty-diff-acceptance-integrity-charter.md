# 001 — Empty-diff acceptance integrity: a zero-change merge must never grade as delivered

Filed 2026-08-30 by homelab's steady-state-loop-hardening coordination
seat at the homelab maintainer's direction. Provenance: homelab
dogfooding — Fix Track 3 of the recovered `homelab/hl-s2kiob`
empty-commit findings. Full evidence record: homelab repo,
`plan/steady-state-loop-hardening/research/014-recovered-last-session-fabro-and-config-research.md`
(commit `18594f9`). Sibling filings from the same program:
`plan/janitor-argv-declared-resolution` (epic `bd-ib-6pshji`, the
adopter integration contract — complementary, see §5) and the archived
`plan/archive/dispatcher-staleness-gate-comparand` (epic `bd-ib-3oeq3g`).

## 1. The live instance (homelab PR #1044, merged 2026-08-27)

homelab PR #1044 merged with ZERO files changed under a title claiming
work item `homelab/hl-s2kiob` was delivered. Along the way:

- The janitor's `check-no-workflow-edits` scoped check passed VACUOUSLY
  over the empty diff all four review rounds — its file scope matched
  zero files, and zero matches rendered as success.
- The dispatcher's acceptance path graded the zero-change merge as a
  deliverable: nothing between merge and disposition asked whether the
  merged diff contained any change at all.

Root cause of the emptiness itself is settled and is NOT this plan's
subject: homelab's own committed write-time hook denied sandbox writes,
agents worked in an in-sandbox worktree fabro never reads, and fabro's
unconditional `--allow-empty` stage checkpoints minted the empty commits
(recorded 2026-08-30 as the root-cause comment on epic `bd-ib-6pshji`,
and in homelab note 014 Finding 1). This plan's subject is that the
orchestrator's gates then ACCEPTED the result.

## 2. Why the refusal belongs to the orchestrator, not fabro

Fabro deliberately treats a zero-change run as success at every version
including nightly HEAD: `--allow-empty` checkpoint commits are
unconditional (`sandbox_git.rs:122-125`), an empty patch skips the PR
and still reports success (`pipeline/publish.rs:73-75`), and the
`RunNoticeCode` enum has no empty-diff variant. Upstream added
`PublishOutcome::NoChanges` on 2026-07-27 and REMOVED it on 2026-07-28
because no consumer distinguished it — a direct upstream statement that
zero-change runs are normal engine behavior and the CONSUMER owns any
refusal. This orchestrator is that consumer: acceptance is where "was
anything delivered?" is a ratified question (§3), so acceptance is the
layer that must refuse.

## 3. The ratified clauses this defect class violates

Verified at HEAD `4b200f7e` (line numbers against
`SPECIFICATION/contracts.md` at that commit):

- **The evidence rule** (contracts.md:3084-3101): "A verdict MUST NOT be
  manufactured from absent evidence." PASS requires every leg OBSERVED —
  "an observed green outcome, a gradeable merged diff, and a non-empty
  effective-criteria check set with every check passing"
  (contracts.md:3090-3092). NEEDS_ATTENTION is the verdict "when the
  pass CANNOT OBSERVE what a judgment needs: the merged diff is
  unobservable or ungradeable ..." (contracts.md:3096-3099).
- **Never a rubber stamp** (contracts.md:3067-3071): the AI acceptance
  pass is "a read-and-judge of the merged diff against the item's
  acceptance criteria".
- **The NEEDS_ATTENTION verdict** (contracts.md:3148-3176): parks the
  item in `acceptance` for a human under every policy, journaled with
  the absent evidence leg(s).
- **Effective acceptance criteria / gradeability**
  (contracts.md:2986-3021): gradeability is defined at the assertion
  level; the pre-dispatch wall already refuses zero-gradeable-assertion
  items.
- **Parked-acceptance attention composition** (contracts.md:926-934).

The gap: none of this text says what an EMPTY merged diff is. The
shipped pass treated "diff observed, contains nothing" as a gradeable
diff and graded on. But for an item whose acceptance criteria imply file
changes, an empty merged diff cannot constitute passing evidence for any
criterion — grading it PASS is precisely a verdict manufactured from
absent evidence, the defect class the evidence rule was ratified against
(a gate judging with no evidence; a verdict not about the code — homelab
matrix §01/§16 vocabulary).

## 4. Charter — what this plan carries to propose-change

C1. **Acceptance: an empty merged diff is not passing evidence.** For a
work item whose effective acceptance criteria imply file changes, the
acceptance pass MUST treat an empty merged diff as failing the
evidence rule — NEEDS_ATTENTION (the merged-diff leg observed empty,
therefore ungradeable against change-implying criteria), never PASS.
NO_CHANGE_NEEDED remains reachable only through its own ratified
OBSERVED-evidence route (change already present / superseded,
contracts.md:3102-3111) — an empty diff alone is not that evidence.

C2. **Scoped checks report vacuity, not success.** A janitor/scoped
check whose file scope matched ZERO files in the diff under judgment
MUST report a distinct vacuous-match outcome, not a pass. A
vacuous-match outcome is not failure evidence either; it composes as
"this check observed nothing" so a gate cannot count it toward passing.

C3. **Dispatcher composition.** A zero-change merged run composes into
the needs-attention surface (the existing parked-acceptance composition
class, contracts.md:926-934) naming the empty-diff evidence leg — so the
condition is one attention item with a handoff, not a silent `done`.

C4. **Controls.** Positive: a real-change merge still grades normally.
Discriminating: replaying a zero-change merge (the PR #1044 shape) parks
NEEDS_ATTENTION and the vacuous-match outcome is visible. Control: an
item whose criteria genuinely imply no file change (pure
verification/telemetry-watch items, if any exist) is not misclassified —
the propose-change must say how "criteria imply file changes" is
determined, or default to treating all gradeable criteria as
change-implying with `human-only` as the escape hatch.

## 5. Non-overlap with the sibling plans

- `janitor-argv-declared-resolution` (bd-ib-6pshji) owns the adopter
  integration contract: PREVENTION at prepare/validation time (its
  R-series, and the sandbox writability probe direction from the
  root-cause comment). This plan owns REFUSAL at acceptance time: even
  with every prevention in place, a zero-change merge that slips through
  for any future reason must not be accepted. Different clauses,
  different pipeline stage; the two amendments can land independently.
- `dispatcher-staleness-gate-comparand` (bd-ib-3oeq3g, archived) fixed a
  gate comparand; same "moving/vacuous gate" family, disjoint scope.

## 6. Route

Propose-change into this repository's `SPECIFICATION/` lifecycle (the
evidence-rule and NEEDS_ATTENTION clauses above are the amendment
sites), then revise per this repo's designation, then implementation
children via the `spec_commitments` mechanism. In-session spec work; no
factory route.

## 7. Caveats

Line citations measured at `4b200f7e` (post-0.98.1); fabro facts
measured against fork build `8de6611` (= v0.254.0 + 10 local commits)
and upstream nightly `v0.330.0-nightly.0` per homelab note 014
Finding 3. Re-verify both before drafting the propose-change.
