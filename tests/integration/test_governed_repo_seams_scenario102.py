"""Members-and-adopters-identical is a FAILING TEST, not prose.

Binds `SPECIFICATION/scenarios.md` Scenario 102 and the adopter-and-member-fixtures
bullet of `SPECIFICATION/constraints.md`'s governed-repository integration
constraints. Every case below is one dispatch-path seam -- preflight, contract
resolution, plan build, input rendering, workflow validation, and the sandbox's
prepare parameters with the sandbox itself stubbed -- run through PRODUCTION code
and parametrized over BOTH committed governed-repository fixtures.

WHAT THE ADOPTER LEG BUYS THAT THE MEMBER LEG CANNOT. The member fixture rests on
fleet defaults, so a fleet premise smuggled into the orchestrator agrees with it
and stays invisible; the adopter fixture declares every point through the schema
and carries none of this fleet's tooling, so the same premise has nowhere to be
read from and the seam answers with a literal the adopter never chose. That is
why the last case scans every rendered projection with the literal-ban gate's own
matcher and asserts a fleet token appears on the member leg and on NO adopter
one: an absence-assertion whose instrument is proven able to return a hit.
"""

from __future__ import annotations

from livespec_orchestrator_beads_fabro.commands._dispatcher_ci_pipeline_view import (
    resolve_master_ci_pipeline,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_declaration import (
    declaration_from_config_text,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_projection import (
    CONTRACT_INPUT_NAMES,
    contract_prepare_parameters,
    contract_prompt_variables,
    contract_workflow_inputs,
    merge_method_flag,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    INTEGRATION_FIELDS,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_validation import (
    validate_declaration,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan, build_plan

from tests.integration.governed_repo_fixtures import (
    FLEET_TOOLCHAIN_FILES,
    PAYLOAD_RUN_CONFIG,
    PROBED_DEFAULT_BRANCH,
    GovernedRepo,
    fleet_toolchain_token,
    over_both_fixtures,
)


@over_both_fixtures
def test_the_committed_fixture_carries_the_toolchain_shape_it_claims(
    governed: GovernedRepo,
) -> None:
    """The member carries the whole fleet toolchain; the adopter carries none of it.

    Structurally AND textually. File presence alone would pass an adopter tree
    that had grown a fleet invocation inside a file of its own naming, so the
    whole tree is also read line by line through the literal-ban gate's matcher.
    """
    present = {name for name in FLEET_TOOLCHAIN_FILES if (governed.root / name).is_file()}
    expected = set(FLEET_TOOLCHAIN_FILES) if governed.carries_fleet_toolchain else set()
    tokens = {
        token
        for path in governed.files
        for line in path.read_text(encoding="utf-8").splitlines()
        if (token := fleet_toolchain_token(line=line)) is not None
    }

    assert present == expected
    assert bool(tokens) is governed.carries_fleet_toolchain
    assert (governed.root / ".livespec.jsonc").is_file()
    assert (governed.root / "hooks" / "pre-commit").is_file()


@over_both_fixtures
def test_the_preflight_seam_admits_the_declaration_and_looks_up_its_own_pipeline(
    governed: GovernedRepo,
) -> None:
    """Seam: pre-dispatch. Both fixtures are admitted, each on its OWN pipeline."""
    validation = validate_declaration(
        declaration=declaration_from_config_text(config_text=governed.config_text)
    )
    pipeline = resolve_master_ci_pipeline(cwd=governed.root)

    assert validation.defects == ()
    assert pipeline.defect is None
    assert (pipeline.workflow, pipeline.job) == governed.master_ci


@over_both_fixtures
def test_the_contract_resolution_seam_answers_every_point_with_no_defect(
    governed: GovernedRepo,
) -> None:
    """Seam: contract resolution. The whole closed set resolves for both fixtures."""
    resolved = governed.resolved()

    assert resolved.defects == ()
    assert set(resolved.resolutions) == {field.attribute for field in INTEGRATION_FIELDS}
    assert resolved.contract.janitor_check_suite == governed.janitor_check_suite
    assert resolved.contract.sandbox_check_suite == governed.sandbox_check_suite
    assert resolved.contract.janitor_bootstrap_recipe == governed.bootstrap_recipe
    assert resolved.contract.default_branch == PROBED_DEFAULT_BRANCH


@over_both_fixtures
def test_the_plan_build_seam_projects_the_janitor_off_the_one_resolved_contract(
    governed: GovernedRepo,
) -> None:
    """Seam: plan build. The host janitor argv is a projection, never a second read."""
    plan = _plan(governed=governed)

    assert plan.integration.contract == governed.resolved().contract
    assert plan.janitor == governed.janitor_check_suite
    assert merge_method_flag(resolved=plan.integration) == f"--{governed.merge_mode}"


@over_both_fixtures
def test_the_input_rendering_seam_sends_exactly_what_the_payload_declares(
    governed: GovernedRepo,
) -> None:
    """Seam: input rendering and workflow validation, against the REAL payload.

    The three sets the ratified seam-equivalence clause compares -- what the
    payload declares, what the schema projects, and what the Dispatcher renders
    for THIS repository -- are asserted identical here per fixture, which is the
    per-fixture half of the repo-wide `check-seam-equivalence` gate.
    """
    declared = contract_workflow_inputs(
        committed_text=PAYLOAD_RUN_CONFIG.read_text(encoding="utf-8")
    )
    plan = _plan(governed=governed)
    rendered = {pair.split("=", 1)[0]: pair.split("=", 1)[1] for pair in plan.integration_inputs}

    assert declared == frozenset(CONTRACT_INPUT_NAMES.values())
    assert set(rendered) == set(declared)
    assert rendered == dict(contract_prompt_variables(resolved=plan.integration))


@over_both_fixtures
def test_the_sandbox_seam_receives_the_values_it_never_resolves(
    governed: GovernedRepo,
) -> None:
    """Seam: the sandbox prepare chain, stubbed. It consumes values, never a resolver."""
    parameters = contract_prepare_parameters(resolved=governed.resolved())

    assert parameters.sandbox_exempt_marker == "livespec.sandboxExempt"
    assert parameters.conformance_hook_install == governed.conformance_hook_install
    # The prepare-toolchain premises are the ratified explicit no-op VALUE for
    # both fixtures -- a member's are provisioned by the payload's own chain, and
    # an adopter carries none at all. Neither is an absence anybody inferred.
    assert parameters.toolchain_mise == ()
    assert parameters.toolchain_lefthook == ()


@over_both_fixtures
def test_no_fleet_toolchain_literal_reaches_an_adopter_projection(
    governed: GovernedRepo,
) -> None:
    """The teeth: an undeclared fleet premise fails HERE, not in an adopter's production.

    The member leg is the positive control. It must find a token, because an
    absence reported by an instrument that cannot return a hit is not evidence.
    """
    plan = _plan(governed=governed)
    lines = [
        *plan.janitor,
        *plan.integration_inputs,
        plan.janitor_core_repo_url,
        plan.janitor_core_ref,
        *contract_prepare_parameters(resolved=plan.integration).conformance_hook_install,
    ]
    tokens = {token for line in lines if (token := fleet_toolchain_token(line=line)) is not None}

    assert bool(tokens) is governed.carries_fleet_toolchain


def _plan(*, governed: GovernedRepo) -> DispatchPlan:
    """One dispatch plan for a fixture, built exactly as the Dispatcher builds one."""
    return build_plan(
        repo=governed.root,
        work_item_id="fixture-1",
        workflow_toml=governed.root / "workflow.toml",
        goal_file=governed.root / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=governed.root / "janitor-checkout",
        config_text=governed.config_text,
        default_branch=PROBED_DEFAULT_BRANCH,
        committed_workflow_text=PAYLOAD_RUN_CONFIG.read_text(encoding="utf-8"),
    )
