"""Declared janitor-core provisioning: refuse-on-defect for the ref, fleet default for the repo.

The livespec core the post-merge janitor clones is a DECLARATION of the
governed repository, not a fleet assumption. `compat.pinned` has no safe
default -- a missing pin used to answer a bare `master`, a tip that can move
under an in-flight dispatch -- so absence resolves to the unresolved sentinel
and the provisioning degrades naming the key. `compat.core_repo` DOES have a
safe default, because an absent key completely answers "clone the fleet
livespec core"; a present-but-unusable one refuses instead of sliding onto it.

Every case reaches the resolver through `_module()`, which asserts the module
FILE exists before importing it, so a slice that has not landed yet fails on a
genuine assertion rather than on an unimportable module.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

_COMMANDS = Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
_MODULE_PATH = _COMMANDS / "_dispatcher_core_provisioning_view.py"

_PUBLIC_NAMES = {
    "FLEET_JANITOR_CORE_REPO_URL",
    "JANITOR_CORE_PINNED_KEY",
    "JANITOR_CORE_REPO_KEY",
    "UNRESOLVED_JANITOR_CORE",
    "JanitorCoreProvisioning",
    "janitor_core_provisioning_defect",
    "resolve_janitor_core_provisioning",
}


def _module() -> ModuleType:
    assert _MODULE_PATH.is_file()
    return importlib.import_module(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_core_provisioning_view"
    )


def _config(*, compat: str) -> str:
    return '{ "livespec-orchestrator-beads-fabro": { "compat": ' + compat + " } }"


def test_janitor_core_provisioning_module_owns_the_declared_resolution() -> None:
    """The resolver is its own cohesive module, exporting exactly its public surface."""
    module = _module()
    assert set(module.__all__) == _PUBLIC_NAMES
    for name in _PUBLIC_NAMES:
        assert hasattr(module, name)


def test_absent_or_unreadable_pinned_declaration_resolves_to_the_unresolved_sentinel() -> None:
    """The forbidden silent default: a missing pin never answers a moving branch tip."""
    module = _module()
    sentinel = module.UNRESOLVED_JANITOR_CORE
    for config_text in ("{}", "not-jsonc", "[]", '{ "livespec-orchestrator-beads-fabro": {} }'):
        resolved = module.resolve_janitor_core_provisioning(config_text=config_text)
        assert resolved.ref == sentinel, config_text
        assert resolved.ref != "master", config_text
        assert resolved.defect is not None, config_text
        assert module.JANITOR_CORE_PINNED_KEY in resolved.defect, config_text
    # A `compat` value that is not a mapping is the same answer: nothing readable
    # names a pin.
    assert (
        module.resolve_janitor_core_provisioning(config_text=_config(compat='"v1"')).ref == sentinel
    )


def test_present_but_unusable_pinned_declaration_refuses_naming_the_key() -> None:
    """A declaration that names nothing is a defect, never a slide onto a default."""
    module = _module()
    for pinned in ('{ "pinned": "" }', '{ "pinned": null }', '{ "pinned": 7 }'):
        resolved = module.resolve_janitor_core_provisioning(config_text=_config(compat=pinned))
        assert resolved.ref == module.UNRESOLVED_JANITOR_CORE, pinned
        assert resolved.defect is not None, pinned
        assert module.JANITOR_CORE_PINNED_KEY in resolved.defect, pinned


def test_declared_pinned_value_is_honored_including_the_bootstrap_master() -> None:
    """What is forbidden is the silent default, never a value the repository CHOSE."""
    module = _module()
    for declared, expected in (("v0.38.2", "v0.38.2"), ("master", "master"), ("  v1  ", "v1")):
        resolved = module.resolve_janitor_core_provisioning(
            config_text=_config(compat='{ "pinned": "' + declared + '" }')
        )
        assert resolved.ref == expected
        assert resolved.defect is None


def test_core_repo_declaration_resolves_the_clone_repository() -> None:
    """An adopter that mirrors livespec core provisions from its own mirror."""
    module = _module()
    resolved = module.resolve_janitor_core_provisioning(
        config_text=_config(
            compat='{ "pinned": "v1", "core_repo": " https://git.example/mirror.git " }'
        )
    )
    assert resolved.repo_url == "https://git.example/mirror.git"
    assert resolved.defect is None


def test_absent_core_repo_resolves_to_the_fleet_livespec_core_repository() -> None:
    """`core_repo` is OPTIONAL: an absent key completely answers "use the fleet core"."""
    module = _module()
    fleet = module.FLEET_JANITOR_CORE_REPO_URL
    assert fleet == "https://github.com/thewoolleyman/livespec.git"
    declared = module.resolve_janitor_core_provisioning(
        config_text=_config(compat='{ "pinned": "v1" }')
    )
    assert (declared.repo_url, declared.defect) == (fleet, None)
    # Even where the pin itself is unresolved, an absent `core_repo` still names
    # the fleet repository rather than a second sentinel.
    assert module.resolve_janitor_core_provisioning(config_text="{}").repo_url == fleet


def test_present_but_unusable_core_repo_refuses_rather_than_sliding_onto_the_default() -> None:
    """A present key says this repository's core is NOT the fleet's."""
    module = _module()
    for core_repo in ('"core_repo": ""', '"core_repo": null', '"core_repo": []'):
        resolved = module.resolve_janitor_core_provisioning(
            config_text=_config(compat='{ "pinned": "v1", ' + core_repo + " }")
        )
        assert resolved.repo_url == module.UNRESOLVED_JANITOR_CORE, core_repo
        assert resolved.repo_url != module.FLEET_JANITOR_CORE_REPO_URL, core_repo
        assert resolved.defect is not None, core_repo
        assert module.JANITOR_CORE_REPO_KEY in resolved.defect, core_repo


def test_both_unresolved_fields_are_reported_in_one_defect() -> None:
    """An adopter that declared neither learns both at once, not one dispatch at a time."""
    module = _module()
    resolved = module.resolve_janitor_core_provisioning(
        config_text=_config(compat='{ "core_repo": 7 }')
    )
    assert resolved.defect is not None
    assert module.JANITOR_CORE_PINNED_KEY in resolved.defect
    assert module.JANITOR_CORE_REPO_KEY in resolved.defect


def test_provisioning_defect_reads_the_sentinels_a_plan_carries() -> None:
    """The plan carries resolved strings, so the sentinel is what the janitor reads back."""
    module = _module()
    sentinel = module.UNRESOLVED_JANITOR_CORE
    fleet = module.FLEET_JANITOR_CORE_REPO_URL
    assert module.janitor_core_provisioning_defect(ref="v1", repo_url=fleet) is None
    ref_only = module.janitor_core_provisioning_defect(ref=sentinel, repo_url=fleet)
    assert ref_only is not None
    assert module.JANITOR_CORE_PINNED_KEY in ref_only
    assert module.JANITOR_CORE_REPO_KEY not in ref_only
    repo_only = module.janitor_core_provisioning_defect(ref="v1", repo_url=sentinel)
    assert repo_only is not None
    assert module.JANITOR_CORE_REPO_KEY in repo_only
    both = module.janitor_core_provisioning_defect(ref=sentinel, repo_url=sentinel)
    assert both is not None
    assert module.JANITOR_CORE_PINNED_KEY in both
    assert module.JANITOR_CORE_REPO_KEY in both


def test_planning_layer_accessors_project_the_resolved_provisioning() -> None:
    """The two `*_from_config` accessors the Dispatcher reads are the same resolution."""
    module = _module()
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands._dispatcher_plan")
    declared = _config(compat='{ "pinned": "master", "core_repo": "https://git.example/m.git" }')
    assert plan.janitor_core_ref_from_config(config_text=declared) == "master"
    assert (
        plan.janitor_core_repo_url_from_config(config_text=declared) == "https://git.example/m.git"
    )
    assert plan.janitor_core_ref_from_config(config_text="{}") == module.UNRESOLVED_JANITOR_CORE
    assert plan.janitor_core_repo_url_from_config(config_text="{}") == (
        module.FLEET_JANITOR_CORE_REPO_URL
    )


def test_plan_build_no_longer_carries_a_hardcoded_moving_core_ref_default() -> None:
    """The second hardcoded `master` default is gone; the plan defaults to the sentinel."""
    plan_build = importlib.import_module(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_plan_build"
    )
    assert not hasattr(plan_build, "_DEFAULT_JANITOR_CORE_REF")
    assert not hasattr(plan_build, "_DEFAULT_JANITOR_CORE_REPO_URL")
    source = (_COMMANDS / "_dispatcher_plan_build.py").read_text(encoding="utf-8")
    assert "_DEFAULT_JANITOR_CORE_REF" not in source
