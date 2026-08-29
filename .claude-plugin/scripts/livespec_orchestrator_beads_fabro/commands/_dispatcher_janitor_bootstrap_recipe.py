"""What the `janitor-bootstrap` step bootstraps: the recipe the repository DECLARES.

Split out of `_dispatcher_step_janitor_bootstrap` along the same seam
`_dispatcher_master_ci_pipeline` is split from its preflight: WHAT recipe is
bootstrapped and re-verified is a declared property of the governed repository,
and the record of why a default exists belongs beside its own resolver rather
than inside the check that consumes it.

WHY THE RECIPE IS DECLARED AT ALL. The shipped step hard-coded this fleet's
`just install-commit-refuse-hooks` recipe -- our own toolchain, silently assumed
of every adopter. `SPECIFICATION/contracts.md` ratifies that members and
adopters consume the orchestrator IDENTICALLY, so an adopter with its own
hook-install mechanism could satisfy the step only by adopting our `just`
recipe, or by carrying a waiver for an integration point it does in fact
provide. The committed `dispatcher.janitor_bootstrap` key makes the topology a
DECLARATION and the fleet recipe a DECLARED DEFAULT: every unresolvable-recipe
refusal names which of the two resolutions was attempted and names the key that
declares it, so an adopter can tell "your recipe is missing" apart from "I
looked for a recipe you never claimed to have".

ONLY AN ABSENT KEY FALLS BACK, exactly as for the master-CI pipeline. A key that
is PRESENT but unusable -- not a mapping, naming no recipe, or carrying a
non-string, empty, or unparseable command -- is a DEFECT, never a silent slide
onto the convention. An absent key says "this repository uses the fleet
convention"; a present one says "this repository's recipe is NOT the
convention", and completing it from the convention would bootstrap, and then
re-verify, a recipe the adopter has already said is the wrong one.

Declaration changes WHAT recipe is bootstrapped and re-verified, never WHETHER
absence of proof refuses (`SPECIFICATION/contracts.md`, the janitor-bootstrap
recipe resolution clause).
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands._config import dispatcher_block
from livespec_orchestrator_beads_fabro.commands._dispatcher_step_waivers import WAIVER_ESCAPE
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt

__all__: list[str] = [
    "DECLARED_RESOLUTION",
    "DEFAULT_RECIPE",
    "DEFAULT_RESOLUTION",
    "JANITOR_BOOTSTRAP_KEY",
    "UNRESOLVED_RECIPE",
    "JanitorBootstrapRecipe",
    "integration_point",
    "janitor_bootstrap_recipe_from_block",
    "recipe_resolution_sentence",
    "remedy",
    "resolve_janitor_bootstrap_recipe",
]

# The committed key that declares the recipe, named verbatim in every
# unresolvable-recipe refusal so the reader knows where to write the answer.
JANITOR_BOOTSTRAP_KEY = "dispatcher.janitor_bootstrap"

# The fleet default convention, spelled as the ratified clause spells it.
DEFAULT_RECIPE = "just install-commit-refuse-hooks"

# How the fleet default convention is INVOKED on this fleet. `just` reaches
# these hosts through mise, so the default's argv keeps the `mise exec --`
# prefix the shipped bootstrap always used. A DECLARED recipe is invoked exactly
# as the adopter wrote it: imposing our wrapper on someone else's command is the
# same assumed-tooling defect one layer down.
_DEFAULT_COMMAND: tuple[str, ...] = ("mise", "exec", "--", "just", "install-commit-refuse-hooks")

DECLARED_RESOLUTION = "declared"
DEFAULT_RESOLUTION = "default"

# What a defective declaration renders its recipe as. It is a sentinel rather
# than the convention's text precisely because the convention is the wrong
# answer here: prose reading `just install-commit-refuse-hooks` would tell the
# operator we looked for a recipe they never declared.
UNRESOLVED_RECIPE = "<unresolved>"

_JANITOR_BOOTSTRAP_BLOCK = "janitor_bootstrap"
_RECIPE_KEY = "recipe"


@dataclass(frozen=True, kw_only=True)
class JanitorBootstrapRecipe:
    """The hook-install recipe the janitor invokes, plus where it came from.

    `command` is the argv the post-merge janitor runs; `text` is the recipe as
    the repository declares it (or as the convention spells it), and is what
    every operator-facing sentence renders. The two differ for the default,
    whose argv carries this fleet's `mise exec --` prefix.

    `resolution` is `declared` when the committed key supplied the recipe and
    `default` when the convention did. It is carried rather than re-derived
    because the refusal text and the journal record both have to say which
    resolution was attempted, and a second derivation could disagree with the
    first.

    `defect` names what is wrong with a PRESENT declaration, and is `None` on
    every usable recipe. A defective recipe still reports `declared` as its
    attempted resolution -- the adopter did declare, the declaration is just not
    readable -- so the refusal names the key the operator has to go and fix
    rather than blaming the convention it never chose.
    """

    command: tuple[str, ...]
    text: str
    resolution: str
    defect: str | None = None


def resolve_janitor_bootstrap_recipe(*, cwd: Path) -> JanitorBootstrapRecipe:
    """Resolve the governed repository's recipe from its committed `.livespec.jsonc`.

    An absent key is an ANSWER -- this repository uses the fleet convention --
    so it rides the same block reader as every other dispatcher key rather than
    a special absent-file path of its own.
    """
    return janitor_bootstrap_recipe_from_block(block=dispatcher_block(cwd=cwd))


def janitor_bootstrap_recipe_from_block(*, block: dict[str, Any]) -> JanitorBootstrapRecipe:
    """Resolve the recipe from a `dispatcher` block; ABSENT key -> the convention.

    Presence is tested with `in` rather than a `get` sentinel because a key
    written as JSON `null` is a present declaration that names nothing, and
    reading it as absent is exactly the fallback this refuses.
    """
    if _JANITOR_BOOTSTRAP_BLOCK not in block:
        return JanitorBootstrapRecipe(
            command=_DEFAULT_COMMAND,
            text=DEFAULT_RECIPE,
            resolution=DEFAULT_RESOLUTION,
        )
    raw = block[_JANITOR_BOOTSTRAP_BLOCK]
    if not isinstance(raw, dict):
        return _defective(
            defect=(
                f"`{JANITOR_BOOTSTRAP_KEY}` is present but is not a mapping naming "
                f"`{_RECIPE_KEY}`"
            )
        )
    declared = cast("dict[str, Any]", raw)
    if _RECIPE_KEY not in declared:
        return _defective(
            defect=(
                f"`{JANITOR_BOOTSTRAP_KEY}.{_RECIPE_KEY}` is absent; a declared key names "
                "the recipe it declares, since defaulting it would bootstrap and re-verify "
                "a recipe this repository never named"
            )
        )
    text = declared[_RECIPE_KEY]
    if not isinstance(text, str) or text.strip() == "":
        return _defective(
            defect=(
                f"`{JANITOR_BOOTSTRAP_KEY}.{_RECIPE_KEY}` is present but is not a non-empty "
                f"string"
            )
        )
    command = _parse_command(text=text)
    if command is None:
        return _defective(
            defect=(
                f"`{JANITOR_BOOTSTRAP_KEY}.{_RECIPE_KEY}` is present but does not parse as "
                f"a shell command: {text!r}"
            )
        )
    return JanitorBootstrapRecipe(command=command, text=text, resolution=DECLARED_RESOLUTION)


def recipe_resolution_sentence(*, recipe: JanitorBootstrapRecipe) -> str:
    """One line naming the attempted resolution and the key that declares it."""
    if recipe.defect is not None:
        return (
            f"Resolution attempted: declared, from the committed `{JANITOR_BOOTSTRAP_KEY}` "
            f"key, which is present but unusable: {recipe.defect}. A present declaration is "
            "never completed from the default convention, because that would bootstrap a "
            "recipe this repository has said is not its own."
        )
    if recipe.resolution == DECLARED_RESOLUTION:
        return (
            f"Resolution attempted: declared, from the committed `{JANITOR_BOOTSTRAP_KEY}` "
            f"key (recipe `{recipe.text}`)."
        )
    return (
        f"Resolution attempted: default convention (recipe `{recipe.text}`); declare this "
        f"repository's own hook-install recipe under the committed `{JANITOR_BOOTSTRAP_KEY}` "
        "key."
    )


def integration_point(*, recipe: JanitorBootstrapRecipe) -> str:
    """The integration point a degraded janitor-bootstrap outcome names."""
    return f"the governed repository's `{recipe.text}` hook-install recipe"


def remedy(*, recipe: JanitorBootstrapRecipe) -> str:
    """The way out of a degraded janitor-bootstrap outcome, both routes named.

    An adopter reaching this has two honest answers and the refusal must not
    presume which: provide the recipe that was looked for, or declare the one it
    already has. The waiver escape stays last, unchanged, for the repository
    that genuinely provides no such recipe at all.
    """
    return (
        f"provide the `{recipe.text}` hook-install recipe in the governed repository so the "
        "post-merge janitor can bootstrap its commit-refuse hooks, or declare the recipe "
        f"this repository does provide under the committed `{JANITOR_BOOTSTRAP_KEY}` key, "
        f"{WAIVER_ESCAPE}."
    )


def _defective(*, defect: str) -> JanitorBootstrapRecipe:
    """A present-but-unusable declaration: no recipe resolved, and the reason carried."""
    return JanitorBootstrapRecipe(
        command=(),
        text=UNRESOLVED_RECIPE,
        resolution=DECLARED_RESOLUTION,
        defect=defect,
    )


def _parse_command(*, text: str) -> tuple[str, ...] | None:
    """Split a declared recipe into argv; None when it is not a shell command.

    An unbalanced quote raises rather than returning a best guess, and a text
    whose first token is empty (`''`, which splits to one empty string) names no
    program -- both are the same answer to the caller, which is that this
    declaration resolves nothing.
    """
    split = attempt(action=lambda: shlex.split(text), exceptions=(ValueError,))
    if isinstance(split, AttemptFailure):
        return None
    tokens = tuple(split)
    return tokens if tokens and tokens[0] else None
