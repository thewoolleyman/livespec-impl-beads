"""What a governed repository DECLARES, read once into one mapping.

The generic integration-contract resolver grades a declaration; it does not go
looking for one. This module is the seam between the two: it turns a source of
declared values into the nested mapping `_dispatcher_integration_resolver` walks,
and it is the only place that knows a declaration comes out of `.livespec.jsonc`
at all.

WHY TWO READERS RATHER THAN ONE. The two dispatch-path entry points differ in
what an UNREADABLE `.livespec.jsonc` means to them, and that difference is
ratified behaviour, not an accident to be unified away. The core-provisioning
path is handed raw config TEXT and treats an unparseable file as "declares
nothing", so `compat.pinned` refuses naming the key rather than blaming a parse
error the operator cannot see from the degradation. The dispatcher-block path
reaches the file through `_config.dispatcher_block`, which RAISES on an
unreadable file, because folding an unreadable file into a `dispatcher` answer
tells an operator their factory is not configured when what actually happened is
a stray comma. Both readers produce the SAME shape, so the resolver stays blind
to which one ran.

THE MAPPING IS ROOTED AT THE PLUGIN BLOCK, not at the file. Every schema field's
lookup path is relative to that block (`dispatcher.master_ci.workflow`,
`compat.pinned`), which is what lets one field set span the two committed blocks
without either reader carrying the plugin block's name a second time.
"""

from __future__ import annotations

from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands import _jsonc

__all__: list[str] = [
    "PLUGIN_BLOCK",
    "declaration_from_config_text",
    "declaration_from_dispatcher_block",
]

# The `.livespec.jsonc` block this plugin's declarations hang off.
PLUGIN_BLOCK = "livespec-orchestrator-beads-fabro"

_DISPATCHER_BLOCK = "dispatcher"


def declaration_from_config_text(*, config_text: str) -> dict[str, object]:
    """The plugin block of a `.livespec.jsonc` text; `{}` when nothing readable names one.

    An unreadable config is not a third answer: it means no key could be read,
    which is every optional field at its fleet default and every REQUIRED field
    resolving to `Defective` -- exactly as an empty but well-formed config
    resolves.
    """
    parsed = _jsonc.parse(text=config_text)
    if isinstance(parsed, _jsonc.JsoncFailure) or not isinstance(parsed, dict):
        return {}
    plugin: object = cast("dict[str, object]", parsed).get(PLUGIN_BLOCK)
    if not isinstance(plugin, dict):
        return {}
    return cast("dict[str, object]", plugin)


def declaration_from_dispatcher_block(*, block: dict[str, Any]) -> dict[str, object]:
    """A declaration carrying ONLY the `dispatcher` block a caller already read.

    Fields outside that block resolve exactly as they would for a repository
    that declares nothing there, which is what every `dispatcher`-scoped caller
    wants: it is asking about its own keys, and inventing a `compat` answer from
    a block that cannot contain one would be a defect reported against a file
    this reader never opened.
    """
    return {_DISPATCHER_BLOCK: block}
