"""The named Fabro workflow-variant registry, and which variant a dispatch runs.

Split out of `_config` for the same reason `_node_timeouts` is: the policy --
what `dispatcher.workflows` and `dispatcher.default_workflow` mean, which name
one dispatch selects, and the reserved name that is never read from the
registry -- belongs next to its own resolver rather than inside the general
connection-resolution module. `_config.resolve_workflow_variant` /
`_config.resolve_workflow_registry` are the config-reading seams that feed it.

WHY A REGISTRY AT ALL. `SPECIFICATION/contracts.md` section "Self-contained
plugin dispatch" already lets a dispatch target carry its OWN
`implement-work-item` workflow, which governs exactly ONE graph per target. A
target wanting a SECOND graph -- different edges, retry and review discipline,
prompts, run configuration and sandbox image -- had nowhere to put it. The
registry names those directories so a dispatch can select one by name.

WHY THERE IS NO ENVIRONMENT LAYER, where `fabro_bin` and the factory both
have one. The selector is a recorded argument for the reason section "ACP node
adapter configuration" gives for the adapter layers: an ad-hoc shell MUST NOT
be able to change which graph the factory runs with nothing in the committed
record or the journal to show for it.

WHY `implement-work-item` IS RESERVED RATHER THAN MERELY DEFAULTED. The
reserved name resolves through the target-local-then-bundle rule of
`_dispatcher_paths.workflow_toml`, which has TWO candidate locations and falls
back between them; a registry entry has exactly one and never falls back.
Letting a registry entry claim the name would make "which file won" depend on
whether an entry happened to be registered, so the reserved name is never read
from the registry, and a registry that redefines it is refused instead.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

__all__: list[str] = [
    "RESERVED_WORKFLOW_NAME",
    "WorkflowVariant",
    "workflow_registry",
    "workflow_variant_from_block",
]

_WORKFLOWS_KEY = "workflows"
_DEFAULT_WORKFLOW_KEY = "default_workflow"

# The one workflow name every dispatch target defines whether it declares a
# registry or not. `_dispatcher_paths` builds the reserved subpath from this
# name rather than repeating the literal, so the two cannot drift.
RESERVED_WORKFLOW_NAME = "implement-work-item"


@dataclass(frozen=True, kw_only=True)
class WorkflowVariant:
    """Which named workflow one dispatch runs, and where its directory lives.

    `directory` is the registry-declared path RELATIVE TO THE DISPATCH TARGET's
    repository root, or None for the reserved variant -- whose two candidate
    locations `_dispatcher_paths.workflow_toml` resolves between, and which is
    therefore not a registry answer at all. A None `directory` under any OTHER
    name means the registry does not define that name; the dispatch-time seam
    refuses on it rather than falling back, because a silent fallback would run
    the reserved graph under the name of the one the operator asked for.
    """

    name: str
    directory: str | None


def workflow_registry(*, block: dict[str, Any]) -> Mapping[str, str]:
    """The `dispatcher.workflows` table: variant name -> repo-relative directory.

    An absent or non-table value yields an empty registry, which is what every
    target that declares none has: the registry is an OPTIONAL target-declared
    capability in the class of `dispatcher.acp_nodes`, not an integration point
    the orchestrator requires, so declaring nothing incurs nothing.

    An entry whose value is not a non-empty string is DROPPED here rather than
    refused. An unusable value and an unregistered name are the same fact for
    every consumer -- the directory cannot be resolved -- and the refusal that
    names the SELECTED variant is more actionable than one naming a table row
    the operator may never have selected.
    """
    raw = block.get(_WORKFLOWS_KEY)
    if not isinstance(raw, dict):
        return {}
    return {
        name: value
        for name, value in cast("dict[str, Any]", raw).items()
        if isinstance(value, str) and value != ""
    }


def workflow_variant_from_block(
    *,
    block: dict[str, Any],
    name: str | None = None,
) -> WorkflowVariant:
    """Which variant this dispatch runs, most specific first.

    An explicit `name` wins; otherwise `dispatcher.default_workflow` when it
    names a registered entry; otherwise the reserved `implement-work-item`.

    The reserved name short-circuits the registry lookup outright, so its
    directory is None however the registry is written. That is the mechanical
    half of "never read from the registry": the refusal against a registry
    entry claiming the name lives in the dispatch-time seam, and this function
    stays total so the precedence itself has no failure track.
    """
    registry = workflow_registry(block=block)
    selected = (
        name if name is not None and name != "" else _default_name(block=block, registry=registry)
    )
    if selected == RESERVED_WORKFLOW_NAME:
        return WorkflowVariant(name=selected, directory=None)
    return WorkflowVariant(name=selected, directory=registry.get(selected))


def _default_name(*, block: dict[str, Any], registry: Mapping[str, str]) -> str:
    """`dispatcher.default_workflow` when it names a registered entry, else reserved.

    A default naming an UNREGISTERED variant falls through to the reserved name
    rather than refusing: it is the same shape as `_config`'s factory default,
    where a `default_factory` naming nothing registered yields the implicit
    target instead of failing every dispatch the target makes.
    """
    configured = block.get(_DEFAULT_WORKFLOW_KEY)
    if isinstance(configured, str) and configured in registry:
        return configured
    return RESERVED_WORKFLOW_NAME
