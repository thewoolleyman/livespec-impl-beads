"""The `janitor-bootstrap` step's integration point, and how to re-verify it.

The post-merge janitor bootstraps the GOVERNED repository's commit-refuse hooks
by running that repository's own `just install-commit-refuse-hooks` recipe. That
recipe is a required INTEGRATION POINT the adopter provides: when it is absent
the bootstrap cannot run, and the janitor can only observe that AFTER the merge
-- which is what makes this a post-merge step rather than a preflight.

WHY THE RE-VERIFICATION IS A PRESENCE CHECK ON THE RECIPE, not a re-run of the
bootstrap. The degraded outcome names a missing integration point; what clears
it is that integration point being PROVIDED, and the pre-dispatch moment cannot
run a post-merge janitor to find out. Reading the governed repository's own
justfile answers exactly the question the degradation asked, before any sandbox
work, which is where a pre-dispatch verification has to be able to answer.

It reads the committed justfile rather than shelling out to `just --summary`
deliberately: the dispatching host is not guaranteed to carry `just` on its
PATH, and a re-verification that can only fail on such a host would make the
refusal permanent for a repository that had already fixed the thing.
"""

from __future__ import annotations

from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_step_waivers import WAIVER_ESCAPE

__all__: list[str] = [
    "HOOK_INSTALL_RECIPE",
    "INTEGRATION_POINT",
    "REMEDY",
    "hook_install_recipe_present",
]

HOOK_INSTALL_RECIPE = "install-commit-refuse-hooks"

INTEGRATION_POINT = f"the governed repository's `just {HOOK_INSTALL_RECIPE}` hook-install recipe"

REMEDY = (
    f"declare an `{HOOK_INSTALL_RECIPE}` recipe in the governed repository's "
    f"justfile so the post-merge janitor can bootstrap its commit-refuse hooks, "
    f"{WAIVER_ESCAPE}."
)

# The filenames `just` itself accepts for a repository's root justfile.
_JUSTFILE_NAMES: tuple[str, ...] = ("justfile", "Justfile", ".justfile")


def hook_install_recipe_present(*, repo: Path) -> bool:
    """Whether `repo` declares the hook-install recipe -- the re-verification.

    A recipe declaration starts at column zero and is followed by `:`, with any
    dependencies after it, so the prefix test matches both the bare recipe and
    one carrying dependencies while ignoring every mention inside a comment or a
    recipe body (both of which are indented or prefixed).
    """
    for name in _JUSTFILE_NAMES:
        path = repo / name
        if not path.is_file():
            continue
        if _declares_recipe(path=path):
            return True
    return False


def _declares_recipe(*, path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    prefix = f"{HOOK_INSTALL_RECIPE}:"
    return any(line.startswith(prefix) for line in text.splitlines())
