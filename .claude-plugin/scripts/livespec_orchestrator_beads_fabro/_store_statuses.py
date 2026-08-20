"""Status projection helpers for the beads-backed store."""

from __future__ import annotations

from typing import get_args

from livespec_orchestrator_beads_fabro.types import WorkItemStatus

__all__: list[str] = [
    "ALLOWED_BEADS_STATUSES",
    "PARKED_BEADS_STATUSES",
    "livespec_status_for",
]


def livespec_status_for(*, status: str) -> str:
    """Map a beads status onto its livespec status (`closed` -> `done`)."""
    return "done" if status == "closed" else status


# `deferred` is a beads-native parked state, not a dispatch lane. It is
# accepted by conformance so a scheduled item cannot block unrelated dispatches
# tenant-wide; `ready`/`pending-approval` selection still excludes it.
PARKED_BEADS_STATUSES: frozenset[str] = frozenset({"deferred"})

ALLOWED_BEADS_STATUSES: frozenset[str] = (
    frozenset("closed" if status == "done" else status for status in get_args(WorkItemStatus))
    | PARKED_BEADS_STATUSES
)
