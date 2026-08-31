"""The two committed governed-repository fixtures every dispatch-path seam runs over.

`SPECIFICATION/constraints.md`, the governed-repository integration constraints,
requires the integration test tier to carry a FLEET-MEMBER fixture carrying the
fleet toolchain and an ADOPTER fixture carrying none of it, and requires every
dispatch-path seam test to be parametrized over both. This module is the half
that is not a test: what the two fixtures ARE, where they live, and what each
seam owes each of them.

WHY THE EXPECTATIONS RIDE THE DESCRIPTOR RATHER THAN THE TESTS. "Members and
adopters consume the orchestrator identically" is a claim about the SEAM, not
about the values -- a member resting on fleet defaults and an adopter running
`make` must get answers of the same SHAPE from the same code path, and those
answers are different strings. Putting each fixture's expected answer on its own
descriptor is what lets one parametrized test body assert the shape for both
legs, instead of an `if` on the fixture's name inside every test, which would be
two tests wearing one name and would let an adopter-leg regression hide in the
arm nobody read.

THE MATCHER IS BORROWED, NOT RESTATED. The fleet-toolchain token set belongs to
`dev-tooling/checks/_fleet_toolchain_literals_matcher`, which is what the
`check-no-fleet-toolchain-literals` gate reads; loading that module by path
rather than copying its tuple is what stops the adopter leg from silently
testing a stale list while the gate tests a current one.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_contract import (
    ResolvedIntegrationContract,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    JANITOR_BOOTSTRAP_RECIPE_DEFAULT,
    JANITOR_CHECK_SUITE_DEFAULT,
    MASTER_CI_JOB_DEFAULT,
    MASTER_CI_WORKFLOW_DEFAULT,
    MERGE_MODE_DEFAULT,
    SANDBOX_CHECK_SUITE_DEFAULT,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan_build import (
    resolve_repo_integration_contract,
)

__all__: list[str] = [
    "ADOPTER",
    "FLEET_MEMBER",
    "FLEET_TOOLCHAIN_FILES",
    "GOVERNED_REPOS",
    "PAYLOAD_RUN_CONFIG",
    "PROBED_DEFAULT_BRANCH",
    "REPO_ROOT",
    "GovernedRepo",
    "fleet_toolchain_token",
    "over_both_fixtures",
]

_TIER_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TIER_DIR.parents[1]
_FIXTURES = _TIER_DIR / "fixtures" / "governed_repos"

# The run config the Dispatcher intersects its rendered inputs against. It is the
# REAL committed payload rather than a fixture of one, because the question the
# input-rendering seam answers is what this build would actually send.
PAYLOAD_RUN_CONFIG = (
    REPO_ROOT / ".claude-plugin" / ".fabro" / "workflows" / "implement-work-item" / "workflow.toml"
)

# What the ratified two-route probe answered about each fixture's own git state.
# Deliberately NEITHER `master` NOR `main`: a branch name this fleet would have
# hardcoded cannot distinguish a projection from a literal that happens to agree.
PROBED_DEFAULT_BRANCH = "release"

# The fleet-toolchain files a member carries and an adopter has none of. Presence
# is the structural half of the fixture contract; the literal scan below is the
# textual half, and neither alone would catch a fixture that drifted.
FLEET_TOOLCHAIN_FILES: tuple[str, ...] = (".mise.toml", "justfile", "lefthook.yml")


@dataclass(frozen=True, kw_only=True)
class GovernedRepo:
    """One committed fixture, and the answer each dispatch-path seam owes it."""

    name: str
    carries_fleet_toolchain: bool
    master_ci: tuple[str, str]
    janitor_check_suite: tuple[str, ...]
    sandbox_check_suite: tuple[str, ...]
    bootstrap_recipe: tuple[str, ...]
    merge_mode: str
    conformance_hook_install: tuple[str, ...]

    @property
    def root(self) -> Path:
        """The committed fixture tree."""
        return _FIXTURES / self.name

    @property
    def config_text(self) -> str:
        """This repository's committed declaration, exactly as the Dispatcher reads it."""
        return (self.root / ".livespec.jsonc").read_text(encoding="utf-8")

    @property
    def files(self) -> list[Path]:
        """Every committed file of the fixture tree, for a whole-tree text scan."""
        return sorted(path for path in self.root.rglob("*") if path.is_file())

    def resolved(self) -> ResolvedIntegrationContract:
        """The contract this repository resolves to, through the one production resolver."""
        return resolve_repo_integration_contract(
            config_text=self.config_text, default_branch=PROBED_DEFAULT_BRANCH
        )


# Declares NO optional key, so every seam exercises the `FleetDefault` arm.
FLEET_MEMBER = GovernedRepo(
    name="fleet_member",
    carries_fleet_toolchain=True,
    master_ci=(MASTER_CI_WORKFLOW_DEFAULT, MASTER_CI_JOB_DEFAULT),
    janitor_check_suite=JANITOR_CHECK_SUITE_DEFAULT,
    sandbox_check_suite=SANDBOX_CHECK_SUITE_DEFAULT,
    bootstrap_recipe=JANITOR_BOOTSTRAP_RECIPE_DEFAULT,
    merge_mode=MERGE_MODE_DEFAULT,
    conformance_hook_install=(),
)

# Declares every point through the schema and carries none of this fleet's
# tooling, so every seam exercises the `Declared` arm on an answer that has no
# fleet literal anywhere in it.
ADOPTER = GovernedRepo(
    name="adopter",
    carries_fleet_toolchain=False,
    master_ci=("build.yml", "verify"),
    janitor_check_suite=("make", "verify"),
    sandbox_check_suite=("make", "verify"),
    bootstrap_recipe=("make", "install-hooks"),
    merge_mode="squash",
    conformance_hook_install=("make", "install-hooks"),
)

GOVERNED_REPOS: tuple[GovernedRepo, ...] = (FLEET_MEMBER, ADOPTER)

# The one decoration every dispatch-path seam test carries. A seam test that runs
# against the member fixture only is non-conforming, so the parametrization is a
# shared name rather than a per-test literal nobody would notice the absence of.
over_both_fixtures = pytest.mark.parametrize(
    "governed",
    GOVERNED_REPOS,
    ids=[repo.name for repo in GOVERNED_REPOS],
)


def _load_text_token() -> Callable[..., str | None]:
    """The literal-ban gate's OWN matcher, loaded by path from `dev-tooling/checks/`."""
    path = REPO_ROOT / "dev-tooling" / "checks" / "_fleet_toolchain_literals_matcher.py"
    spec = importlib.util.spec_from_file_location("fleet_toolchain_matcher_for_fixtures", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast("Callable[..., str | None]", module.text_token)


fleet_toolchain_token = _load_text_token()
