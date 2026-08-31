"""A governed repository's declared merge strategy, resolved and projected.

Binds `SPECIFICATION/scenarios.md` Scenario 107: `dispatcher.merge_mode` is a
typed field of the repository integration contract, so a repository that
declares `squash` gets a squash merge, one that declares nothing gets the fleet
`rebase`, and one that declares something outside the admitted set resolves to
`Defective` and arms no strategy at all. Every case runs through the production
plan build over a committed governed-repository fixture, and reads the answer
back off the argv the auto-merge step would actually spawn -- `pr_arm_argv` --
rather than off the resolution object alone, because the ratified obligation is
about what the dispatch DOES with the value.

ALL THREE ARMS ARE EXERCISED ON BOTH LEGS. The two fixtures sit on different
arms as committed -- the adopter declares `squash`, the fleet member declares
nothing and rests on the default -- so a test that only read them as they stand
would exercise one arm per leg and none of the defective one. Each case
therefore rewrites `dispatcher.merge_mode` inside that fixture's OWN
declaration, leaving every other point exactly as the fixture wrote it, so the
member's fleet-default posture and the adopter's fully-declared one are both
carried through all three arms.

THE DEFECTIVE ARM ARMS NO METHOD, WHICH IS NOT THE SAME AS DEFAULTING. `gh pr
merge` refuses an invocation naming no method, and that refusal is the point:
the alternative is arming a strategy the repository has already said is not its
own. The argv assertion below is therefore about an ABSENCE, so it is made
against the whole list rather than by searching it for a flag.
"""

from __future__ import annotations

import json
from typing import cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_argv import pr_arm_argv
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_contract import (
    ResolvedIntegrationContract,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_declaration import (
    PLUGIN_BLOCK,
    declaration_from_config_text,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    MERGE_MODE_DEFAULT,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_projection import (
    merge_method_flag,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Declared,
    Defective,
    FleetDefault,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    MERGE_MODE_FIELD,
    MERGE_MODE_KEY,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan, build_plan

from tests.integration.governed_repo_fixtures import (
    PAYLOAD_RUN_CONFIG,
    PROBED_DEFAULT_BRANCH,
    GovernedRepo,
    over_both_fixtures,
)

_MERGE_MODE_ATTRIBUTE = MERGE_MODE_FIELD.attribute
_DISPATCHER_BLOCK = "dispatcher"
_UNADMITTED_MODE = "fast-forward"
_PR_NUMBER = 7


def _config_text(*, governed: GovernedRepo, merge_mode: str | None) -> str:
    """This fixture's own declaration with the merge strategy rewritten or removed.

    `None` REMOVES the key, which is the only way to reach the fleet-default arm
    from the adopter fixture: that fixture declares `squash`, and a declaration
    that is present cannot fall back on anything.
    """
    declaration = dict(declaration_from_config_text(config_text=governed.config_text))
    block = dict(cast("dict[str, object]", declaration.get(_DISPATCHER_BLOCK, {})))
    if merge_mode is None:
        _ = block.pop(_MERGE_MODE_ATTRIBUTE, None)
    else:
        block[_MERGE_MODE_ATTRIBUTE] = merge_mode
    declaration[_DISPATCHER_BLOCK] = block
    return json.dumps({PLUGIN_BLOCK: declaration})


def _plan(*, governed: GovernedRepo, config_text: str) -> DispatchPlan:
    """One dispatch plan for a fixture, built exactly as the Dispatcher builds one."""
    return build_plan(
        repo=governed.root,
        work_item_id="fixture-107",
        workflow_toml=governed.root / "workflow.toml",
        goal_file=governed.root / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=governed.root / "janitor-checkout",
        config_text=config_text,
        default_branch=PROBED_DEFAULT_BRANCH,
        committed_workflow_text=PAYLOAD_RUN_CONFIG.read_text(encoding="utf-8"),
    )


def _plan_declaring(*, governed: GovernedRepo, merge_mode: str | None) -> DispatchPlan:
    """A plan off this fixture's declaration with the merge strategy rewritten."""
    return _plan(
        governed=governed, config_text=_config_text(governed=governed, merge_mode=merge_mode)
    )


def _resolution(*, resolved: ResolvedIntegrationContract) -> object:
    """The merge-strategy point's own resolution, off the ONE resolved contract."""
    return resolved.resolutions[_MERGE_MODE_ATTRIBUTE]


def _armed(*, plan: DispatchPlan) -> list[str]:
    return pr_arm_argv(plan=plan, number=_PR_NUMBER)


@over_both_fixtures
def test_the_merge_mode_field_resolves_each_arm_and_projects_to_the_merge_method_flag(
    governed: GovernedRepo,
) -> None:
    """Declared, FleetDefault and Defective, each read back off the auto-merge argv."""
    declared = _plan_declaring(governed=governed, merge_mode="squash")
    conventional = _plan_declaring(governed=governed, merge_mode=None)
    defective = _plan_declaring(governed=governed, merge_mode=_UNADMITTED_MODE)

    assert isinstance(_resolution(resolved=declared.integration), Declared)
    assert declared.integration.contract.merge_mode == "squash"
    assert merge_method_flag(resolved=declared.integration) == "--squash"
    assert _armed(plan=declared) == [
        "gh",
        "pr",
        "merge",
        str(_PR_NUMBER),
        "--squash",
        "--auto",
        "--delete-branch",
    ]

    assert isinstance(_resolution(resolved=conventional.integration), FleetDefault)
    assert conventional.integration.contract.merge_mode == MERGE_MODE_DEFAULT
    assert merge_method_flag(resolved=conventional.integration) == f"--{MERGE_MODE_DEFAULT}"
    assert _armed(plan=conventional)[4] == f"--{MERGE_MODE_DEFAULT}"

    unresolved = _resolution(resolved=defective.integration)
    assert isinstance(unresolved, Defective)
    assert unresolved.key == MERGE_MODE_KEY
    assert _UNADMITTED_MODE in unresolved.reason
    assert merge_method_flag(resolved=defective.integration) is None
    # An ABSENCE, so it is asserted against the whole argv rather than searched for.
    assert _armed(plan=defective) == [
        "gh",
        "pr",
        "merge",
        str(_PR_NUMBER),
        "--auto",
        "--delete-branch",
    ]


@over_both_fixtures
def test_the_committed_fixture_arms_the_strategy_its_own_declaration_names(
    governed: GovernedRepo,
) -> None:
    """The fixtures as committed, so the arms above are anchored to real repositories.

    The adopter's `squash` and the member's fleet `rebase` are DIFFERENT strings
    reached through the same code path, which is what the
    members-and-adopters-identical claim means for this field.
    """
    plan = _plan(governed=governed, config_text=governed.config_text)

    assert plan.integration.defects == ()
    assert merge_method_flag(resolved=plan.integration) == f"--{governed.merge_mode}"
    assert _armed(plan=plan)[4] == f"--{governed.merge_mode}"
