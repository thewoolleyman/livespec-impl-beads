#!/bin/sh
set -eu

if [ "$#" -ne 5 ]; then
  printf '%s\n' "usage: $0 SHAPE CLIENT_KEY CLIENT_DIR BD112 RECEIPT_SCRIPT" >&2
  exit 64
fi

shape=$1
client_key=$2
client_dir=$3
bd112=$4
receipt_script=$5
: "${WITH_CLIENT:?WITH_CLIENT required}"

mkdir -p "$(dirname "$receipt_script")"
{
  printf '%s\n' '#!/bin/sh'
  printf '%s\n' 'set -eu'
  printf 'WITH_CLIENT=%s\n' "$WITH_CLIENT"
  printf 'CLIENT_KEY=%s\n' "$client_key"
  printf 'CLIENT_DIR=%s\n' "$client_dir"
  printf 'BD112=%s\n' "$bd112"
  cat <<'EOF'
parent_id="$("$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" create "rehearsal parent" --type epic --priority 2 --labels 'origin:rehearsal,intake:triaged,admission:manual' --metadata '{"rank":"m","origin":"rehearsal"}' --silent)"
child_id="$("$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" create "rehearsal child" --type task --priority 3 --labels 'acceptance:ai-then-human,factory-safety:needs-privileged-host' --metadata '{"acceptance_criteria":"round-trip","rank":"n"}' --silent)"
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" update "$child_id" --status active --type bug --set-metadata origin=rehearsal-update --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" dep add "$child_id" "$parent_id" --type discovered-from --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" comments add "$child_id" 'isolated v1.1.2 round-trip comment' --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" close "$child_id" --reason 'isolated v1.1.2 round-trip complete' --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" list --all --id "$parent_id,$child_id" --json
"$WITH_CLIENT" "$CLIENT_KEY" "$BD112" -C "$CLIENT_DIR" show "$child_id" --include-comments --json
EOF
} > "$receipt_script"
chmod 700 "$receipt_script"
printf '{"schema":"livespec.beads_v112_rehearsal.round_trip_script_receipt.v1","shape":"%s"}\n' "$shape"
