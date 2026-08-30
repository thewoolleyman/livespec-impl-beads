"""The check-suite AS THE JANITOR RUNS IT: a resolved argv, its text, and its origin.

This is a PROJECTION of the typed repository-integration contract, not a
resolver. `_dispatcher_integration_resolver` answers what
`dispatcher.janitor.check_suite` resolves to for the HOST-JANITOR venue; this
module shapes that answer into the argv the janitor invokes, the text every
operator-facing sentence renders, and the pre-dispatch refusal an unusable
declaration earns.

WHY THE CHECK-SUITE IS DECLARED AT ALL. The shipped janitor hard-coded this
fleet's `mise exec -- just check-no-workflow-edits install-worktree-pack check`
argv -- our own toolchain, silently assumed of every adopter, whose only override
was an UNCOMMITTED per-invocation `--janitor` argv. Measured on homelab, an
adopter that does not import livespec-dev-tooling: its first clean hardened run
produced a real merge and then FAILED at janitor-post-merge because its justfile
has no `install-worktree-pack` recipe, stranding the merged item `active` and
failing every further dispatch identically. The committed key makes the topology
a DECLARATION and the fleet argv a DECLARED DEFAULT, so an adopter can tell "your
check-suite is red" apart from "I ran a recipe you never claimed to have".

A DECLARED COMMAND IS INVOKED VERBATIM. The default's argv carries this fleet's
`mise exec --` prefix because `just` reaches these hosts through mise; a declared
command is invoked exactly as the adopter wrote it, because imposing our own
invocation wrapper on someone else's command is the same assumed-tooling defect
one layer down.

AND THE COMMITTED DECLARATION OUTRANKS THE PER-INVOCATION `--janitor` OVERRIDE.
An uncommitted per-invocation argv silently overriding committed policy is
exactly what the committed-configuration-only class forbids
(`SPECIFICATION/contracts.md`, the control-surface-and-audit rules): a dial that
overrides a safety-relevant committed policy is committed configuration with a
reviewable diff. Where `--janitor` remains it is scoped to a repository that has
declared no check-suite -- which is why it is consulted only once the generic
resolver has answered `FleetDefault`, never when it answered `Declared` and never
when it answered `Defective`.

Declaration changes WHAT check-suite runs, never WHETHER absence of proof refuses
(`SPECIFICATION/contracts.md`, the janitor check-suite resolution clause).
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from livespec_orchestrator_beads_fabro.commands._config import dispatcher_block
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_declaration import (
    declaration_from_dispatcher_block,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    JANITOR_CHECK_SUITE_DEFAULT,
    UNRESOLVED_NAME,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Declared,
    Defective,
    resolve_integration_field,
    resolved_argv,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    JANITOR_CHECK_SUITE_FIELD,
    JANITOR_CHECK_SUITE_KEY,
)

__all__: list[str] = [
    "DECLARED_RESOLUTION",
    "DEFAULT_CHECK_SUITE",
    "DEFAULT_RESOLUTION",
    "JANITOR_CHECK_SUITE_KEY",
    "OVERRIDE_RESOLUTION",
    "UNRESOLVED_CHECK_SUITE",
    "JanitorCheckSuite",
    "check_suite_refusal",
    "check_suite_resolution_sentence",
    "janitor_check_suite_from_block",
    "resolve_janitor_check_suite",
]

# The fleet default convention as one command line, which is what every
# operator-facing sentence renders. Derived from the schema's own default rather
# than spelled a second time, so the prose cannot drift from the command run.
DEFAULT_CHECK_SUITE = shlex.join(JANITOR_CHECK_SUITE_DEFAULT)

DECLARED_RESOLUTION = "declared"
DEFAULT_RESOLUTION = "default"
OVERRIDE_RESOLUTION = "override"

# What a defective declaration renders its check-suite as. A sentinel rather than
# the convention's text precisely because the convention is the wrong answer
# here: prose reading `mise exec -- just ...` would tell the operator we looked
# for a check-suite they never declared.
UNRESOLVED_CHECK_SUITE = UNRESOLVED_NAME


@dataclass(frozen=True, kw_only=True)
class JanitorCheckSuite:
    """The check-suite the post-merge janitor runs, plus where it came from.

    `command` is the argv the janitor invokes; `text` is that argv as one
    command line, and is what every operator-facing sentence renders.

    `resolution` is `declared` when the committed key supplied the command,
    `override` when the per-invocation `--janitor` argv did, and `default` when
    the convention did. It is carried rather than re-derived because the refusal
    text and the journal record both have to say which resolution was attempted,
    and a second derivation could disagree with the first.

    `defect` names what is wrong with a PRESENT declaration, and is `None` on
    every usable check-suite. A defective check-suite still reports `declared`
    as its attempted resolution -- the adopter did declare, the declaration is
    just not readable -- so the refusal names the key the operator has to go and
    fix rather than blaming the convention it never chose.
    """

    command: tuple[str, ...]
    text: str
    resolution: str
    defect: str | None = None


def resolve_janitor_check_suite(*, cwd: Path, janitor: tuple[str, ...] | None) -> JanitorCheckSuite:
    """Resolve the governed repository's check-suite from its committed `.livespec.jsonc`.

    An absent key is an ANSWER -- this repository uses the fleet convention --
    so it rides the same block reader as every other dispatcher key rather than
    a special absent-file path of its own.
    """
    return janitor_check_suite_from_block(block=dispatcher_block(cwd=cwd), janitor=janitor)


def janitor_check_suite_from_block(
    *, block: dict[str, Any], janitor: tuple[str, ...] | None
) -> JanitorCheckSuite:
    """Project the host-janitor venue's check-suite field; declared wins over `janitor`."""
    resolution = resolve_integration_field(
        field=JANITOR_CHECK_SUITE_FIELD,
        declaration=declaration_from_dispatcher_block(block=block),
    )
    if isinstance(resolution, Defective):
        return JanitorCheckSuite(
            command=(),
            text=UNRESOLVED_CHECK_SUITE,
            resolution=DECLARED_RESOLUTION,
            defect=resolution.reason,
        )
    if isinstance(resolution, Declared):
        command = resolved_argv(resolution=resolution)
        return JanitorCheckSuite(
            command=command, text=shlex.join(command), resolution=DECLARED_RESOLUTION
        )
    if janitor:
        return JanitorCheckSuite(
            command=janitor, text=shlex.join(janitor), resolution=OVERRIDE_RESOLUTION
        )
    return JanitorCheckSuite(
        command=resolved_argv(resolution=resolution),
        text=DEFAULT_CHECK_SUITE,
        resolution=DEFAULT_RESOLUTION,
    )


