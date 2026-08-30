"""Ledger close mutations for Dispatcher completion dispositions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import utc_now_iso
from livespec_orchestrator_beads_fabro.commands._dispatcher_lifecycle_writes import (
    close_work_item_and_reconcile,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import store_config
from livespec_orchestrator_beads_fabro.types import AuditRecord, WorkItem

__all__: list[str] = [
    "close_dispatch_item",
    "no_change_needed_reason",
]


def no_change_needed_reason(*, outcome: DispatchOutcome) -> str:
    return (
        f"Fabro dispatch produced an empty merged diff for PR #{outcome.pr_number}; "
        "closed as no-change-needed, not resolution:completed. "
        "Pre-dispatch staleness detection is deferred."
    )


def close_dispatch_item(
    *,
    repo: Path,
    item: WorkItem,
    outcome: DispatchOutcome,
    resolution: str,
    reason: str,
    audit_merge: bool = True,
) -> None:
    merge_sha = outcome.merge_sha
    audit = (
        AuditRecord(
            verification_timestamp=utc_now_iso(),
            commits=(),
            files_changed=(),
            merge_sha=merge_sha,
            pr_number=outcome.pr_number,
        )
        if audit_merge and merge_sha is not None
        else None
    )
    closed = replace(
        item,
        status="done",
        resolution=resolution,
        reason=reason,
        audit=audit,
    )
    close_work_item_and_reconcile(path=store_config(repo=repo), item=closed)
