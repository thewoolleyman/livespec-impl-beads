#!/bin/sh
set -eu

if [ "$#" -ne 7 ]; then
  printf '%s\n' "usage: $0 PORT_BEFORE PORT_AFTER REGISTRY_SHA256_BEFORE REGISTRY_SHA256_AFTER BACKUP_CONFIG_SHA256_BEFORE BACKUP_CONFIG_SHA256_AFTER RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" "$4" "$5" "$6" "$7" <<'PY'
import json
import sys
from pathlib import Path

# Every `*_unchanged` field is a BEFORE/AFTER comparison, so both sides are
# parameters. The earlier signature took only the BEFORE values and published
# three hardcoded true assertions, which meant a script named
# prove-production-unchanged could not observe a change of any kind.
#
# The rehearsal's execution boundary forbids this package from touching the
# production endpoint, so the AFTER values are captured by the attended
# operator outside this wrapper and handed in, exactly as the BEFORE values
# always were.
(
    port_before,
    port_after,
    registry_before,
    registry_after,
    backup_before,
    backup_after,
    receipt_path,
) = sys.argv[1:8]
receipt = Path(receipt_path)
payload = {
    "schema": "livespec.beads_v112_rehearsal.production_unchanged_receipt.v1",
    "production_port_before": port_before,
    "production_port_after": port_after,
    "production_port_3307_unchanged": port_before == port_after,
    "production_registry_sha256_before": registry_before,
    "production_registry_sha256_after": registry_after,
    "production_registry_digest_unchanged": registry_before == registry_after,
    "production_backup_config_sha256_before": backup_before,
    "production_backup_config_sha256_after": backup_after,
    "production_backup_config_digest_unchanged": backup_before == backup_after,
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")
PY
