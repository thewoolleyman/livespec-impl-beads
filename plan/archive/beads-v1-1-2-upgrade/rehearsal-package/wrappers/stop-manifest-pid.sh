#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  printf '%s\n' "usage: $0 TOPOLOGY_MANIFEST RECEIPT_PATH" >&2
  exit 64
fi

python3 - "$1" "$2" <<'PY'
import json
import re
import sys
from pathlib import Path

# This receipt gates which process the stop boundary may kill, so it halts on a
# failed check. The earlier version read the pid_file PATH out of the manifest
# and published `pid_scope_verified: true` without opening it, without
# resolving a pid, and without establishing that the pid was the isolated
# server rather than the production one.

manifest = json.loads(Path(sys.argv[1]).read_text())
receipt = Path(sys.argv[2])
isolated = manifest.get("isolated_server", {})
pid_file_value = isolated.get("pid_file")

# Values that identify the isolated server's own state tree. A cmdline naming
# one of these is running out of the rehearsal's RUN_ROOT, not production.
isolated_markers = [
    str(isolated[key])
    for key in ("data_dir", "config_dir", "socket", "all_state_under")
    if isolated.get(key)
]

pid = None
pid_file_state = "absent"
cmdline = ""
process_state = "absent"
references_isolated_state = False
production_port_absent = False

if pid_file_value:
    pid_file = Path(pid_file_value)
    if pid_file.is_file():
        pid_file_state = "present"
        raw = pid_file.read_text().strip()
        if raw.isdigit() and int(raw) > 0:
            pid = int(raw)
            cmdline_path = Path("/proc") / str(pid) / "cmdline"
            if cmdline_path.is_file():
                process_state = "running"
                cmdline = cmdline_path.read_bytes().decode("utf-8", "replace").replace("\0", " ")
                references_isolated_state = any(marker in cmdline for marker in isolated_markers)
                # 13307 contains the digits 3307, so a substring test would
                # flag the isolated port as production. Match 3307 only when it
                # is not part of a longer number.
                production_port_absent = re.search(r"(?<![0-9])3307(?![0-9])", cmdline) is None

pid_scope_verified = (
    pid is not None
    and process_state == "running"
    and bool(isolated_markers)
    and references_isolated_state
    and production_port_absent
)

payload = {
    "schema": "livespec.beads_v112_rehearsal.stop_boundary_receipt.v1",
    "pid_file": pid_file_value,
    "pid_file_state": pid_file_state,
    "pid": pid,
    "process_state": process_state,
    "isolated_state_markers": isolated_markers,
    "cmdline_references_isolated_state": references_isolated_state,
    "production_port_absent_from_cmdline": production_port_absent,
    "pid_scope_verified": pid_scope_verified,
}
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps(payload, sort_keys=True) + "\n")

if not pid_scope_verified:
    raise SystemExit(
        "HALT: manifest pid is not provably the isolated server; refusing to name a stop target",
    )
PY
