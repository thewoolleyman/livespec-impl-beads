#!/bin/sh
set -eu

if [ "$#" -lt 2 ]; then
  printf '%s\n' "usage: $0 CLIENT_KEY COMMAND..." >&2
  exit 64
fi

client_key=$1
shift

for name in $(env | sed -n 's/=.*//p'); do
  case "$name" in
    BEADS_DOLT_PASSWORD | BEADS_DOLT_PASSWORD_* | DOLT_PASSWORD | DOLT_ROOT_PASSWORD | MYSQL_PWD)
      printf '%s\n' "HALT: parent environment already carries $name" >&2
      exit 70
      ;;
    LIVESPEC_ENV_WRAPPER | WITH_LIVESPEC_ENV | LIVESPEC_BD_PATH | OP_SERVICE_ACCOUNT_TOKEN)
      printf '%s\n' "HALT: parent environment carries forbidden wrapper marker $name" >&2
      exit 70
      ;;
  esac
done

: "${RUN_ID:?RUN_ID required}"
: "${RUN_ROOT:?RUN_ROOT required}"
: "${RECEIPT_ROOT:?RECEIPT_ROOT required}"
: "${TOPOLOGY_MANIFEST:?TOPOLOGY_MANIFEST required}"

if [ -z "${BEADS112_CREDENTIAL_HELPER:-}" ] || [ ! -x "$BEADS112_CREDENTIAL_HELPER" ]; then
  printf '%s\n' "HALT: credential helper required" >&2
  exit 70
fi

resolved=$(
  CLIENT_KEY=$client_key TOPOLOGY_MANIFEST=$TOPOLOGY_MANIFEST python3 - <<'PY'
import json
import os
from pathlib import Path

client_key = os.environ["CLIENT_KEY"]
manifest = json.loads(Path(os.environ["TOPOLOGY_MANIFEST"]).read_text())
clients = [row for row in manifest["clients"] if row["client_key"] == client_key]
if len(clients) != 1:
    raise SystemExit("HALT: topology manifest must resolve exactly one client row")
client = clients[0]
print(client["sql_user"])
PY
) || {
  printf '%s\n' "$resolved" >&2
  exit 70
}

sql_user=$(printf '%s\n' "$resolved" | sed -n '1p')
if [ -z "$sql_user" ]; then
  printf '%s\n' "HALT: topology manifest must resolve exactly one client row" >&2
  exit 70
fi

if ! secret=$(sh -eu "$BEADS112_CREDENTIAL_HELPER" "$client_key" "$sql_user"); then
  printf '%s\n' "HALT: credential-source/user mismatch" >&2
  exit 70
fi
case "$secret" in
  *'
'*)
    printf '%s\n' "HALT: credential-source/user mismatch" >&2
    exit 70
    ;;
esac
if [ -z "$secret" ]; then
  printf '%s\n' "HALT: isolated credential missing" >&2
  exit 70
fi

credential_byte_count=$(env -i BEADS_DOLT_PASSWORD=$secret printenv BEADS_DOLT_PASSWORD | wc -c | tr -d ' ')
if [ "$credential_byte_count" -le 0 ]; then
  printf '%s\n' "HALT: isolated credential missing" >&2
  exit 70
fi

anchor=${ASSERT_CLIENT_ANCHOR:-$(dirname "$0")/assert-client-anchor.sh}
sequence=${BEADS112_COMMAND_SEQUENCE:-1}
category=${BEADS112_COMMAND_CATEGORY:-wrapped-command}
receipt="$RECEIPT_ROOT/anchor-${sequence}-${category}.json"
BEADS_DOLT_PASSWORD=$secret \
BEADS112_CREDENTIAL_BYTE_COUNT=$credential_byte_count \
BEADS112_COMMAND_CATEGORY=$category \
BEADS112_COMMAND_SEQUENCE=$sequence \
  "$anchor" "$client_key" "$receipt"

exec env -i \
  PATH="${PATH:-/usr/bin:/bin}" \
  HOME="${HOME:-/tmp}" \
  BEADS_DOLT_PASSWORD="$secret" \
  "$@"
