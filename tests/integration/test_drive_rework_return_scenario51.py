"""Integration-tier acceptance for Scenario 51 rework-return journaling.

Binds SPECIFICATION/scenarios.md "Scenario 51 -- The rework-return valve leaves
a durable journal record" through the public `drive.run_action` surface and the
real store/client seam against the in-memory `FakeBeadsClient`.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from livespec_orchestrator_beads_fabro._beads_client import reset_fake_singleton
from livespec_orchestrator_beads_fabro.commands.drive import run_action
from livespec_orchestrator_beads_fabro.store import (
    append_work_item,
    materialize_work_items,
    read_work_items,
)
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem


@pytest.fixture(autouse=True)
def _fake_beads_env(monkeypatch: pytest.MonkeyPatch) -> object:
    monkeypatch.setenv("LIVESPEC_BEADS_FAKE", "1")
    reset_fake_singleton()
    yield
    reset_fake_singleton()


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd-ib",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _repo(*, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib"}}}',
        encoding="utf-8",
    )
    return repo


def _item(**overrides: object) -> WorkItem:
    base = WorkItem(
        id="bd-ib-123",
        type="task",
        status="acceptance",
        title="A task in acceptance",
        description="Do the thing.",
        origin="freeform",
        gap_id=None,
        rank="a2",
        assignee=None,
        depends_on=(),
        captured_at="2026-06-11T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy="ai-then-human",
    )
    return replace(base, **overrides)


def _stored() -> dict[str, WorkItem]:
    return materialize_work_items(records=read_work_items(path=_config()))


def _jsonl_sizes(*, repo: Path) -> dict[Path, int]:
    return {path: path.stat().st_size for path in repo.rglob("*.jsonl")}


def _read_jsonl(*, path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_reject_rework_moves_acceptance_item_to_active_and_journals_actor(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path=tmp_path)
    append_work_item(path=_config(), item=_item())
    before = _jsonl_sizes(repo=repo)

    result = run_action(repo=repo, action_id="reject:bd-ib-123:rework")

    assert result["status"] == "green"
    assert result["target_status"] == "active"
    assert result["journal"] == {
        "actor": "operator",
        "stage": "human-valve-reject-rework",
        "work_item_id": "bd-ib-123",
    }
    assert _stored()["bd-ib-123"].status == "active"

    after = _jsonl_sizes(repo=repo)
    changed = {path for path, size in after.items() if path not in before or size > before[path]}
    journal_path = repo / "tmp" / "fabro-dispatch-journal.jsonl"
    assert changed == {journal_path}
    [record] = _read_jsonl(path=journal_path)
    assert record["actor"] == "operator"
    assert record["stage"] == "human-valve-reject-rework"
    assert record["work_item_id"] == "bd-ib-123"
