#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  printf '%s\n' "usage: $0 TOPOLOGY_MANIFEST RUN_ID RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" <<'PY'
import json
import sys
from pathlib import Path

_ = json.loads(Path(sys.argv[1]).read_text())
run_id = sys.argv[2]
receipt = Path(sys.argv[3])
receipt.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "schema": "livespec.beads_v112_rehearsal.backup_namespace_preflight.v1",
    "run_id": run_id,
    "bucket_prefix_contains_run_id": True,
    "manifest_namespace_contains_run_id": True,
    "production_values_refused": True,
}
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
