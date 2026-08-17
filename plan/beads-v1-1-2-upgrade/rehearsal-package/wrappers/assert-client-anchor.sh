#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  printf '%s\n' "usage: $0 CLIENT_KEY RECEIPT_PATH" >&2
  exit 64
fi

client_key=$1
receipt_path=$2

case "$client_key" in
  *"${RUN_ID:-__missing_run_id__}"*) ;;
  *)
    printf '%s\n' "HALT: client key must contain RUN_ID" >&2
    exit 70
    ;;
esac

case "$receipt_path" in
  "${RECEIPT_ROOT:-__missing_receipt_root__}"/*) ;;
  *)
    printf '%s\n' "HALT: anchor receipt must be under RECEIPT_ROOT" >&2
    exit 70
    ;;
esac

printf '%s\n' "planned anchor assertion for $client_key" > "$receipt_path"
