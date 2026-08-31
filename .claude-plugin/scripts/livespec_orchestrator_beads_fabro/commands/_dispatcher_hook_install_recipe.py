"""The governed repository's hook-install recipe: what it resolves to, and whether it is there.

Both halves of ONE integration point live here. The recipe the post-merge
janitor bootstraps is a PROJECTION of the typed repository-integration contract
(`_dispatcher_integration_resolver` answers what
`dispatcher.janitor_bootstrap.recipe` resolves to), and the pre-dispatch
re-verification asks whether the repository actually PROVIDES the recipe that
resolution named. Splitting the two would put the question and its subject in
different files, and the question is only meaningful about the resolved answer.

WHY THE RECIPE IS DECLARED AT ALL. The shipped step hard-coded this fleet's
`just install-commit-refuse-hooks` recipe -- our own toolchain, silently assumed
of every adopter. `SPECIFICATION/contracts.md` ratifies that members and adopters
consume the orchestrator IDENTICALLY, so an adopter with its own hook-install
mechanism could satisfy the step only by adopting our `just` recipe, or by
carrying a waiver for an integration point it does in fact provide. The committed
key makes the topology a DECLARATION and the fleet recipe a DECLARED DEFAULT, so
an adopter can tell "your recipe is missing" apart from "I looked for a recipe
you never claimed to have".

ONLY AN ABSENT KEY FALLS BACK, and a DECLARED BLOCK MUST NAME ITS RECIPE. A key
that is PRESENT but unusable is a DEFECT, never a silent slide onto the
convention: completing it from the convention would bootstrap, and then
re-verify, a recipe the adopter has already said is the wrong one. That rule is
the schema's `parent_key` on the recipe field, applied by the one generic
resolver rather than restated here.

WHY THE RE-VERIFICATION IS A RESOLVABILITY CHECK ON THE RECIPE, not a re-run of
the bootstrap. The degraded outcome names a missing integration point; what
clears it is that integration point being PROVIDED, and the pre-dispatch moment
cannot run a post-merge janitor to find out. Answering "is this recipe there?"
before any sandbox work is exactly the question the degradation asked, at the one
moment a pre-dispatch verification can answer it.

TWO SHAPES OF PROVISION, because the recipe is the adopter's to name. A `just`
recipe is answered from the governed repository's OWN committed justfile rather
than by shelling out to `just --summary`: the dispatching host is not guaranteed
to carry `just` on its PATH, and a re-verification that can only fail on such a
host would make the refusal permanent for a repository that had already fixed the
thing. Any other command has no declaration surface we can read, so it is
answered by whether it is INVOKABLE -- a repository-relative executable, or a
program on PATH. The asymmetry is deliberate: where the repository itself states
what it provides, that statement is the stronger and more host-independent
evidence, and we prefer it.

Declaration changes WHAT recipe is bootstrapped and re-verified, never WHETHER
absence of proof refuses (`SPECIFICATION/contracts.md`, the janitor-bootstrap
recipe resolution clause).
"""

from __future__ import annotations

