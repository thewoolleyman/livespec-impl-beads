"""Shared predicates for advertised and enforced drive valves."""

from __future__ import annotations

from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.commands._dispatcher_policy_settings import (
    effective_admission_policy,
)

if TYPE_CHECKING:
    from pathlib import Path

    from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "awaits_dispatcher_admission",
    "can_approve_item",
]

_PENDING_APPROVAL = "pending-approval"
_AUTO_ADMISSION = "auto"
_MANUAL_ADMISSION = "manual"


def can_approve_item(*, item: WorkItem, cwd: Path) -> bool:
    """Return whether the human approve valve can fire for this item now."""
    return (
        item.status == _PENDING_APPROVAL
        and effective_admission_policy(item=item, cwd=cwd) == _MANUAL_ADMISSION
    )


def awaits_dispatcher_admission(*, item: WorkItem, cwd: Path) -> bool:
    """Return whether the Dispatcher, not a human approve valve, owns admission."""
    return (
        item.status == _PENDING_APPROVAL
        and effective_admission_policy(item=item, cwd=cwd) == _AUTO_ADMISSION
    )
