#!/usr/bin/env bash
# Compare a factory host's RESOLVED fabro settings against its expected set.
#
#   ./check-settings.sh hosts/hp-xubuntu.env      # run ON that host
#
# Why resolved settings rather than the settings.toml file: a missing table
# does not read as missing, it reads as the built-in default, and the server
# reports no warning. hp silently ran max_concurrent_runs=5 against vps's 10
# for exactly that reason (bd-ib-l3nptz.16) -- a file diff would have shown an
# absent section and been easy to dismiss; a resolved-value diff shows a
# number that is wrong.

set -euo pipefail

# Read `url` from settings.toml's [cli.target] table.
#
# Extracted as a function so it can be tested against fixtures: it is a
# hand-rolled TOML reader, and the file it parses contains a `url` key in
# several OTHER tables ([server.api], [server.web]). Matching the wrong one
# would compare the right key against the wrong value and report `ok`.
#
# The awk state machine: arm on the [cli.target] header, disarm on ANY
# subsequent table header (so sibling tables cannot leak in), and while armed
# take the first `url =` line, stripping the key and the surrounding quotes.
read_cli_target_url() {
    local toml="$1"
    awk '
        /^\[cli\.target\]/ { in_table = 1; next }
        /^\[/                { in_table = 0 }
        in_table && /^url[[:space:]]*=/ {
            gsub(/^url[[:space:]]*=[[:space:]]*"|"$/, "")
            print
            exit
        }
    ' "${toml}"
}

# Sourceable for testing: the runtime body below runs only on direct execution.
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return 0
fi

HOST_ENV="${1:?usage: check-settings.sh <hosts/NAME.env>}"
EXPECTED="${HOST_ENV%.env}.settings.expected"

[[ -f "${HOST_ENV}" ]] || { echo "ERROR: no such host env file: ${HOST_ENV}" >&2; exit 2; }
[[ -f "${EXPECTED}" ]] || { echo "ERROR: no expectations file: ${EXPECTED}" >&2; exit 2; }
command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 2; }

set -a
# shellcheck source=/dev/null
source "${HOST_ENV}"
set +a
: "${FABRO_HOST_HOME:?host env must set FABRO_HOST_HOME}"
: "${FABRO_CANONICAL_HOST:?host env must set FABRO_CANONICAL_HOST}"

SERVER_ENV="${FABRO_HOST_HOME}/.fabro/storage/server.env"
[[ -r "${SERVER_ENV}" ]] || { echo "ERROR: cannot read ${SERVER_ENV} (run as the service account)" >&2; exit 2; }

# Probe-only: the token is used, never printed.
token="$(grep -E '^FABRO_DEV_TOKEN=' "${SERVER_ENV}" | cut -d= -f2-)"
[[ -n "${token}" ]] || { echo "ERROR: FABRO_DEV_TOKEN missing from ${SERVER_ENV}" >&2; exit 2; }

settings="$(curl -fsS --max-time 10 \
    -H "Authorization: Bearer ${token}" \
    -H "Host: ${FABRO_CANONICAL_HOST}" \
    "http://127.0.0.1:32276/api/v1/settings")" || {
    echo "ERROR: could not read resolved settings from the local fabro server" >&2
    exit 1
}

status=0
while IFS= read -r line; do
    [[ "${line}" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line//[[:space:]]/}" ]] && continue
    key="${line%%=*}"
    want="${line#*=}"
    # Dotted key -> jq path. The API nests everything under a settings object
    # on some builds and at the root on others; try both.
    got="$(jq -r --arg k "${key}" '
        [ (.settings? // empty), . ]
        | map(getpath($k | split("."))? // empty)
        | map(select(. != null))
        | first // "<<missing>>"
    ' <<<"${settings}")"
    if [[ "${got}" != "${want}" ]]; then
        printf 'DRIFT  %-46s expected=%-42s actual=%s\n' "${key}" "${want}" "${got}"
        status=1
    else
        printf 'ok     %-46s %s\n' "${key}" "${got}"
    fi
done < "${EXPECTED}"

# cli.target is NOT exposed by /api/v1/settings -- it is client-side config
# read straight from settings.toml. It is checked separately rather than
# dropped, because it is load-bearing: auth.json is keyed by this URL, so
# pointing it at the tailnet name silently invalidates the stored credential.
settings_toml="${FABRO_HOST_HOME}/.fabro/settings.toml"
if [[ -r "${settings_toml}" ]]; then
    want_cli="${FABRO_CLI_TARGET_URL:-http://127.0.0.1:32276}"
    got_cli="$(read_cli_target_url "${settings_toml}")"
    if [[ "${got_cli}" != "${want_cli}" ]]; then
        printf 'DRIFT  %-46s expected=%-42s actual=%s\n' "cli.target.url" "${want_cli}" "${got_cli:-<<missing>>}"
        status=1
    else
        printf 'ok     %-46s %s\n' "cli.target.url" "${got_cli}"
    fi
else
    echo "WARN   cli.target.url could not be checked: ${settings_toml} unreadable" >&2
fi

[[ ${status} -eq 0 ]] && echo "[ok] ${FABRO_CANONICAL_HOST} matches ${EXPECTED##*/}"
exit "${status}"
