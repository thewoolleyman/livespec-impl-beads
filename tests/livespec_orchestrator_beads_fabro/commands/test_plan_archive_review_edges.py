"""Edge-shape coverage for plan archive child detection."""

from __future__ import annotations

from typing import cast

from livespec_orchestrator_beads_fabro._beads_client import BeadsClient
from livespec_orchestrator_beads_fabro.commands._plan_archive_review import (
    undisposed_plan_child_ids,
)


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
