#!/bin/sh
set -eu

if [ "$#" -ne 4 ]; then
  printf '%s\n' "usage: $0 MIGRATED_SCHEMA_JSON GOLDEN_SCHEMA_JSON GOLDEN_CLIENT_DIR RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" "$4" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

# Both sides of the comparison are read here. A receipt that hashed only the
# migrated side and published a hardcoded match could not fail; the schema
# pins `schema_hash_matches` to true, so a computed false is REJECTED at
# validation instead of being reported as a pass.
migrated = Path(sys.argv[1])
golden = Path(sys.argv[2])
receipt = Path(sys.argv[4])
migrated_sha = hashlib.sha256(migrated.read_bytes()).hexdigest()
golden_sha = hashlib.sha256(golden.read_bytes()).hexdigest()
payload = {
    "schema": "livespec.beads_v112_rehearsal.golden_schema_comparison.v1",
    "migrated_schema_path": str(migrated),
    "migrated_schema_sha256": migrated_sha,
    "golden_schema_path": str(golden),
    "golden_schema_sha256": golden_sha,
    "golden_client_dir": sys.argv[3],
    "schema_hash_matches": migrated_sha == golden_sha,
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
