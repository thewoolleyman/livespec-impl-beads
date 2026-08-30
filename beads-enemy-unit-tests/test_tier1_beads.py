"""Tier 1 Enemy Unit Tests: live `bd` mutations against a THROWAWAY store.

Creates, updates, closes, links, and comments on EUT-scoped issues in an
isolated store, then reads them back. Deliberately excluded from
`just beads-enemy-tier0` and `just check`; invoke it explicitly against the
isolated server:

    BEADS_EUT_BIN=/path/to/bd BEADS_EUT_CWD=/scratch/client just beads-enemy-tier1

Every test SKIPS when `BEADS_EUT_BIN` is unset (via the `client` fixture).
"""

# ruff: noqa: S101 — assert is the assertion idiom in an Enemy Unit Test suite.
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnusedCallResult=false
# Records cross the seam as `dict[str, Any]`, so traversing them is inherently
# partially-unknown, and mutation verbs' results are intentionally discarded.

from __future__ import annotations

from _tier0_support import BeadsTier0Config, run_raw
from _tier1_support import (
    make_draft,
    parsed_metadata,
    record_assignee,
    record_status,
    unique_issue_id,
)
from livespec_orchestrator_beads_fabro._beads_client import (
    EDGE_BLOCKS,
    ShellBeadsClient,
)
from livespec_orchestrator_beads_fabro._beads_client_argv import build_create_argv

__all__: list[str] = []


def _has_blocks_edge(*, record: dict[str, object], to_id: str) -> bool:
    edges = record.get("dependencies")
    if not isinstance(edges, list):
        return False
    # Raw `bd show --json` inlines each dependency as the FULL target record plus
    # a `dependency_type` field: the target id is `id` (NOT `depends_on_id`, which
    # is the package projection's key) and the edge kind is `dependency_type`
    # (NOT `type`). Measured live against v1.0.5 and v1.2.2, 2026-08-30.
    return any(
        isinstance(edge, dict)
        and edge.get("id") == to_id
        and edge.get("dependency_type") == EDGE_BLOCKS
        for edge in edges
    )


def test_create_update_close_round_trip(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    client.register_custom_statuses()
    issue_id = unique_issue_id(config=config)

    created = client.create_issue(draft=make_draft(issue_id=issue_id, title="rt"))
    assert created == issue_id
    assert client.exists(issue_id=issue_id) is True

    client.update_issue(issue_id=issue_id, status="ready", assignee="eut-doer")
    updated = client.show_issue(issue_id=issue_id)
    assert record_status(record=updated) == "ready"
    assert record_assignee(record=updated) == "eut-doer"

    client.close_issue(issue_id=issue_id, reason="eut round-trip complete")
    closed = client.show_issue(issue_id=issue_id)
    assert record_status(record=closed) == "closed"


def test_two_step_create_normalization_leaves_lifecycle_status_not_open(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    client.register_custom_statuses()
    issue_id = unique_issue_id(config=config)

    client.create_issue(draft=make_draft(issue_id=issue_id, title="two-step"))
    # Step one of the store's create is a bare `bd create`, which lands the
    # native intake status `open` — NOT a livespec lifecycle status.
    assert record_status(record=client.show_issue(issue_id=issue_id)) == "open"

    # Step two normalizes it onto a lifecycle status. The whole point of the
    # guard's two-step create is that a new item is never LEFT at `open` when the
    # follow-up succeeds; a fail-open follow-up that silently dropped would leave
    # the observable `open` this assertion forbids.
    client.update_issue(issue_id=issue_id, status="backlog")
    assert record_status(record=client.show_issue(issue_id=issue_id)) == "backlog"


def test_create_stdout_reports_the_new_id(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    store_config = config.store_config()
    issue_id = unique_issue_id(config=config)
    draft = make_draft(issue_id=issue_id, title="stdout-id")

    completed = run_raw(config=store_config, verb_args=build_create_argv(draft=draft))

    # The guard parses the new id out of `bd create` stdout; assert the id the
    # binary reports is the one we asked for, the contract that recovery relies on.
    assert issue_id in completed.stdout
    # ...and the reported id names a really-created issue, not just an echo.
    assert client.exists(issue_id=issue_id) is True


def test_clear_assignee_empties_the_native_field(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    issue_id = unique_issue_id(config=config)
    client.create_issue(draft=make_draft(issue_id=issue_id, title="assignee", assignee="eut-owner"))
    assert record_assignee(record=client.show_issue(issue_id=issue_id)) == "eut-owner"

    client.update_issue(issue_id=issue_id, clear_assignee=True)
    assert record_assignee(record=client.show_issue(issue_id=issue_id)) == ""


def test_metadata_round_trips_as_a_parsed_structure(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    issue_id = unique_issue_id(config=config)
    metadata: dict[str, object] = {
        "rank": "0500",
        "audit": {"actor": "eut", "at": "2026-08-30T00:00:00Z"},
    }
    client.create_issue(draft=make_draft(issue_id=issue_id, title="metadata", metadata=metadata))

    record = client.show_issue(issue_id=issue_id)
    # Compared as PARSED structures, never as strings: bd stores compact,
    # sorted-key JSON, so a byte comparison would fail on key order alone.
    assert parsed_metadata(record=record) == metadata


def test_add_and_remove_dependency_round_trip(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    blocker_id = unique_issue_id(config=config)
    blocked_id = unique_issue_id(config=config)
    client.create_issue(draft=make_draft(issue_id=blocker_id, title="dep-blocker"))
    client.create_issue(draft=make_draft(issue_id=blocked_id, title="dep-blocked"))

    client.add_dependency(from_id=blocked_id, to_id=blocker_id, edge_type=EDGE_BLOCKS)
    assert _has_blocks_edge(record=client.show_issue(issue_id=blocked_id), to_id=blocker_id)

    client.remove_dependency(from_id=blocked_id, to_id=blocker_id)
    assert not _has_blocks_edge(record=client.show_issue(issue_id=blocked_id), to_id=blocker_id)


def test_add_comment_round_trip(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    issue_id = unique_issue_id(config=config)
    client.create_issue(draft=make_draft(issue_id=issue_id, title="comment"))
    body = "Beads Enemy Unit Test comment body"

    client.add_comment(issue_id=issue_id, body=body)

    comments = client.list_comments(issue_id=issue_id)
    # The comment body lives under `text` (NOT `body`/`content`) — the trap the
    # AGENTS.md catalogue records; assert against the correct key.
    assert any(comment.get("text") == body for comment in comments)
