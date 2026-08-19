#!/usr/bin/env bash
# Install/refresh the Fabro dark-factory systemd unit on ANY factory host.
#
#   sudo ./install.sh hosts/hp-xubuntu.env
#
# Derived from vps-info/services/fabro-server/install.sh, which hardcoded the
# vps host throughout. Every vps-specific literal is now read from the host
# env file, so hp and vps run the same installer.
#
# What is NOT versioned, deliberately: ~/.fabro/storage/server.env holds a
# host-generated SESSION_SECRET and FABRO_DEV_TOKEN. This installer REQUIRES
# that file and never creates it.

set -euo pipefail

HOST_ENV="${1:?usage: sudo install.sh <hosts/NAME.env>}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
UNIT_NAME="fabro-server.service"
UNIT_DEST="/etc/systemd/system/${UNIT_NAME}"
DROPIN_DIR="/etc/systemd/system/${UNIT_NAME}.d"
OTEL_SRC="${SCRIPT_DIR}/otel.conf"
VERIFY_SRC="${SCRIPT_DIR}/fabro-server-verify-web"
VERIFY_DEST="/usr/local/libexec/fabro-server-verify-web"
HEALTH_URL="http://127.0.0.1:32276/api/v1/health"

[[ -f "${HOST_ENV}" ]] || { echo "ERROR: no such host env file: ${HOST_ENV}" >&2; exit 2; }
set -a
# shellcheck source=/dev/null
source "${HOST_ENV}"
set +a
: "${FABRO_HOST_USER:?host env must set FABRO_HOST_USER}"
: "${FABRO_HOST_HOME:?host env must set FABRO_HOST_HOME}"
: "${FABRO_HOST_CHECKOUT:?host env must set FABRO_HOST_CHECKOUT}"

FABRO_BIN="${FABRO_HOST_HOME}/.fabro/bin/fabro"
SERVER_RECORD="${FABRO_HOST_HOME}/.fabro/storage/server.json"
SERVER_ENV="${FABRO_HOST_HOME}/.fabro/storage/server.env"

require_root() {
    [[ ${EUID} -eq 0 ]] || { echo "ERROR: must be run as root (try: sudo $0 ${HOST_ENV})" >&2; exit 1; }
}

require_host_matches() {
    # Refuse to install hp's unit on vps, or vice versa. The host env file
    # names the canonical host; its leading label must be this machine.
    local expected="${FABRO_CANONICAL_HOST%%.*}"
    local actual; actual="$(hostname -s)"
    [[ "${expected}" == "${actual}" ]] || {
        echo "ERROR: ${HOST_ENV} targets '${expected}' but this host is '${actual}'" >&2
        exit 2
    }
}

require_inputs() {
    for path in "${OTEL_SRC}" "${VERIFY_SRC}" "${FABRO_BIN}" "${SERVER_ENV}"; do
        [[ -f "${path}" ]] || { echo "ERROR: required file missing: ${path}" >&2; exit 2; }
    done
    [[ -x "${FABRO_BIN}" ]] || { echo "ERROR: Fabro binary is not executable: ${FABRO_BIN}" >&2; exit 2; }
    [[ -d "${FABRO_HOST_CHECKOUT}" ]] || { echo "ERROR: checkout root missing: ${FABRO_HOST_CHECKOUT}" >&2; exit 2; }
    grep -qE '^SESSION_SECRET=.+' "${SERVER_ENV}" || { echo "ERROR: SESSION_SECRET is missing from ${SERVER_ENV}" >&2; exit 2; }
    grep -qE '^FABRO_DEV_TOKEN=.+' "${SERVER_ENV}" || { echo "ERROR: FABRO_DEV_TOKEN is missing from ${SERVER_ENV}" >&2; exit 2; }
    command -v curl >/dev/null
    command -v jq >/dev/null
}

