"""WHICH livespec core the post-merge janitor clones, and at WHAT ref.

Split out of `_dispatcher_fabro_argv` along the same seam
`_dispatcher_janitor_check_suite` and `_dispatcher_janitor_bootstrap_recipe`
are split from their own steps: WHICH livespec core the janitor provisions is a
declared property of the governed repository, and the record of why one field
carries a fleet default while the other refuses without one belongs beside its
own resolver rather than inside the argv builders that consume it.

THE REF REFUSES ON ABSENCE; IT DOES NOT FALL BACK TO A MOVING TIP. The shipped
resolver answered a missing `compat.pinned` with a bare `master`, so a
repository that declared no pin silently got whatever livespec core happened to
be at the tip when the janitor cloned -- a ref that can MOVE under an in-flight
dispatch, leaving two janitor runs of the same item graded against two
different cores with nothing in the journal saying which. The
janitor-core-provisioning-resolution clause of `SPECIFICATION/contracts.md`
forbids exactly that substitution: an absent or unreadable declaration resolves
to `UNRESOLVED_JANITOR_CORE`, and provisioning becomes a journaled degraded
outcome that NAMES the missing declaration.

WHAT IS FORBIDDEN IS THE SILENT DEFAULT, NEVER A DECLARED VALUE. A repository
MAY declare `pinned: "master"` -- the ratified bootstrap state that fires
doctor's `contract-version-compatibility` warn as expected -- and that value is
honored verbatim, because it is a ref the repository explicitly CHOSE rather
than one the Dispatcher imposed on its behalf.

THE REPOSITORY URL HAS A FLEET DEFAULT; THE REF HAS NONE. `core_repo` is
OPTIONAL, and an absent key is a complete answer -- "clone the fleet livespec
core" -- so it resolves to `FLEET_JANITOR_CORE_REPO_URL` and an adopter that
mirrors core points at its own. A PRESENT but unusable `core_repo` is a DEFECT
and refuses, on the same reasoning the check-suite resolver records: a present
key says this repository's core is NOT the fleet's, and completing it from the
fleet default would clone, and then grade a merge against, a core the adopter
has already said is the wrong one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from livespec_orchestrator_beads_fabro.commands import _jsonc

__all__: list[str] = [
    "FLEET_JANITOR_CORE_REPO_URL",
    "JANITOR_CORE_PINNED_KEY",
    "JANITOR_CORE_REPO_KEY",
    "UNRESOLVED_JANITOR_CORE",
    "JanitorCoreProvisioning",
    "janitor_core_provisioning_defect",
    "resolve_janitor_core_provisioning",
]

_PLUGIN_BLOCK = "livespec-orchestrator-beads-fabro"
_COMPAT_BLOCK = "compat"
_PINNED_KEY = "pinned"
_CORE_REPO_KEY = "core_repo"

# The committed keys that declare janitor-core provisioning, spelled out in
# full and named verbatim in every refusal, so a reader of the degradation
# knows exactly where in `.livespec.jsonc` to write the answer.
JANITOR_CORE_PINNED_KEY = f"{_PLUGIN_BLOCK}.{_COMPAT_BLOCK}.{_PINNED_KEY}"
JANITOR_CORE_REPO_KEY = f"{_PLUGIN_BLOCK}.{_COMPAT_BLOCK}.{_CORE_REPO_KEY}"

# The fleet livespec core, which is what an UNDECLARED `core_repo` means.
FLEET_JANITOR_CORE_REPO_URL = "https://github.com/thewoolleyman/livespec.git"

# What a field that resolved nothing renders as. A sentinel rather than a ref
# or URL literal, for the reason this module exists: the wrong answer here is a
# value we guessed at, and prose naming `master` would tell an operator we
# resolved a pin they never declared.
UNRESOLVED_JANITOR_CORE = "<unresolved>"


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
    """Resolve the janitor-core ref and repository from a `.livespec.jsonc` text.

    An unreadable config is not a third answer: it means neither key could be
    read, which is `pinned` absent (a defect) and `core_repo` absent (the fleet
    default), exactly as an empty but well-formed config would resolve.
    """
    compat = _compat_block(config_text=config_text)
    ref, ref_defect = _resolve_ref(compat=compat)
    repo_url, repo_defect = _resolve_repo_url(compat=compat)
    defects = tuple(defect for defect in (ref_defect, repo_defect) if defect is not None)
    return JanitorCoreProvisioning(
        ref=ref,
        repo_url=repo_url,
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


def _compat_block(*, config_text: str) -> dict[str, object] | None:
    """The repository's `compat` mapping, or None when nothing readable names one."""
    parsed_raw = _jsonc.parse(text=config_text)
    if isinstance(parsed_raw, _jsonc.JsoncFailure):
        return None
    if not isinstance(parsed_raw, dict):
        return None
    plugin_raw: object = cast("dict[str, object]", parsed_raw).get(_PLUGIN_BLOCK)
    if not isinstance(plugin_raw, dict):
        return None
    compat_raw: object = cast("dict[str, object]", plugin_raw).get(_COMPAT_BLOCK)
    if not isinstance(compat_raw, dict):
        return None
    return cast("dict[str, object]", compat_raw)


def _resolve_ref(*, compat: dict[str, object] | None) -> tuple[str, str | None]:
    """The declared janitor-core ref; the sentinel plus a defect when there is none.

    Presence is tested with `in` rather than a `get` sentinel because a key
    written as JSON `null` is a PRESENT declaration naming nothing, which earns
    the unusable wording rather than the absent one.
    """
    if compat is None or _PINNED_KEY not in compat:
        return UNRESOLVED_JANITOR_CORE, _absent_defect(key=JANITOR_CORE_PINNED_KEY)
    declared = compat[_PINNED_KEY]
    if not isinstance(declared, str) or declared.strip() == "":
        return UNRESOLVED_JANITOR_CORE, _unusable_defect(key=JANITOR_CORE_PINNED_KEY)
    return declared.strip(), None


def _resolve_repo_url(*, compat: dict[str, object] | None) -> tuple[str, str | None]:
    """The declared clone repository; the fleet livespec core when the key is ABSENT."""
    if compat is None or _CORE_REPO_KEY not in compat:
        return FLEET_JANITOR_CORE_REPO_URL, None
    declared = compat[_CORE_REPO_KEY]
    if not isinstance(declared, str) or declared.strip() == "":
        return UNRESOLVED_JANITOR_CORE, _unusable_defect(key=JANITOR_CORE_REPO_KEY)
    return declared.strip(), None


def _absent_defect(*, key: str) -> str:
    """A required declaration that is not there at all."""
    return (
        f"`{key}` is absent or unreadable, and a missing pin is never completed from a moving "
        "branch tip"
    )


def _unusable_defect(*, key: str) -> str:
    """A declaration that IS there but names nothing a clone could use."""
    return (
        f"`{key}` is present but is not a non-empty string, and a present declaration is never "
        "completed from a default this repository has said is not its own"
    )
