"""Tier 0 fixtures. Module-scoped fixtures cannot cross test files, so both
tier 0 modules share ONE fabro port and one config through this conftest.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from _tier0_support import _DEFAULT_SERVER_URL, _FabroTier0Config
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner
from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroPort, FabroTarget

__all__: list[str] = []


@pytest.fixture(scope="module")
def config() -> _FabroTier0Config:
    return _FabroTier0Config(
        fabro_bin=os.environ.get("FABRO_EUT_BIN", "fabro"),
        server_url=os.environ.get("FABRO_EUT_SERVER", _DEFAULT_SERVER_URL),
        expected_client_version=os.environ.get("FABRO_EUT_EXPECTED_CLIENT_VERSION", "0.254.0"),
        expected_client_commit=os.environ.get("FABRO_EUT_EXPECTED_CLIENT_COMMIT", "8de6611"),
        expected_client_date=os.environ.get("FABRO_EUT_EXPECTED_CLIENT_DATE", "2026-07-30"),
        expected_server_version=os.environ.get("FABRO_EUT_EXPECTED_SERVER_VERSION", "0.254.0"),
        expected_server_commit=os.environ.get("FABRO_EUT_EXPECTED_SERVER_COMMIT", "8de6611"),
        expected_server_date=os.environ.get("FABRO_EUT_EXPECTED_SERVER_DATE", "2026-08-02"),
        completed_run_id=os.environ.get("FABRO_EUT_COMPLETED_RUN_ID"),
    )


@pytest.fixture(scope="module")
def port(*, config: _FabroTier0Config) -> FabroPort:
    return FabroPort(
        fabro_bin=config.fabro_bin,
        target=FabroTarget(server_url=config.server_url),
        runner=ShellCommandRunner(),
        cwd=Path.cwd(),
    )
