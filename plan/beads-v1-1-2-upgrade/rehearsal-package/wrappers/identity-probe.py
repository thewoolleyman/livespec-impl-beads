#!/usr/bin/env python3
"""Compute a version-neutral inventory identity from Beads JSON issue output."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_ARGC = 2
ERROR_EXPECTED_ARRAY = "expected top-level JSON array"
ERROR_EXPECTED_RECORD = "expected every issue entry to be a JSON object"
ERROR_EXPECTED_LABEL_ARRAY = "expected labels to be a JSON array when present"
ERROR_EXPECTED_LABEL_STRING = "expected every label to be a string"
ERROR_USAGE = "usage: identity-probe.py ISSUES_JSON"

__all__: list[str] = [
    "main",
]


def _as_issue_records(*, value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise SystemExit(ERROR_EXPECTED_ARRAY)
    records: list[Mapping[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise SystemExit(ERROR_EXPECTED_RECORD)
        records.append(item)
    return records


def _count_sequence(*, record: Mapping[str, Any], key: str) -> int:
    value = record.get(key)
    if value is None:
        return 0
    if isinstance(value, Sequence) and not isinstance(value, str):
        return len(value)
    message = f"expected {key} to be a JSON array when present"
    raise SystemExit(message)


def _labels(*, record: Mapping[str, Any]) -> list[str]:
    raw = record.get("labels")
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, str):
        raise SystemExit(ERROR_EXPECTED_LABEL_ARRAY)
    labels: list[str] = []
    for label in raw:
        if not isinstance(label, str):
            raise SystemExit(ERROR_EXPECTED_LABEL_STRING)
        labels.append(label)
    return labels


def _has_metadata(*, record: Mapping[str, Any]) -> bool:
    metadata = record.get("metadata")
    return isinstance(metadata, Mapping) and bool(metadata)


def _inventory_digest(*, records: list[Mapping[str, Any]]) -> str:
    stable = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(stable).hexdigest()


def main() -> int:
    if len(sys.argv) != EXPECTED_ARGC:
        raise SystemExit(ERROR_USAGE)
    records = _as_issue_records(value=json.loads(Path(sys.argv[1]).read_text()))
    labels = {label for record in records for label in _labels(record=record)}
    receipt = {
        "schema": "livespec.beads_v112_rehearsal.identity_probe_receipt.v1",
        "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bd_version_stdout": "not-captured-by-json-only-probe",
        "inventory_digest": _inventory_digest(records=records),
        "issue_count": len(records),
        "dependency_count": sum(
            _count_sequence(record=record, key="dependencies") for record in records
        ),
        "comment_count": sum(int(record.get("comment_count", 0) or 0) for record in records),
        "metadata_issue_count": sum(1 for record in records if _has_metadata(record=record)),
        "distinct_label_count": len(labels),
    }
    json.dump(receipt, sys.stdout, sort_keys=True, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
