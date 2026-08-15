"""Tests for dispatcher factory ledger pinning."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_factory_ledger import (
    resolve_dispatch_factory_target,
)
from livespec_orchestrator_beads_fabro.store import (
    append_work_item,
    dispatch_factory_for,
)
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="livespec-impl-beads",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _item() -> WorkItem:
    return WorkItem(
        id="li-factory",
        type="task",
        status="ready",
        title="Factory target",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-15T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )


def test_env_factory_is_recorded_when_no_cli_factory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib"}}}',
        encoding="utf-8",
    )
    append_work_item(path=_config(), item=_item())
    monkeypatch.setenv("LIVESPEC_FABRO_FACTORY", "env-remote")

    target = resolve_dispatch_factory_target(
        args=argparse.Namespace(factory=None),
        repo=repo,
        work_item_id="li-factory",
    )

    assert target.name == "env-remote"
    assert dispatch_factory_for(path=_config(), work_item_id="li-factory") == "env-remote"