require_quiet_server() {
    curl -fsS --max-time 2 "${HEALTH_URL}" -o /dev/null || return 0
    local running
    running="$(sudo -u "${FABRO_HOST_USER}" env HOME="${FABRO_HOST_HOME}" "${FABRO_BIN}" --json ps)"
    if [[ "$(jq 'length' <<<"${running}")" -ne 0 ]]; then
        echo "ERROR: Fabro has active runs; refusing to interrupt them" >&2
        jq . <<<"${running}" >&2
        exit 3
    fi
}

trusted_fabro_executable() {
    local proc_exe="$1" expected="$2" candidate
    [[ "${proc_exe}" -ef "${expected}" ]] && return 0
    while IFS= read -r -d '' candidate; do
        [[ "${proc_exe}" -ef "${candidate}" ]] && return 0
    done < <(find "$(dirname -- "${expected}")" -maxdepth 1 -type f -name 'fabro.*' -print0)
    return 1
}

stop_legacy_daemon() {
    systemctl is-active --quiet "${UNIT_NAME}" && return 0
    [[ -f "${SERVER_RECORD}" ]] || return 0

    local pid exe expected deadline
    pid="$(jq -r '.pid // empty' "${SERVER_RECORD}")"
    [[ "${pid}" =~ ^[0-9]+$ ]] || return 0
    kill -0 "${pid}" 2>/dev/null || return 0

    exe="$(readlink -f "/proc/${pid}/exe" 2>/dev/null || true)"
    expected="$(readlink -f "${FABRO_BIN}")"
    if ! trusted_fabro_executable "/proc/${pid}/exe" "${expected}"; then
        echo "ERROR: refusing to stop PID ${pid}; executable is ${exe}, and no trusted Fabro binary matches its inode" >&2
        exit 4
    fi

    echo "[+] stopping legacy Fabro daemon PID ${pid}"
    kill -TERM "${pid}"
    deadline=$((SECONDS + 90))
    while kill -0 "${pid}" 2>/dev/null; do
        ((SECONDS >= deadline)) && { echo "ERROR: legacy Fabro daemon PID ${pid} did not stop within 90 seconds" >&2; exit 5; }
        sleep 1
    done
}

install_files() {
    install -d -o root -g root -m 0755 "$(dirname -- "${VERIFY_DEST}")"
    install -o root -g root -m 0755 "${VERIFY_SRC}" "${VERIFY_DEST}"
    # Rendered, not copied: this is the whole point of the parameterization.
    "${SCRIPT_DIR}/render-unit.sh" "${HOST_ENV}" > "${UNIT_DEST}.tmp"
    install -o root -g root -m 0644 "${UNIT_DEST}.tmp" "${UNIT_DEST}"
    rm -f "${UNIT_DEST}.tmp"
    install -d -o root -g root -m 0755 "${DROPIN_DIR}"
    install -o root -g root -m 0644 "${OTEL_SRC}" "${DROPIN_DIR}/otel.conf"
    # Supersede the hand-made drop-in that predates the unit carrying this value.
    rm -f "${DROPIN_DIR}/verify-timeout-override.conf"
    systemctl daemon-reload
}

start_and_verify() {
    systemctl enable "${UNIT_NAME}"
    systemctl restart "${UNIT_NAME}"
    if ! systemctl is-active --quiet "${UNIT_NAME}"; then
        systemctl status --no-pager "${UNIT_NAME}" >&2 || true
        exit 6
    fi
    FABRO_CANONICAL_HOST="${FABRO_CANONICAL_HOST}" "${VERIFY_DEST}"

    local pid cwd
    pid="$(systemctl show -p MainPID --value "${UNIT_NAME}")"
    cwd="$(readlink -f "/proc/${pid}/cwd")"
    [[ "${cwd}" == "${FABRO_HOST_CHECKOUT}" ]] || {
        echo "ERROR: Fabro has unstable working directory: ${cwd} (expected ${FABRO_HOST_CHECKOUT})" >&2
        exit 7
    }
    echo "[ok] ${UNIT_NAME} is enabled, supervised, and serving the web console on ${FABRO_CANONICAL_HOST}"
}

main() {
    require_root
    require_host_matches
    require_inputs
    require_quiet_server
    stop_legacy_daemon
    install_files
    start_and_verify
}

main "$@"
