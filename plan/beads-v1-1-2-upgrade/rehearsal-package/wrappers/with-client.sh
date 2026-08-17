#!/bin/sh
set -eu

if [ "$#" -lt 2 ]; then
  printf '%s\n' "usage: $0 CLIENT_KEY COMMAND..." >&2
  exit 64
fi

client_key=$1
shift

case "${BEADS_DOLT_PASSWORD+x}" in
  x)
    printf '%s\n' "HALT: parent environment already carries BEADS_DOLT_PASSWORD" >&2
    exit 70
    ;;
esac

for name in LIVESPEC_ENV_WRAPPER WITH_LIVESPEC_ENV LIVESPEC_BD_PATH; do
  eval "value=\${$name-}"
  if [ -n "$value" ]; then
    printf '%s\n' "HALT: parent environment carries forbidden wrapper marker $name" >&2
    exit 70
  fi
done

case "$client_key" in
  *"${RUN_ID:-__missing_run_id__}"*) ;;
  *)
    printf '%s\n' "HALT: client key must contain RUN_ID" >&2
    exit 70
    ;;
esac

credential_length=${BEADS112_ISOLATED_CREDENTIAL_LENGTH:-}
if [ -z "$credential_length" ]; then
  printf '%s\n' "HALT: isolated credential length marker missing" >&2
  exit 70
fi

BEADS_DOLT_PASSWORD=$(printf '%*s' "$credential_length" "" | tr ' ' x)
export BEADS_DOLT_PASSWORD
exec "$@"
