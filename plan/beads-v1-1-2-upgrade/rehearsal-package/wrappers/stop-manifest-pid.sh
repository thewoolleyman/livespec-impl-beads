#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  printf '%s\n' "usage: $0 TOPOLOGY_MANIFEST RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
receipt = Path(sys.argv[2])
payload = {
    "schema": "livespec.beads_v112_rehearsal.stop_boundary_receipt.v1",
    "pid_file": manifest.get("isolated_server", {}).get("pid_file"),
    "pid_scope_verified": True,
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
