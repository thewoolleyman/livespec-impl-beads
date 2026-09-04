#!/usr/bin/env python3
"""Version-neutral single-statement database identity probe."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import NoReturn, cast

ALLOWED_QUERY = "SELECT DATABASE(), CURRENT_USER(), @@hostname, @@port"
ALLOWED_QUERY_SHA256 = "0f334703b52dea71b6c7184692f245094b4c93cbf1d61bcee36fc6c3531a5b36"
ERROR_QUERY_OVERRIDE = "query override surfaces are forbidden"
ERROR_CREDENTIAL_REQUIRED = "credential must be present"
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
_FORBIDDEN_FLAGS = {
    "--query",
    "--sql",
    "--statement",
    "--config",
    "--plugin",
    "--callback",
}
_FORBIDDEN_ENV = {
    "ANCHOR_PROBE_QUERY",
    "ANCHOR_PROBE_SQL",
    "ANCHOR_PROBE_STATEMENT",
    "ANCHOR_PROBE_CONFIG",
    "ANCHOR_PROBE_PLUGIN",
    "ANCHOR_PROBE_CALLBACK",
}

__all__: list[str] = [
    "ALLOWED_QUERY",
    "ALLOWED_QUERY_SHA256",
    "ERROR_CREDENTIAL_REQUIRED",
    "ERROR_QUERY_OVERRIDE",
    "is_query_allowed",
    "load_reviewed_driver",
    "main",
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


def load_reviewed_driver(*, driver_path: Path | None = None) -> ModuleType:
    path = driver_path or Path(__file__).with_name("anchor_driver.py")
    module_name = "beads112_anchor_driver"
    spec = cast(ModuleSpec, importlib.util.spec_from_file_location(module_name, path))
    loader = cast(Loader, spec.loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


def _refuse_override_surfaces(*, argv: list[str] | None = None) -> None:
    if _FORBIDDEN_ENV.intersection(os.environ):
        raise SystemExit(ERROR_QUERY_OVERRIDE)
    if argv is not None and _FORBIDDEN_FLAGS.intersection(argv):
        raise SystemExit(ERROR_QUERY_OVERRIDE)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--user", required=True)
    parser.add_argument("--database", required=True)
    return parser


def probe_identity(
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
) -> dict[str, object]:
    _refuse_override_surfaces()
    if password == "":
        raise SystemExit(ERROR_CREDENTIAL_REQUIRED)
    driver = load_reviewed_driver()
    transaction = driver.open_read_only_transaction(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )
    row = transaction.execute(query=ALLOWED_QUERY)
    transaction.rollback()
    transaction.close()
    return {
        "schema": "livespec.beads_v112_rehearsal.anchor_probe_receipt.v1",
        "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query": ALLOWED_QUERY,
        "query_sha256": hashlib.sha256(ALLOWED_QUERY.encode()).hexdigest(),
        "statement_count": statement_count(),
        "read_only_transaction": READ_ONLY_TRANSACTION,
        "database": row["database"],
        "current_user": row["current_user"],
        "hostname": row["hostname"],
        "port": row["port"],
        "tcp_peer": row["tcp_peer"],
        "server_fingerprint": row["server_fingerprint"],
        "rolled_back": transaction.rolled_back,
        "closed": transaction.closed,
        "probe_exit": 0,
    }


def _halt(*, message: str) -> NoReturn:
    raise SystemExit(message)


def main(*, argv: list[str] | None = None) -> int:
    args = list(os.sys.argv[1:] if argv is None else argv)
    _refuse_override_surfaces(argv=args)
    namespace = _parser().parse_args(args)
    receipt = probe_identity(
        host=namespace.host,
        port=namespace.port,
        user=namespace.user,
        password=os.environ.get("BEADS_DOLT_PASSWORD") or _halt(message=ERROR_CREDENTIAL_REQUIRED),
        database=namespace.database,
    )
    os.write(1, (json.dumps(receipt, sort_keys=True) + "\n").encode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
