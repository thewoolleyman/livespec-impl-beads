"""Ready-dwell metadata helpers for the beads-backed store."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

from livespec_orchestrator_beads_fabro._beads_client import BeadsRecord, make_beads_client
from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "READY_SINCE_META_KEY",
    "read_ready_dwell_instants",
    "ready_dwell_instants_from_records",
    "ready_transition_metadata",
    "utc_now_iso",
]

READY_SINCE_META_KEY = "ready_since"


def utc_now_iso() -> str:
    """Return a UTC wall-clock instant in the repo's canonical JSON timestamp form."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ready_transition_metadata(
    *,
    existing_metadata: dict[str, Any],
    now_iso: str,
) -> dict[str, Any]:
    """Overlay the durable instant for the latest transition into `ready`."""
    metadata = dict(existing_metadata)
    metadata[READY_SINCE_META_KEY] = now_iso
    return metadata


def ready_dwell_instants_from_records(
    *,
    records: list[BeadsRecord],
) -> dict[str, str | None]:
    """Project every ready item to its durable ready-dwell instant, if known."""
    instants: dict[str, str | None] = {}
    for record in records:
        if record.get("status") != "ready":
            continue
        issue_id = record.get("id")
        if not isinstance(issue_id, str):
            continue
        metadata_raw = record.get("metadata")
        metadata = cast("dict[str, Any]", metadata_raw) if isinstance(metadata_raw, dict) else {}
        ready_since = metadata.get(READY_SINCE_META_KEY)
        instants[issue_id] = ready_since if isinstance(ready_since, str) else None
    return instants


def read_ready_dwell_instants(*, path: StoreConfig) -> dict[str, str | None]:
    """Return ready item ids mapped to their durable ready-dwell instant or unknown."""
    client = make_beads_client(config=path)
    return ready_dwell_instants_from_records(records=client.list_issues())
