#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  printf '%s\n' "usage: $0 RECEIPT_ROOT SANITIZED_ENV_NAMES" >&2
  exit 64
fi

if grep -R "BEADS_DOLT_PASSWORD=.*" "$1" >/dev/null 2>&1; then
  printf '%s\n' "HALT: receipt root contains secret-looking value" >&2
  exit 70
fi
printf '{"schema":"livespec.beads_v112_rehearsal.secret_scan_receipt.v1","sanitized_env_names":"%s"}\n' "$2"
