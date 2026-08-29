"""Focused tests for the declared janitor-bootstrap recipe and its resolution.

Covers `_dispatcher_janitor_bootstrap_recipe`: the committed
`dispatcher.janitor_bootstrap` reader, the fleet default convention an ABSENT
key falls back to, the defects a PRESENT key can carry (which never slide onto
the convention), and the operator-facing prose every unresolvable-recipe
refusal renders -- the resolution sentence, the integration point, and the
remedy.
"""

from __future__ import annotations

from inspect import signature
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_bootstrap_recipe import (
    DECLARED_RESOLUTION,
    DEFAULT_RECIPE,
    DEFAULT_RESOLUTION,
    JANITOR_BOOTSTRAP_KEY,
    UNRESOLVED_RECIPE,
    integration_point,
    janitor_bootstrap_recipe_from_block,
    recipe_resolution_sentence,
    remedy,
    resolve_janitor_bootstrap_recipe,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_step_waivers import STEP_WAIVERS_KEY
from livespec_orchestrator_beads_fabro.commands._drive_config_schema import config_key_by_name

_ADOPTER_RECIPE = "./scripts/install-hooks.sh --force"


def test_an_absent_key_resolves_the_fleet_default_convention() -> None:
    """An absent key is an ANSWER -- this repository uses the convention."""
    recipe = janitor_bootstrap_recipe_from_block(block={})

    assert recipe.resolution == DEFAULT_RESOLUTION
    assert recipe.text == DEFAULT_RECIPE
    assert recipe.defect is None
    # The convention reaches these hosts through mise, so its argv keeps the
    # prefix the shipped bootstrap always used.
    assert recipe.command == ("mise", "exec", "--", "just", "install-commit-refuse-hooks")


def test_a_declared_recipe_is_resolved_verbatim_with_no_wrapper_imposed() -> None:
    recipe = janitor_bootstrap_recipe_from_block(
        block={"janitor_bootstrap": {"recipe": _ADOPTER_RECIPE}}
    )

    assert recipe.resolution == DECLARED_RESOLUTION
    assert recipe.text == _ADOPTER_RECIPE
    assert recipe.defect is None
    assert recipe.command == ("./scripts/install-hooks.sh", "--force")


def test_a_declared_recipe_is_split_with_shell_quoting_honoured() -> None:
    recipe = janitor_bootstrap_recipe_from_block(
        block={"janitor_bootstrap": {"recipe": "sh -c 'install the hooks'"}}
    )

    assert recipe.command == ("sh", "-c", "install the hooks")


@pytest.mark.parametrize(
    ("declared", "expected_defect_fragment"),
    [
        pytest.param("just hooks", "is not a mapping", id="not-a-mapping"),
        pytest.param(
            {"owner": "dana"},
            f"`{JANITOR_BOOTSTRAP_KEY}.recipe` is absent",
            id="no-recipe",
        ),
        pytest.param({"recipe": None}, "not a non-empty string", id="null-recipe"),
        pytest.param({"recipe": 7}, "not a non-empty string", id="non-string-recipe"),
        pytest.param({"recipe": "   "}, "not a non-empty string", id="blank-recipe"),
        pytest.param({"recipe": "sh -c 'unbalanced"}, "does not parse", id="unbalanced-quote"),
        pytest.param({"recipe": "''"}, "does not parse", id="no-tokens"),
    ],
)
def test_a_present_but_unusable_declaration_is_a_defect_not_a_fallback(
    declared: object, expected_defect_fragment: str
) -> None:
    """Falling back here would bootstrap a recipe the repository denied is its own."""
    recipe = janitor_bootstrap_recipe_from_block(block={"janitor_bootstrap": declared})

    assert recipe.defect is not None
    assert expected_defect_fragment in recipe.defect
    assert recipe.resolution == DECLARED_RESOLUTION
    assert recipe.text == UNRESOLVED_RECIPE
    assert recipe.command == ()


def test_a_declared_null_key_is_present_rather_than_absent() -> None:
    """`in` rather than a `get` sentinel: JSON null names nothing, but it is a declaration."""
    recipe = janitor_bootstrap_recipe_from_block(block={"janitor_bootstrap": None})

    assert recipe.defect is not None
    assert recipe.text != DEFAULT_RECIPE


def test_the_resolution_sentence_names_the_default_and_where_to_declare_otherwise() -> None:
    sentence = recipe_resolution_sentence(recipe=janitor_bootstrap_recipe_from_block(block={}))

    assert "Resolution attempted: default convention" in sentence
    assert DEFAULT_RECIPE in sentence
    assert JANITOR_BOOTSTRAP_KEY in sentence


def test_the_resolution_sentence_names_a_declared_recipe_and_its_key() -> None:
    sentence = recipe_resolution_sentence(
        recipe=janitor_bootstrap_recipe_from_block(
            block={"janitor_bootstrap": {"recipe": _ADOPTER_RECIPE}}
        )
    )

    assert "Resolution attempted: declared" in sentence
    assert _ADOPTER_RECIPE in sentence
    assert JANITOR_BOOTSTRAP_KEY in sentence


def test_the_resolution_sentence_reports_a_defect_as_a_declaration_not_the_convention() -> None:
    sentence = recipe_resolution_sentence(
        recipe=janitor_bootstrap_recipe_from_block(block={"janitor_bootstrap": {"recipe": ""}})
    )

    assert "Resolution attempted: declared" in sentence
    assert "present but unusable" in sentence
    assert DEFAULT_RECIPE not in sentence


def test_the_integration_point_and_remedy_name_the_resolved_recipe() -> None:
    recipe = janitor_bootstrap_recipe_from_block(
        block={"janitor_bootstrap": {"recipe": _ADOPTER_RECIPE}}
    )

    assert integration_point(recipe=recipe) == (
        f"the governed repository's `{_ADOPTER_RECIPE}` hook-install recipe"
    )
    remediation = remedy(recipe=recipe)
    # Both honest routes are named -- provide the recipe looked for, or declare
    # the one the repository already has -- with the waiver escape last.
    assert _ADOPTER_RECIPE in remediation
    assert JANITOR_BOOTSTRAP_KEY in remediation
    assert STEP_WAIVERS_KEY in remediation


def test_the_recipe_resolves_from_the_committed_livespec_jsonc(tmp_path: Path) -> None:
    _ = (tmp_path / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"dispatcher": '
        '{"janitor_bootstrap": {"recipe": "make install-hooks"}}}}',
        encoding="utf-8",
    )

    recipe = resolve_janitor_bootstrap_recipe(cwd=tmp_path)

    assert recipe.command == ("make", "install-hooks")
    assert recipe.resolution == DECLARED_RESOLUTION


def test_a_repository_declaring_no_dispatcher_block_at_all_uses_the_convention(
    tmp_path: Path,
) -> None:
    assert resolve_janitor_bootstrap_recipe(cwd=tmp_path).text == DEFAULT_RECIPE


def test_the_key_has_no_per_item_override(tmp_path: Path) -> None:
    """Committed configuration only: nothing per-item can redirect the bootstrap.

    Two halves, because either alone would let an override back in. The key is
    absent from the API-configurable / per-item-override registry, so no ledger
    label or API call can set it; and NO resolution surface accepts a work-item
    at all, so there is no input a per-item value could arrive through.
    """
    assert config_key_by_name(key="janitor_bootstrap") is None
    assert set(signature(resolve_janitor_bootstrap_recipe).parameters) == {"cwd"}
    assert set(signature(janitor_bootstrap_recipe_from_block).parameters) == {"block"}
    # The repository-level declaration is what decides, on its own.
    _ = (tmp_path / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"dispatcher": '
        '{"janitor_bootstrap": {"recipe": "make install-hooks"}}}}',
        encoding="utf-8",
    )
    assert resolve_janitor_bootstrap_recipe(cwd=tmp_path).text == "make install-hooks"
