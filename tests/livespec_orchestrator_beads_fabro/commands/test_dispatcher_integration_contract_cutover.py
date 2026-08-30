"""The per-key resolvers are RETIRED, and every family now reads one generic resolver.

Eight modules across four families each re-derived the same three-arm
absent/default/defective decision, each with its own copy of the wording and each
free to drift. `SPECIFICATION/contracts.md`, the repository-integration-contract
section, retires them in favour of one schema and one resolver. These tests pin
the retirement itself -- the modules are GONE, not shimmed -- and pin that each
retired family's committed key still resolves, unchanged, as a schema field.

The retirement is asserted on the FILESYSTEM rather than on an import failure: a
module emptied down to a re-export shim still imports perfectly well, and a shim
is exactly the half-migration this item exists to avoid. Each surviving
projection is likewise reached through `_view()`, which asserts its module FILE
exists before importing it, so a cutover that has not landed yet fails on a
genuine assertion rather than on an unimportable module.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    FLEET_CORE_REPO_URL,
    JANITOR_BOOTSTRAP_RECIPE_DEFAULT,
    JANITOR_CHECK_SUITE_DEFAULT,
    MASTER_CI_JOB_DEFAULT,
    MASTER_CI_WORKFLOW_DEFAULT,
    UNRESOLVED_NAME,
)

_COMMANDS = Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
_PACKAGE = "livespec_orchestrator_beads_fabro.commands"

_RETIRED_MODULES = (
    "_dispatcher_master_ci_pipeline.py",
    "_dispatcher_master_ci_lookups.py",
    "_dispatcher_master_ci_preflight.py",
    "_dispatcher_master_ci_refusals.py",
    "_dispatcher_janitor_bootstrap_recipe.py",
    "_dispatcher_step_janitor_bootstrap.py",
    "_dispatcher_janitor_check_suite.py",
    "_dispatcher_janitor_core_provisioning.py",
)

_CALL_SITES = ("_dispatcher_plan_build.py", "_dispatcher_janitor_venue.py")


def _view(*, name: str) -> ModuleType:
    assert (_COMMANDS / f"{name}.py").is_file()
    return importlib.import_module(f"{_PACKAGE}.{name}")


def test_every_per_key_resolver_module_is_deleted_rather_than_shimmed() -> None:
    """The eight modules are GONE: a re-export shim would leave two resolution paths alive."""
    surviving = [name for name in _RETIRED_MODULES if (_COMMANDS / name).exists()]
    assert surviving == []


def test_no_module_anywhere_still_imports_a_retired_per_key_resolver() -> None:
    """A partial migration leaving two resolution paths alive is worse than none."""
    stems = tuple(name.removesuffix(".py") for name in _RETIRED_MODULES)
    offenders = [
        f"{path}:{stem}"
        for path in (*_COMMANDS.rglob("*.py"), *Path("tests").rglob("*.py"))
        if path.name != Path(__file__).name
        for stem in stems
        if stem in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_the_two_named_call_sites_read_integration_points_through_the_contract() -> None:
    """Plan build and the janitor venue name no per-key module, and both read the contract.

    The venue no longer resolves the default-branch FIELD itself: the plan
    resolves the whole contract once and the venue projects `default_branch`
    off it, which is the resolve-once-project-everywhere rule one step further
    than the cutover this file guards left it.
    """
    for name in _CALL_SITES:
        source = (_COMMANDS / name).read_text(encoding="utf-8")
        assert "_dispatcher_integration_" in source
    venue = (_COMMANDS / "_dispatcher_janitor_venue.py").read_text(encoding="utf-8")
    assert "plan.integration.contract.default_branch" in venue
    assert "resolve_default_branch" not in venue


def test_the_master_ci_key_still_resolves_with_its_ratified_semantics() -> None:
    """Absent falls back to the convention; a declared block must name BOTH halves."""
    from_block = _view(name="_dispatcher_ci_pipeline_view").master_ci_pipeline_from_block
    absent = from_block(block={})
    assert (absent.workflow, absent.job) == (MASTER_CI_WORKFLOW_DEFAULT, MASTER_CI_JOB_DEFAULT)
    assert absent.defect is None
    declared = from_block(block={"master_ci": {"workflow": "B", "job": "g"}})
    assert (declared.workflow, declared.job, declared.defect) == ("B", "g", None)
    half = from_block(block={"master_ci": {"workflow": "B"}})
    assert half.defect is not None
    assert (half.workflow, half.job) == (UNRESOLVED_NAME, UNRESOLVED_NAME)


def test_the_check_suite_key_still_resolves_with_its_ratified_semantics() -> None:
    """Absent falls back; the committed declaration still outranks the `--janitor` override."""
    from_block = _view(name="_dispatcher_check_suite_view").janitor_check_suite_from_block
    override = ("make", "ci")
    assert from_block(block={}, janitor=None).command == JANITOR_CHECK_SUITE_DEFAULT
    assert from_block(block={}, janitor=override).command == override
    declared = from_block(block={"janitor": {"check_suite": "just verify"}}, janitor=override)
    assert declared.command == ("just", "verify")


def test_the_bootstrap_recipe_key_still_resolves_and_is_still_re_verified(tmp_path: Path) -> None:
    """Both halves of the one integration point now live in one module."""
    recipes = _view(name="_dispatcher_hook_install_recipe")
    absent = recipes.janitor_bootstrap_recipe_from_block(block={})
    assert absent.command == JANITOR_BOOTSTRAP_RECIPE_DEFAULT
    _ = (tmp_path / "justfile").write_text("install-commit-refuse-hooks:\n\techo hi\n")
    assert recipes.hook_install_recipe_present(repo=tmp_path, recipe=absent) is True
    defective = recipes.janitor_bootstrap_recipe_from_block(block={"janitor_bootstrap": {}})
    assert defective.defect is not None
    assert recipes.hook_install_recipe_present(repo=tmp_path, recipe=defective) is False


def test_the_compat_keys_still_resolve_with_their_ratified_asymmetry() -> None:
    """The repo URL has a fleet default; the pin has none and never gets a moving tip."""
    resolve = _view(name="_dispatcher_core_provisioning_view").resolve_janitor_core_provisioning
    silent = resolve(config_text="{}")
    assert silent.repo_url == FLEET_CORE_REPO_URL
    assert silent.ref == UNRESOLVED_NAME
    assert silent.defect is not None
    declared = resolve(
        config_text=(
            '{ "livespec-orchestrator-beads-fabro": { "compat": '
            '{ "pinned": "v1", "core_repo": "https://example.test/c.git" } } }'
        )
    )
    assert (declared.ref, declared.repo_url, declared.defect) == (
        "v1",
        "https://example.test/c.git",
        None,
    )
