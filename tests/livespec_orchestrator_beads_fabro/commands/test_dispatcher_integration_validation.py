"""The pre-dispatch schema-validation pass over a governed repository's declaration.

`SPECIFICATION/contracts.md`, the repository-integration-contract section's
"contract version is schema version" clause, requires the executing build to name
the schema version it requires, to validate the repository's declaration against
that version before the dispatch, and to refuse as a pre-dispatch precondition
error (exit `3`, journaled) enumerating EVERY `Defective` point in ONE message,
with no hand-maintained list of keys anywhere and no already-admitted
mid-pipeline item stranded on an expectation a later build added.

These tests pin all four halves of that clause, plus the two boundaries it is
easiest to get wrong at. The first is `SPECIFICATION/scenarios.md` Scenario 97's
fleet-member case: a repository that declares NONE of the integration keys is
ADMITTED, which is also the mechanism by which a later build's added expectation
-- an ABSENCE, in an earlier repository -- cannot strand an item that is already
mid-pipeline. The second is the default branch, the one schema field whose
declaration is the repository itself, which a declaration pass never grades.

The module is reached through `_validation()`, which asserts the module FILE
exists before importing it, so a slice that has not landed yet fails on a genuine
assertion rather than on an unimportable module.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_check_suite_view import (
    check_suite_refusal,
    resolve_janitor_check_suite,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    INTEGRATION_CONTRACT_SCHEMA_VERSION,
    INTEGRATION_FIELDS,
    JANITOR_CHECK_SUITE_KEY,
    MERGE_MODE_KEY,
)
from livespec_orchestrator_beads_fabro.commands.dispatcher import dispatch_preamble

_COMMANDS = Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
_PACKAGE = "livespec_orchestrator_beads_fabro.commands"
_VALIDATION_PATH = _COMMANDS / "_dispatcher_integration_validation.py"

_EXIT_PRECONDITION_ERROR = 3
_PLUGIN_BLOCK = "livespec-orchestrator-beads-fabro"
_CORE_REPO_KEY = f"{_PLUGIN_BLOCK}.compat.core_repo"


def _validation() -> ModuleType:
    assert _VALIDATION_PATH.is_file()
    return importlib.import_module(f"{_PACKAGE}._dispatcher_integration_validation")


def _repo_with(*, tmp_path: Path, declaration: dict[str, object]) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        json.dumps({_PLUGIN_BLOCK: declaration}), encoding="utf-8"
    )
    return repo


def _declaring_null_at(*, paths: tuple[str, ...]) -> dict[str, object]:
    """A declaration that WRITES an unusable value at each of the given lookup paths."""
    root: dict[str, object] = {}
    for path in paths:
        block = root
        segments = path.split(".")
        for segment in segments[:-1]:
            child = block.get(segment)
            if not isinstance(child, dict):
                child = {}
                block[segment] = child
            block = cast("dict[str, object]", child)
        block[segments[-1]] = None
    return root


def test_the_pass_grades_a_declaration_against_the_version_this_build_requires() -> None:
    """The verdict names the schema version the EXECUTING BUILD requires."""
    validation = _validation().validate_declaration(declaration={})

    assert validation.schema_version == INTEGRATION_CONTRACT_SCHEMA_VERSION
    assert validation.defects == ()


def test_a_repository_that_declares_none_of_the_integration_keys_is_admitted() -> None:
    """Scenario 97's fleet-member case, and the non-stranding mechanism itself.

    An expectation a LATER build adds appears in an EARLIER repository as an
    ABSENCE. Refusing on absence would refuse every governed repository the
    moment the schema grew -- including one whose item is already mid-pipeline --
    so the pass grades what the repository WROTE and admits what it did not.
    """
    module = _validation()

    assert module.validation_refusal(validation=module.validate_declaration(declaration={})) is None


def test_a_merge_mode_outside_the_closed_enum_is_defective_and_named() -> None:
    """Scenario 107's third case: an unsupported merge method refuses pre-dispatch."""
    module = _validation()

    validation = module.validate_declaration(declaration={"dispatcher": {"merge_mode": "octopus"}})

    assert [defect.key for defect in validation.defects] == [MERGE_MODE_KEY]
    refusal = module.validation_refusal(validation=validation)
    assert refusal is not None
    assert MERGE_MODE_KEY in refusal
    assert "octopus" in refusal


def test_every_defective_point_is_enumerated_in_one_message() -> None:
    """The whole unmet set at once, not the first entry of it."""
    module = _validation()

    validation = module.validate_declaration(
        declaration={
            "dispatcher": {"merge_mode": "octopus", "janitor": {"check_suite": None}},
            "compat": {"core_repo": ""},
        }
    )

    refusal = module.validation_refusal(validation=validation)
    assert refusal is not None
    named = {defect.key for defect in validation.defects}
    assert named == {MERGE_MODE_KEY, JANITOR_CHECK_SUITE_KEY, _CORE_REPO_KEY}
    assert all(key in refusal for key in named)
    assert str(INTEGRATION_CONTRACT_SCHEMA_VERSION) in refusal


