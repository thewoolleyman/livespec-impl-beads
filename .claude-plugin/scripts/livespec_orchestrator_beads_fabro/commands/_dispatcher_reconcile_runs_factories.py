"""Enumerate every factory the reconciler must survey.

Reconciliation is an INVENTORY question, so it cannot be asked of one
factory: a run this repo launched on `vps` is invisible to a survey of `hp`,
and a bare `fabro ps` answers for the local server while reporting nothing
at all about either. Every declared factory is surveyed, and each is
surveyed through its OWN resolved target.

Resolution goes through `resolve_fabro_factory` per name rather than
re-reading the factories table here, so a target the reconciler acts on is
byte-identical to the one a dispatch to that same name would use — including
the per-factory dev token, which is read from the environment there.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands._config import (
    FactoryTarget,
    dispatcher_block,
    resolve_fabro_factory,
)

__all__: list[str] = [
    "declared_factory_names",
    "reconcile_factory_targets",
]

_FACTORIES_KEY = "factories"
_DEFAULT_FACTORY_KEY = "default_factory"


def declared_factory_names(*, block: dict[str, Any]) -> tuple[str, ...]:
    """Every factory name a dispatcher block declares, in a stable order.

    The `default_factory` name is included even when the factories table
    does not carry it: a default naming a factory nobody declared is a
    configuration fault the reconciler must REPORT, and it can only report
    what it enumerates.
    """
    names: list[str] = []
    factories_raw: object = block.get(_FACTORIES_KEY)
    if isinstance(factories_raw, dict):
        names.extend(sorted(cast("dict[str, Any]", factories_raw)))
    default_raw: object = block.get(_DEFAULT_FACTORY_KEY)
    if isinstance(default_raw, str) and default_raw != "" and default_raw not in names:
        names.append(default_raw)
    return tuple(names)


def reconcile_factory_targets(
    *,
    repo: Path,
    factory: str | None = None,
) -> tuple[FactoryTarget, ...]:
    """Resolve the factory targets to survey; one name narrows it to that one."""
    if factory is not None and factory != "":
        return (resolve_fabro_factory(cwd=repo, factory=factory),)
    names = declared_factory_names(block=dispatcher_block(cwd=repo))
    return tuple(resolve_fabro_factory(cwd=repo, factory=name) for name in names)