import os
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from livespec_orchestrator_beads_fabro.commands._config import dispatcher_block
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_declaration import (
    declaration_from_dispatcher_block,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    FLEET_RECIPE_RUNNER,
    JANITOR_BOOTSTRAP_RECIPE_DEFAULT,
    UNRESOLVED_NAME,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Declared,
    Defective,
    resolve_integration_field,
    resolved_argv,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    JANITOR_BOOTSTRAP_KEY,
    JANITOR_BOOTSTRAP_RECIPE_FIELD,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_step_waivers import WAIVER_ESCAPE

__all__: list[str] = [
    "DECLARED_RESOLUTION",
    "DEFAULT_RECIPE",
    "DEFAULT_RESOLUTION",
    "JANITOR_BOOTSTRAP_KEY",
    "UNRESOLVED_RECIPE",
    "JanitorBootstrapRecipe",
    "hook_install_recipe_present",
    "integration_point",
    "janitor_bootstrap_recipe_from_block",
    "recipe_resolution_sentence",
    "remedy",
    "resolve_janitor_bootstrap_recipe",
]

# The fleet default convention, spelled as the ratified clause spells it: the
# recipe itself, without this fleet's `mise exec --` invocation wrapper, which is
# an argv detail rather than part of the recipe's name.
DEFAULT_RECIPE = shlex.join(JANITOR_BOOTSTRAP_RECIPE_DEFAULT[3:])

DECLARED_RESOLUTION = "declared"
DEFAULT_RESOLUTION = "default"

# What a defective declaration renders its recipe as. A sentinel rather than the
# convention's text precisely because the convention is the wrong answer here.
UNRESOLVED_RECIPE = UNRESOLVED_NAME

# The filenames `just` itself accepts for a repository's root justfile.
_JUSTFILE_NAMES: tuple[str, ...] = ("justfile", "Justfile", ".justfile")


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
    """Project the recipe field of a `dispatcher` block into the bootstrap's argv."""
    resolution = resolve_integration_field(
        field=JANITOR_BOOTSTRAP_RECIPE_FIELD,
        declaration=declaration_from_dispatcher_block(block=block),
    )
    if isinstance(resolution, Defective):
        return JanitorBootstrapRecipe(
            command=(),
            text=UNRESOLVED_RECIPE,
            resolution=DECLARED_RESOLUTION,
            defect=resolution.reason,
        )
    command = resolved_argv(resolution=resolution)
    if isinstance(resolution, Declared):
        return JanitorBootstrapRecipe(
            command=command, text=shlex.join(command), resolution=DECLARED_RESOLUTION
        )
    return JanitorBootstrapRecipe(
        command=command, text=DEFAULT_RECIPE, resolution=DEFAULT_RESOLUTION
    )


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


def hook_install_recipe_present(*, repo: Path, recipe: JanitorBootstrapRecipe) -> bool:
    """Whether `repo` provides the resolved recipe -- the re-verification.

    A defective declaration resolves no command at all, so there is nothing to
    look for and nothing that could be found: it is unresolvable by
    construction, and the refusal names the declaration rather than the repo.
    """
    if recipe.defect is not None:
        return False
    names = _just_recipe_names(command=recipe.command)
    if names:
        return _declares_any(repo=repo, names=names)
    return _invokable(repo=repo, program=recipe.command[0])


def _just_recipe_names(*, command: tuple[str, ...]) -> tuple[str, ...]:
    """The recipe names a `just` invocation names, or () when it invokes no `just`.

    Every non-flag token after `just` is a candidate rather than only the first,
    because `just` accepts options before its recipes and a flag's VALUE is
    indistinguishable from a recipe name without knowing every option's arity.
    Over-collecting is the safe direction here: the caller asks whether ANY
    candidate is declared, so a stray flag value simply never matches.

    The runner's NAME comes from the fleet-defaults module rather than from a
    parser constant of its own. It is the same name the bootstrap recipe default
    is composed from, so a fleet that changed its recipe runner would otherwise
    change the default and leave this discrimination looking for the old one --
    and it is a fleet-toolchain literal, which that module is the single place
    the ratified ban admits.
    """
    for index, token in enumerate(command):
        if PurePosixPath(token).name != FLEET_RECIPE_RUNNER:
            continue
        return tuple(token for token in command[index + 1 :] if not token.startswith("-"))
    return ()


def _declares_any(*, repo: Path, names: tuple[str, ...]) -> bool:
    """Whether any named recipe is declared in the repository's own justfile.

    A recipe declaration starts at column zero and is followed by `:`, with any
    dependencies after it, so the prefix test matches both the bare recipe and
    one carrying dependencies while ignoring every mention inside a comment or a
    recipe body (both of which are indented or prefixed).
    """
    for justfile in _JUSTFILE_NAMES:
        path = repo / justfile
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if any(line.startswith(f"{name}:") for name in names for line in lines):
            return True
    return False


def _invokable(*, repo: Path, program: str) -> bool:
    """Whether a non-`just` recipe's program can actually be run.

    The repository-relative candidate is tried FIRST so an adopter shipping its
    own `scripts/install-hooks.sh` is answered from the repository itself, the
    same evidence a justfile gives; PATH is the fallback for a recipe that
    invokes an ordinary tool.
    """
    candidate = repo / program
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return True
    return shutil.which(program) is not None
