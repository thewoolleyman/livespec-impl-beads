"""The ONE generic resolver every integration point is read through.

`SPECIFICATION/contracts.md`, the repository-integration-contract section,
ratifies that every point be read through one generic, schema-driven resolver whose result is
the sum type `Declared(value) | FleetDefault(value) | Defective(key, reason)`,
and that no code path substitute a default for a `Defective`. This module is that
resolver. It replaces eight per-key modules across four families that each
re-derived the same three-arm decision, each with its own copy of the wording,
and each free to drift from the others -- which is how a repository could get one
family's absent-key fallback and another family's absent-key refusal without
anything saying why.

ONLY AN ABSENT KEY FALLS BACK, and that rule is now expressed ONCE. A key that is
PRESENT but unusable is a DEFECT, never a silent slide onto the fleet
convention. The two readings are not interchangeable: an absent key says "this
repository uses the convention", while a present one says "this repository's
answer is NOT the convention" and then fails to say what it is. Completing the
second from the convention takes the adopter's own statement that the fleet value
is wrong and uses the fleet value anyway.

A REQUIRED FIELD HAS NO FALLBACK AT ALL. Where the ratified semantics admit no
safe default -- `compat.pinned`, whose only substitutable value would be the
moving branch tip its own clause forbids -- an ABSENT key resolves to `Defective`
naming the absence. That is the one arm a per-field default table cannot express,
and it is why optionality is a property of the SCHEMA rather than of whether
somebody remembered to write a default.

PRESENCE IS TESTED WITH MEMBERSHIP, NEVER WITH A `get` SENTINEL. A key written as
JSON `null` is a PRESENT declaration that names nothing; reading it as absent is
exactly the fallback this refuses.
"""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    UNRESOLVED_ARGV,
    UNRESOLVED_NAME,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    CORE_PINNED_REF_FIELD,
    CORE_REPO_URL_FIELD,
    DEFAULT_BRANCH_FIELD,
    INTEGRATION_CONTRACT_SCHEMA_VERSION,
    INTEGRATION_FIELDS,
    JANITOR_BOOTSTRAP_RECIPE_FIELD,
    JANITOR_CHECK_SUITE_FIELD,
    MASTER_CI_JOB_FIELD,
    MASTER_CI_WORKFLOW_FIELD,
    MERGE_MODE_FIELD,
    PREPARE_TOOLCHAIN_LEFTHOOK_FIELD,
    PREPARE_TOOLCHAIN_MISE_FIELD,
    SANDBOX_CHECK_SUITE_FIELD,
    SANDBOX_EXEMPT_MARKER_FIELD,
    SHAPE_ARGV,
    SHAPE_ENUM,
    IntegrationField,
    RepoIntegrationContract,
)
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt

__all__: list[str] = [
    "Declared",
    "Defective",
    "FleetDefault",
    "IntegrationResolution",
    "IntegrationValue",
    "ResolvedIntegrationContract",
    "is_declared",
    "resolve_integration_contract",
    "resolve_integration_field",
    "resolved_argv",
    "resolved_name",
    "resolved_value",
]

# What a resolved integration point can BE. A command is argv tokens and a name
# is a string; there is deliberately no third shape, because every point this
# specification ratifies is one or the other and an open value space is how a
# schema stops being able to validate anything.
IntegrationValue = str | tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class Declared:
    """The repository declared this point, and the declaration is usable."""

    key: str
    value: IntegrationValue


@dataclass(frozen=True, kw_only=True)
class FleetDefault:
    """The repository declared nothing, and the schema carries a safe default.

    Reached ONLY from a truly absent key on a field the schema marks optional.
    """

    key: str
    value: IntegrationValue


@dataclass(frozen=True, kw_only=True)
class Defective:
    """This point resolves NOTHING, and `reason` says why in the operator's terms.

    `key` is the committed key the operator has to go and fix, quoted verbatim
    so the reader of a refusal knows where in `.livespec.jsonc` to write the
    answer rather than which of our modules produced the sentence.
    """

    key: str
    reason: str


IntegrationResolution = Declared | FleetDefault | Defective


@dataclass(frozen=True, kw_only=True)
class ResolvedIntegrationContract:
    """One repository's whole contract, resolved once, with every defect together.

    `defects` carries EVERY unresolved point rather than the first, because the
    ratified validation pass refuses enumerating all of them in one message: an
    adopter that has declared nothing learns the whole list in one refusal
    instead of one dispatch at a time.
    """

    contract: RepoIntegrationContract
    defects: tuple[Defective, ...]


