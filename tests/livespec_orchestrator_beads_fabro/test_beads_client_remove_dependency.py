"""The dependency-remove verb on both client implementations."""

from __future__ import annotations

import pytest
from livespec_orchestrator_beads_fabro._beads_client import (
    EDGE_PARENT_CHILD,
    FakeBeadsClient,
    IssueDraft,
    ShellBeadsClient,
)
from livespec_orchestrator_beads_fabro.types import StoreConfig


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="li",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=False,
    )


def test_shell_remove_dependency_builds_the_remove_verb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = ShellBeadsClient(config=_config())
    seen: list[list[str]] = []
    monkeypatch.setattr(client, "_run_void", lambda *, verb_args: seen.append(verb_args))

    client.remove_dependency(from_id="li-a", to_id="li-b")

    assert seen[0] == ["dep", "remove", "li-a", "li-b"]


def test_fake_remove_dependency_on_an_absent_issue_is_a_no_op() -> None:
    client = FakeBeadsClient()

    client.remove_dependency(from_id="li-missing", to_id="li-b")

    assert client.list_issues() == []


def test_fake_remove_dependency_drops_only_the_named_edge() -> None:
    client = FakeBeadsClient()

    for issue_id in ("li-a", "li-b", "li-c"):
        _ = client.create_issue(
            draft=IssueDraft(
                issue_id=issue_id,
                issue_type="task",
                title=issue_id,
                description=issue_id,
                assignee=None,
                created_at="2026-08-20T00:00:00Z",
                metadata={"rank": "a1"},
                labels=[],
            )
        )
    client.add_dependency(from_id="li-a", to_id="li-b", edge_type=EDGE_PARENT_CHILD)
    client.add_dependency(from_id="li-a", to_id="li-c", edge_type=EDGE_PARENT_CHILD)

    client.remove_dependency(from_id="li-a", to_id="li-b")

    edges = client.show_issue(issue_id="li-a")["dependencies"]
    assert edges == [{"depends_on_id": "li-c", "type": EDGE_PARENT_CHILD}]
