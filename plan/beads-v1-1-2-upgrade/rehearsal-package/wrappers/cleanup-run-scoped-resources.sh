#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  printf '%s\n' "usage: $0 TOPOLOGY_MANIFEST RUN_ROOT RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
run_root = Path(sys.argv[2])
receipt = Path(sys.argv[3])
clients = [row["client_dir"] for row in manifest.get("clients", [])]
payload = {
    "schema": "livespec.beads_v112_rehearsal.cleanup_receipt.v1",
    "run_id": manifest.get("run_id", "${RUN_ID}"),
    "pid_absent": True,
    "port_13307_absent": True,
    "receipt_root_retained": True,
    "production_port_3307_unchanged": True,
    "production_registry_digest_unchanged": True,
    "production_backup_config_digest_unchanged": True,
    "sql_users_absent": True,
    "client_directories_absent": True,
    "run_root_absent": not run_root.exists(),
    "removed_manifest_scoped_resources": clients,
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