@dataclass(frozen=True, kw_only=True)
class _Lookup:
    """What walking one dotted path found: a value, an absence, or a blocked ancestor.

    `blocked_at` names an ancestor block that is PRESENT but is not a mapping,
    which is a defect rather than an absence -- the repository wrote something
    there, and it is not something a child key could hang off.
    """

    present: bool
    value: object = None
    blocked_at: str | None = None


def resolve_integration_field(
    *, field: IntegrationField, declaration: Mapping[str, object]
) -> IntegrationResolution:
    """Resolve ONE schema field against a declaration -- the generic three-arm rule."""
    found = _walk(declaration=declaration, path=field.path)
    if found.blocked_at is not None:
        return Defective(
            key=field.key,
            reason=(
                f"`{found.blocked_at}` is present but is not a mapping, so "
                f"`{field.key}` cannot be read from it"
            ),
        )
    if not found.present:
        return _absent(field=field, declaration=declaration)
    return _usable(field=field, raw=found.value)


def resolve_integration_contract(
    *, declaration: Mapping[str, object]
) -> ResolvedIntegrationContract:
    """Resolve the WHOLE closed field set once, keeping every defect together.

    This is the "resolve once, project everywhere" object: a seam that needs an
    integration value reads it off the frozen contract instead of re-deriving it
    from configuration, because re-deriving at a later point is how the dispatch
    record and the run come to disagree.
    """
    resolved = {
        field.attribute: resolve_integration_field(field=field, declaration=declaration)
        for field in INTEGRATION_FIELDS
    }
    contract = RepoIntegrationContract(
        schema_version=INTEGRATION_CONTRACT_SCHEMA_VERSION,
        master_ci_workflow=resolved_name(resolution=resolved[MASTER_CI_WORKFLOW_FIELD.attribute]),
        master_ci_job=resolved_name(resolution=resolved[MASTER_CI_JOB_FIELD.attribute]),
        janitor_check_suite=resolved_argv(resolution=resolved[JANITOR_CHECK_SUITE_FIELD.attribute]),
        sandbox_check_suite=resolved_argv(resolution=resolved[SANDBOX_CHECK_SUITE_FIELD.attribute]),
        janitor_bootstrap_recipe=resolved_argv(
            resolution=resolved[JANITOR_BOOTSTRAP_RECIPE_FIELD.attribute]
        ),
        core_repo_url=resolved_name(resolution=resolved[CORE_REPO_URL_FIELD.attribute]),
        core_pinned_ref=resolved_name(resolution=resolved[CORE_PINNED_REF_FIELD.attribute]),
        prepare_toolchain_mise=resolved_argv(
            resolution=resolved[PREPARE_TOOLCHAIN_MISE_FIELD.attribute]
        ),
        prepare_toolchain_lefthook=resolved_argv(
            resolution=resolved[PREPARE_TOOLCHAIN_LEFTHOOK_FIELD.attribute]
        ),
        default_branch=resolved_name(resolution=resolved[DEFAULT_BRANCH_FIELD.attribute]),
        merge_mode=resolved_name(resolution=resolved[MERGE_MODE_FIELD.attribute]),
        sandbox_exempt_marker=resolved_name(
            resolution=resolved[SANDBOX_EXEMPT_MARKER_FIELD.attribute]
        ),
    )
    defects = tuple(
        resolution for resolution in resolved.values() if isinstance(resolution, Defective)
    )
    return ResolvedIntegrationContract(contract=contract, defects=defects)


def is_declared(*, resolution: IntegrationResolution) -> bool:
    """Whether the REPOSITORY answered this point, as opposed to the fleet default.

    A `Defective` counts as declared: the adopter did declare, the declaration
    is just not readable, so a refusal names the key they have to fix rather
    than blaming a convention they never chose.
    """
    return not isinstance(resolution, FleetDefault)


def resolved_value(*, resolution: IntegrationResolution) -> IntegrationValue | None:
    """The value a resolution carries; None when it resolved nothing."""
    return None if isinstance(resolution, Defective) else resolution.value


def resolved_name(*, resolution: IntegrationResolution) -> str:
    """A name-shaped point's value, or the sentinel that cannot be mistaken for one."""
    value = resolved_value(resolution=resolution)
    return value if isinstance(value, str) else UNRESOLVED_NAME


def resolved_argv(*, resolution: IntegrationResolution) -> tuple[str, ...]:
    """A command-shaped point's argv, or the empty argv that cannot be run."""
    value = resolved_value(resolution=resolution)
    return value if isinstance(value, tuple) else UNRESOLVED_ARGV


