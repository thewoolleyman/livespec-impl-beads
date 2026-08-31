"""What an UNDECLARED conformance premise means, said out loud at dispatch time.

`SPECIFICATION/contracts.md`'s dispatch-time-baseline-conformance-gate section
requires the sandbox prepare chain to install the commit-refuse Mechanism and to
run the two Verifiers; the factory-sandbox-toolchain-disposition clause requires
each of those premises to be either a declared-and-validated integration point or
a ratified no-op, NEVER a silent degrade. The schema makes them fields and the
resolver grades them. This module owns the third obligation, which neither of
those can discharge: SAYING SO.

WHY AN ABSENT PREMISE HAS TO SPEAK. An absent conformance key resolves to the
explicit no-op, which is a legitimate value and produces a perfectly healthy
dispatch -- and a sandbox that quietly skips the commit-refuse install. That is
the exact shape of a silent degrade: nothing fails, so nothing is ever
investigated. The distinction the ratified clause draws is between a no-op the
adopter CHOSE and one that merely happened, and the only place that distinction
is observable is the resolution ARM. So the warning fires on `FleetDefault` and
not on the VALUE, and declaring `no_op` explicitly silences it -- the choice is
then on the record, which is the whole thing the warning was asking for.

IT NEVER REFUSES. Refusing would strand every repository that has not yet
declared these keys, including the ones with items already mid-pipeline -- the
same reasoning that keeps the schema-validation pass off absent keys. The
dispatch proceeds; the operator is told.

THE WORDING ASSUMES NO FLEET CONTEXT. It names the config file, quotes the exact
keys to write, and explains all three modes by name, because its reader is an
adopter who has never seen this fleet's tooling and is being told that something
they did not know existed is not going to run.
"""

from __future__ import annotations

