"""Every integration point resolves from what the repository DECLARES, or not at all.

Binds `SPECIFICATION/scenarios.md` Scenario 96: each governed-repo integration
point resolves from a committed declaration, with a fleet default only where one
exists. Both cases run the ONE production resolver over BOTH committed
governed-repository fixtures, injecting each probe into that fixture's OWN
committed declaration rather than hand-writing a third repository -- the same
discipline the sibling Scenario 100/101/107 bindings use, so the two legs stay
the member's fleet-default posture and the adopter's fully-declared one.

WHY THE THREE ARMS ARE ASSERTED FIELD BY FIELD OVER THE CLOSED SET. The claim
the scenario makes is about the RESOLUTION RULE, not about one key: a per-key
assertion would pass while a newly ratified field resolved by some other rule,
which is exactly the eight-divergent-helpers defect the one-resolver clause
retires. The loop therefore walks `INTEGRATION_FIELDS` itself, so a field added
later is graded here with no edit to this module, and the case states its own
scope -- every field the schema marks `declared_in_config`, which is the closed
set minus the default branch alone, whose declaration is the repository itself
and which no `.livespec.jsonc` may answer.

AND THE DEFECTIVE ARM IS SHOWN TO BE REACHABLE BEFORE IT IS ASSERTED. "Defective
where no fleet default exists" is an assertion about an arm that would be
vacuously true if no such field existed, so the case first pins WHICH field that
is -- the required core pin -- and fails if the schema ever stops carrying one.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from typing import cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_declaration import (
    PLUGIN_BLOCK,
    declaration_from_config_text,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    CONFORMANCE_MODE_SHELL_ARGV,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_field import (
    SHAPE_ARGV,
    SHAPE_CONFORMANCE,
    SHAPE_ENUM,
    IntegrationField,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Declared,
    Defective,
    FleetDefault,
    IntegrationValue,
    resolve_integration_field,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    COMPAT_PINNED_KEY,
    DEFAULT_BRANCH_FIELD,
    INTEGRATION_FIELDS,
    JANITOR_CHECK_SUITE_FIELD,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan, build_plan

from tests.integration.governed_repo_fixtures import (
    PAYLOAD_RUN_CONFIG,
    PROBED_DEFAULT_BRANCH,
    GovernedRepo,
    fleet_toolchain_token,
    over_both_fixtures,
)

# Every point a repository ANSWERS in its committed declaration -- the closed set
# minus the default branch, whose declaration is the repository's own git state.
_DECLARABLE: tuple[IntegrationField, ...] = tuple(
    field for field in INTEGRATION_FIELDS if field.declared_in_config
)

# The probe values written into a fixture's declaration. Neither carries a token
# of this fleet's toolchain, so a resolution that agreed with a fleet literal
# could not pass by coincidence.
_DECLARED_ARGV = ("adopter-tool", "verify", "--strict")
_DECLARED_NAME = "declared.example.invalid/value"
_OVERRIDE_ARGV = ("override-tool", "check")


@over_both_fixtures
def test_every_declarable_integration_point_resolves_declared_fleet_default_or_defective(
    governed: GovernedRepo,
) -> None:
    """The three arms, per point, over the schema's own closed set.

    DECLARED carries the declaration VERBATIM -- an argv-shaped point resolves
    exactly the tokens written and nothing prepended, which is the "no wrapper is
    imposed" half of the scenario. FLEET DEFAULT is reached only from a truly
    absent key on a field the schema gives one to. DEFECTIVE is what an absence
    earns where no safe default exists, and what a PRESENT-but-unusable
    declaration earns everywhere -- never a slide onto the convention the
    repository has just said is not its own.
    """
    committed = declaration_from_config_text(config_text=governed.config_text)

    assert (
        tuple(field for field in INTEGRATION_FIELDS if field is not DEFAULT_BRANCH_FIELD)
        == _DECLARABLE
    )
    # The Defective-on-absence arm below is only evidence if the schema carries a
    # field with no fleet default at all; this names the one that does.
    assert {field.key for field in _DECLARABLE if field.fleet_default is None} == {
        COMPAT_PINNED_KEY
    }

    for field in _DECLARABLE:
        declared = resolve_integration_field(
            field=field,
            declaration=_written(
                declaration=committed, path=field.path, value=_probe_declaration(field=field)
            ),
        )
        absent = resolve_integration_field(
            field=field, declaration=_stripped(declaration=committed, field=field)
        )
        present_but_null = resolve_integration_field(
            field=field, declaration=_written(declaration=committed, path=field.path, value=None)
        )

        assert declared == Declared(key=field.key, value=_probe_value(field=field)), field.key
        if field.fleet_default is None:
            assert absent == Defective(key=field.key, reason=_absent_reason(field=field)), field.key
        else:
            assert absent == FleetDefault(key=field.key, value=field.fleet_default), field.key
        assert isinstance(present_but_null, Defective), field.key
        assert present_but_null.key == field.key


@over_both_fixtures
def test_a_committed_check_suite_is_invoked_verbatim_and_outranks_the_per_invocation_override(
    governed: GovernedRepo,
) -> None:
    """The declared command reaches the janitor unwrapped, and the override does not displace it.

    Both legs run the SAME per-invocation override against the SAME repository,
    differing only in whether its check-suite key is written -- so the second
    assertion is the positive control the first needs: an override that could
    never be reached would make "the declaration won" unfalsifiable.
    """
    committed = declaration_from_config_text(config_text=governed.config_text)

    declaring = _plan(
        governed=governed,
        declaration=_written(
            declaration=committed,
            path=JANITOR_CHECK_SUITE_FIELD.path,
            value=list(_DECLARED_ARGV),
        ),
    )
    inheriting = _plan(
        governed=governed,
        declaration=_stripped(declaration=committed, field=JANITOR_CHECK_SUITE_FIELD),
    )

    assert declaring.janitor == _DECLARED_ARGV
    assert inheriting.janitor == _OVERRIDE_ARGV
    assert [
        token for token in declaring.janitor if fleet_toolchain_token(line=token) is not None
    ] == []


def _probe_declaration(*, field: IntegrationField) -> object:
    """What a repository would WRITE at this point to declare it usably."""
    if field.shape == SHAPE_ARGV:
        return list(_DECLARED_ARGV)
    if field.shape == SHAPE_CONFORMANCE:
        return {"mode": CONFORMANCE_MODE_SHELL_ARGV, "argv": list(_DECLARED_ARGV)}
    if field.shape == SHAPE_ENUM:
        return field.admitted[-1]
    return _DECLARED_NAME


def _probe_value(*, field: IntegrationField) -> IntegrationValue:
    """What that declaration must resolve to -- the written value, carried verbatim."""
    if field.shape in {SHAPE_ARGV, SHAPE_CONFORMANCE}:
        return _DECLARED_ARGV
    if field.shape == SHAPE_ENUM:
        return field.admitted[-1]
    return _DECLARED_NAME


def _absent_reason(*, field: IntegrationField) -> str:
    """The refusal a required point earns on absence, quoted from the ratified wording."""
    return (
        f"`{field.key}` is absent, and this point has no safe default: the only "
        "substitutable value would be one this repository never chose, so it is "
        "named rather than guessed at"
    )


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


def _stripped(
    *, declaration: Mapping[str, object], field: IntegrationField
) -> Mapping[str, object]:
    """This fixture's own declaration with the point TRULY absent.

    A declared PARENT makes the child required, so the parent block goes with the
    leaf: leaving it behind would produce the declared-block-names-every-half
    defect instead of the absence the fleet-default arm is reached from.
    """
    stripped = cast("dict[str, object]", copy.deepcopy(dict(declaration)))
    paths = (field.path,) if field.parent_key is None else (field.path, field.parent_key)
    for path in paths:
        _delete(block=stripped, segments=path.split("."))
    return stripped


def _delete(*, block: dict[str, object], segments: list[str]) -> None:
    for segment in segments[:-1]:
        child: object = block.get(segment)
        if not isinstance(child, dict):
            return
        block = cast("dict[str, object]", child)
    _ = block.pop(segments[-1], None)


def _plan(*, governed: GovernedRepo, declaration: Mapping[str, object]) -> DispatchPlan:
    """One dispatch plan off `declaration`, always carrying the per-invocation override."""
    return build_plan(
        repo=governed.root,
        work_item_id="fixture-96",
        workflow_toml=governed.root / "workflow.toml",
        goal_file=governed.root / "goal.md",
        fabro_bin="fabro",
        janitor=_OVERRIDE_ARGV,
        janitor_checkout=governed.root / "janitor-checkout",
        config_text=json.dumps({PLUGIN_BLOCK: dict(declaration)}),
        default_branch=PROBED_DEFAULT_BRANCH,
        committed_workflow_text=PAYLOAD_RUN_CONFIG.read_text(encoding="utf-8"),
    )
