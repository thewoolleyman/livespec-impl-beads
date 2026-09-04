#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  printf '%s\n' "usage: $0 CLIENT_KEY RECEIPT_PATH" >&2
  exit 64
fi

client_key=$1
receipt_path=$2

case "$receipt_path" in
  "${RECEIPT_ROOT:-__missing_receipt_root__}"/*) ;;
  *)
    printf '%s\n' "HALT: anchor receipt must be under RECEIPT_ROOT" >&2
    exit 70
    ;;
esac

CLIENT_KEY=$client_key RECEIPT_PATH=$receipt_path python3 - <<'PY'
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_KEYS = {
    "dolt.auto-start",
    "dolt.mode",
    "dolt.server-host",
    "dolt.server-port",
    "dolt.server-user",
    "dolt.database",
    "dolt.prefix",
}


def halt(message: str) -> None:
    print(f"HALT: {message}", file=sys.stderr)
    raise SystemExit(70)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_pointer(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if ":" not in line:
            halt("pointer contains unparsable line")
        key, value = line.split(":", 1)
        rows[key.strip()] = value.strip()
    dolt_keys = {key for key in rows if key.startswith("dolt.")}
    if dolt_keys != EXPECTED_KEYS:
        halt("pointer contains extra dolt key")
    return rows


client_key = os.environ["CLIENT_KEY"]
manifest = json.loads(Path(os.environ["TOPOLOGY_MANIFEST"]).read_text())
clients = [row for row in manifest["clients"] if row["client_key"] == client_key]
if len(clients) != 1:
    halt("topology manifest must resolve exactly one client row")
client = clients[0]
client_dir = Path(client["client_dir"]).resolve()
if str(client_dir) != str(Path(client["client_dir"])):
    halt("client directory must be canonical realpath")
all_dirs = [str(Path(row["client_dir"]).resolve()) for row in manifest["clients"]]
if all_dirs.count(str(client_dir)) != 1:
    halt("duplicate client-directory realpath")
pointer_path = client_dir / ".beads" / "config.yaml"
if not pointer_path.is_file():
    halt("pointer missing")
pointer_bytes = pointer_path.read_bytes()
if not pointer_bytes.endswith(b"\n"):
    halt("pointer must end with one newline")
pointer_hash = hashlib.sha256(pointer_bytes).hexdigest()
pointer = parse_pointer(pointer_path)
if pointer_hash != client["pointer_sha256"]:
    halt("pointer hash mismatch")
if pointer["dolt.server-host"] != "127.0.0.1" or pointer["dolt.server-port"] != "13307":
    halt("pointer endpoint mismatch")
if pointer["dolt.database"] != client["database"] or pointer["dolt.server-user"] != client["sql_user"]:
    halt("pointer identity mismatch")
metadata_path = client_dir / ".beads" / "metadata.json"
metadata = {"state": "absent", "sha256": None}
if metadata_path.exists():
    metadata = {"state": "present", "sha256": sha256(metadata_path)}
if metadata != client["metadata"]:
    halt("metadata state/hash mismatch")
probe = Path(manifest["anchor_probe"])
dependency_lock = Path(manifest["dependency_lock"])
with_client = Path(manifest["with_client"])
if sha256(probe) != manifest["anchor_probe_sha256"]:
    halt("anchor probe hash mismatch")
if sha256(dependency_lock) != manifest["dependency_lock_sha256"]:
    halt("dependency lock hash mismatch")
if sha256(with_client) != manifest["with_client_sha256"]:
    halt("with-client hash mismatch")
env = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "BEADS_DOLT_PASSWORD": os.environ["BEADS_DOLT_PASSWORD"],
}
result = subprocess.run(
    [
        str(probe),
        "--host",
        "127.0.0.1",
        "--port",
        "13307",
        "--user",
        client["sql_user"],
        "--database",
        client["database"],
    ],
    text=True,
    capture_output=True,
    env=env,
    check=False,
)
if result.returncode != 0:
    halt("anchor probe failed")
identity = json.loads(result.stdout)
expected_user = client["sql_user"] + "@%"
if identity["database"] != client["database"] or identity["current_user"] != expected_user:
    halt("probe identity mismatch")
if identity["port"] != 13307 or identity["tcp_peer"] != "127.0.0.1:13307":
    halt("probe endpoint mismatch")
if identity["server_fingerprint"] != manifest["expected_server_fingerprint"]:
    halt("server fingerprint mismatch")
receipt = {
    "schema": "livespec.beads_v112_rehearsal.anchor_receipt.v1",
    "client_key": client_key,
    "client_dir_realpath": str(client_dir),
    "database": client["database"],
    "sql_user": client["sql_user"],
    "pointer": {
        "sha256": pointer_hash,
        "key_count": len(pointer),
        "canonical_keys": sorted(pointer),
    },
    "metadata": metadata,
    "wrapper_sha256": manifest["with_client_sha256"],
    "anchor_probe_sha256": manifest["anchor_probe_sha256"],
    "dependency_lock_sha256": manifest["dependency_lock_sha256"],
    "credential_byte_count": int(os.environ["BEADS112_CREDENTIAL_BYTE_COUNT"]),
    "query": "SELECT DATABASE(), CURRENT_USER(), @@hostname, @@port",
    "query_sha256": "0f334703b52dea71b6c7184692f245094b4c93cbf1d61bcee36fc6c3531a5b36",
    "read_only_transaction": True,
    "statement_count": 1,
    "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "finished_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "probe_exit": result.returncode,
    "identity": identity,
    "tcp_peer": identity["tcp_peer"],
    "server_fingerprint": identity["server_fingerprint"],
    "following_command": {
        "category": os.environ.get("BEADS112_COMMAND_CATEGORY", "wrapped-command"),
        "sequence": int(os.environ.get("BEADS112_COMMAND_SEQUENCE", "1")),
    },
}
Path(os.environ["RECEIPT_PATH"]).write_text(json.dumps(receipt, sort_keys=True) + "\n")
PY
