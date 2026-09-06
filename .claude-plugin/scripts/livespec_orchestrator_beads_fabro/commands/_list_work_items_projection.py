"""JSON projection helpers for `list-work-items`."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, fields, is_dataclass
from typing import TYPE_CHECKING, Any, cast

from livespec_runtime.cross_repo.types import RefStatus
from livespec_runtime.work_items.lifecycle import lane_of

from livespec_orchestrator_beads_fabro._beads_client import EDGE_PARENT_CHILD, make_beads_client
from livespec_orchestrator_beads_fabro._store_merge_hold import merge_hold_from_labels

if TYPE_CHECKING:
    from livespec_runtime.cross_repo.types import CrossRepoManifest

    from livespec_orchestrator_beads_fabro._beads_client import BeadsRecord
    from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

__all__: list[str] = [
    "WorkItemSubstrateFacts",
    "substrate_facts_for",
    "substrate_facts_from_records",
    "work_item_to_dict",
]


@dataclass(frozen=True, kw_only=True)
class WorkItemSubstrateFacts:
    """Beads-native fields projected alongside the shared WorkItem model."""

    parent: str | None
    labels: tuple[str, ...]


def substrate_facts_for(*, path: StoreConfig) -> dict[str, WorkItemSubstrateFacts]:
    client = make_beads_client(config=path)
    records = client.list_issues()
    return substrate_facts_from_records(
        records=records,
        child_parent_links=_implicit_dotted_child_parent_links(records=records),
    )


def substrate_facts_from_records(
    *,
    records: list[BeadsRecord],
    child_parent_links: dict[str, str] | None = None,
) -> dict[str, WorkItemSubstrateFacts]:
    facts: dict[str, WorkItemSubstrateFacts] = {}
    for record in records:
        issue_id = record.get("id")
        if isinstance(issue_id, str):
            parent = _parent_of(record=record)
            facts[issue_id] = WorkItemSubstrateFacts(
                parent=parent
                if parent is not None
                else _child_parent_of(
                    issue_id=issue_id,
                    child_parent_links=child_parent_links,
                ),
                labels=_labels_of(record=record),
            )
    return facts


def work_item_to_dict(
    *,
    item: WorkItem,
    facts: WorkItemSubstrateFacts | None,
    index: dict[str, WorkItem],
    dispatch_factory: str | None,
    manifest: CrossRepoManifest,
    sibling_status_lookup: Callable[[str, str], RefStatus] | None = None,
) -> dict[str, object]:
    payload = _dataclass_payload(value=item)
    payload["depends_on"] = [_json_ready(value=entry) for entry in item.depends_on]
    payload["parent"] = None if facts is None else facts.parent
    payload["labels"] = [] if facts is None else list(facts.labels)
    # Derived here rather than left for each reader to re-derive from `labels`:
    # the hold gates an automated merge, and a downstream surface that spelled
    # the prefix itself could read a held item as free with nothing to say so.
    payload["merge_hold"] = facts is not None and merge_hold_from_labels(labels=facts.labels)
    payload["dispatch_factory"] = dispatch_factory
    lane = lane_of(
        item=item, index=index, manifest=manifest, sibling_status_lookup=sibling_status_lookup
    )
    payload["lane"] = lane.name
    payload["lane_reason"] = lane.reason
    return payload


def _dataclass_payload(*, value: Any) -> dict[str, object]:
    return {field.name: _json_ready(value=getattr(value, field.name)) for field in fields(value)}


def _json_ready(*, value: object) -> object:
    if is_dataclass(value):
        return _dataclass_payload(value=value)
    if isinstance(value, tuple):
        tuple_items = cast("tuple[object, ...]", value)
        return [_json_ready(value=item) for item in tuple_items]
    if isinstance(value, list):
        list_items = cast("list[object]", value)
        return [_json_ready(value=item) for item in list_items]
    if isinstance(value, dict):
        dict_items = cast("dict[object, object]", value)
        return {str(key): _json_ready(value=item) for key, item in dict_items.items()}
    return value


def _labels_of(*, record: BeadsRecord) -> tuple[str, ...]:
    raw = record.get("labels")
    if not isinstance(raw, list):
        return ()
    labels = cast("list[object]", raw)
    return tuple(label for label in labels if isinstance(label, str))


def _parent_of(*, record: BeadsRecord) -> str | None:
    native_parent = record.get("parent")
    if isinstance(native_parent, str):
        return native_parent
    parent_id = record.get("parent_id")
    if isinstance(parent_id, str):
        return parent_id
    return _parent_from_edges(record=record)


def _parent_from_edges(*, record: BeadsRecord) -> str | None:
    raw = record.get("dependencies")
    if not isinstance(raw, list):
        return None
    edges = cast("list[object]", raw)
    for edge in edges:
        if isinstance(edge, dict):
            edge_dict = cast("dict[str, object]", edge)
            parent_id = edge_dict.get("depends_on_id")
            edge_type = edge_dict.get("type")
        else:
            continue
        if edge_type == EDGE_PARENT_CHILD and isinstance(parent_id, str):
            return parent_id
    return None


def _implicit_dotted_child_parent_links(*, records: list[BeadsRecord]) -> dict[str, str]:
    record_ids = frozenset(
        issue_id for record in records if isinstance(issue_id := record.get("id"), str)
    )
    links: dict[str, str] = {}
    for issue_id in record_ids:
        parent_id = _dotted_parent(issue_id=issue_id, record_ids=record_ids)
        if parent_id is not None:
            links[issue_id] = parent_id
    return links


def _dotted_parent(*, issue_id: str, record_ids: frozenset[str]) -> str | None:
    parent_id = issue_id.rpartition(".")[0]
    if parent_id in record_ids:
        return parent_id
    return None


def _child_parent_of(
    *,
    issue_id: str,
    child_parent_links: dict[str, str] | None,
) -> str | None:
    if child_parent_links is None:
        return None
    return child_parent_links.get(issue_id)
