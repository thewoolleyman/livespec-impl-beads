# 003 — Triage of the two adversarial reviews of the six pending proposals

Written 2026-08-25 by the `homelab-loop-hardening-orchestrator` session.
Reviews: `research/reviews/phase2-proposals-review-codex.md` (C1–C15) and
`…-review-claude.md` (F1–F23), commissioned per handoff 3's next action and
the propose-change → adversarial review → revise lifecycle. Every Blocker
claim was independently re-verified by this session against primary
sources before triage (the "observe only" verb row, the `--item`
never-bypasses clause, the default-branch no-hardcode clause, the three
documented fail-open cases, both direct journal writers, the
`count(active)` capacity clauses, the stale door-rules sentences, the
`NO_CHANGE_NEEDED` branch). Dispositions below are REPAIRED-IN-PLACE
(the pending proposal file is edited in the same PR as this note),
REVISE-TIME (an instruction the accepting revise executes), or RECORDED
(no change warranted, reason stated).

## Cross-cutting dispositions

- **Ratification ordering (C11, F7, F8)**: the six ratify in dependency
  order — acceptance-rework-state-machine → needs-attention-verdict →
  journal-invoker-attribution → dispatch-preflight-persistence →
  temporary-setting-restore → loop-probe — and each dependent proposal
  now STATES its ordering gate instead of a false stands-alone claim.
- **API-configurability (F3)**: repaired by explicit amendment, landed in
  journal-invoker-attribution (the first settings-declaring proposal in
  the order): §"Control surface and audit"'s "Every setting" is scoped to
  the policy settings of §"Dispatcher policy settings"; a ratified
  committed-configuration-only class is defined (require_invoker,
  step_waivers, master_ci; shipped precedent fabro_bin / codex_models
  noted), and the wip_cap "one setting with no per-item override" heading
  sentence is scoped to that section's settings.
  dispatch-preflight-persistence adds its two keys to that class.
- **Stale door-rules text (F5)**: co-edited by
  acceptance-rework-state-machine (first in order): the two "writes no
  journal record today" sentences are replaced by the met-state text the
  ratified clause itself anticipates, citing bd-ib-ktxb / PR #1048.
- **Journal chokepoint (C7, F6)**: journal-invoker-attribution now
  forbids direct journal-path writes, names the two shipped bypassing
  writers as migration obligations, and adds the mechanical
  no-direct-append control.

## Per-proposal dispositions

### acceptance-rework-state-machine
- C2/F1 (Blockers) REPAIRED: explicit co-edits of §"Work-item state
  semantics" (`active` definition gains the parked-rework-pending
  condition), §"Per-state operator verb vocabulary" (marked-item
  dispatch verb), §"Dispatcher loop invocation surface" (rework
  eligibility; the over-cap phrasing is DROPPED — ratified text says
  `--item` never bypasses the free-slot condition, and the pending
  wip-cap-bound-honesty claim to the contrary is that thread's to
  reconcile). Capacity restated self-containedly in count(active) terms:
  a rework re-dispatch excludes the item's OWN parked row
  (`count(active) - 1 < wip_cap`), preserving wip_cap 0 dispatch-off;
  counted-claims moves to a compatibility note.
- C3 (Blocker) REPAIRED: the marker is NOT cleared at launch; it clears
  at the rework dispatch's terminal disposition (or any exit from
  `active`); the live dispatch lock is the double-selection guard; a
  rework dispatch that dies pre-publish leaves the item marked,
  lock-less, and re-selectable — self-healing instead of the recreated
  dead end.
- C6 (Major) REPAIRED: §"Work-item beads-issue mapping" co-edit added —
  rework-pending becomes a mapped logical field on the materialized
  WorkItem, so selection/accounting/discrimination can read it.
- F16 REPAIRED: the move-target motivation sentence is removed; the
  ratified four-way self-contradiction on move-into-active is recorded
  here as prior-art for a future proposal, deliberately NOT resolved by
  this one.
- F17 REPAIRED: the reconcile-merged refusal keys on the MARKER, not on
  `active` status (covers the shipped wider status set); the
  pre-existing spec/impl divergence on allowed statuses is recorded, not
  resolved.
- F18/F19/C14/C15 REPAIRED: Scenario 35 line reworded; §2a gains the
  same-sentence merge instruction vs factory-headroom-preflight;
  Scenario 68 gains the unmarked-item control; the ready-only
  overstatement gains the pending-approval projection nuance.

### needs-attention-verdict
- F4 (Major) REPAIRED: NO_CHANGE_NEEDED is ratified as the FOURTH
  verdict with its own evidence rule (observed evidence the change is no
  longer applicable; closes with resolution no-longer-applicable),
  matching the shipped, tested branch; its current unreachability
  through run_acceptance_pass is stated.
- C9/F21 REPAIRED: the criteria resolution is TWO steps — the
  materialized merged criteria value (native winning over metadata; a
  metadata-held field is not absent), else the description "Exit
  criteria" section — with source ∈ {criteria-field, description}.
- C12/F9 REPAIRED: the proposal now ADDS a ratified "Dispatcher exit
  codes" section (0/1/2/3/4/5) instead of updating a nonexistent one.