def check_suite_resolution_sentence(*, check_suite: JanitorCheckSuite) -> str:
    """One line naming the attempted resolution and the key that declares it."""
    if check_suite.defect is not None:
        return (
            f"Resolution attempted: declared, from the committed "
            f"`{JANITOR_CHECK_SUITE_KEY}` key, which is present but unusable: "
            f"{check_suite.defect}. A present declaration is never completed from the "
            "default convention, because that would run a check-suite this repository "
            "has said is not its own."
        )
    if check_suite.resolution == DECLARED_RESOLUTION:
        return (
            f"Resolution attempted: declared, from the committed "
            f"`{JANITOR_CHECK_SUITE_KEY}` key (check-suite `{check_suite.text}`), "
            "which is invoked verbatim."
        )
    if check_suite.resolution == OVERRIDE_RESOLUTION:
        return (
            f"Resolution attempted: the per-invocation `--janitor` override "
            f"(check-suite `{check_suite.text}`), which is scoped to a repository that "
            f"declares no `{JANITOR_CHECK_SUITE_KEY}`."
        )
    return (
        f"Resolution attempted: default convention (check-suite `{check_suite.text}`); "
        f"declare this repository's own check-suite under the committed "
        f"`{JANITOR_CHECK_SUITE_KEY}` key."
    )


def check_suite_refusal(*, check_suite: JanitorCheckSuite) -> str | None:
    """The pre-dispatch refusal a present-but-unusable declaration earns; else None.

    It refuses BEFORE any run exists rather than letting an unresolvable
    declaration reach the janitor as an empty argv, which would surface after
    the merge has already landed.
    """
    if check_suite.defect is None:
        return None
    return (
        f"ERROR: the post-merge janitor check-suite is unresolvable: {check_suite.defect}. "
        f"{check_suite_resolution_sentence(check_suite=check_suite)}\n"
    )
