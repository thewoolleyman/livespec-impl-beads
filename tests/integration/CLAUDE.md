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

Coverage rules: 100% line + branch on every covered module, as everywhere in
this repo. Build state through the public store/client seam (or a small
read-only stub for shapes the fake's public surface never produces); never read
or write a live tenant DB.
