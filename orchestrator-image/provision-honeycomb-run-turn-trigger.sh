#!/usr/bin/env bash
set -euo pipefail

api_key="${HONEYCOMB_CONFIG_KEY_LIVESPEC:-${HONEYCOMB_TEAM_KEY_LIVESPEC:-}}"
api_base="${HONEYCOMB_API_BASE:-https://api.honeycomb.io}"
dataset="${HONEYCOMB_FABRO_DATASET:-fabro}"
trigger_name="${HONEYCOMB_FABRO_RUN_TURN_TRIGGER_NAME:-Fabro run_turn dead-man}"
recipient_selector="${HONEYCOMB_OPERATOR_ALERT_RECIPIENT:-}"
dry_run="${DRY_RUN:-0}"

if [[ -z "${api_key}" ]]; then
  printf '%s\n' "HONEYCOMB_CONFIG_KEY_LIVESPEC is required." >&2
  exit 2
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

recipients_json="${tmpdir}/recipients.json"
triggers_json="${tmpdir}/triggers.json"
payload_json="${tmpdir}/trigger.json"

curl_json() {
  local method="$1"
  local url="$2"
  local data_arg=()
  if [[ "$#" -eq 3 ]]; then
    data_arg=(--data @"$3")
  fi
  curl --fail-with-body --silent --show-error \
    --request "${method}" \
    --url "${url}" \
    --header "X-Honeycomb-Team: ${api_key}" \
    --header "Content-Type: application/json" \
    "${data_arg[@]}"
}

curl_json GET "${api_base}/1/recipients" >"${recipients_json}"

recipient_id="$(
  python3 - "${recipients_json}" "${recipient_selector}" <<'PY'
import json
import sys

path, selector = sys.argv[1:]
with open(path, encoding="utf-8") as handle:
    recipients = json.load(handle)


def redact(value):
    if not value:
        return None
    if "@" not in value:
        return value
    local, domain = value.split("@", maxsplit=1)
    if len(local) <= 2:
        redacted_local = local[0] + "***" if local else "***"
    else:
        redacted_local = f"{local[0]}***{local[-1]}"
    return f"{redacted_local}@{domain}"


def describe(recipient):
    details = recipient.get("details") or {}
    parts = [
        f"id={recipient.get('id', '<missing>')}",
        f"type={recipient.get('type', '<missing>')}",
    ]
    for key in ("email_address", "name", "webhook_name", "slack_channel"):
        value = details.get(key)
        if value:
            display = redact(value) if key == "email_address" else value
            parts.append(f"{key}={display}")
    target = recipient.get("target")
    if target:
        parts.append(f"target={target}")
    return " ".join(parts)


def print_available():
    print("available Honeycomb recipients:", file=sys.stderr)
    for recipient in recipients:
        print(f"  - {describe(recipient)}", file=sys.stderr)


if not selector:
    print("HONEYCOMB_OPERATOR_ALERT_RECIPIENT is required.", file=sys.stderr)
    print("Set it to a Honeycomb recipient id, name, email address, webhook name, or Slack channel.", file=sys.stderr)
    print_available()
    raise SystemExit(1)

for recipient in recipients:
    details = recipient.get("details") or {}
    candidates = {
        recipient.get("id"),
        recipient.get("target"),
        details.get("email_address"),
        details.get("name"),
        details.get("webhook_name"),
        details.get("slack_channel"),
    }
    if selector in candidates:
        print(recipient["id"])
        raise SystemExit(0)

print(f"no Honeycomb recipient matched {selector!r}", file=sys.stderr)
print_available()
raise SystemExit(1)
PY
)"

python3 - "${payload_json}" "${trigger_name}" "${recipient_id}" <<'PY'
import json
import sys

path, trigger_name, recipient_id = sys.argv[1:]
payload = {
    "name": trigger_name,
    "description": (
        "Dead-man trigger for the livespec Fabro dataset: fires when no "
        "run_turn spans arrive over the trailing 10 minutes."
    ),
    "tags": [
        {"key": "owner", "value": "livespec"},
        {"key": "work-item", "value": "bd-ib-ehrdid"},
    ],
    "threshold": {"op": "<=", "value": 0, "exceeded_limit": 1},
    "frequency": 600,
    "alert_type": "on_change",
    "disabled": False,
    "recipients": [{"id": recipient_id}],
    "auto_investigate": False,
    "query": {
        "calculations": [{"op": "COUNT"}],
        "filters": [{"column": "name", "op": "=", "value": "run_turn"}],
        "filter_combination": "AND",
        "time_range": 600,
    },
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

if [[ "${dry_run}" == "1" ]]; then
  cat "${payload_json}"
  exit 0
fi

curl_json GET "${api_base}/1/triggers/${dataset}" >"${triggers_json}"

trigger_id="$(
  python3 - "${triggers_json}" "${trigger_name}" <<'PY'
import json
import sys

path, trigger_name = sys.argv[1:]
with open(path, encoding="utf-8") as handle:
    triggers = json.load(handle)

for trigger in triggers:
    if trigger.get("name") == trigger_name:
        print(trigger["id"])
        raise SystemExit(0)
PY
)"

if [[ -n "${trigger_id}" ]]; then
  curl_json PUT "${api_base}/1/triggers/${dataset}/${trigger_id}" "${payload_json}" >/dev/null
  printf 'updated Honeycomb trigger %s on dataset %s\n' "${trigger_id}" "${dataset}"
else
  curl_json POST "${api_base}/1/triggers/${dataset}" "${payload_json}" >/dev/null
  printf 'created Honeycomb trigger %s on dataset %s\n' "${trigger_name}" "${dataset}"
fi
