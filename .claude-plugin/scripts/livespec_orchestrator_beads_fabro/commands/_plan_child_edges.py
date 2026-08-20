"""Plan child/dependency edge classification.

Raw `dependencies[]` records are the authoritative read surface for plan child
enumeration. `bd children` is intentionally used only by the mismatch probe
below because upstream currently derives it from `bd list --parent`, whose
query is narrower than the dependency surface this plugin must trust.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro._beads_client import (
    EDGE_BLOCKS,
    EDGE_PARENT_CHILD,
    EDGE_TRACKS,
    BeadsRecord,
)

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro._beads_client import BeadsClient

__all__: list[str] = [
    "bd_child_surface_mismatch_ids",
    "blocking_dependency_ids",
    "has_blocks_edge_to_epic",
    "is_blocks_dependency_edge",
    "is_blocks_edge_to_epic",
    "linked_plan_gate_ids_for_epic",
    "plan_child_ids_from_dependencies",
]


def bd_child_surface_mismatch_ids(*, client: BeadsClient, epic_id: str) -> tuple[str, ...]:
    """Return ids where `bd children` disagrees with raw dependency membership."""
    dependency_child_ids = plan_child_ids_from_dependencies(
        records=client.list_issues(),
        epic_id=epic_id,
    )
    children_ids = frozenset(
        issue_id
        for record in client.children(parent_id=epic_id)
        if isinstance(issue_id := record.get("id"), str)
    )
    return tuple(sorted(dependency_child_ids ^ children_ids))


def linked_plan_gate_ids_for_epic(
    *,
    records: list[BeadsRecord],
    epic_id: str,
) -> frozenset[str]:
    """Return dependency-authoritative child ids plus blockers named on the epic."""
    return plan_child_ids_from_dependencies(
        records=records, epic_id=epic_id
    ) | _blocking_ids_for_epic(
        records=records,
        epic_id=epic_id,
    )


def plan_child_ids_from_dependencies(
    *,
    records: list[BeadsRecord],
    epic_id: str,
) -> frozenset[str]:
    """Return issue ids with raw `parent-child` or `tracks` edges to `epic_id`."""
    return frozenset(
        issue_id
        for record in records
        if isinstance(issue_id := record.get("id"), str)
        and _has_plan_child_edge_to_epic(record=record, epic_id=epic_id)
    )


def _blocking_ids_for_epic(*, records: list[BeadsRecord], epic_id: str) -> frozenset[str]:
    for record in records:
        if record.get("id") == epic_id:
            return blocking_dependency_ids(record=record)
    return frozenset()


def _has_plan_child_edge_to_epic(*, record: BeadsRecord, epic_id: str) -> bool:
    dependencies = record.get("dependencies")
    if not isinstance(dependencies, list):
        return False
    typed_dependencies = cast("list[object]", dependencies)
    return any(
        _is_plan_child_edge_to_epic(edge=edge, epic_id=epic_id) for edge in typed_dependencies
    )


def _is_plan_child_edge_to_epic(*, edge: object, epic_id: str) -> bool:
    if not isinstance(edge, dict):
        return False
    typed_edge = cast("dict[str, Any]", edge)
    depends_on_id = typed_edge.get("depends_on_id")
    return typed_edge.get("type") in (EDGE_PARENT_CHILD, EDGE_TRACKS) and depends_on_id == epic_id


def blocking_dependency_ids(*, record: BeadsRecord) -> frozenset[str]:
    """Return ids of records that block `record` through `blocks` dependencies."""
    dependencies = record.get("dependencies")
    if not isinstance(dependencies, list):
        return frozenset()
    typed_dependencies = cast("list[object]", dependencies)
    return frozenset(
        dependency_id
        for edge in typed_dependencies
        if (dependency_id := is_blocks_dependency_edge(edge=edge)) is not None
    )


def is_blocks_dependency_edge(*, edge: object) -> str | None:
    """Return the dependency id when one edge is a `blocks` dependency."""
    if not isinstance(edge, dict):
        return None
    typed_edge = cast("dict[str, Any]", edge)
    depends_on_id = typed_edge.get("depends_on_id")
    if typed_edge.get("type") != EDGE_BLOCKS or not isinstance(depends_on_id, str):
        return None
    return depends_on_id


def has_blocks_edge_to_epic(*, record: BeadsRecord, epic_id: str) -> bool:
    """Return whether `record` carries a legacy-shaped dependency on `epic_id`."""
    return epic_id in blocking_dependency_ids(record=record)


def is_blocks_edge_to_epic(*, edge: object, epic_id: str) -> bool:
    """Return whether one legacy-shaped dependency edge points at `epic_id`."""
    return is_blocks_dependency_edge(edge=edge) == epic_id
