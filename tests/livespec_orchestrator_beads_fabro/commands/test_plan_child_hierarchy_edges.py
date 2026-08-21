"""ID-hierarchy children count toward the plan archive child-disposition gate.

Beads recognises a child by ID hierarchy (`<epic-id>.<suffix>`) and REFUSES to
let a caller add an explicit `parent-child` or `tracks` edge for one, rejecting
it as a deadlock because the relation already exists. A gate reading only
explicit edges therefore cannot see such a child, and cannot be repaired from
the ledger side. Observed on `livespec-s43svm.30`, an open P1 item invisible to
its own plan's archive gate.
"""

from __future__ import annotations

from typing import cast

from livespec_orchestrator_beads_fabro._beads_client import (
    EDGE_PARENT_CHILD,
    BeadsClient,
)
from livespec_orchestrator_beads_fabro.commands._plan_archive_review import (
    undisposed_plan_child_ids,
)


class _HierarchyOnlyChildClient:
    def list_issues(self) -> list[dict[str, object]]:
        return [
            {
                "id": "bd-ib-epic",
                "status": "active",
                "dependencies": [],
            },
            {
                "id": "bd-ib-epic.30",
                "status": "open",
                "dependencies": None,
            },
            {
                "id": "bd-ib-epic.29",
                "status": "closed",
                "dependencies": None,
            },
            {
                "id": "bd-ib-epic.1",
                "status": "ready",
                "dependencies": [
                    {"depends_on_id": "bd-ib-epic", "type": EDGE_PARENT_CHILD},
                ],
            },
            {
                "id": "bd-ib-epic2.7",
                "status": "open",
                "dependencies": None,
            },
        ]


def test_hierarchy_only_child_counts_as_undisposed() -> None:
    client = cast("BeadsClient", _HierarchyOnlyChildClient())

    assert undisposed_plan_child_ids(client=client, epic_id="bd-ib-epic") == (
        "bd-ib-epic.1",
        "bd-ib-epic.30",
    )
