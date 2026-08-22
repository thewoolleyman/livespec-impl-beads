#!/bin/sh
set -eu

if [ "$#" -ne 4 ]; then
  printf '%s\n' "usage: $0 TOPOLOGY_MANIFEST RUN_ID BACKUP_BUCKET_PREFIX RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" "$4" <<'PY'
import json
import sys
from pathlib import Path

# This is a PREFLIGHT REFUSAL GATE, so it both measures and halts. The earlier
# version parsed the manifest into `_` and discarded it, then published three
# hardcoded true assertions -- including `production_values_refused`, the one
# that stops the rehearsal writing into a production namespace. It would have
# reported success against a manifest naming production outright.
#
# The bucket prefix is a parameter because no manifest field carries it; the
# assertion about it cannot be computed from the manifest alone.

# Fragments that must never appear in a rehearsal BACKUP NAMESPACE. 3307 is the
# production Dolt port; the two paths are the production state trees named by
# the command plan's own `execution_boundary.forbidden_fragments`. That list
# also names the private delegate binary, which is a command path rather than a
# namespace value, and which this package's wrapper-content gate forbids a
# wrapper from naming at all -- so it is deliberately not part of this tuple.
PRODUCTION_FRAGMENTS = ("3307", "/var/lib/doltdb", "/var/backups")

manifest = json.loads(Path(sys.argv[1]).read_text())
run_id = sys.argv[2]
bucket_prefix = sys.argv[3]
receipt = Path(sys.argv[4])

clients = manifest.get("clients", [])
if not clients:
    raise SystemExit("HALT: topology manifest declares no clients")

isolated = manifest.get("isolated_server", {})
# Every value a backup could be namespaced by, gathered explicitly so the
# receipt can record exactly which surface was examined.
namespace_values = [
    *[str(row["database"]) for row in clients],
    *[str(row["sql_user"]) for row in clients],
]
examined_values = [
    bucket_prefix,
    *namespace_values,
    *[str(row["client_dir"]) for row in clients],
    *[str(value) for key, value in isolated.items() if key.endswith(("_dir", "_file", "socket"))],
]

manifest_run_id = manifest.get("run_id")
manifest_namespace_contains_run_id = all(run_id in value for value in namespace_values) and (
    manifest_run_id is None or manifest_run_id == run_id
)
bucket_prefix_contains_run_id = run_id in bucket_prefix
offending = sorted(
    {value for value in examined_values for fragment in PRODUCTION_FRAGMENTS if fragment in value},
)
production_values_refused = not offending

payload = {
    "schema": "livespec.beads_v112_rehearsal.backup_namespace_preflight.v1",
    "run_id": run_id,
    "backup_bucket_prefix": bucket_prefix,
    "examined_value_count": len(examined_values),
    "offending_values": offending,
    "bucket_prefix_contains_run_id": bucket_prefix_contains_run_id,
    "manifest_namespace_contains_run_id": manifest_namespace_contains_run_id,
    "production_values_refused": production_values_refused,
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")

# The receipt is written before the halt so a refusal leaves durable evidence
# of what was measured rather than only a non-zero exit.
if not production_values_refused:
    raise SystemExit(f"HALT: production value in rehearsal namespace: {offending}")
if not bucket_prefix_contains_run_id:
    raise SystemExit("HALT: backup bucket prefix missing RUN_ID")
if not manifest_namespace_contains_run_id:
    raise SystemExit("HALT: manifest namespace missing RUN_ID")
PY
