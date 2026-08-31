"""One up-front pass admits what a repository wrote and refuses the whole unmet set.

Binds `SPECIFICATION/scenarios.md` Scenario 97. Both cases drive the REAL
pre-dispatch `validate_declaration` / `validation_refusal` pair over BOTH
committed governed-repository fixtures, injecting their variations into each
fixture's OWN declaration.

HOW THIS DIFFERS FROM THE SCENARIO 101 BINDING NEXT DOOR, which also exercises a
refusal of this pass. That one measures what an OPERATOR sees -- the CLI exit
code, the journal record, and the claim only the whole CLI path can make, that no
factory run was created -- for a declaration carrying two unusable points. This
one measures the PASS's own two-sided verdict on one declaration: that the
committed declaration is admitted UNCHANGED, and that the same declaration with
two points unmet earns exactly ONE refusal enumerating BOTH. The fleet-member leg
is what makes the first half the scenario's own control, since that fixture
declares none of the optional integration keys and must still be admitted.

AND THE SECOND CASE IS THE HALF NEITHER BINDING COVERED: a plugin upgrade that
adds an integration-point expectation. It is modelled the way an upgrade
actually arrives -- a new field appended to the schema's closed set -- so the two
directions can be told apart. An EARLIER repository that never wrote at the new
point is an ABSENCE, which the pass leaves ungraded, and that is precisely why an
already-admitted mid-pipeline item is not stranded by the upgrade. A repository
that DID write there, unusably, is a defect OF THE DECLARATION and refuses fast
naming the new point.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import cast

import pytest
from livespec_orchestrator_beads_fabro.commands import _dispatcher_integration_validation
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_declaration import (
    declaration_from_config_text,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_field import (
    SHAPE_NAME,
    IntegrationField,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    COMPAT_CORE_REPO_KEY,
    INTEGRATION_FIELDS,
    MERGE_MODE_KEY,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_validation import (
    validate_declaration,
    validation_refusal,
)

from tests.integration.governed_repo_fixtures import GovernedRepo, over_both_fixtures

# The two points written UNMET. One hangs off the plugin block and one off the
# `dispatcher` block, so the enumeration is shown to cross the two committed
# blocks rather than listing one family twice. `None` names nothing at all and
# `fast-forward` is not one of the admitted merge modes.
_UNMET: tuple[tuple[str, object], ...] = (
    ("compat.core_repo", None),
    ("dispatcher.merge_mode", "fast-forward"),
)
_UNMET_KEYS = (COMPAT_CORE_REPO_KEY, MERGE_MODE_KEY)

# The expectation an UPGRADED plugin build adds. Required, like every point whose
# ratified semantics would admit no safe default, and absent from both committed
# fixtures -- which is what an earlier repository looks like to a later build.
_LATER_BUILD_FIELD = IntegrationField(
    attribute="later_build_expectation",
    key="dispatcher.later_build_expectation",
    path="dispatcher.later_build_expectation",
    shape=SHAPE_NAME,
    required=True,
)


@over_both_fixtures
def test_the_committed_declaration_is_admitted_while_two_unmet_points_refuse_once_naming_both(
    governed: GovernedRepo,
) -> None:
    """Admitted unchanged on one side; one refusal carrying the COMPLETE list on the other."""
    committed = declaration_from_config_text(config_text=governed.config_text)

    admitted = validate_declaration(declaration=committed)
    refused = validate_declaration(declaration=_unmet(declaration=committed))
    message = validation_refusal(validation=refused)

    assert admitted.defects == ()
    assert validation_refusal(validation=admitted) is None
    assert [defect.key for defect in refused.defects] == list(_UNMET_KEYS)
    assert message is not None
    assert len([line for line in message.splitlines() if line.startswith("ERROR: refusing")]) == 1
    for key in _UNMET_KEYS:
        assert f"`{key}`" in message


@over_both_fixtures
def test_an_expectation_a_later_build_adds_refuses_when_written_and_never_strands_an_absence(
    governed: GovernedRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The upgraded build admits an absence and refuses a written-but-unusable point.

    The refusing half is the positive control for the admitting one: if the
    appended field never reached the pass, no refusal could name it, and the
    "an absence is admitted" assertion would be measuring a schema that never
    grew.
    """
    monkeypatch.setattr(
        _dispatcher_integration_validation,
        "INTEGRATION_FIELDS",
        (*INTEGRATION_FIELDS, _LATER_BUILD_FIELD),
    )
    committed = declaration_from_config_text(config_text=governed.config_text)

    upgraded = validate_declaration(declaration=committed)
    written = validate_declaration(
        declaration=_written(declaration=committed, path=_LATER_BUILD_FIELD.path, value=None)
    )
    message = validation_refusal(validation=written)

    assert upgraded.defects == ()
    assert validation_refusal(validation=upgraded) is None
    assert [defect.key for defect in written.defects] == [_LATER_BUILD_FIELD.key]
    assert message is not None
    assert f"`{_LATER_BUILD_FIELD.key}`" in message


def _unmet(*, declaration: Mapping[str, object]) -> Mapping[str, object]:
    """This fixture's own declaration with both points written so neither resolves."""
    unmet = declaration
    for path, value in _UNMET:
        unmet = _written(declaration=unmet, path=path, value=value)
    return unmet


def _written(
    *, declaration: Mapping[str, object], path: str, value: object
) -> Mapping[str, object]:
    """This fixture's own declaration with one dotted point written to `value`."""
    written = cast("dict[str, object]", copy.deepcopy(dict(declaration)))
    block = written
    segments = path.split(".")
    for segment in segments[:-1]:
        child: object = block.get(segment)
        if not isinstance(child, dict):
            child = {}
            block[segment] = child
        block = cast("dict[str, object]", child)
    block[segments[-1]] = value
    return written
