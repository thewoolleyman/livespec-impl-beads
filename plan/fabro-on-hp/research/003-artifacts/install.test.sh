#!/usr/bin/env bash
# Exercise install.sh's pure guards without root and without touching a host.
#
#   ./install.test.sh
#
# Covers require_host_matches, which the README lists as unexercised: it is the
# guard that stops hp's unit being installed on vps or vice versa, and getting
# it wrong is silent — the wrong unit installs and starts fine, pointed at the
# wrong checkout and the wrong canonical host.
#
# The real function is sourced and run unmodified. `hostname` is stubbed via a
# PATH shim rather than by parameterising the function, so the shipped code
# path is what gets tested.
#
# NOTE on harness design, because the obvious version silently lies. Sourcing
# install.sh with NO argument trips its `${1:?usage}` and exits before any
# function is defined — so a naive harness sees a non-zero status and scores
# every "refuses" case as a pass while never reaching the guard at all. The
# first draft of this file did exactly that: 2 real failures and 2 false
# passes. install.sh is therefore sourced WITH a real hosts/*.env so its
# top-level setup completes, and FABRO_CANONICAL_HOST is overridden AFTERWARDS
# (the source would otherwise reset it). The positive cases are what prove the
# harness reaches the guard; without them the negatives are worthless.

set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PASS=0
FAIL=0

report() {
    local ok="$1" name="$2" detail="${3:-}"
    if [[ "${ok}" == "yes" ]]; then
        PASS=$((PASS + 1)); printf 'ok   %s\n' "${name}"
    else
        FAIL=$((FAIL + 1)); printf 'FAIL %s%s\n' "${name}" "${detail:+ — ${detail}}"
    fi
}

# Run require_host_matches with a stubbed hostname and a chosen canonical host.
# Returns the guard's own exit status.
run_guard() {
    local fake_host="$1" canonical="$2" seed_env="$3" shim rc
    shim="$(mktemp -d)"
    cat > "${shim}/hostname" <<EOF
#!/usr/bin/env bash
printf '%s\n' "${fake_host}"
EOF
    chmod +x "${shim}/hostname"
    (
        PATH="${shim}:${PATH}"
        # Source WITH an argument so install.sh's top-level setup completes and
        # its functions get defined; see the note at the top of this file.
        # shellcheck source=/dev/null
        source "${SCRIPT_DIR}/install.sh" "${seed_env}"
        # Override AFTER sourcing: the source sets this from the seed env file.
        export FABRO_CANONICAL_HOST="${canonical}"
        require_host_matches
    ) >/dev/null 2>&1
    rc=$?
    rm -rf "${shim}"
    return "${rc}"
}

SEED="${SCRIPT_DIR}/hosts/vps.env"

# --- the guard accepts a matching host -------------------------------------
# These also prove the harness actually reaches the guard.
for pair in \
    "hp-xubuntu|hp-xubuntu.perch-rudd.ts.net:32276" \
    "vps|vps.perch-rudd.ts.net:32276"
do
    host="${pair%%|*}"; canon="${pair#*|}"
    if run_guard "${host}" "${canon}" "${SEED}"; then
        report yes "accepts ${host} against ${canon}"
    else
        report no "accepts ${host} against ${canon}" "guard refused a matching host"
    fi
done

# --- the guard refuses a cross-host install --------------------------------
# The case that matters: installing hp's values while standing on vps.
for pair in \
    "vps|hp-xubuntu.perch-rudd.ts.net:32276" \
    "hp-xubuntu|vps.perch-rudd.ts.net:32276"
do
    host="${pair%%|*}"; canon="${pair#*|}"
    if run_guard "${host}" "${canon}" "${SEED}"; then
        report no "refuses ${host} against ${canon}" "guard ALLOWED a cross-host install"
    else
        report yes "refuses ${host} against ${canon}"
    fi
done

# --- rendering stays consistent with the host files ------------------------
# Each hosts/<name>.env must render a unit whose WorkingDirectory matches the
# checkout root that same file declares. A copy-paste slip between the two is
# otherwise invisible until the installer's cwd assertion fails at start.
for env_file in "${SCRIPT_DIR}"/hosts/*.env; do
    name="$(basename "${env_file}" .env)"
    checkout="$(grep -E '^FABRO_HOST_CHECKOUT=' "${env_file}" | cut -d= -f2-)"
    rendered_wd="$("${SCRIPT_DIR}/render-unit.sh" "${env_file}" \
        | grep -E '^WorkingDirectory=' | cut -d= -f2-)"
    if [[ -n "${checkout}" && "${checkout}" == "${rendered_wd}" ]]; then
        report yes "${name}: WorkingDirectory matches FABRO_HOST_CHECKOUT"
    else
        report no "${name}: WorkingDirectory matches FABRO_HOST_CHECKOUT" \
            "env=${checkout:-<unset>} rendered=${rendered_wd:-<unset>}"
    fi
done

printf '\n%d passed, %d failed\n' "${PASS}" "${FAIL}"
[[ "${FAIL}" -eq 0 ]]
