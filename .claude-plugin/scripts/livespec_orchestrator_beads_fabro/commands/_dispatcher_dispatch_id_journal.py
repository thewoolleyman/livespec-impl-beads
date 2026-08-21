"""Dispatch-id journal record emission."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile

__all__: list[str] = [
    "DispatchJournalIdentity",
    "append_dispatch_id_record",
]


@dataclass(frozen=True, kw_only=True)
class DispatchJournalIdentity:
    dispatch_id: str
    dispatch_factory: str | None


def append_dispatch_id_record(
    *,
    journal: JournalFile,
    work_item_id: str,
    identity: DispatchJournalIdentity,
    started_at_epoch: float,
    workflow_toml: Path,
) -> None:
    record: dict[str, object] = {
        "stage": "dispatch-id",
        "work_item_id": work_item_id,
        "dispatch_id": identity.dispatch_id,
        "started_at_epoch": started_at_epoch,
        "workflow_toml": str(workflow_toml),
    }
    if identity.dispatch_factory is not None:
        record["dispatch_factory"] = identity.dispatch_factory
    journal.append(record=record)