- F10 REPAIRED: the tfpdya premise is corrected (indented joins and
  header-drops already shipped in 8cc2d2dd; non-indented wraps survive)
  and the wall-implementation gate gains a completion criterion: the
  formatting-independence test (same text reflowed yields the same
  gradeable count) plus the genuinely-unmet-criterion control.
- F13 REPAIRED: the wall lives solely at the approve transition and
  auto-approve routing; the admission-valve bullet is removed.
- C14/F22/F23 REPAIRED: Scenario 69 wording (gradeable through the
  merged read / fallback); heading citations use the ratified arrow;
  bd-ib-au4t described as shipped-not-accepted with a revise
  coordination note.

### journal-invoker-attribution
- C7/F6 (Majors) REPAIRED: chokepoint obligation + migration of the two
  bypassing writers + mechanical negative control.
- F3 (Major) REPAIRED: the Control-surface scoping amendment (above).
- C8 (Major) REPAIRED: `probe` added to the entry-point enumeration,
  with an inheritance clause for later-ratified entry points.
- F20 REPAIRED: Scenario 73's console assertion re-keyed to THIS repo's
  API-configurable key manifest; Scenario 72's writer-supplied-field
  assertion moved to its own properly-Given block.
- F5 cross-noted (co-edit landed in acceptance-rework-state-machine).

### dispatch-preflight-persistence
- C1 (Blocker) REPAIRED: outcomes split by step class — pre-dispatch
  steps: pass / refusal / waived; post-merge steps: pass / DEGRADED
  (first-class, persisted) / waived — over a NAMED closed step set
  (source-checkout, master-ci, janitor-bootstrap; extensible only by
  ratification); the ratified cost-gate posture and the pending
  factory-headroom gauge posture are named as out-of-scope
  observability postures, not steps of this section.
- C4 (Blocker) REPAIRED: default-branch resolution added (resolved, not
  configured, per §"Self-contained plugin dispatch"); the three shipped
  fail-open cases (no gh binary, no stored credential, no CI runs yet)
  are EXPLICITLY RETIRED — each becomes an unprovable refusal naming its
  remedy, with the committed step waiver as the sanctioned escape;
  a still-pending run remains an unprovable refusal.
- C10 (Major) REPAIRED: closed step-id vocabulary; degraded outcomes
  carry the structured step id; waivers key on the same ids; a journaled
  clearing record is required on re-verification pass.
- F14/F15 REPAIRED: the incident disclaimer now rests on the timing
  evidence (homelab@162a0a0 landed 2m13s after the refusal; the row's
  gh_stderr is quoted); the "demonstrably resolved" claim is restated as
  what the absence-only surface can support.
- C14 REPAIRED: Scenario 77 split into green/red/unprovable branches.
- F3 REPAIRED: step_waivers and master_ci join the ratified
  committed-configuration-only class.

### temporary-setting-restore
- C11/F8 (Major) REPAIRED: explicit ordering gate on
  needs-attention-verdict's §"Effective acceptance criteria".
- C13 (Minor) REPAIRED: the owner is queryable — an `owner:<name>`
  ledger label on the restore item, in addition to prose.
- F20/C14 REPAIRED: Scenario 78 rewritten with a decidable negative leg
  (a committed settings change with only a comment and no restore item
  is the reviewable violation) and the calibration note on TODO-bound
  process scenarios recorded.

### loop-probe
- F2 (Blocker) REPAIRED: the probe REFUSES a designated item whose
  effective acceptance_policy is not `ai-only`, naming the label to set
  at filing — terminal `done` is machine-reachable by construction.
- C5 (Blocker) REPAIRED: confinement is asserted PRE-merge (the driven
  cycle fails without merging on escape); the post-merge diff check is
  the backstop and a merged escape FAILS the probe naming the revert
  obligation and the merged SHA; the reserved identifier set is defined
  (the designated item id + a journaled `probe:<item-id>:<timestamp>`
  run id); cleanup is sanctioned removal of the single replaced artifact
  file, stated as such.
- F7 (Major) REPAIRED: the ordering gate replaces the false
  degrades-gracefully sentence; the probe ratifies LAST.
- F11 (Major) REPAIRED: hard assertions scope to the probe's OWN
  identifiers; the unrelated before/after delta is REPORTED, never
  failed on — the mirror of the global-emptiness rejection.
- F12 (Major) REPAIRED: stated — each invocation consumes its designated
  item; a standing cadence files a fresh probe item per run (per-run
  consent is intended); consumers cite the latest outcome.
- C8 cross-noted (probe's --invoker lands in journal-invoker-attribution).
- C14 REPAIRED: Scenario 74 gains eligibility setup and the cleanup
  line.

## Recorded, no change

- F3's "Every setting" scope question is settled BY amendment (above)
  rather than reported to the maintainer: the shipped six-entry
  CONFIG_KEYS manifest and the ratified fabro_bin/codex_models keys are
  the existing practice the amendment ratifies; the revise pass presents
  the amendment explicitly.
- F16's four-way move-into-active self-contradiction and F17's
  reconcile-merged status divergence are PRIOR-ART records for follow-up
  filings; neither is silently resolved by this thread.
- C15/F-obs motivation nuances repaired as wording only; the dead-end
  and parking conclusions stand.
- The wip-cap-bound-honesty over-cap `--item` claim vs ratified
  never-bypasses text is that thread's contradiction to reconcile; noted
  to its owner via the maintainer-visible record here.