def test_an_ancestor_that_is_present_and_is_not_a_mapping_is_a_written_defect() -> None:
    """The repository put something at the block, and a child cannot hang off it."""
    module = _validation()

    validation = module.validate_declaration(declaration={"dispatcher": "just-a-string"})

    assert MERGE_MODE_KEY in {defect.key for defect in validation.defects}


def test_the_graded_points_come_from_the_schema_rather_than_a_key_list() -> None:
    """No hand-maintained list of keys: the closed field set IS the graded set.

    A declaration writing an unusable value at EVERY declared point yields
    exactly the schema's own declared key set, so a field ratified later is
    graded with no edit here; and the module's source carries no committed key of
    its own for such a field to have to be added to.
    """
    module = _validation()
    declarable = tuple(field for field in INTEGRATION_FIELDS if field.declared_in_config)

    validation = module.validate_declaration(
        declaration=_declaring_null_at(paths=tuple(field.path for field in declarable))
    )

    assert {defect.key for defect in validation.defects} == {field.key for field in declarable}
    source = _VALIDATION_PATH.read_text(encoding="utf-8")
    assert [field.key for field in INTEGRATION_FIELDS if field.key in source] == []


def test_the_default_branch_is_not_graded_by_a_declaration_pass() -> None:
    """The one field whose declaration is the repository itself is skipped.

    Refusing here on an unprobed branch would send an operator to fix a committed
    key that does not exist; its own two-route resolution refuses at the seam
    that probes it.
    """
    validation = _validation().validate_declaration(declaration={"default_branch": ""})

    assert validation.defects == ()


def test_a_declared_parent_s_missing_half_is_left_to_the_step_that_owns_it() -> None:
    """A half-declaration is an ABSENCE at the missing point, not a written defect.

    The master-CI preflight already refuses on it pre-dispatch, naming its own
    resolution and its committed waiver; grading it here as well would move that
    refusal to a surface with no waiver and silently retire the escape hatch.
    """
    validation = _validation().validate_declaration(
        declaration={"dispatcher": {"master_ci": {"workflow": "build.yml"}}}
    )

    assert validation.defects == ()


def test_the_dispatch_preamble_refuses_with_exit_three_and_journals_the_refusal(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """The ratified pre-dispatch refusal: exit 3, every point named, journaled."""
    repo = _repo_with(
        tmp_path=tmp_path,
        declaration={"dispatcher": {"merge_mode": "octopus", "janitor": {"check_suite": None}}},
    )
    journal = tmp_path / "journal.jsonl"
    args = argparse.Namespace(fabro_bin=None, janitor=None, journal=str(journal))

    outcome = dispatch_preamble(args=args, repo=repo)

    assert outcome == (None, _EXIT_PRECONDITION_ERROR)
    stderr = capsys.readouterr().err
    assert MERGE_MODE_KEY in stderr
    assert JANITOR_CHECK_SUITE_KEY in stderr
    records = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    assert [record["stage"] for record in records] == [_validation().SCHEMA_VALIDATION_STAGE]
    assert records[0]["schema_version"] == INTEGRATION_CONTRACT_SCHEMA_VERSION
    assert records[0]["outcome"] == "refused"
    assert {defect["key"] for defect in records[0]["defects"]} == {
        MERGE_MODE_KEY,
        JANITOR_CHECK_SUITE_KEY,
    }


def test_an_admitted_declaration_is_neither_refused_nor_journaled(tmp_path: Path) -> None:
    """A sound declaration proceeds, and writes no record of its own.

    The dispatch record already journals the whole resolved contract, and a
    second record here would cost a LATER preflight's refusal its
    zero-side-effect guarantee.
    """
    repo = _repo_with(tmp_path=tmp_path, declaration={"dispatcher": {"merge_mode": "squash"}})
    journal = tmp_path / "journal.jsonl"
    args = argparse.Namespace(fabro_bin=None, janitor=None, journal=str(journal))

    assert _validation().schema_validation_refusal(args=args, repo=repo) is None
    assert not journal.exists()


def test_an_already_admitted_mid_pipeline_item_is_not_refused_by_a_later_expectation(
    tmp_path: Path,
) -> None:
    """The reconcile valve carries an admitted item forward on its OWN point only.

    Same declaration, two surfaces: the admission gate refuses it, while the
    surface that finishes an already-admitted item gates on the single point it
    is about to use and proceeds. That asymmetry is what keeps a mid-pipeline
    item off an expectation a later build added.
    """
    declaration: dict[str, object] = {"dispatcher": {"merge_mode": "octopus"}}
    repo = _repo_with(tmp_path=tmp_path, declaration=declaration)
    module = _validation()

    admission = module.validation_refusal(
        validation=module.validate_declaration(declaration=declaration)
    )
    mid_pipeline = check_suite_refusal(
        check_suite=resolve_janitor_check_suite(cwd=repo, janitor=None)
    )

    assert admission is not None
    assert mid_pipeline is None
