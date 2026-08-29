"""Tenant-scoped enumeration of this repository's checkouts.

`wip_cap` bounds COUNTED CLAIMS across the TENANT
(`SPECIFICATION/contracts.md`), but the claim artifact — the dispatch lock —
is written under the invoking `--repo` checkout, so N checkouts of one tenant
admitted up to N x `wip_cap` independently. Measured 2026-08-22: two checkouts
of ONE repository, read in the same second against ONE ledger holding 11 rows
at `active`, reported DISJOINT counted-claim totals of 2 and 1
(`bd-ib-snyquw.6`). Worktrees, janitor checkouts and fresh clones are all
normal configurations here, so this was the ordinary case rather than a
contrived one.

A tenant owns no shared directory. A worktree, a janitor checkout and a fresh
clone share an origin and a beads tenant; they never share a filesystem root,
and a fresh clone knows nothing of its siblings. So a checkout REGISTERS
itself — keyed by the tenant its committed `.livespec.jsonc` declares — at the
one moment it makes a claim, and every checkout of that tenant reads the same
registry back.

Two properties this module is built to hold, both load-bearing for callers:

- MONOTONICITY. Enumeration yields the invoking checkout FIRST and only ever
  ADDS peers. A registry that is absent, empty, or unreadable therefore
  degrades to exactly the previous per-checkout answer, so widening the scope
  can only ever count MORE claims, never fewer. That is what keeps the
  fail-closed guarantees of the WIP-cap predicate intact: a green-terminal row
  still does not count, and an unreadable journal still counts more.
- SCOPE. The registry records checkouts of THIS repository's own tenant and
  nothing else, and is read only to resolve this repository's own claims. It
  observes no Fabro host state and no other repository's state; the spec
  admits tenant-scoped bookkeeping across a repository's own checkouts as NOT
  host observation, and this stays inside that fence.

ONE FILE PER CHECKOUT rather than one shared list file, because registration
is then a whole-file write with no read-modify-write step: two checkouts
registering concurrently cannot lose each other's entry, which a shared list
could do silently and in the under-counting direction.

Reads are tolerant and writes are strict. A registry directory that cannot be
listed yields no peers, which is the pre-existing behaviour rather than a new
failure mode; a registration that cannot be written raises, because a claim
whose checkout was never recorded is a claim the bound cannot see.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands import _jsonc
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import state_root
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt, parse_json

__all__: list[str] = [
    "register_tenant_checkout",
    "tenant_checkout_registry_dir",
    "tenant_checkouts",
]

_LIVESPEC_CONFIG = ".livespec.jsonc"
_PLUGIN_BLOCK = "livespec-orchestrator-beads-fabro"
_CONNECTION_KEY = "connection"
_TENANT_KEY = "tenant"
_REGISTRY_SUBDIR = "tenant-checkouts"
_CHECKOUT_KEY = "checkout"
_DIGEST_CHARS = 16
_UNSAFE_SLUG_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def tenant_checkout_registry_dir(*, repo: Path) -> Path | None:
    """Where this repo's TENANT records its checkouts, or None when unidentified.

    None is the honest answer for a checkout whose `.livespec.jsonc` names no
    tenant: without a tenant identity there is no set of checkouts to belong
    to, and callers degrade to the invoking checkout alone rather than
    guessing at a grouping.
    """
    tenant = _tenant_name(repo=repo)
    if tenant is None:
        return None
    return state_root() / _PLUGIN_BLOCK / _REGISTRY_SUBDIR / _slug(name=tenant)


def register_tenant_checkout(*, repo: Path) -> None:
    """Record `repo` as a checkout of its tenant, idempotently.

    Called where a CLAIM is made rather than where the ledger is merely read:
    a checkout that has never dispatched holds no dispatch lock, so recording
    it would widen the enumeration without widening what can be found.
    """
    directory = tenant_checkout_registry_dir(repo=repo)
    if directory is None:
        return
    checkout = repo.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    _prune_departed_checkouts(directory=directory)
    _ = _entry_path(directory=directory, checkout=checkout).write_text(
        json.dumps({_CHECKOUT_KEY: str(checkout)}, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def tenant_checkouts(*, repo: Path) -> tuple[Path, ...]:
    """Every checkout of `repo`'s tenant, the invoking one first.

    The invoking checkout leads unconditionally and is never duplicated among
    the peers, so the result is a superset of the single-checkout answer under
    every registry state — the monotonicity this module's callers rely on.
    """
    here = repo.resolve()
    directory = tenant_checkout_registry_dir(repo=repo)
    if directory is None:
        return (here,)
    peers = sorted(peer for peer in _recorded_checkouts(directory=directory) if peer != here)
    return (here, *peers)


def _entry_path(*, directory: Path, checkout: Path) -> Path:
    digest = hashlib.sha256(str(checkout).encode("utf-8")).hexdigest()[:_DIGEST_CHARS]
    return directory / f"{digest}.json"


def _prune_departed_checkouts(*, directory: Path) -> None:
    """Drop entries whose checkout is gone — a deleted checkout is not one."""
    for entry, checkout in _registry_entries(directory=directory):
        if not checkout.is_dir():
            _ = attempt(action=entry.unlink, exceptions=(OSError,))


def _recorded_checkouts(*, directory: Path) -> tuple[Path, ...]:
    return tuple(checkout for _, checkout in _registry_entries(directory=directory))


def _registry_entries(*, directory: Path) -> tuple[tuple[Path, Path], ...]:
    listed = attempt(action=lambda: sorted(directory.iterdir()), exceptions=(OSError,))
    if isinstance(listed, AttemptFailure):
        return ()
    entries: list[tuple[Path, Path]] = []
    for entry in listed:
        checkout = _recorded_checkout(entry=entry)
        if checkout is not None:
            entries.append((entry, checkout))
    return tuple(entries)


def _recorded_checkout(*, entry: Path) -> Path | None:
    read = attempt(action=lambda: entry.read_text(encoding="utf-8"), exceptions=(OSError,))
    if isinstance(read, AttemptFailure):
        return None
    parsed = parse_json(text=read)
    if not isinstance(parsed, dict):
        return None
    recorded = cast("dict[str, object]", parsed).get(_CHECKOUT_KEY)
    if not isinstance(recorded, str) or not recorded:
        return None
    return Path(recorded)


def _tenant_name(*, repo: Path) -> str | None:
    """The tenant this checkout declares, or None when it declares none.

    Deliberately TOTAL where the store-config resolver is not: that resolver
    raises on a checkout carrying no `connection.prefix`, and an accounting
    read must not fail because a directory is not a configured checkout.
    """
    read = attempt(
        action=lambda: (repo / _LIVESPEC_CONFIG).read_text(encoding="utf-8"),
        exceptions=(OSError,),
    )
    if isinstance(read, AttemptFailure):
        return None
    parsed = _jsonc.parse(text=read)
    if isinstance(parsed, _jsonc.JsoncFailure):
        return None
    return _tenant_from_root(root=parsed)


def _tenant_from_root(*, root: object) -> str | None:
    plugin_block = _mapping_value(mapping=root, key=_PLUGIN_BLOCK)
    connection = _mapping_value(mapping=plugin_block, key=_CONNECTION_KEY)
    tenant = _mapping_value(mapping=connection, key=_TENANT_KEY)
    if not isinstance(tenant, str) or not tenant.strip():
        return None
    return tenant.strip()


def _mapping_value(*, mapping: object, key: str) -> object:
    if not isinstance(mapping, dict):
        return None
    return cast("dict[str, Any]", mapping).get(key)


def _slug(*, name: str) -> str:
    """A filesystem-safe directory name for a tenant, character-substituted."""
    return _UNSAFE_SLUG_CHARS.sub("_", name)
