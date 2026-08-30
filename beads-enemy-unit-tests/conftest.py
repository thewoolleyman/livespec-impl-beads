"""Beads Enemy Unit Test fixtures.

Module-scoped fixtures cannot cross test files, so both tier modules share ONE
`ShellBeadsClient` and one config through this conftest. Mirrors the FabroPort
EUT conftest: env-parameterized construction with the candidate binary injected
as a constructor argument, never a patched global. The client is constructed
DIRECTLY as `ShellBeadsClient` — never `make_beads_client`, which returns the
in-memory fake — and the fixture asserts `config.fake is False`.
"""

# ruff: noqa: S101 — the fixture's `assert config.fake is False` is the load-bearing invariant.

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# The sibling support modules live beside this conftest. The repo pytest config
# runs `--import-mode=importlib`, which does NOT add the rootdir to `sys.path`,
# and `beads-enemy-unit-tests/` is not on the repo `pythonpath`, so make the
# support modules importable without editing pyproject.
sys.path.insert(0, str(Path(__file__).parent))

from _tier0_support import BeadsTier0Config, make_config
from livespec_orchestrator_beads_fabro._beads_client import ShellBeadsClient

__all__: list[str] = []

_SKIP_REASON = "BEADS_EUT_BIN unset; set it to the candidate bd binary to run the Beads EUT"


@pytest.fixture(scope="module")
def config() -> BeadsTier0Config:
    return make_config()


@pytest.fixture(scope="module")
def client(*, config: BeadsTier0Config) -> ShellBeadsClient:
    """Construct the live client for the candidate binary, or SKIP without one."""
    if config.bd_bin is None:
        pytest.skip(_SKIP_REASON)
    store_config = config.store_config()
    assert store_config.fake is False
    return ShellBeadsClient(config=store_config)


@pytest.fixture(scope="module")
def port(*, client: ShellBeadsClient) -> ShellBeadsClient:
    """Alias so tests may name the injected client `port` (FabroPort parity)."""
    return client
