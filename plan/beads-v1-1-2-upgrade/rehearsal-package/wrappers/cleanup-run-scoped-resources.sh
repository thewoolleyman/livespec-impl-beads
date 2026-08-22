#!/bin/sh
set -eu

if [ "$#" -ne 4 ]; then
  printf '%s\n' "usage: $0 TOPOLOGY_MANIFEST RUN_ROOT PRODUCTION_UNCHANGED_RECEIPT RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" "$4" <<'PY'
import json
import os
import socket
import sys
from pathlib import Path

# Nine of this receipt's ten assertions were hardcoded true; only
# `run_root_absent` was computed. Each one below is now measured, derived from
# a measured value, or propagated from the receipt that measured it.
#
# The three production digests are the last kind: this package's execution
# boundary forbids it from touching the production endpoint, so
# prove-production-unchanged.sh measures them and runs FIRST in the cleanup
# stage. Its schema id is checked here so an unrelated JSON file cannot
# silently satisfy the propagation.
PRODUCTION_RECEIPT_SCHEMA = "livespec.beads_v112_rehearsal.production_unchanged_receipt.v1"

manifest = json.loads(Path(sys.argv[1]).read_text())
run_root = Path(sys.argv[2])
production_receipt_path = Path(sys.argv[3])
receipt = Path(sys.argv[4])

production = json.loads(production_receipt_path.read_text())
if production.get("schema") != PRODUCTION_RECEIPT_SCHEMA:
    raise SystemExit(f"HALT: {production_receipt_path} is not a production-unchanged receipt")

isolated = manifest.get("isolated_server", {})
clients = [row["client_dir"] for row in manifest.get("clients", [])]

run_root_absent = not run_root.exists()

pid_absent = True
pid_file_value = isolated.get("pid_file")
if pid_file_value:
    pid_file = Path(pid_file_value)
    if pid_file.is_file():
        raw = pid_file.read_text().strip()
        pid_absent = not (raw.isdigit() and (Path("/proc") / raw).exists())

# A refused connection on the isolated port is the observable form of "the
# isolated server is gone". Production's 3307 is never contacted.
port = int(isolated.get("port", 13307))
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
    probe.settimeout(2.0)
    port_absent = probe.connect_ex(("127.0.0.1", port)) != 0

receipt_root = Path(os.environ.get("RECEIPT_ROOT") or receipt.parent)
receipt_root_retained = receipt_root.is_dir()

client_directories_absent = not any(Path(client_dir).exists() for client_dir in clients)

# The isolated server's SQL users exist only inside its own data directory,
# which the manifest places under RUN_ROOT. Their absence is therefore
# entailed by both trees being gone -- which is measurable after the server
# has stopped, whereas querying the users is not.
isolated_data_dir = isolated.get("data_dir")
isolated_data_dir_absent = not (isolated_data_dir and Path(isolated_data_dir).exists())
sql_users_absent = isolated_data_dir_absent and run_root_absent

payload = {
    "schema": "livespec.beads_v112_rehearsal.cleanup_receipt.v1",
    "run_id": manifest.get("run_id", "${RUN_ID}"),
    "pid_absent": pid_absent,
    "port_13307_absent": port_absent,
    "receipt_root_retained": receipt_root_retained,
    "production_unchanged_receipt": str(production_receipt_path),
    "production_port_3307_unchanged": production["production_port_3307_unchanged"],
    "production_registry_digest_unchanged": production["production_registry_digest_unchanged"],
    "production_backup_config_digest_unchanged": production[
        "production_backup_config_digest_unchanged"
    ],
    "isolated_data_dir_absent": isolated_data_dir_absent,
    "sql_users_absent": sql_users_absent,
    "client_directories_absent": client_directories_absent,
    "run_root_absent": run_root_absent,
    "removed_manifest_scoped_resources": clients,
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