from typing import Protocol

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_contract import (
    ResolvedIntegrationContract,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    CONFORMANCE_MODE_INTERNAL,
    CONFORMANCE_MODE_NO_OP,
    CONFORMANCE_MODE_SHELL_ARGV,
    CONFORMANCE_NO_OP,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_field import (
    IntegrationField,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Defective,
    FleetDefault,
    IntegrationResolution,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    CONFORMANCE_FIELDS,
)
from livespec_orchestrator_beads_fabro.io import write_stderr

__all__: list[str] = [
    "CONFORMANCE_CAVEAT_STAGE",
    "CONFORMANCE_WARNING_STAGE",
    "absent_conformance_keys",
    "conformance_caveat_lines",
    "conformance_field",
    "conformance_mode",
    "conformance_warning_block",
    "emit_conformance_premise_notices",
    "internal_conformance_keys",
]

# The journal stages the two notices record under. Two stages rather than one
# because they answer different questions -- "this repository declared nothing"
# and "this repository opted into unsupported tooling" -- and a reader tallying
# either must not have to distinguish them by re-reading the text.
CONFORMANCE_WARNING_STAGE = "conformance-premise-undeclared"
CONFORMANCE_CAVEAT_STAGE = "conformance-premise-unsupported-mode"

# What each mode MEANS, in the adopter's terms, one line each.
_NO_OP_EXPLANATION = (
    "the sandbox skips this step. Declaring it explicitly silences this warning "
    "and puts the choice on the record."
)
_SHELL_ARGV_EXPLANATION = (
    "your own command, written as an `argv` array beside the mode, run verbatim "
    "in the sandbox as that prepare step."
)
_INTERNAL_EXPLANATION = (
    "uses livespec internal tooling. UNSUPPORTED and may be unreliable; it "
    "introduces a dependency on the livespec-dev-tooling package."
)

# The three modes paired with their prose, keyed by the mode CONSTANT rather than
# by a restated string, so the enumeration this text explains and the enumeration
# the resolver grades against cannot drift apart.
_MODE_EXPLANATIONS: tuple[tuple[str, str], ...] = (
    (CONFORMANCE_MODE_NO_OP, _NO_OP_EXPLANATION),
    (CONFORMANCE_MODE_SHELL_ARGV, _SHELL_ARGV_EXPLANATION),
    (CONFORMANCE_MODE_INTERNAL, _INTERNAL_EXPLANATION),
)

_CONFIG_FILE = ".livespec.jsonc"


class _ConformanceJournal(Protocol):
    """Append-only journal seam for the dispatch-time conformance notices."""

    def append(self, *, record: dict[str, object]) -> None:
        """Persist one journal record."""
        ...


def conformance_field(*, attribute: str) -> IntegrationField | None:
    """The conformance field this schema attribute names, or None for any other field.

    Read off the schema's own `CONFORMANCE_FIELDS` rather than an attribute-name
    match, so a seam asking "is this a conformance premise?" cannot answer yes
    for a field the schema never made one.
    """
    return next((field for field in CONFORMANCE_FIELDS if field.attribute == attribute), None)


def conformance_mode(*, field: IntegrationField, resolution: IntegrationResolution) -> str | None:
    """The MODE a conformance premise resolved under; None where it resolved nothing.

    DERIVED from the resolved value rather than carried alongside it, and that is
    safe rather than clever: the internal invocation is non-empty and unique to
    its field, the no-op is the empty argv, and every remaining argv came from
    the adopter's own `shell_argv`. So the three modes partition the value space
    and the derivation is total -- which is what lets the journal report a mode
    without the resolver having to grow a second parallel record of one.
    """
    if isinstance(resolution, Defective):
        return None
    if resolution.value == field.internal_argv:
        return CONFORMANCE_MODE_INTERNAL
    if resolution.value == CONFORMANCE_NO_OP:
        return CONFORMANCE_MODE_NO_OP
    return CONFORMANCE_MODE_SHELL_ARGV


def absent_conformance_keys(*, resolved: ResolvedIntegrationContract) -> tuple[str, ...]:
    """Every conformance key this repository left unwritten, in schema order.

    Keyed on the `FleetDefault` ARM, never on the no-op VALUE: a repository that
    declares `no_op` resolves to the same empty argv and has answered, so it is
    absent from this list and earns no warning.
    """
    return tuple(
        field.key
        for field in CONFORMANCE_FIELDS
        if isinstance(resolved.resolutions[field.attribute], FleetDefault)
    )


def internal_conformance_keys(*, resolved: ResolvedIntegrationContract) -> tuple[str, ...]:
    """Every conformance key declared under the internal mode, in schema order."""
    return tuple(
        field.key
        for field in CONFORMANCE_FIELDS
        if conformance_mode(field=field, resolution=resolved.resolutions[field.attribute])
        == CONFORMANCE_MODE_INTERNAL
    )


def conformance_warning_block(*, keys: tuple[str, ...]) -> str:
    """The ONE block an undeclared premise earns, naming each key and every mode."""
    named = "".join(
        f"  - `{key}`: the sandbox will SKIP this step for this repository.\n" for key in keys
    )
    modes = "".join(f"  - `{mode}`: {explanation}\n" for mode, explanation in _MODE_EXPLANATIONS)
    return (
        "WARN: this repository declares no dispatch-time conformance premise for "
        f"the following {len(keys)} key(s), so nothing is run in their place:\n"
        f"{named}"
        f"Declare each key in `{_CONFIG_FILE}` as a mapping naming one mode:\n"
        f"{modes}"
        "This is informational: the dispatch proceeds either way.\n"
    )


def conformance_caveat_lines(*, keys: tuple[str, ...]) -> tuple[str, ...]:
    """The one-line reminder each internally-declared premise earns.

    A repository that CHOSE the unsupported mode already read the caveat when it
    wrote the key, so it gets the reminder rather than the block -- but it does
    get one, every dispatch, because the mode's unreliability is a standing
    property of the dispatch and not a one-time notice.
    """
    return tuple(_caveat_line(key=key) for key in keys)


def _caveat_line(*, key: str) -> str:
    """One internally-declared premise's standing caveat, as one line."""
    return (
        f"WARN: `{key}` is declared `{CONFORMANCE_MODE_INTERNAL}`: it uses livespec "
        "internal tooling, which is UNSUPPORTED and may be unreliable.\n"
    )


def emit_conformance_premise_notices(
    *, resolved: ResolvedIntegrationContract, journal: _ConformanceJournal
) -> None:
    """Surface both conformance notices at dispatch; never refuse the dispatch."""
    absent = absent_conformance_keys(resolved=resolved)
    if absent:
        _ = write_stderr(text=conformance_warning_block(keys=absent))
        journal.append(
            record={
                "stage": CONFORMANCE_WARNING_STAGE,
                "keys": list(absent),
                "blocking": False,
            }
        )
    internal = internal_conformance_keys(resolved=resolved)
    if internal:
        _ = write_stderr(text="".join(conformance_caveat_lines(keys=internal)))
        journal.append(
            record={
                "stage": CONFORMANCE_CAVEAT_STAGE,
                "keys": list(internal),
                "mode": CONFORMANCE_MODE_INTERNAL,
                "blocking": False,
            }
        )
