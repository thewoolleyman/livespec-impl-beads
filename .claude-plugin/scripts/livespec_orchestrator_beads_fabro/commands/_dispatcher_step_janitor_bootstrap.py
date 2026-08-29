"""The `janitor-bootstrap` step's integration point, and how to re-verify it.

The post-merge janitor bootstraps the GOVERNED repository's commit-refuse hooks
by running that repository's own hook-install recipe -- the one it DECLARES
under `dispatcher.janitor_bootstrap.recipe`, or the fleet default convention
when it declares none (`_dispatcher_janitor_bootstrap_recipe` owns that
resolution). That recipe is a required INTEGRATION POINT the adopter provides:
when it is absent the bootstrap cannot run, and the janitor can only observe
that AFTER the merge -- which is what makes this a post-merge step rather than a
preflight.

WHY THE RE-VERIFICATION IS A RESOLVABILITY CHECK ON THE RECIPE, not a re-run of
the bootstrap. The degraded outcome names a missing integration point; what
clears it is that integration point being PROVIDED, and the pre-dispatch moment
cannot run a post-merge janitor to find out. Answering "is this recipe there?"
before any sandbox work is exactly the question the degradation asked, at the
one moment a pre-dispatch verification can answer it.

TWO SHAPES OF PROVISION, because the recipe is now the adopter's to name. A
`just` recipe is answered from the governed repository's OWN committed justfile
rather than by shelling out to `just --summary`: the dispatching host is not
guaranteed to carry `just` on its PATH, and a re-verification that can only fail
on such a host would make the refusal permanent for a repository that had
already fixed the thing. Any other command has no declaration surface we can
read, so it is answered by whether it is INVOKABLE -- a repository-relative
executable, or a program on PATH. The asymmetry is deliberate: where the
repository itself states what it provides, that statement is the stronger and
more host-independent evidence, and we prefer it.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path, PurePosixPath

from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_bootstrap_recipe import (
    JanitorBootstrapRecipe,
)

__all__: list[str] = ["hook_install_recipe_present"]

# The command name whose arguments are recipe names in a repository's justfile.
_JUST = "just"

# The filenames `just` itself accepts for a repository's root justfile.
_JUSTFILE_NAMES: tuple[str, ...] = ("justfile", "Justfile", ".justfile")


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
    """
    for index, token in enumerate(command):
        if PurePosixPath(token).name != _JUST:
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
