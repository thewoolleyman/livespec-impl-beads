#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  printf '%s\n' "usage: $0 CLIENT_KEY OUTPUT_DIR CAPTURE_POINT" >&2
  exit 64
fi

client_key=$1
output_dir=$2
capture_point=$3

case "$capture_point" in
  pre-backup-v49-baseline | after-first-gate-decision | post-migration-v53 | post-round-trip | post-restore-v49) ;;
  *)
    printf '%s\n' "HALT: unsupported inventory capture point" >&2
    exit 70
    ;;
esac

case "$output_dir" in
  "${RECEIPT_ROOT:-__missing_receipt_root__}"/*) ;;
  *)
    printf '%s\n' "HALT: inventory output must be under RECEIPT_ROOT" >&2
    exit 70
    ;;
esac

mkdir -p "$output_dir"
bd=${BD_PATH:-/usr/local/bin/bd}
with_client=${WITH_CLIENT:-$(dirname "$0")/with-client.sh}
sequence=1

for projection in \
  status-type-counts \
  issues \
  dependencies \
  comments \
  labels \
  policy-metadata \
  schema-migrations \
  schema \
  branches \
  table-counts \
  remotes
do
  artifact="$projection.json"
  tmp="$output_dir/$artifact.tmp"
  BEADS112_COMMAND_CATEGORY=inventory \
  BEADS112_COMMAND_SEQUENCE=$sequence \
    "$with_client" "$client_key" "$bd" inventory "$projection" --json > "$tmp"
  python3 - "$tmp" "$output_dir/$artifact" <<'PY'
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
payload = json.loads(source.read_text())
if isinstance(payload, list):
    payload = sorted(payload, key=lambda row: json.dumps(row, sort_keys=True))
target.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
source.unlink()
PY
  sequence=$((sequence + 1))
done

latest_anchor=$(ls -1 "$RECEIPT_ROOT"/anchor-*-inventory.json | tail -1)
cp "$latest_anchor" "$output_dir/client-anchor.json"

(
  cd "$output_dir"
  sha256sum \
    status-type-counts.json \
    issues.json \
    dependencies.json \
    comments.json \
    labels.json \
    policy-metadata.json \
    schema-migrations.json \
    schema.json \
    branches.json \
    table-counts.json \
    remotes.json \
    client-anchor.json > SHA256SUMS
  sha256sum SHA256SUMS | awk '{print $1}' > combined.sha256
)

python3 - "$client_key" "$capture_point" "$output_dir" <<'PY'
import json
import sys
from pathlib import Path

client_key = sys.argv[1]
capture_point = sys.argv[2]
output_dir = Path(sys.argv[3])
entries: dict[str, str] = {}
for line in (output_dir / "SHA256SUMS").read_text().splitlines():
    digest, artifact = line.split(maxsplit=1)
    entries[artifact] = digest
receipt = {
    "schema": "livespec.beads_v112_rehearsal.inventory_receipt.v1",
    "client_key": client_key,
    "capture_point": capture_point,
    "artifacts": sorted(entries),
    "per_artifact_sha256": dict(sorted(entries.items())),
    "combined_sha256": (output_dir / "combined.sha256").read_text().strip(),
}
(output_dir / "inventory-receipt.json").write_text(
    json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
)
PY
