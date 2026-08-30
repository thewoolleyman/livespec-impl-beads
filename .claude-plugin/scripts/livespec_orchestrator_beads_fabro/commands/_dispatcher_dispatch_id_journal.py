"""Dispatch-id journal record emission.

THE RECORD CARRIES THE RESOLVED INTEGRATION CONTRACT. The
resolve-once-project-everywhere clause requires the frozen contract to be
journaled WITH the dispatch record, and this is that record: it is the one
artifact written before the run starts, so it is the only place a reader can
later establish what the orchestrator believed about the governed repository at
the moment it dispatched. Without it, a post-hoc question -- which check-suite
was this repository declaring, was its core pin declared or defective, which
merge strategy armed -- can only be answered by re-reading a `.livespec.jsonc`
that may have changed since, which answers a different question.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_projection import (
    integration_contract_journal_record,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    ResolvedIntegrationContract,
)
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
    integration: ResolvedIntegrationContract,
) -> None:
    record: dict[str, object] = {
        "stage": "dispatch-id",
        "work_item_id": work_item_id,
        "dispatch_id": identity.dispatch_id,
        "started_at_epoch": started_at_epoch,
        "workflow_toml": str(workflow_toml),
        **integration_contract_journal_record(resolved=integration),
    }
    if identity.dispatch_factory is not None:
        record["dispatch_factory"] = identity.dispatch_factory
    journal.append(record=record)
