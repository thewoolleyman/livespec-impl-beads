# 002 — The full coupling sweep, and the fail-fast declared-contract requirement

Added 2026-08-29 at the homelab maintainer's direction, widening this
plan's scope: every located instance of the implicit fleet-tooling
coupling rolls into THIS plan, together with a fail-fast contract
requirement. Measured against build ba30bc662f07 (v0.96.1) from the
homelab (adopter) side; the propose-change should re-verify each at
HEAD and complete the sweep from inside this repo.

## 1. Located instances (adopter-facing premises)

Dispatcher-side, run on the host against the governed repo:

- I1. Post-merge janitor argv (research/001's subject).
  `_dispatcher_fabro_argv.py` `_DEFAULT_JANITOR`: mise + just +
  recipe names check-no-workflow-edits / install-worktree-pack /
  check. Broke twice on homelab. Fails LATE (post-merge), strands the
  merged item. Only override: per-invocation `--janitor` flag.
- I2. Janitor-bootstrap step default
  (`_dispatcher_janitor_bootstrap_recipe.py`): `mise exec -- just
  install-commit-refuse-hooks` when undeclared. v087 fixed the
  resolution (declared recipe runs VERBATIM — its own comment states
  "imposing our wrapper on someone else's command is the same
  assumed-tooling defect one layer down", the right principle to
  generalize). Residue: the DEFAULT still premises mise/just + a
  dev-tooling recipe name. Fail mode is the good one: pre-dispatch
  refuse-or-waive with a named step id.
- I3. Janitor core provisioning: the janitor clones livespec CORE
  into its checkout (`.livespec-core`; `janitor_core_clone_argv`),
  default repo thewoolleyman/livespec.git at ref MASTER — a moving
  ref — unless the governed repo's
  `livespec-orchestrator-beads-fabro.compat.pinned` names a ref.
  Network-dependent at janitor time; failure lands post-merge (late);
  the moving-ref default contradicts the release-currency posture the
  dispatcher enforces about its own build.

Factory-sandbox side, from the shipped .fabro workflow:

- I4. Sandbox prepare runs `mise install` resolving the governed
  repo's `.mise.toml` aqua pins. An adopter without `.mise.toml`
  (homelab) silently gets nothing — latent, undefined-by-contract.
- I5. Node prompts hardwire `mise exec -- git ...` for all git writes
  and `mise exec -- just check` as THE check suite
  (implement.md, pr.md, fix.md, review.md, review-fix.md). Premises:
  a justfile with a `check` recipe and mise semantics. homelab
  happens to satisfy the names with its own plain-shell recipes; an
  adopter without them gets undefined agent behavior at the exact
  seam that produced the hollow-merge class.
- I6. Sandbox prepare provisions "exactly like `just bootstrap`" with
  lefthook Red-Green-Replay gates (workflow.toml prepare comments).
  An adopter without lefthook.yml silently runs WITHOUT those gates —
  a quality gate that exists for members and silently vanishes for
  adopters, with no declaration and no refusal.

Ratified-as-no-op degrades (the GOOD existing pattern, kept): the
fleet-manifest sibling-clone projection renders empty when no
manifest is present (contracts.md states this MUST degrade cleanly).

## 2. The failure-mode taxonomy, which is the actual defect

The same implicit contract fails at three different times today:
pre-dispatch refusal (I2 — the model), post-merge stranding (I1, I3 —
after the irreversible merge, before disposition), and silent
degradation (I4, I5, I6 — the worst class: nothing refuses, nothing
surfaces, behavior just differs for adopters). Each instance is
discovered one broken dispatch at a time. A seventh instance, I7 —
the reconcile janitor venue pinned to the item's historical merge
sha, making post-merge environment fixes unable to ever clear
earlier items — was found after this note's text was fixed and is
recorded as a comment on this plan's epic (2026-08-29); fold it in.

## 3. The requirement this plan adds (maintainer directive, 2026-08-29)

Make the adopter contract EXPLICIT and FAIL-FAST, like a programmatic
API version check:

- R1. One committed declaration surface for the governed repo's
  integration points: post-merge janitor argv, bootstrap recipe
  (exists, v087), master-CI (exists), factory check-suite invocation,
  core-provisioning ref, and any tool-wrapper expectations. Declared
  values run VERBATIM (v087 principle); fleet defaults apply only
  when undeclared.
- R2. One up-front validation pass — at first dispatcher invocation
  against a repo (and re-run when the plugin build or the declaration
  changes) — that checks EVERY declared-or-defaulted expectation
  against the repo and refuses with the COMPLETE enumerated list of
  unmet points in one message, before any dispatch, merge, or
  factory run. No per-instance discovery, no post-merge stranding,
  no silent degrade: an expectation is either met, declared-and-met,
  or a named refusal item.
- R3. Version the contract: a plugin upgrade that ADDS expectations
  fails the validation pass fast with the new points named — never
  strands a mid-pipeline item on an expectation that did not exist
  when the dispatch was admitted.
- R4. Silent degrades are abolished except where a ratified clause
  names the degrade (fleet-manifest projection). I4/I5/I6 each become
  either declared-and-validated or ratified-as-no-op explicitly.

## 4. Verification shape

Positive: an adopter repo with a complete declaration passes
validation and dispatches with zero fleet-tooling present.
Discriminating: removing one declared integration point fails the
validation pass pre-dispatch, naming exactly that point; it never
reaches post-merge. Control: a fleet-member repo with no declarations
still runs today's defaults unchanged and passes validation.

## 5. Provenance

Instances I1-I6 located 2026-08-29 by homelab's coordination seat
from the shipped v0.96.1 payload after I1 stranded homelab's first
clean hardened dispatch (research/001); I7 added the same day from
the hl-cid234 reconcile deadlock. The sweep from the adopter side is
evidence, not the completed audit: the propose-change should finish
the audit in-repo so the class ends here.
