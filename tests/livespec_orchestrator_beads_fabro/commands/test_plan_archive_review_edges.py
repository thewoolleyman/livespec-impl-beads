"""Edge-shape coverage for plan archive child detection."""

from __future__ import annotations

from typing import cast

from livespec_orchestrator_beads_fabro._beads_client import (
    EDGE_BLOCKS,
    EDGE_PARENT_CHILD,
    EDGE_SUPERSEDES,
    BeadsClient,
)
from livespec_orchestrator_beads_fabro.commands._plan_archive_review import (
    undisposed_plan_child_ids,
)

EDGE_TRACKS = "tracks"

EDGE_HANDLING_BY_TYPE = {
    EDGE_PARENT_CHILD: "child",
    EDGE_TRACKS: "child",
    EDGE_BLOCKS: "blocker-when-on-epic",
    EDGE_SUPERSEDES: "ignored-supersession-is-not-plan-membership",
}


class _MalformedParentChildEdgeClient:
    def children(self, *, parent_id: str) -> list[dict[str, object]]:
        assert parent_id == "bd-ib-epic"
        return []

    def list_issues(self) -> list[dict[str, object]]:
        return [
            {
                "id": "bd-ib-text-deps",
                "status": "ready",
                "dependencies": "not-a-list",
            },
            {
                "id": "bd-ib-object-edge",
                "status": "ready",
                "dependencies": [object()],
            },
        ]


def test_parent_child_edge_scan_ignores_malformed_dependency_shapes() -> None:
    client = cast("BeadsClient", _MalformedParentChildEdgeClient())

    assert undisposed_plan_child_ids(client=client, epic_id="bd-ib-epic") == ()


class _RelationCoverageClient:
    def children(self, *, parent_id: str) -> list[dict[str, object]]:
        assert parent_id == "bd-ib-epic"
        return []

    def list_issues(self) -> list[dict[str, object]]:
        return [
            {
                "id": "bd-ib-epic",
                "status": "active",
                "dependencies": [
                    {"depends_on_id": "bd-ib-blocker", "type": EDGE_BLOCKS},
                ],
            },
            {
                "id": "bd-ib-blocker",
                "status": "ready",
                "dependencies": [],
            },
            {
                "id": "bd-ib-parent-child",
                "status": "ready",
                "dependencies": [
                    {"depends_on_id": "bd-ib-epic", "type": EDGE_PARENT_CHILD},
                ],
            },
            {
                "id": "bd-ib-tracked-open",
                "status": "backlog",
                "dependencies": [
                    {"depends_on_id": "bd-ib-epic", "type": EDGE_TRACKS},
                ],
            },
            {
                "id": "bd-ib-tracked-closed",
                "status": "closed",
                "dependencies": [
                    {"depends_on_id": "bd-ib-epic", "type": EDGE_TRACKS},
                ],
            },
            {
                "id": "bd-ib-supersedes",
                "status": "ready",
                "dependencies": [
                    {"depends_on_id": "bd-ib-epic", "type": EDGE_SUPERSEDES},
                ],
            },
        ]


class _ClosedTrackedChildClient:
    def children(self, *, parent_id: str) -> list[dict[str, object]]:
        assert parent_id == "bd-ib-closed-epic"
        return []

    def list_issues(self) -> list[dict[str, object]]:
        return [
            {
                "id": "bd-ib-tracked-closed",
                "status": "closed",
                "dependencies": [
                    {"depends_on_id": "bd-ib-closed-epic", "type": EDGE_TRACKS},
                ],
            },
        ]


def test_plan_archive_relation_coverage_is_explicit() -> None:
    assert EDGE_HANDLING_BY_TYPE == {
        "parent-child": "child",
        "tracks": "child",
        "blocks": "blocker-when-on-epic",
        "supersedes": "ignored-supersession-is-not-plan-membership",
    }

    client = cast("BeadsClient", _RelationCoverageClient())

    assert undisposed_plan_child_ids(client=client, epic_id="bd-ib-epic") == (
        "bd-ib-blocker",
        "bd-ib-parent-child",
        "bd-ib-tracked-open",
    )


def test_closed_tracked_children_are_disposed() -> None:
    client = cast("BeadsClient", _ClosedTrackedChildClient())

    assert undisposed_plan_child_ids(client=client, epic_id="bd-ib-closed-epic") == ()
