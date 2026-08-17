"""Dispatch-factory marker metadata for beads work-items."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro._store_comments import read_work_item_comments

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro._beads_client import BeadsRecord
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "backfill_dispatch_factory_metadata",
    "dispatch_factories_for",
    "dispatch_factory_for",
    "dispatch_factory_from_record",
    "record_dispatch_factory",
]

_MARKER_PREFIX = "livespec-dispatch-factory: "
_META_DISPATCH_FACTORY = "dispatch_factory"
_BEADS_CLOSED = "closed"


def dispatch_factory_for(*, path: StoreConfig, work_item_id: str) -> str | None:
    """Return the persisted factory marker for a work-item, if present."""
    client = make_beads_client(config=path)
    record = client.show_issue(issue_id=work_item_id)
    factory = dispatch_factory_from_record(record=record)
    if factory is not None:
        return factory
    return _latest_comment_marker(path=path, work_item_id=work_item_id)


def dispatch_factory_from_record(*, record: BeadsRecord) -> str | None:
    """Return the dispatch-factory marker carried by an issue record."""
    raw = _metadata_of(record=record).get(_META_DISPATCH_FACTORY)
    if isinstance(raw, str) and raw.strip() != "":
        return raw.strip()
    return None


def dispatch_factories_for(*, path: StoreConfig) -> dict[str, str | None]:
    """Return metadata-carried dispatch factories from one issue-list payload."""
    client = make_beads_client(config=path)
    return {
        issue_id: dispatch_factory_from_record(record=record)
        for record in client.list_issues()
        if isinstance((issue_id := record.get("id")), str)
    }


def backfill_dispatch_factory_metadata(*, path: StoreConfig) -> int:
    """Backfill open issue metadata from legacy comment-borne markers."""
    client = make_beads_client(config=path)
    changed = 0
    for record in client.list_issues():
        issue_id = record.get("id")
        if not isinstance(issue_id, str) or record.get("status") == _BEADS_CLOSED:
            continue
        if dispatch_factory_from_record(record=record) is not None:
            continue
        factory = _latest_comment_marker(path=path, work_item_id=issue_id)
        if factory is None:
            continue
        client.update_issue(
            issue_id=issue_id,
            metadata=_metadata_with_dispatch_factory(record=record, factory=factory),
        )
        changed += 1
    return changed


def _latest_comment_marker(*, path: StoreConfig, work_item_id: str) -> str | None:
    factory: str | None = None
    for comment in read_work_item_comments(path=path, work_item_id=work_item_id):
        if comment.text.startswith(_MARKER_PREFIX):
            candidate = comment.text.removeprefix(_MARKER_PREFIX).strip()
            if candidate != "":
                factory = candidate
    return factory


def record_dispatch_factory(*, path: StoreConfig, work_item_id: str, factory: str) -> None:
    """Persist the dispatch-factory marker and keep a comment audit trail."""
    client = make_beads_client(config=path)
    record = client.show_issue(issue_id=work_item_id)
    if dispatch_factory_from_record(record=record) == factory:
        return
    client.update_issue(
        issue_id=work_item_id,
        metadata=_metadata_with_dispatch_factory(record=record, factory=factory),
    )
    client.add_comment(issue_id=work_item_id, body=f"{_MARKER_PREFIX}{factory}")


def _metadata_with_dispatch_factory(*, record: BeadsRecord, factory: str) -> dict[str, Any]:
    metadata = _metadata_of(record=record)
    metadata[_META_DISPATCH_FACTORY] = factory
    return metadata


def _metadata_of(*, record: BeadsRecord) -> dict[str, Any]:
    raw = record.get("metadata")
    if isinstance(raw, dict):
        return dict(cast("dict[str, Any]", raw))
    return {}
