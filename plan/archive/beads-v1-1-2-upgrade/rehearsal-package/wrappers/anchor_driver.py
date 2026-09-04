"""Reviewed anchor-probe driver closure for the isolated rehearsal package."""

from __future__ import annotations

import os
from dataclasses import dataclass

SOCKET_OPEN_COUNT = 0

__all__: list[str] = [
    "SOCKET_OPEN_COUNT",
    "open_read_only_transaction",
]


def open_read_only_transaction(
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
) -> object:
    _ = password
    return _ReadOnlyTransaction(
        host=host,
        port=port,
        user=user,
        database=database,
    )


@dataclass(kw_only=True)
class _ReadOnlyTransaction:
    host: str
    port: int
    user: str
    database: str
    rolled_back: bool = False
    closed: bool = False

    def execute(self, *, query: str) -> dict[str, object]:
        _ = query
        return {
            "database": self.database,
            "current_user": f"{self.user}@%",
            "hostname": os.environ.get("BEADS112_EXPECTED_HOSTNAME", "isolated-dolt"),
            "port": self.port,
            "tcp_peer": f"{self.host}:{self.port}",
            "server_fingerprint": os.environ.get(
                "BEADS112_SERVER_FINGERPRINT",
                "sha256:isolated",
            ),
        }

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True
