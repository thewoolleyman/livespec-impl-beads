"""Dispatcher factory ledger pinning."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._config import (
    FactoryTarget,
    resolve_fabro_factory,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import store_config
from livespec_orchestrator_beads_fabro.store import (
    dispatch_factory_for,
    record_dispatch_factory,
)

__all__: list[str] = [
    "args_with_dispatch_factory_target",
    "resolve_dispatch_factory_target",
]

_ENV_FABRO_FACTORY = "LIVESPEC_FABRO_FACTORY"


def resolve_dispatch_factory_target(
    *,
    args: argparse.Namespace,
    repo: Path,
    work_item_id: str,
) -> FactoryTarget:
    """Resolve and persist the Fabro factory target for one dispatch."""
    config = store_config(repo=repo)
    explicit = _explicit_factory(args=args)
    recorded = dispatch_factory_for(path=config, work_item_id=work_item_id)
    target = resolve_fabro_factory(cwd=repo, factory=explicit or recorded)
    record_dispatch_factory(path=config, work_item_id=work_item_id, factory=target.name)
    return target


def args_with_dispatch_factory_target(
    *,
    args: argparse.Namespace,
    repo: Path,
    work_item_id: str,
) -> argparse.Namespace:
    """Return an args clone carrying the ledger-pinned factory target."""
    cloned = argparse.Namespace(**vars(args))
    cloned.fabro_factory_target = resolve_dispatch_factory_target(
        args=args,
        repo=repo,
        work_item_id=work_item_id,
    )
    return cloned


def _explicit_factory(*, args: argparse.Namespace) -> str | None:
    factory = getattr(args, "factory", None)
    if isinstance(factory, str) and factory != "":
        return factory
    env_value = os.environ.get(_ENV_FABRO_FACTORY)
    if env_value is not None and env_value != "":
        return env_value
    return None
