#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  printf '%s\n' "usage: $0 CLIENT_KEY OUTPUT_DIR COMMAND_CATEGORY" >&2
  exit 64
fi

client_key=$1
output_dir=$2
category=$3

case "$output_dir" in
  "${RECEIPT_ROOT:-__missing_receipt_root__}"/*) ;;
  *)
    printf '%s\n' "HALT: inventory output must be under RECEIPT_ROOT" >&2
    exit 70
    ;;
esac

mkdir -p "$output_dir"
printf '{"client_key":"%s","command_category":"%s","planned_only":true}\n' \
  "$client_key" "$category" > "$output_dir/client-anchor.json"
