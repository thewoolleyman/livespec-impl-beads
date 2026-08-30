# dev-tooling/checks/

Impl-beads-PRIVATE enforcement scripts — checks that depend on the
beads-issue mapping this plugin defines and therefore cannot ship from
the shared `livespec-dev-tooling` package. Each `<name>.py` here is a
standalone module exposing `main() -> int` (0 = pass, non-zero = fail),
invoked from the `justfile`'s private block via
`uv run python dev-tooling/checks/<name>.py` (NOT `python -m`, since these
are in-repo, not part of the installed `livespec_dev_tooling.checks`
package).

Constraints an agent editing this directory must satisfy:

- **Output discipline.** `print` (ruff T20) and direct `sys.stderr.write`
  (`check-no-write-direct`) are banned. Diagnostics flow through structlog
  (JSON to stderr) — the only sanctioned output surface. structlog is not
  vendored in this repo's own tree, so it is imported from the installed
  `livespec_dev_tooling` package's vendored copy (its path is added to
  `sys.path` at import time); a file-level `# pyright:` pragma silences the
  untyped-structlog diagnostics.
- **Comment discipline.** No line-number anchors in docstrings or comments
  (`check-comment-line-anchors` scans `dev-tooling/`). Reference spec
  sections and symbol names, never line numbers.
- **Per-file 100% coverage** + a paired test at
  `tests/dev-tooling/checks/test_<name>.py` (`check-tests-mirror-pairing`).
- Keyword-only arguments, a `__main__` guard, and a sub-250 LLOC ceiling.

Current checks:

- `work_item_merge_evidence.py` — the beads-private port of the spec'd
  merge-evidence static check (SPECIFICATION/contracts.md
  §"`work_item_merge_evidence` static check"). Reads each closed issue's
  `AuditRecord` from `metadata` via the store; same git-reachability rules
  as the plaintext sibling's JSONL-shaped equivalent; epics exempt
  (child-closure checked instead). Passes trivially when the store is
  empty (the hermetic-fake default tier).
- `spec_id_presence_discipline.py` — executable guard for the narrowing of
  the OVERLOADED spec id field (`WorkItem.spec_commitment_hint`, persisted as
  the beads-native `spec_id` column, carrying both the `plan:<slug>` anchor
  marker and a genuine spec-clause commitment). AST-scans the orchestrator
  package and fails on a bare presence / truthiness test outside a measured
  allowlist; everything else must ask `is_spec_commitment` / `is_plan_anchor`
  from `commands/_plan_anchor.py`. It reports an ABSENCE, so it carries two
  positive controls — a discovery control over the package walk and a matcher
  control over `fixtures/spec_id_presence_control.py.txt` — and refuses to
  report a clean scan when either fails. Editing the allowlist means
  re-measuring: add an entry only after confirming the site fires without it.
- `no_fleet_toolchain_literals.py` — executable guard for
  SPECIFICATION/constraints.md §"Fleet-toolchain literal ban". AST-scans the
  orchestrator package and fails on any fleet-toolchain literal (`mise`, a fleet
  `just` recipe name, `lefthook`, `livespec_dev_tooling`, `livespec-step-timer`,
  or a bare default-branch name used as a ref) outside the single fleet-defaults
  module the `RepoIntegrationContract` schema designates. Only two literal shapes
  count — the constant IS the token, or the token sits in shell command position
  inside it — so comments, docstrings, `__all__` entries and operator-facing
  prose are out of scope by construction. Two MEASURED allow-lists carry work
  already sliced elsewhere: the workflow payload and prompt files (retired by
  carrier C5-payload) and the dispatcher-package sites still resolving a premise
  from a constant. A STALE entry in either list FAILS, so a converted site cannot
  stay exempt. It reports an ABSENCE, so it carries four positive controls —
  package and payload discovery, a designation control asserting the exempt
  module is the one the schema imports, and a matcher control over
  `fixtures/fleet_toolchain_literal_control.py.txt` — and refuses to report a
  clean scan when any fails. The two concerns live in two modules because they
  change for different reasons: this one owns the scope, the allow-lists and the
  controls, while the sibling private helper
  `_fleet_toolchain_literals_matcher.py` owns what counts as a literal at all.
- `work_item_state_invariants.py` — the beads-private work-item-state
  doctor check (SPECIFICATION/contracts.md §"Work-item beads-issue
  mapping" invariants block; L1a slice S6). Walks every materialized
  work-item and emits the fail-soft non-sentinel-`rank` + rank-key-length
  WARNINGS for live heads (advisory, exit 0) plus the hard
  `active ⟹ assignee` and stored
  `blocked ⟹ blocked_reason ∈ {needs-human, infra-external}` ERRORS
  (exit non-zero). No git / network I/O; passes trivially on the empty
  hermetic-fake tenant.
