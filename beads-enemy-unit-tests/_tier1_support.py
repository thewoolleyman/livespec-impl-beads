"""Shared tier 1 mutation helpers for the Beads Enemy Unit Tests.

Tier 1 mutates a THROWAWAY isolated store: create / update / close / dependency
/ comment round-trips, the two-step create normalization, assignee clearing,
and the metadata compact-JSON round-trip. Every id it mints is EUT-scoped so a
run leaves an inspectable, disposable trail.
"""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro._beads_client import IssueDraft

if TYPE_CHECKING:
    from _tier0_support import BeadsTier0Config

__all__: list[str] = []

_CREATED_AT = "2026-08-30T00:00:00Z"


def unique_issue_id(*, config: BeadsTier0Config) -> str:
    """Mint a collision-free, EUT-scoped issue id under the tenant prefix."""
    return f"{config.prefix}-eut{uuid.uuid4().hex[:10]}"


def make_draft(
    *,
    issue_id: str,
    title: str,
    assignee: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> IssueDraft:
    """Build a minimal, valid IssueDraft for a tier 1 create."""
    return IssueDraft(
        issue_id=issue_id,
        issue_type="task",
        title=title,
        description=f"Beads Enemy Unit Test fixture: {title}",
        assignee=assignee,
        created_at=_CREATED_AT,
        metadata=metadata if metadata is not None else {},
    )


def parsed_metadata(*, record: dict[str, Any]) -> dict[str, Any]:
    """Return an issue record's `metadata` as a parsed dict.

    `bd ... --json` may render the metadata column as a nested object or as a
    JSON string; both are normalized to a dict so callers compare PARSED
    structures, never raw text.
    """
    raw = record.get("metadata")
    if isinstance(raw, dict):
        return cast("dict[str, Any]", raw)
    if isinstance(raw, str) and raw.strip() != "":
        decoded: Any = json.loads(raw)
        if isinstance(decoded, dict):
            return cast("dict[str, Any]", decoded)
    return {}


def record_status(*, record: dict[str, Any]) -> str | None:
    """Return a record's status string, if present."""
    status = record.get("status")
    return status if isinstance(status, str) else None


def record_assignee(*, record: dict[str, Any]) -> str:
    """Return a record's assignee as a string ('' when cleared or absent)."""
    assignee = record.get("assignee")
    return assignee if isinstance(assignee, str) else ""
