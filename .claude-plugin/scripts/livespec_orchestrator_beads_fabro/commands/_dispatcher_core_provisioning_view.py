"""WHICH livespec core the post-merge janitor clones, and at WHAT ref.

This is a PROJECTION of the typed repository-integration contract, not a
resolver: `_dispatcher_integration_resolver` answers what `compat.pinned` and
`compat.core_repo` resolve to, and this module shapes the pair into what the
dispatch plan carries and what a degradation says.

THE REF REFUSES ON ABSENCE; IT DOES NOT FALL BACK TO A MOVING TIP. The shipped
resolver answered a missing `compat.pinned` with a bare `master`, so a repository
that declared no pin silently got whatever livespec core happened to be at the
tip when the janitor cloned -- a ref that can MOVE under an in-flight dispatch,
leaving two janitor runs of the same item graded against two different cores with
nothing in the journal saying which. That is why the field is REQUIRED in the
schema: the only substitutable value is the one its own clause forbids, so an
absent declaration resolves to `Defective` and provisioning becomes a journaled
degraded outcome that NAMES the missing declaration.

WHAT IS FORBIDDEN IS THE SILENT DEFAULT, NEVER A DECLARED VALUE. A repository MAY
declare `pinned: "master"` -- the ratified bootstrap state that fires doctor's
`contract-version-compatibility` warn as expected -- and that value is honored
verbatim, because it is a ref the repository explicitly CHOSE rather than one the
Dispatcher imposed on its behalf.

THE REPOSITORY URL HAS A FLEET DEFAULT; THE REF HAS NONE. `core_repo` is
OPTIONAL, and an absent key is a complete answer -- "clone the fleet livespec
core" -- so an adopter that mirrors core points at its own. A PRESENT but
unusable `core_repo` is a DEFECT and refuses, on the same reasoning every other
field records: a present key says this repository's core is NOT the fleet's, and
completing it from the fleet default would clone, and then grade a merge against,
a core the adopter has already said is the wrong one.
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_contract import (
    ResolvedIntegrationContract,
    resolve_integration_contract,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_declaration import (
    declaration_from_config_text,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    FLEET_CORE_REPO_URL,
    UNRESOLVED_NAME,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Defective,
    resolved_name,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    COMPAT_CORE_REPO_KEY,
    COMPAT_PINNED_KEY,
    CORE_PINNED_REF_FIELD,
    CORE_REPO_URL_FIELD,
)

__all__: list[str] = [
    "FLEET_JANITOR_CORE_REPO_URL",
    "JANITOR_CORE_PINNED_KEY",
    "JANITOR_CORE_REPO_KEY",
    "UNRESOLVED_JANITOR_CORE",
    "JanitorCoreProvisioning",
    "janitor_core_provisioning_defect",
    "janitor_core_provisioning_from_contract",
    "resolve_janitor_core_provisioning",
]

JANITOR_CORE_PINNED_KEY = COMPAT_PINNED_KEY
JANITOR_CORE_REPO_KEY = COMPAT_CORE_REPO_KEY

FLEET_JANITOR_CORE_REPO_URL = FLEET_CORE_REPO_URL

# What a field that resolved nothing renders as. A sentinel rather than a ref or
# URL literal, for the reason this module exists: the wrong answer here is a
# value we guessed at, and prose naming `master` would tell an operator we
# resolved a pin they never declared.
UNRESOLVED_JANITOR_CORE = UNRESOLVED_NAME


@dataclass(frozen=True, kw_only=True)
class JanitorCoreProvisioning:
    """The livespec core the janitor clones, and what is wrong with the declaration.

    `ref` and `repo_url` are `UNRESOLVED_JANITOR_CORE` on every arm that
    resolved nothing, so a caller that ignores `defect` provisions from a
    sentinel that cannot resolve rather than from a plausible-looking moving
    tip -- the same discipline `_dispatcher_janitor_venue`'s `UNRESOLVED_VENUE`
    keeps for the venue ref.

    `defect` carries EVERY unresolved key at once rather than the first, so an
    adopter that has declared neither field learns both in one degradation
    instead of one dispatch at a time.
    """

    ref: str
    repo_url: str
    defect: str | None = None


def resolve_janitor_core_provisioning(*, config_text: str) -> JanitorCoreProvisioning:
    """Project the janitor-core ref and repository out of a `.livespec.jsonc` text.

    An unreadable config is not a third answer: it means neither key could be
    read, which is `pinned` absent (a defect) and `core_repo` absent (the fleet
    default), exactly as an empty but well-formed config would resolve.

    This is the PRE-PLAN entry point. A dispatch that HAS a plan reads its core
    provisioning off the contract that plan already resolved, through
    `janitor_core_provisioning_from_contract`.
    """
    return janitor_core_provisioning_from_contract(
        resolved=resolve_integration_contract(
            declaration=declaration_from_config_text(config_text=config_text)
        )
    )


def janitor_core_provisioning_from_contract(
    *, resolved: ResolvedIntegrationContract
) -> JanitorCoreProvisioning:
    """Shape the ALREADY-RESOLVED core pin and clone repository for the dispatch plan.

    The declared-core-provisioning behaviour is HOMED on the one resolved
    contract rather than on a reading of its own: the pin and the clone
    repository are two of that contract's fields, and re-reading them beside it
    is how the plan and the journaled record could name different cores for one
    dispatch.
    """
    ref = resolved.resolutions[CORE_PINNED_REF_FIELD.attribute]
    repo_url = resolved.resolutions[CORE_REPO_URL_FIELD.attribute]
    defects = tuple(
        resolution.reason for resolution in (ref, repo_url) if isinstance(resolution, Defective)
    )
    return JanitorCoreProvisioning(
        ref=resolved_name(resolution=ref),
        repo_url=resolved_name(resolution=repo_url),
        defect="; ".join(defects) if defects else None,
    )


def janitor_core_provisioning_defect(*, ref: str, repo_url: str) -> str | None:
    """The defect a plan's unresolved janitor-core ref / repository stands for.

    The dispatch plan carries the RESOLVED strings, not the resolution object,
    so the sentinel is what survives into the post-merge flow. Reading it back
    into a sentence HERE, beside the keys it names, is what lets the janitor
    degrade on a missing declaration without a second copy of these key names
    growing at the post-merge call site.
    """
    unresolved = tuple(
        key
        for key, value in (
            (JANITOR_CORE_PINNED_KEY, ref),
            (JANITOR_CORE_REPO_KEY, repo_url),
        )
        if value == UNRESOLVED_JANITOR_CORE
    )
    if not unresolved:
        return None
    keys = " and ".join(f"`{key}`" for key in unresolved)
    return (
        f"the livespec-core clone resolves nothing from {keys}: the committed declaration is "
        "absent, unreadable, or unusable, and it is never completed from a moving `master` / "
        "`main` tip that can move under an in-flight dispatch"
    )
