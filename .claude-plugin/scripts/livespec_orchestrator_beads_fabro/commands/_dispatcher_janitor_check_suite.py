"""What the post-merge janitor RUNS: the check-suite the repository DECLARES.

Split out of `_dispatcher_fabro_argv` along the same seam
`_dispatcher_janitor_bootstrap_recipe` is split from its own step: WHAT
check-suite the janitor invokes is a declared property of the governed
repository, and the record of why a default exists belongs beside its own
resolver rather than inside the argv builders that consume it.

WHY THE CHECK-SUITE IS DECLARED AT ALL. The shipped janitor hard-coded this
fleet's `mise exec -- just check-no-workflow-edits install-worktree-pack check`
argv -- our own toolchain, silently assumed of every adopter, whose only
override was an UNCOMMITTED per-invocation `--janitor` argv. Measured on
homelab, an adopter that does not import livespec-dev-tooling: its first clean
hardened run produced a real merge and then FAILED at janitor-post-merge
because its justfile has no `install-worktree-pack` recipe, stranding the
merged item `active` and failing every further dispatch identically. The
committed `dispatcher.janitor.check_suite` key makes the topology a
DECLARATION and the fleet argv a DECLARED DEFAULT: every
unresolvable-check-suite refusal names which resolution was attempted and
names the key that declares it, so an adopter can tell "your check-suite is
red" apart from "I ran a recipe you never claimed to have".

A DECLARED COMMAND IS INVOKED VERBATIM. The default's argv carries this
fleet's `mise exec --` prefix because `just` reaches these hosts through mise;
a declared command is invoked exactly as the adopter wrote it, because imposing
our own invocation wrapper on someone else's command is the same
assumed-tooling defect one layer down.

ONLY AN ABSENT KEY FALLS BACK, exactly as for the master-CI pipeline and the
janitor-bootstrap recipe. A key that is PRESENT but unusable -- carrying a
non-string, empty, or unparseable command, or hanging off a
`dispatcher.janitor` value that is not a mapping at all -- is a DEFECT, never
a silent slide onto the convention. An absent key says "this repository uses
the fleet convention"; a present one says "this repository's check-suite is
NOT the convention", and completing it from the convention would run, and then
grade a merge on, a check-suite the adopter has already said is the wrong one.

AND THE COMMITTED DECLARATION OUTRANKS THE PER-INVOCATION `--janitor`
OVERRIDE. An uncommitted per-invocation argv silently overriding committed
policy is exactly what the committed-configuration-only class forbids
(`SPECIFICATION/contracts.md`, the control-surface-and-audit rules): a dial
that overrides a safety-relevant committed policy is committed configuration
with a reviewable diff. Where `--janitor` remains it is scoped to a repository
that has declared no check-suite.

Declaration changes WHAT check-suite runs, never WHETHER absence of proof
refuses (`SPECIFICATION/contracts.md`, the janitor check-suite resolution
clause).
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands._config import dispatcher_block
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt

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

# The committed key that declares the check-suite, named verbatim in every
# unresolvable-check-suite refusal so the reader knows where to write the
# answer.
JANITOR_CHECK_SUITE_KEY = "dispatcher.janitor.check_suite"

# `install-worktree-pack` PRECEDES `check` because the janitor checkout is a
# fresh worktree that never ran `just bootstrap`, and the worktree-discipline
# pack is gitignored — so it is absent there by construction. Since
# livespec-dev-tooling v0.54.24 an absent pack is a FAIL by default, which reds
# the janitor's own `just check` on a fully conformant repo (observed on the
# `bd-ib-hvuhxp` reconcile: PR #1018 merged green, then reconcile-merged failed
# at janitor-post-merge with worktree_pack_absent and stranded the claim).
#
# The janitor is a normal worktree-equivalent, NOT a declared sandbox, so this
# PROVISIONS the pack rather than exempting the venue: the asserted property
# becomes TRUE instead of skipped. Presence enforcement stays intact and no
# second `livespec.sandboxExempt` marker is introduced.
_DEFAULT_COMMAND: tuple[str, ...] = (
    "mise",
    "exec",
    "--",
    "just",
    "check-no-workflow-edits",
    "install-worktree-pack",
    "check",
)

# The fleet default convention as one command line, which is what every
# operator-facing sentence renders. Derived from the argv above rather than
# spelled a second time, so the prose cannot drift from the command actually
# run.
DEFAULT_CHECK_SUITE = shlex.join(_DEFAULT_COMMAND)

DECLARED_RESOLUTION = "declared"
DEFAULT_RESOLUTION = "default"
OVERRIDE_RESOLUTION = "override"

# What a defective declaration renders its check-suite as. It is a sentinel
# rather than the convention's text precisely because the convention is the
# wrong answer here: prose reading `mise exec -- just ...` would tell the
# operator we looked for a check-suite they never declared.
UNRESOLVED_CHECK_SUITE = "<unresolved>"

_JANITOR_BLOCK = "janitor"
_CHECK_SUITE_KEY = "check_suite"


@dataclass(frozen=True, kw_only=True)
class JanitorCheckSuite:
    """The check-suite the post-merge janitor runs, plus where it came from.

    `command` is the argv the janitor invokes; `text` is the check-suite as the
    repository declares it (or as the convention spells it, or as the
    per-invocation override supplied it), and is what every operator-facing
    sentence renders.

    `resolution` is `declared` when the committed key supplied the command,
    `override` when the per-invocation `--janitor` argv did, and `default` when
    the convention did. It is carried rather than re-derived because the
    refusal text and the journal record both have to say which resolution was
    attempted, and a second derivation could disagree with the first.

    `defect` names what is wrong with a PRESENT declaration, and is `None` on
    every usable check-suite. A defective check-suite still reports `declared`
    as its attempted resolution -- the adopter did declare, the declaration is
    just not readable -- so the refusal names the key the operator has to go
    and fix rather than blaming the convention it never chose.
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
    """Resolve the check-suite from a `dispatcher` block; declared wins over `janitor`.

    `janitor` is the uncommitted per-invocation `--janitor` argv. It is
    consulted only once the committed declaration has been found ABSENT,
    because an uncommitted per-invocation argv may not displace committed
    policy; with no declaration and no override the fleet convention stands.
    """
    declared = _declared_check_suite(block=block)
    if declared is not None:
        return declared
    if janitor:
        return JanitorCheckSuite(
            command=janitor,
            text=shlex.join(janitor),
            resolution=OVERRIDE_RESOLUTION,
        )
    return JanitorCheckSuite(
        command=_DEFAULT_COMMAND,
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


def _declared_check_suite(*, block: dict[str, Any]) -> JanitorCheckSuite | None:
    """The repository's declaration, or None when the key is truly ABSENT.

    Presence is tested with `in` rather than a `get` sentinel because a key
    written as JSON `null` is a present declaration that names nothing, and
    reading it as absent is exactly the fallback this refuses.
    """
    if _JANITOR_BLOCK not in block:
        return None
    raw = block[_JANITOR_BLOCK]
    if not isinstance(raw, dict):
        return _defective(
            defect=(
                f"`dispatcher.{_JANITOR_BLOCK}` is present but is not a mapping naming "
                f"`{_CHECK_SUITE_KEY}`"
            )
        )
    declared = cast("dict[str, Any]", raw)
    if _CHECK_SUITE_KEY not in declared:
        return None
    text = declared[_CHECK_SUITE_KEY]
    if not isinstance(text, str) or text.strip() == "":
        return _defective(
            defect=f"`{JANITOR_CHECK_SUITE_KEY}` is present but is not a non-empty string"
        )
    command = _parse_command(text=text)
    if command is None:
        return _defective(
            defect=(
                f"`{JANITOR_CHECK_SUITE_KEY}` is present but does not parse as a shell "
                f"command: {text!r}"
            )
        )
    return JanitorCheckSuite(command=command, text=text, resolution=DECLARED_RESOLUTION)


def _defective(*, defect: str) -> JanitorCheckSuite:
    """A present-but-unusable declaration: no command resolved, and the reason carried."""
    return JanitorCheckSuite(
        command=(),
        text=UNRESOLVED_CHECK_SUITE,
        resolution=DECLARED_RESOLUTION,
        defect=defect,
    )


def _parse_command(*, text: str) -> tuple[str, ...] | None:
    """Split a declared check-suite into argv; None when it is not a shell command.

    An unbalanced quote raises rather than returning a best guess, and a text
    whose first token is empty (`''`, which splits to one empty string) names
    no program -- both are the same answer to the caller, which is that this
    declaration resolves nothing.
    """
    split = attempt(action=lambda: shlex.split(text), exceptions=(ValueError,))
    if isinstance(split, AttemptFailure):
        return None
    tokens = tuple(split)
    return tokens if tokens and tokens[0] else None
