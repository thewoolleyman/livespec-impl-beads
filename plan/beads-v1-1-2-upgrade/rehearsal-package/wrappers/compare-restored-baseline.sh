#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  printf '%s\n' "usage: $0 SOURCE_BASELINE_DIR RESTORED_DIR RECEIPT_PATH" >&2
  exit 64
fi

source_sha=$(sha256sum "$1/combined.sha256" | awk '{print $1}')
restored_sha=$(sha256sum "$2/combined.sha256" | awk '{print $1}')
python3 - "$3" "$source_sha" "$restored_sha" <<'PY'
import json
import sys
from pathlib import Path

receipt = Path(sys.argv[1])
payload = {
    "schema": "livespec.beads_v112_rehearsal.restored_baseline_comparison_receipt.v1",
    "shape": receipt.stem,
    "source_baseline_combined_sha256": sys.argv[2],
    "restored_combined_sha256": sys.argv[3],
    "all_artifacts_match": sys.argv[2] == sys.argv[3],
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
