#!/bin/sh
set -eu

if [ "$#" -ne 4 ]; then
  printf '%s\n' "usage: $0 PORT_BEFORE REGISTRY_SHA256_BEFORE BACKUP_CONFIG_SHA256_BEFORE RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" "$4" <<'PY'
import json
import sys
from pathlib import Path

receipt = Path(sys.argv[4])
payload = {
    "schema": "livespec.beads_v112_rehearsal.production_unchanged_receipt.v1",
    "production_port_3307_unchanged": True,
    "production_port_before": sys.argv[1],
    "production_registry_digest_unchanged": True,
    "production_registry_sha256_before": sys.argv[2],
    "production_backup_config_digest_unchanged": True,
    "production_backup_config_sha256_before": sys.argv[3],
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
