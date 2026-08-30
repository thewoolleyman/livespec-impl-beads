"""Shared tier 0 config type and raw-verb helpers for the Beads Enemy Unit Tests.

Mirrors `fabro-enemy-unit-tests/_tier0_support.py`: the env-parameterized
config dataclass plus the small helpers the tier modules share. The candidate
`bd` binary is injected as a `StoreConfig.bd_path`, exactly the FabroPort
mechanism of parameterizing the port by a constructor argument rather than a
patched global.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro._beads_client_argv import parse_json_output
from livespec_orchestrator_beads_fabro.effects._beads_client_shell import invoke
from livespec_orchestrator_beads_fabro.types import StoreConfig

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: list[str] = []

# The twelve BeadsClient protocol methods (the whole seam the store needs). The
# harness asserts ShellBeadsClient exposes EXACTLY these — no more (the prep
# note's Deliverable-2 twelve-method surface, `remove_dependency` included).
TWELVE_METHODS: frozenset[str] = frozenset(
    {
        "list_issues",
        "show_issue",
        "list_comments",
        "children",
        "exists",
        "create_issue",
        "update_issue",
        "close_issue",
        "remove_dependency",
        "add_dependency",
        "add_comment",
        "register_custom_statuses",
    }
)

# Verbs the client deliberately never calls (prep note §2 exclusion list). The
# surface test asserts none leaks in as a client method.
EXCLUDED_VERB_METHODS: frozenset[str] = frozenset(
    {
        "ready",
        "init",
        "version",
        "migrate",
        "doctor",
        "export",
        "bootstrap",
        "config_get",
        "reopen",
        "defer",
        "create_prefix",
        "search",
        "label",
        "delete",
    }
)

# The seven livespec LIFECYCLE statuses (ALLOWED_BEADS_STATUSES minus the parked
# `deferred`). `done` is stored beads-native as `closed`.
SEVEN_LIFECYCLE_STATUSES: frozenset[str] = frozenset(
    {
        "backlog",
        "ready",
        "blocked",
        "active",
        "acceptance",
        "pending-approval",
        "closed",
    }
)

_DEFAULT_TENANT = "beads-eut"
_DEFAULT_PREFIX = "beads-eut"
_DEFAULT_SERVER_USER = "root"
_DEFAULT_DATABASE = "beads-eut"
_DEFAULT_SERVER_HOST = "127.0.0.1"
_DEFAULT_SERVER_PORT = 13307


@dataclass(frozen=True, kw_only=True)
class BeadsTier0Config:
    """Everything the fixtures need to point the client at a candidate binary.

    `bd_bin` is `None` when `BEADS_EUT_BIN` is unset; the `client` fixture then
    SKIPS so `pytest --collect-only` and a bare run never touch a live store.
    `cwd` (`BEADS_EUT_CWD`) is the scratch client directory whose
    `.beads/config.yaml` routes `bd` auto-discovery at the isolated server; it
    becomes `StoreConfig.repo_root`. No password field exists here or on
    `StoreConfig` — a family password would let the harness reach a real tenant,
    which the isolated-store plan forbids.
    """

    bd_bin: str | None
    cwd: str | None
    tenant: str
    prefix: str
    server_user: str
    database: str
    server_host: str
    server_port: int

    def store_config(self) -> StoreConfig:
        """Build the live (`fake=False`) StoreConfig for the candidate binary."""
        if self.bd_bin is None:
            msg = "BEADS_EUT_BIN is unset; no candidate bd binary to point at"
            raise RuntimeError(msg)
        return StoreConfig(
            tenant=self.tenant,
            prefix=self.prefix,
            server_user=self.server_user,
            database=self.database,
            bd_path=self.bd_bin,
            server_host=self.server_host,
            server_port=self.server_port,
            repo_root=Path(self.cwd) if self.cwd is not None else None,
            fake=False,
        )


def make_config() -> BeadsTier0Config:
    """Read the env-parameterized tier 0 config (mirrors the FabroPort conftest)."""
    # An EMPTY value counts as unset: `compare.py` exports `BEADS_EUT_BIN=""`
    # for a leg with no binary, and a bare `BEADS_EUT_BIN= just ...` is the same
    # intent. Normalizing "" -> None makes the `client` fixture SKIP rather than
    # run against an empty binary path (which would also read the cwd's real
    # `.beads/`).
    return BeadsTier0Config(
        bd_bin=os.environ.get("BEADS_EUT_BIN") or None,
        cwd=os.environ.get("BEADS_EUT_CWD") or None,
        tenant=os.environ.get("BEADS_EUT_TENANT", _DEFAULT_TENANT),
        prefix=os.environ.get("BEADS_EUT_PREFIX", _DEFAULT_PREFIX),
        server_user=os.environ.get("BEADS_EUT_SERVER_USER", _DEFAULT_SERVER_USER),
        database=os.environ.get("BEADS_EUT_DATABASE", _DEFAULT_DATABASE),
        server_host=os.environ.get("BEADS_EUT_SERVER_HOST", _DEFAULT_SERVER_HOST),
        server_port=int(os.environ.get("BEADS_EUT_SERVER_PORT", str(_DEFAULT_SERVER_PORT))),
    )


def run_raw(*, config: StoreConfig, verb_args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run a raw `bd <verb_args...>` the client does not expose.

    Reuses the production `invoke` seam so the candidate binary, cwd routing,
    and nonzero-exit mapping are identical to a real client call. `invoke`
    raises the typed `Beads*Error` surface on a nonzero exit.
    """
    return invoke(config=config, argv=[config.bd_path, *verb_args])


def parse_records(*, stdout: str, argv_repr: str) -> list[dict[str, Any]]:
    """Parse a raw `bd ... --json` stdout into a list of issue dicts."""
    parsed = parse_json_output(stdout=stdout, argv_repr=argv_repr)
    if isinstance(parsed, list):
        raw = cast("list[Any]", parsed)
        return [cast("dict[str, Any]", record) for record in raw if isinstance(record, dict)]
    if isinstance(parsed, dict):
        envelope = cast("dict[str, Any]", parsed)
        issues = envelope.get("issues")
        if isinstance(issues, list):
            rows = cast("list[Any]", issues)
            return [cast("dict[str, Any]", record) for record in rows if isinstance(record, dict)]
    return []


def record_ids(*, records: list[dict[str, Any]]) -> set[str]:
    """Collect the `id` of every record that carries a string id."""
    return {record["id"] for record in records if isinstance(record.get("id"), str)}
