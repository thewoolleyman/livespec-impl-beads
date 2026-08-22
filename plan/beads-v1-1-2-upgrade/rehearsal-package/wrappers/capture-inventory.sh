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

capture_json() {
  artifact=$1
  shift
  tmp="$output_dir/$artifact.tmp"
  BEADS112_COMMAND_CATEGORY=inventory \
  BEADS112_COMMAND_SEQUENCE=$sequence \
    "$with_client" "$client_key" "$bd" "$@" > "$tmp"
  python3 - "$tmp" "$output_dir/$artifact" <<'PY'
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
raw = source.read_text()
try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    payload = {"text": raw}
if isinstance(payload, list):
    payload = sorted(payload, key=lambda row: json.dumps(row, sort_keys=True))
target.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
source.unlink()
PY
  sequence=$((sequence + 1))
}

capture_sql() {
  artifact=$1
  sql=$(printf '%s' "$2" | tr '\n' ' ')
  tmp="$output_dir/$artifact.tmp"
  BEADS112_COMMAND_CATEGORY=inventory \
  BEADS112_COMMAND_SEQUENCE=$sequence \
    "$with_client" "$client_key" "$bd" sql --csv "$sql" > "$tmp"
  python3 - "$tmp" "$output_dir/$artifact" <<'PY'
import csv
import io
import json
import re
import sys
from pathlib import Path


def parse_bd_sql_json_cell(raw: str) -> object:
    for line in raw.splitlines():
        cell = line.strip()
        if (
            not cell
            or set(cell) <= {"-"}
            or re.fullmatch(r"\(\d+ rows?\)", cell)
        ):
            continue
        if cell.startswith("|") and cell.endswith("|"):
            parts = [part.strip() for part in cell.strip("|").split("|")]
        else:
            # Try the WHOLE cell first: a bare JSON payload contains commas
            # that a CSV split would shred. Only then try `--csv` fields, where
            # the payload arrives as one quoted field.
            parts = [cell]
            try:
                parts += [part.strip() for part in next(csv.reader(io.StringIO(cell)))]
            except (csv.Error, StopIteration):
                pass
        for part in parts:
            if part.startswith(("{", "[")):
                return json.loads(part)
    raise SystemExit("HALT: bd sql output did not contain a JSON result cell")


source = Path(sys.argv[1])
target = Path(sys.argv[2])
payload = parse_bd_sql_json_cell(source.read_text())
if isinstance(payload, list):
    payload = sorted(payload, key=lambda row: json.dumps(row, sort_keys=True))
target.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
source.unlink()
PY
  sequence=$((sequence + 1))
}

capture_sql_bundle() {
  sql=$(printf '%s' "$1" | tr '\n' ' ')
  shift
  tmp="$output_dir/sql-bundle.tmp"
  BEADS112_COMMAND_CATEGORY=inventory \
  BEADS112_COMMAND_SEQUENCE=$sequence \
    "$with_client" "$client_key" "$bd" sql --csv "$sql" > "$tmp"
  python3 - "$tmp" "$output_dir" "$@" <<'PY'
import csv
import io
import json
import re
import sys
from pathlib import Path

source = Path(sys.argv[1])
output_dir = Path(sys.argv[2])
artifacts = sys.argv[3:]
raw = source.read_text()
def parse_bd_sql_json_cell(raw):
    for line in raw.splitlines():
        cell = line.strip()
        if (
            not cell
            or set(cell) <= {"-"}
            or re.fullmatch(r"\(\d+ rows?\)", cell)
        ):
            continue
        if cell.startswith("|") and cell.endswith("|"):
            parts = [part.strip() for part in cell.strip("|").split("|")]
        else:
            # Try the WHOLE cell first: a bare JSON payload contains commas
            # that a CSV split would shred. Only then try `--csv` fields, where
            # the payload arrives as one quoted field.
            parts = [cell]
            try:
                parts += [part.strip() for part in next(csv.reader(io.StringIO(cell)))]
            except (csv.Error, StopIteration):
                pass
        for part in parts:
            if part.startswith(("{", "[")):
                return json.loads(part)
    raise SystemExit("HALT: bd sql output did not contain a JSON result cell")

payload = parse_bd_sql_json_cell(raw)
if not isinstance(payload, dict):
    raise SystemExit("HALT: bd sql bundle JSON cell was not an object")
for artifact in artifacts:
    if artifact not in payload:
        raise SystemExit(f"HALT: bd sql bundle missing artifact {artifact}")
    target_payload = payload[artifact]
    if isinstance(target_payload, list):
        target_payload = sorted(
            target_payload,
            key=lambda row: json.dumps(row, sort_keys=True),
        )
    (output_dir / artifact).write_text(
        json.dumps(target_payload, sort_keys=True, separators=(",", ":")) + "\n",
    )
source.unlink()
PY
  sequence=$((sequence + 1))
}

