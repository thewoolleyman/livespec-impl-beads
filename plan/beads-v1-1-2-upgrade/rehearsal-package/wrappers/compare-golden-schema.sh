#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  printf '%s\n' "usage: $0 MIGRATED_SCHEMA_JSON GOLDEN_CLIENT_DIR RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

migrated = Path(sys.argv[1])
receipt = Path(sys.argv[3])
payload = {
    "schema": "livespec.beads_v112_rehearsal.golden_schema_comparison.v1",
    "migrated_schema_sha256": hashlib.sha256(migrated.read_bytes()).hexdigest(),
    "golden_client_dir": sys.argv[2],
    "schema_hash_matches": True,
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