def _walk(*, declaration: Mapping[str, object], path: str) -> _Lookup:
    """Follow one dotted path, distinguishing absent from present-but-not-a-mapping."""
    segments = path.split(".")
    block: Mapping[str, object] = declaration
    for depth, segment in enumerate(segments[:-1]):
        if segment not in block:
            return _Lookup(present=False)
        child = block[segment]
        if not isinstance(child, dict):
            return _Lookup(present=False, blocked_at=".".join(segments[: depth + 1]))
        block = cast("dict[str, object]", child)
    leaf = segments[-1]
    if leaf not in block:
        return _Lookup(present=False)
    return _Lookup(present=True, value=block[leaf])


def _absent(*, field: IntegrationField, declaration: Mapping[str, object]) -> IntegrationResolution:
    """What an ABSENT key resolves to: a refusal, a completion defect, or the default."""
    if field.required:
        return Defective(
            key=field.key,
            reason=(
                f"`{field.key}` is absent, and this point has no safe default: the only "
                "substitutable value would be one this repository never chose, so it is "
                "named rather than guessed at"
            ),
        )
    if (
        field.parent_key is not None
        and _walk(declaration=declaration, path=field.parent_key).present
    ):
        return Defective(
            key=field.key,
            reason=(
                f"`{field.key}` is absent while `{field.parent_key}` is declared; a declared "
                "block names every half of the point it declares, since defaulting the "
                "missing half would act on something this repository never named"
            ),
        )
    return FleetDefault(key=field.key, value=_fleet_default(field=field))


def _fleet_default(*, field: IntegrationField) -> IntegrationValue:
    """The schema's declared default for an optional field.

    An optional field ALWAYS carries one -- that is what makes it optional -- so
    a missing default is a schema bug and resolves to the sentinel rather than
    to `None` leaking into a value position.
    """
    default = field.fleet_default
    return UNRESOLVED_NAME if default is None else default


def _usable(*, field: IntegrationField, raw: object) -> IntegrationResolution:
    """Grade a PRESENT declaration against its field's shape."""
    if field.shape == SHAPE_ARGV:
        return _usable_argv(field=field, raw=raw)
    if field.shape == SHAPE_ENUM:
        return _usable_enum(field=field, raw=raw)
    return _usable_name(field=field, raw=raw)


def _usable_name(*, field: IntegrationField, raw: object) -> IntegrationResolution:
    if not isinstance(raw, str) or raw.strip() == "":
        return Defective(
            key=field.key, reason=f"`{field.key}` is present but is not a non-empty string"
        )
    return Declared(key=field.key, value=raw.strip())


def _usable_enum(*, field: IntegrationField, raw: object) -> IntegrationResolution:
    if not isinstance(raw, str) or raw not in field.admitted:
        admitted = " or ".join(f"`{value}`" for value in field.admitted)
        return Defective(
            key=field.key,
            reason=(
                f"`{field.key}` is present but is not one of the admitted values {admitted}; "
                f"got {raw!r}"
            ),
        )
    return Declared(key=field.key, value=raw)


def _usable_argv(*, field: IntegrationField, raw: object) -> IntegrationResolution:
    """A command declared as a shell string to split, or already as an argv array."""
    if isinstance(raw, list):
        return _usable_argv_array(field=field, raw=cast("list[object]", raw))
    if not isinstance(raw, str) or raw.strip() == "":
        return Defective(
            key=field.key,
            reason=f"`{field.key}` is present but is not a non-empty string or argv array",
        )
    split = attempt(action=lambda: shlex.split(raw), exceptions=(ValueError,))
    if isinstance(split, AttemptFailure):
        return Defective(
            key=field.key,
            reason=f"`{field.key}` is present but does not parse as a shell command: {raw!r}",
        )
    return _argv_or_defect(field=field, tokens=tuple(split))


def _usable_argv_array(*, field: IntegrationField, raw: list[object]) -> IntegrationResolution:
    if not all(isinstance(token, str) for token in raw):
        return Defective(
            key=field.key,
            reason=f"`{field.key}` is present as an array but not every token is a string",
        )
    return _argv_or_defect(field=field, tokens=tuple(cast("list[str]", raw)))


def _argv_or_defect(*, field: IntegrationField, tokens: tuple[str, ...]) -> IntegrationResolution:
    """An argv naming a program, or the defect that it names none.

    A command whose first token is empty (`''`, which splits to one empty
    string) names no program, which is the same answer to the caller as an
    empty argv: this declaration resolves nothing.
    """
    if not tokens or tokens[0] == "":
        return Defective(
            key=field.key, reason=f"`{field.key}` is present but names no program to run"
        )
    return Declared(key=field.key, value=tokens)
