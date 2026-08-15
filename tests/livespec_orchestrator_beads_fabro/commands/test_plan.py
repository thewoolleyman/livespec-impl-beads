"""Plan operation package-command coverage."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._beads_client import (
    EDGE_BLOCKS,
    FakeBeadsClient,
    IssueDraft,
    make_beads_client,
    reset_fake_singleton,
)
from livespec_orchestrator_beads_fabro.types import StoreConfig


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd-ib",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _fake() -> FakeBeadsClient:
    client = make_beads_client(config=_config())
    assert isinstance(client, FakeBeadsClient)
    return client


def _draft(*, issue_id: str, parent_id: str | None) -> IssueDraft:
    return IssueDraft(
        issue_id=issue_id,
        issue_type="task",
        title="child",
        description="child work",
        assignee=None,
        created_at="2026-08-11T00:00:00Z",
        parent_id=parent_id,
        metadata={"rank": "a1"},
        labels=["origin:freeform"],
    )


def test_plan_command_module_exists() -> None:
    module_path = (
        Path(__file__).resolve().parents[3]
        / ".claude-plugin"
        / "scripts"
        / "livespec_orchestrator_beads_fabro"
        / "commands"
        / "plan.py"
    )
    assert module_path.is_file()
    module = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")
    assert hasattr(module, "create_thread")


def test_create_writes_research_and_one_epic_anchor_only(tmp_path: Path) -> None:
    reset_fake_singleton()
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")

    result = plan.create_thread(
        project_root=tmp_path,
        config=_config(),
        slug="harness-smoke",
        title="Harness smoke planning",
        research_filename="initial.md",
        research_text="# Findings\n\nResearch only.\n",
        now="2026-08-11T00:00:00Z",
    )

    assert result["research_path"] == "plan/harness-smoke/research/initial.md"
    assert (tmp_path / "plan" / "harness-smoke" / "research" / "initial.md").read_text(
        encoding="utf-8"
    ) == "# Findings\n\nResearch only.\n"
    assert sorted(
        path.relative_to(tmp_path).as_posix() for path in (tmp_path / "plan").rglob("*")
    ) == [
        "plan/harness-smoke",
        "plan/harness-smoke/research",
        "plan/harness-smoke/research/initial.md",
    ]
    [record] = _fake().list_issues()
    assert record["issue_type"] == "epic"
    assert record["metadata"]["plan_slug"] == "harness-smoke"


def test_handoff_append_is_ledger_comment_and_timeline_readable(tmp_path: Path) -> None:
    reset_fake_singleton()
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")
    created = plan.create_thread(
        project_root=tmp_path,
        config=_config(),
        slug="harness-smoke",
        title="Harness smoke planning",
        research_filename="initial.md",
        research_text="research\n",
        now="2026-08-11T00:00:00Z",
    )

    plan.append_handoff(
        config=_config(),
        epic_id=created["epic_id"],
        body="Next action: dispatch bd-ib-child through the factory.",
        author="factory-test",
        now="2026-08-11T01:02:03Z",
    )
    entries = plan.read_timeline(config=_config(), epic_id=created["epic_id"])

    assert len(entries) == 1
    assert entries[0].author == "factory-test"
    assert entries[0].created_at == "2026-08-11T01:02:03Z"
    assert entries[0].body == "Next action: dispatch bd-ib-child through the factory."


def test_supervisor_handoff_computes_reserved_author_literal(tmp_path: Path) -> None:
    reset_fake_singleton()
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")
    created = plan.create_thread(
        project_root=tmp_path,
        config=_config(),
        slug="harness-smoke",
        title="Harness smoke planning",
        research_filename="initial.md",
        research_text="research\n",
        now="2026-08-11T00:00:00Z",
    )

    plan.append_supervisor_handoff(
        config=_config(),
        epic_id=created["epic_id"],
        slug="harness-smoke",
        body="Resume state before wind-down.",
        now="2026-08-11T01:02:03Z",
    )
    entries = plan.read_timeline(config=_config(), epic_id=created["epic_id"])

    assert len(entries) == 1
    assert entries[0].author == "harness-smoke-supervisor"
    assert entries[0].created_at == "2026-08-11T01:02:03Z"
    assert entries[0].body == "Resume state before wind-down."


def test_scope_event_records_requirements_and_explicit_deferrals(tmp_path: Path) -> None:
    reset_fake_singleton()
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")
    created = plan.create_thread(
        project_root=tmp_path,
        config=_config(),
        slug="scope-thread",
        title="Scope thread",
        research_filename="initial.md",
        research_text="research\n",
        now="2026-08-11T00:00:00Z",
    )

    plan.record_scope_event(
        config=_config(),
        epic_id=created["epic_id"],
        requirements=("archive must gate children",),
        deferrals=("UI polish is deferred",),
        author="factory-test",
        now="2026-08-11T01:02:03Z",
    )

    [entry] = plan.read_timeline(config=_config(), epic_id=created["epic_id"])
    assert "Requirement carriers:" in entry.body
    assert "- archive must gate children" in entry.body
    assert "Explicit deferrals:" in entry.body
    assert "- UI polish is deferred" in entry.body


def test_archive_refuses_undisposed_children(tmp_path: Path) -> None:
    reset_fake_singleton()
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")
    created = plan.create_thread(
        project_root=tmp_path,
        config=_config(),
        slug="archive-thread",
        title="Archive thread",
        research_filename="initial.md",
        research_text="research\n",
        now="2026-08-11T00:00:00Z",
    )
    _ = _fake().create_issue(draft=_draft(issue_id="bd-ib-child", parent_id=None))
    _fake().add_dependency(
        from_id="bd-ib-child",
        to_id=created["epic_id"],
        edge_type=EDGE_BLOCKS,
    )
    _fake().update_issue(issue_id="bd-ib-child", status="ready")

    with pytest.raises(plan.PlanArchiveRefusedError) as exc:
        plan.archive_thread(
            project_root=tmp_path,
            config=_config(),
            slug="archive-thread",
            epic_id=created["epic_id"],
            completeness_review_comment_id="bd-comment-1",
        )

    assert "undisposed child work-items: bd-ib-child" in str(exc.value)


def test_archive_edge_predicate_ignores_malformed_dependency_records() -> None:
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")

    assert not plan._has_blocks_edge_to_epic(  # noqa: SLF001 - malformed ledger-record coverage.
        record={"dependencies": "not-a-list"},
        epic_id="bd-ib-epic",
    )
    assert not plan._is_blocks_edge_to_epic(  # noqa: SLF001 - malformed ledger-edge coverage.
        edge="not-an-edge",
        epic_id="bd-ib-epic",
    )


def test_archive_requires_completeness_review_evidence(tmp_path: Path) -> None:
    reset_fake_singleton()
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")
    created = plan.create_thread(
        project_root=tmp_path,
        config=_config(),
        slug="archive-thread",
        title="Archive thread",
        research_filename="initial.md",
        research_text="research\n",
        now="2026-08-11T00:00:00Z",
    )

    with pytest.raises(plan.PlanArchiveRefusedError) as exc:
        plan.archive_thread(
            project_root=tmp_path,
            config=_config(),
            slug="archive-thread",
            epic_id=created["epic_id"],
            completeness_review_comment_id=None,
        )

    assert "independent completeness-review evidence is required" in str(exc.value)


def test_archive_moves_thread_and_closes_epic_after_two_gates(tmp_path: Path) -> None:
    reset_fake_singleton()
    plan = importlib.import_module("livespec_orchestrator_beads_fabro.commands.plan")
    created = plan.create_thread(
        project_root=tmp_path,
        config=_config(),
        slug="archive-thread",
        title="Archive thread",
        research_filename="initial.md",
        research_text="research\n",
        now="2026-08-11T00:00:00Z",
    )
    _ = _fake().create_issue(draft=_draft(issue_id="bd-ib-child", parent_id=None))
    _fake().add_dependency(
        from_id="bd-ib-child",
        to_id=created["epic_id"],
        edge_type=EDGE_BLOCKS,
    )
    _fake().close_issue(issue_id="bd-ib-child", reason="completed")

    result = plan.archive_thread(
        project_root=tmp_path,
        config=_config(),
        slug="archive-thread",
        epic_id=created["epic_id"],
        completeness_review_comment_id="bd-comment-1",
    )

    assert result == {
        "archive_path": "plan/archive/archive-thread",
        "epic_id": created["epic_id"],
    }
    assert not (tmp_path / "plan" / "archive-thread").exists()
    assert (tmp_path / "plan" / "archive" / "archive-thread" / "research" / "initial.md").is_file()
    assert _fake().show_issue(issue_id=created["epic_id"])["status"] == "closed"
