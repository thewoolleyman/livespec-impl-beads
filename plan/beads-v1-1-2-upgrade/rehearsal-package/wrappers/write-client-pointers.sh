#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  printf '%s\n' "usage: $0 TOPOLOGY_MANIFEST RUN_ROOT RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
run_root = Path(sys.argv[2]).resolve()
receipt = Path(sys.argv[3])
rows = []
for client in manifest.get("clients", []):
    client_dir = Path(client["client_dir"]).resolve()
    if run_root not in [client_dir, *client_dir.parents]:
        raise SystemExit("HALT: client outside RUN_ROOT")
    beads = client_dir / ".beads"
    beads.mkdir(parents=True, exist_ok=True)
    pointer = (
        "dolt.auto-start: false\n"
        "dolt.mode: server\n"
        "dolt.server-host: 127.0.0.1\n"
        "dolt.server-port: 13307\n"
        f"dolt.server-user: {client['sql_user']}\n"
        f"dolt.database: {client['database']}\n"
        "dolt.prefix: b112\n"
    )
    path = beads / "config.yaml"
    path.write_text(pointer)
    rows.append({"client_key": client["client_key"], "sha256": hashlib.sha256(pointer.encode()).hexdigest()})
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps({"schema": "livespec.beads_v112_rehearsal.pointer_receipt.v1", "pointers": rows}, sort_keys=True) + "\n")
PY
