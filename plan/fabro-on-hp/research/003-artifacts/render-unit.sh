#!/usr/bin/env bash
# Render fabro-server.service.in for one host to stdout.
#
#   ./render-unit.sh hosts/hp-xubuntu.env
#
# Kept separate from install.sh so the parameterization can be verified
# without root and without touching a live host: render for a host and diff
# the result against that host's installed unit.

set -euo pipefail

HOST_ENV="${1:?usage: render-unit.sh <hosts/NAME.env>}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
TEMPLATE="${SCRIPT_DIR}/fabro-server.service.in"

[[ -f "${HOST_ENV}" ]] || { echo "ERROR: no such host env file: ${HOST_ENV}" >&2; exit 2; }
[[ -f "${TEMPLATE}" ]] || { echo "ERROR: template missing: ${TEMPLATE}" >&2; exit 2; }

REQUIRED=(
    FABRO_HOST_USER
    FABRO_HOST_GROUP
    FABRO_HOST_HOME
    FABRO_HOST_CHECKOUT
    FABRO_CANONICAL_HOST
    FABRO_WEB_VERIFY_ATTEMPTS
)

set -a
# shellcheck source=/dev/null
source "${HOST_ENV}"
set +a

for name in "${REQUIRED[@]}"; do
    [[ -n "${!name:-}" ]] || { echo "ERROR: ${HOST_ENV} does not set ${name}" >&2; exit 3; }
done

# Strip the template's own explanatory header FIRST: it documents the
# @NAME@ placeholder convention literally, and would otherwise trip the
# unsubstituted-placeholder guard below.
rendered="$(sed -n '/^\[Unit\]/,$p' "${TEMPLATE}")"
for name in "${REQUIRED[@]}"; do
    rendered="${rendered//@${name}@/${!name}}"
done

# Fail loudly rather than installing a unit with an unsubstituted placeholder.
if grep -qE '@[A-Z_]+@' <<<"${rendered}"; then
    echo "ERROR: unsubstituted placeholders remain:" >&2
    grep -oE '@[A-Z_]+@' <<<"${rendered}" | sort -u >&2
    exit 4
fi

printf '%s\n' "${rendered}"