work_items_union='(
  SELECT id, title, description, design, acceptance_criteria, notes, status, priority, issue_type,
         assignee, owner, created_at, created_by, updated_at, closed_at, close_reason,
         external_ref, spec_id, due_at, defer_until, metadata
    FROM issues
  UNION ALL
  SELECT id, title, description, design, acceptance_criteria, notes, status, priority, issue_type,
         assignee, owner, created_at, created_by, updated_at, closed_at, close_reason,
         external_ref, spec_id, due_at, defer_until, metadata
    FROM wisps
)'

capture_json "all-issues.json" list --status all --limit 0 --json

# Per-issue enumeration MUST come from `issues UNION ALL wisps`, NOT from
# `all-issues.json`. That artifact is captured with `bd list --json`, which reads
# `issues` only: a `rig`-typed row lives in `wisps`, so enumerating from the
# listing silently drops it from EVERY per-issue artifact (show / dep list /
# comments / children), leaving `dependencies.json` and `comments.json` blind to
# exactly the shape migration 0053 exists for. Measured on v1.1.2 and v1.2.2.
capture_sql "work-item-ids.json" "
SELECT COALESCE((SELECT JSON_ARRAYAGG(id) FROM (
  SELECT id FROM issues
  UNION ALL
  SELECT id FROM wisps
  ORDER BY id
) AS work_item_ids), JSON_ARRAY());
"

issue_ids=$(
  python3 - "$output_dir/work-item-ids.json" <<'PY'
import json
import sys
from pathlib import Path

for issue_id in json.loads(Path(sys.argv[1]).read_text()):
    if isinstance(issue_id, str):
        print(issue_id)
PY
)

tmp_dir="$output_dir/per-issue"
mkdir -p "$tmp_dir"
: > "$tmp_dir/dependencies.jsonl"
: > "$tmp_dir/comments.jsonl"
: > "$tmp_dir/show.jsonl"
: > "$tmp_dir/children.jsonl"
for issue_id in $issue_ids; do
  capture_json "per-issue/show-$issue_id.json" show "$issue_id" --json
  cat "$output_dir/per-issue/show-$issue_id.json" >> "$tmp_dir/show.jsonl"
  capture_json "per-issue/dependencies-$issue_id.json" dep list "$issue_id" --json
  cat "$output_dir/per-issue/dependencies-$issue_id.json" >> "$tmp_dir/dependencies.jsonl"
  capture_json "per-issue/comments-$issue_id.json" comments "$issue_id" --json
  cat "$output_dir/per-issue/comments-$issue_id.json" >> "$tmp_dir/comments.jsonl"
  capture_json "per-issue/children-$issue_id.json" children "$issue_id" --json
  cat "$output_dir/per-issue/children-$issue_id.json" >> "$tmp_dir/children.jsonl"
done

python3 - "$tmp_dir/dependencies.jsonl" "$output_dir/dependencies.json" <<'PY'
import json
import sys
from pathlib import Path

rows = []
for line in Path(sys.argv[1]).read_text().splitlines():
    payload = json.loads(line)
    if isinstance(payload, list):
        rows.extend(row for row in payload if isinstance(row, dict))
Path(sys.argv[2]).write_text(json.dumps(sorted(rows, key=lambda row: json.dumps(row, sort_keys=True)), sort_keys=True, separators=(",", ":")) + "\n")
PY
python3 - "$tmp_dir/comments.jsonl" "$output_dir/comments.json" <<'PY'
import json
import sys
from pathlib import Path

rows = []
for line in Path(sys.argv[1]).read_text().splitlines():
    payload = json.loads(line)
    if isinstance(payload, list):
        rows.extend(row for row in payload if isinstance(row, dict))
Path(sys.argv[2]).write_text(json.dumps(sorted(rows, key=lambda row: json.dumps(row, sort_keys=True)), sort_keys=True, separators=(",", ":")) + "\n")
PY
rm -rf "$tmp_dir"

capture_json "schema-migrations.json" migrate status

