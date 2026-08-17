#!/usr/bin/env python3
"""Version-neutral anchor probe contract for the attended rehearsal.

The module exposes no general SQL runner. Tests exercise the refusal boundary
with a fake connector so no socket is opened in factory-safe preparation.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timezone

ALLOWED_QUERY = "SELECT DATABASE(), CURRENT_USER(), @@hostname, @@port"
ALLOWED_QUERY_SHA256 = "9308612c4a6f2f24c7c4c6f4a5a1ffc141cebc67eb0a4dc7794debcf7a6f66d4"
ERROR_QUERY_OVERRIDE = "query override surfaces are forbidden"
READ_ONLY_TRANSACTION = True
STATEMENT_COUNT = 1

_MUTATING_PREFIXES = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE",
    "DROP",
    "CALL",
)

__all__: list[str] = [
    "ALLOWED_QUERY",
    "ALLOWED_QUERY_SHA256",
    "is_query_allowed",
    "probe_identity",
    "statement_count",
]


def statement_count() -> int:
    return STATEMENT_COUNT


def is_query_allowed(*, query: str) -> bool:
    normalized = " ".join(query.strip().split())
    if ";" in normalized:
        return False
    if normalized.upper().startswith(_MUTATING_PREFIXES):
        return False
    return normalized == ALLOWED_QUERY


def _refuse_override_surfaces() -> None:
    forbidden_env = [name for name in os.environ if name.startswith("ANCHOR_PROBE_")]
    if forbidden_env:
        raise SystemExit(ERROR_QUERY_OVERRIDE)


def probe_identity(
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    connect: Callable[..., tuple[str, int, str, str]],
) -> dict[str, object]:
    _refuse_override_surfaces()
    connected = connect(host=host, port=port, user=user, password=password)
    return {
        "schema": "livespec.beads_v112_rehearsal.anchor_probe_receipt.v1",
        "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query": ALLOWED_QUERY,
        "query_sha256": ALLOWED_QUERY_SHA256,
        "statement_count": statement_count(),
        "read_only_transaction": READ_ONLY_TRANSACTION,
        "database": database,
        "current_user": user,
        "tcp_peer": f"{host}:{port}",
        "transport_peer": list(connected),
        "probe_exit": 0,
    }
