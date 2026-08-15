"""Dispatch-factory marker comments for beads work-items."""

from __future__ import annotations

from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro._store_comments import read_work_item_comments

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "dispatch_factory_for",
    "record_dispatch_factory",
]

_MARKER_PREFIX = "livespec-dispatch-factory: "


def dispatch_factory_for(*, path: StoreConfig, work_item_id: str) -> str | None:
    """Return the latest factory marker comment for a work-item, if present."""
    factory: str | None = None
    for comment in read_work_item_comments(path=path, work_item_id=work_item_id):
        if comment.text.startswith(_MARKER_PREFIX):
            candidate = comment.text.removeprefix(_MARKER_PREFIX).strip()
            if candidate != "":
                factory = candidate
    return factory


def record_dispatch_factory(*, path: StoreConfig, work_item_id: str, factory: str) -> None:
    """Append the dispatch-factory marker unless the latest marker already matches."""
    if dispatch_factory_for(path=path, work_item_id=work_item_id) == factory:
        return
    client = make_beads_client(config=path)
    client.add_comment(issue_id=work_item_id, body=f"{_MARKER_PREFIX}{factory}")
