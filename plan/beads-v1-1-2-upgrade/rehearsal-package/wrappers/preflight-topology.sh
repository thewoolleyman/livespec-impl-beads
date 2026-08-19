#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  printf '%s\n' "usage: $0 TOPOLOGY_MANIFEST RUN_ID RUN_ROOT" >&2
  exit 64
fi

python3 - "$1" "$2" "$3" <<'PY'
import json
import re
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
run_id = sys.argv[2]
run_root = Path(sys.argv[3])
if not re.fullmatch(r"[0-9]{8}t[0-9]{6}z", run_id):
    raise SystemExit("HALT: invalid RUN_ID")
if run_root.exists() or run_root.is_symlink():
    raise SystemExit("HALT: RUN_ROOT must not exist")
clients = manifest.get("clients", [])
realpaths = [str(Path(row["client_dir"]).resolve()) for row in clients]
users = [row["sql_user"] for row in clients]
databases = [row["database"] for row in clients]
if len(realpaths) != len(set(realpaths)):
    raise SystemExit("HALT: duplicate client-directory realpath")
if len(users) != len(set(users)):
    raise SystemExit("HALT: duplicate SQL user")
if any(run_id not in value for value in [*users, *databases]):
    raise SystemExit("HALT: topology name missing RUN_ID")
print(json.dumps({"schema": "livespec.beads_v112_rehearsal.topology_preflight.v1"}, sort_keys=True))
PY
