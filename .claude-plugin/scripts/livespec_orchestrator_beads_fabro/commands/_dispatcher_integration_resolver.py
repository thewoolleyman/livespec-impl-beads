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

IT RESOLVES ONE POINT AND KNOWS OF NO OTHERS. Assembling the closed field set into
a repository's whole contract lives in `_dispatcher_integration_contract`, which
imports this module and is not imported back. That direction is what keeps the
resolver GENERIC: it cannot come to depend on which fields exist, so a newly
ratified obligation is an edit to the schema and to that assembly and never a
special case here.
"""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    CONFORMANCE_MODE_INTERNAL,
    CONFORMANCE_MODE_SHELL_ARGV,
    CONFORMANCE_NO_OP,
    UNRESOLVED_ARGV,
    UNRESOLVED_NAME,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_field import (
    SHAPE_ARGV,
    SHAPE_CONFORMANCE,
    SHAPE_ENUM,
    IntegrationField,
)
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt

__all__: list[str] = [
    "Declared",
    "Defective",
    "FleetDefault",
    "IntegrationResolution",
    "IntegrationValue",
    "declaration_carries",
    "is_declared",
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


def declaration_carries(*, field: IntegrationField, declaration: Mapping[str, object]) -> bool:
    """Whether this DECLARATION writes anything AT this point.

    The three arms above answer what a point RESOLVES to; this answers the prior
    question of whether the repository wrote at it, which is the distinction the
    pre-dispatch validation pass grades on. A key written as JSON `null` counts
    as written, and so does an ancestor that is present but is not a mapping:
    the repository put something there, and what it put does not resolve.

    A declared PARENT does NOT count. `parent_key` obliges a half the repository
    did not write, and the resolver is right to call that missing half
    `Defective`; but it is an ABSENCE at this point, and the step that consumes
    the point -- the master-CI preflight, the janitor-bootstrap check -- already
    refuses on it pre-dispatch, naming its own resolution and its own committed
    waiver. Grading it here as well would move that refusal to a surface with no
    waiver and silently retire the escape hatch.

    It is deliberately NOT the negation of `is_declared`, which reads a
    RESOLUTION and calls a `Defective` declared whatever produced it. This reads
    the declaration itself, so an absence stays an absence.
    """
    found = _walk(declaration=declaration, path=field.path)
    return found.present or found.blocked_at is not None


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
    if field.shape == SHAPE_CONFORMANCE:
        return _usable_conformance(field=field, raw=raw)
    return _usable_name(field=field, raw=raw)


def _usable_conformance(*, field: IntegrationField, raw: object) -> IntegrationResolution:
    """Grade a conformance premise: a mapping naming one mode of the closed set.

    The MODE, not the argv, is what the declaration is graded on, because two of
    the three modes carry no argv at all and one of those two -- the explicit
    no-op -- is a real answer rather than an omission. A bare command-shaped
    field could not tell "run nothing, deliberately" from "nothing written here".
    """
    declared = _conformance_declaration(raw=raw)
    mode = declared.get("mode")
    if not isinstance(mode, str) or mode not in field.admitted:
        return Defective(key=field.key, reason=_conformance_mode_reason(field=field, raw=raw))
    argv = declared.get("argv")
    if mode == CONFORMANCE_MODE_SHELL_ARGV:
        return _usable_argv(field=field, raw=argv if argv is not None else "")
    if argv is not None:
        return Defective(
            key=field.key,
            reason=f"`{field.key}` names mode `{mode}`, which accepts no `argv` of its own",
        )
    value = field.internal_argv if mode == CONFORMANCE_MODE_INTERNAL else CONFORMANCE_NO_OP
    return Declared(key=field.key, value=value)


def _conformance_declaration(*, raw: object) -> dict[str, object]:
    """A conformance declaration as a mapping; the empty one where it is not one at all.

    An empty mapping names no mode, so a value that is not a mapping earns the
    SAME defect as a mapping naming a mode nobody ratified -- both are a present
    declaration this schema cannot read, and the refusal quotes what was written.
    """
    return cast("dict[str, object]", raw) if isinstance(raw, dict) else {}


def _conformance_mode_reason(*, field: IntegrationField, raw: object) -> str:
    """Why this declaration names no admitted mode, listing the whole closed set."""
    admitted = " or ".join(f"`{value}`" for value in field.admitted)
    return (
        f"`{field.key}` is present but is not a mapping naming one of the admitted modes "
        f"{admitted}; got {raw!r}"
    )


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