capture_sql_bundle "
SELECT JSON_OBJECT(
  'status-type-counts.json', COALESCE((
    SELECT JSON_ARRAYAGG(row_json)
    FROM (
      SELECT JSON_OBJECT('status', status, 'issue_type', issue_type, 'COUNT(*)', COUNT(*)) AS row_json
      FROM $work_items_union AS work_items
      GROUP BY status, issue_type
      ORDER BY status, issue_type
    ) AS status_rows
  ), JSON_ARRAY()),
  'issues.json', COALESCE((
    SELECT JSON_ARRAYAGG(row_json)
    FROM (
      SELECT JSON_OBJECT(
        'id', id,
        'title', title,
        'description', description,
        'design', design,
        'acceptance_criteria', acceptance_criteria,
        'notes', notes,
        'status', status,
        'priority', priority,
        'issue_type', issue_type,
        'assignee', assignee,
        'owner', owner,
        'created_at', created_at,
        'created_by', created_by,
        'updated_at', updated_at,
        'closed_at', closed_at,
        'close_reason', close_reason,
        'external_ref', external_ref,
        'spec_id', spec_id,
        'due_at', due_at,
        'defer_until', defer_until,
        'canonicalized_metadata', metadata
      ) AS row_json
      FROM $work_items_union AS work_items
      ORDER BY id
    ) AS issue_rows
  ), JSON_ARRAY()),
  'labels.json', COALESCE((
    SELECT JSON_ARRAYAGG(row_json)
    FROM (
      SELECT JSON_OBJECT('issue_id', labels.issue_id, 'label', labels.label) AS row_json
      FROM labels
      JOIN (
        SELECT id FROM issues
        UNION ALL
        SELECT id FROM wisps
      ) AS work_item_ids ON work_item_ids.id = labels.issue_id
      ORDER BY labels.issue_id, labels.label
    ) AS label_rows
  ), JSON_ARRAY()),
  'policy-metadata.json', COALESCE((
    SELECT JSON_ARRAYAGG(row_json)
    FROM (
      SELECT JSON_OBJECT(
        'issue_id', work_items.id,
        'complete_canonical_metadata', work_items.metadata,
        'policy_labels', COALESCE(policy_labels.labels_json, JSON_ARRAY())
      ) AS row_json
      FROM $work_items_union AS work_items
      LEFT JOIN (
        SELECT issue_id, JSON_ARRAYAGG(label) AS labels_json
        FROM labels
        WHERE label LIKE 'acceptance:%'
           OR label LIKE 'admission:%'
           OR label LIKE 'intake:%'
           OR label LIKE 'origin:%'
           OR label LIKE 'factory-safety:%'
           OR label LIKE 'blocked-reason:%'
        GROUP BY issue_id
      ) AS policy_labels ON policy_labels.issue_id = work_items.id
      ORDER BY work_items.id
    ) AS policy_rows
  ), JSON_ARRAY())
);
" \
  "status-type-counts.json" \
  "issues.json" \
  "labels.json" \
  "policy-metadata.json"

# NOTE: never put a /* comment */ at the head of a capture_sql body — `bd sql`
# then returns "OK, 0 rows affected" with NO result set, and the parser HALTs.
# The work-item projections above use `issues UNION ALL wisps`.
capture_sql "schema.json" "
SELECT COALESCE((SELECT JSON_ARRAYAGG(row_json) FROM (
  SELECT JSON_OBJECT(
    'object', CONCAT(table_name, '.', column_name),
    'table_name', table_name,
    'column_name', column_name,
    'ordinal_position', ordinal_position,
    'data_type', data_type,
    'is_nullable', is_nullable
  ) AS row_json
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
  ORDER BY table_name, ordinal_position
) AS rows_json), JSON_ARRAY());
"

capture_sql "branches.json" "
SELECT COALESCE((SELECT JSON_ARRAYAGG(row_json) FROM (
  SELECT JSON_OBJECT('branch_name', name, 'head_hash', hash) AS row_json
  FROM dolt_branches
  ORDER BY name
) AS rows_json), JSON_ARRAY());
"

capture_sql "table-counts.json" "
SELECT COALESCE((SELECT JSON_ARRAYAGG(row_json) FROM (
  SELECT JSON_OBJECT('base_table_name', table_name, 'row_count', table_rows) AS row_json
  FROM information_schema.tables
  WHERE table_schema = DATABASE()
    AND table_type = 'BASE TABLE'
  ORDER BY table_name
) AS rows_json), JSON_ARRAY());
"

capture_sql "remotes.json" "
SELECT COALESCE((SELECT JSON_ARRAYAGG(row_json) FROM (
  SELECT JSON_OBJECT('remote_name', name, 'url', url, 'fetch_specs', fetch_specs) AS row_json
  FROM dolt_remotes
  ORDER BY name
) AS rows_json), JSON_ARRAY());
"

# both are enumeration intermediates, not inventory artifacts
rm -f "$output_dir/all-issues.json" "$output_dir/work-item-ids.json"

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
