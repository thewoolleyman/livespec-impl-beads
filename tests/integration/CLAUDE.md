# tests/integration/

Integration-tier behavior journeys for the `livespec_orchestrator_beads_fabro` package —
tests that exercise a primitive through its REAL store/client seam against the
in-memory `FakeBeadsClient` (the hermetic CI backend and the
no-live-connection runtime fallback), rather than mocking the function under
test. This is the tier `SPECIFICATION/constraints.md` §"Heading taxonomy"
requires for a `scenarios.md` heading binding (integration-tier-or-above, never
a unit-tier test); its dotted node-id prefix `tests.integration` is in the
`heading_coverage` check's default allowlist.

- `test_regroom_state_machine_scenario9.py` — binds
  `SPECIFICATION/scenarios.md` "Scenario 9 — needs-regroom state and
  transitions": the three transitions of the `livespec_orchestrator_beads_fabro.regroom`
  state machine (enter on an intake Definition-of-Ready failure, enter on a
  Dispatcher non-convergence bounce, exit by filing `ready` replacement
  slices), plus the refuse-don't-drop guarantee and the expected-error
  surface. Each case owns its backend isolation via a local
  `reset_fake_singleton()` fixture; there is no shared conftest at this tier.
- `test_dispatcher_acceptance_needs_attention.py` — the ratified evidence rule
  of `SPECIFICATION/contracts.md` §"Post-merge acceptance (`acceptance -> done`)"
  and §"The NEEDS_ATTENTION verdict": an unobservable telemetry leg with a
  readable merged diff, and effective criteria that parse to zero gradeable
  assertions, each park the item in `acceptance` under the AI-dispositive
  `ai-only` policy instead of disposing of it. Only `run_dispatch` and the
  acceptance pass's `CommandRunner` are stood in; the verdict function, the
  disposition, and the ledger writes are production code.
- `test_reconcile_runs_ledger_gate_scenarios.py` — binds
  `SPECIFICATION/scenarios.md` Scenarios 104, 105 and 106: the run-inventory
  reconciler driven end to end through `reconcile_runs`, over work-items
  seeded and closed through the REAL store seam, a REAL preserve-by-reference
  ledger comment, and a real on-disk `JournalFile`. Only the two seams that
  leave the process — the `fabro` CLI and the factory's HTTP face — are stood
  in; the HTTP stand-in snapshots the item's ledger comments at each call, so
  the export-before-terminate ordering is OBSERVED rather than inferred from
  the end state.

- `test_governed_repo_seams_scenario102.py` and
  `test_sandbox_exempt_hook_honor_scenario108.py` — bind
  `SPECIFICATION/scenarios.md` Scenarios 102 and 108 and the
  adopter-and-member-fixtures bullet of `SPECIFICATION/constraints.md`
  §"Governed-repository integration constraints". Every dispatch-path seam
  (preflight, contract resolution, plan build, input rendering, workflow
  validation, and the sandbox prepare parameters with the sandbox stubbed) runs
  through PRODUCTION code parametrized over the two committed
  governed-repository fixtures under `fixtures/governed_repos/`: a fleet member
  carrying the fleet toolchain and declaring no optional integration key, and an
  ADOPTER declaring every point through the contract schema while carrying none
  of this fleet's tooling. `governed_repo_fixtures.py` holds what the two
  fixtures are and what each seam owes each of them, so one parametrized test
  body asserts the SHAPE for both legs instead of branching on a fixture's name.
  The second module runs each fixture's commit-blocking hook in a sandbox-shaped
  checkout against the marker key the contract resolved, with a
  refuses-without-the-marker control and a deliberately non-honoring adopter
  variant that must fail.

- `test_seam_equivalence_contract_inputs_scenario100.py`,
  `test_schema_validation_refusal_scenario101.py` and
  `test_merge_mode_projection_scenario107.py` — bind
  `SPECIFICATION/scenarios.md` Scenarios 100, 101 and 107, each over BOTH
  governed-repository fixtures. The first loads the shipped
  `check-seam-equivalence` gate by path and runs it over throwaway repositories
  holding the REAL committed payload beside a fixture's declaration, one seeded
  per ratified disagreement (a token with no rendered input, a rendered input no
  position reads, a token where the pinned engine does not expand it), with the
  unseeded repository as the positive control that the gate can report clean.
  The second drives the REAL `dispatcher.main(argv=["dispatch", ...])` CLI over a
  fixture declaration carrying two unusable points and asserts the pre-dispatch
  precondition exit code, one message enumerating both committed keys, and a
  journal holding that refusal and nothing else; its control is the same
  invocation on the pristine declaration, discriminated by journal STAGE because
  every pre-dispatch precondition error shares one exit code. The third rewrites
  `dispatcher.merge_mode` inside each fixture's own declaration to reach all
  three resolver arms and reads each answer back off the auto-merge argv the
  dispatch would spawn. All three inject their variations into the COMMITTED
  fixture declarations rather than hand-writing a third repository, so the two
  legs stay the member's fleet-default posture and the adopter's fully-declared
  one.

- `test_declared_integration_points_scenario96.py`,
  `test_integration_validation_pass_scenario97.py` and
  `test_janitor_venue_merged_tip_scenario98.py` — bind
  `SPECIFICATION/scenarios.md` Scenarios 96, 97 and 98, each over BOTH
  governed-repository fixtures. The first walks the schema's own closed field
  set through the ONE generic resolver, asserting per point that a committed
  declaration resolves `Declared` carrying its value verbatim, that a truly
  absent key resolves `FleetDefault` where the schema declares one and
  `Defective` where none exists, and that a present-but-null key is `Defective`
  rather than a slide onto the convention; a sibling case asserts a committed
  check-suite outranks the per-invocation `--janitor` override, with the
  inheriting leg as the control that the override is reachable at all. The
  second drives the pre-dispatch validation pass's two-sided verdict — the
  committed declaration admitted unchanged, two unmet points refused once with
  both enumerated — and models a plugin upgrade by appending a field to the
  closed set, so an earlier repository's ABSENCE stays ungraded (nothing
  mid-pipeline is stranded) while a written-but-unusable point refuses fast. The
  third builds a REAL repository whose item merged before a later
  janitor-environment fix landed, resolves the venue and provisions there
  through production code, and controls the claim by provisioning the same
  repository at the retired historical merge sha, which cannot carry the fix;
  its sibling case asserts a tip that does not contain the merge degrades with
  the missing point and remedy, running the merge-presence check and nothing
  else.

Coverage rules: 100% line + branch on every covered module, as everywhere in
this repo. Build state through the public store/client seam (or a small
read-only stub for shapes the fake's public surface never produces); never read
or write a live tenant DB.
