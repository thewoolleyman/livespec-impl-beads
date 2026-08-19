#!/bin/sh
set -eu

if [ "$#" -lt 3 ]; then
  printf '%s\n' "usage: $0 RECEIPT_PATH BD112 DATABASE..." >&2
  exit 64
fi

receipt=$1
bd112=$2
shift 2
sha=$(sha256sum "$bd112" | awk '{print $1}')
python3 - "$receipt" "$sha" "$$" "$@" <<'PY'
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

receipt = Path(sys.argv[1])
payload = {
    "schema": "livespec.beads_v112_rehearsal.designated_migrator_receipt.v1",
    "human_or_session_identity": "attended-operator",
    "process_id": int(sys.argv[3]),
    "candidate_executable_sha256": sys.argv[2],
    "host": socket.gethostname(),
    "start_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "ordered_database_list": sys.argv[4:],
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
