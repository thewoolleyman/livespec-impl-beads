#!/usr/bin/env bash
# Fixture tests for check-settings.sh's hand-rolled TOML reader.
#
#   ./check-settings.test.sh
#
# read_cli_target_url is the one piece of check-settings.sh that parses rather
# than compares, and it runs against a file where `url` appears in SEVERAL
# tables — [cli.target], [server.api], [server.web]. Matching the wrong one
# would compare the right key against the wrong value and print `ok`, which is
# the failure mode this whole artifact set exists to avoid.
#
# The real function is sourced, not reimplemented: check-settings.sh returns
# early when sourced, so only the function definition is evaluated.
#
# MUTATION-CHECKED, and it corrected an assumption. Deleting the awk's
# table-disarm rule (`/^\[/ { in_table = 0 }`) fails exactly ONE case — the
# "cli.target without a url" one. The case that reads as though it guards the
# disarm, "sibling url after cli.target", still PASSES against the mutant,
# because the parser `exit`s on the first match and never reaches the sibling.
# So that test documents behaviour rather than guarding the rule; the labels
# below say which is which. A test that cannot fail is not a guard.

set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/check-settings.sh"

PASS=0
FAIL=0
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

check() {
    local name="$1" want="$2" toml="$3" got
    printf '%s' "${toml}" > "${TMP}/settings.toml"
    got="$(read_cli_target_url "${TMP}/settings.toml")"
    if [[ "${got}" == "${want}" ]]; then
        PASS=$((PASS + 1)); printf 'ok   %s\n' "${name}"
    else
        FAIL=$((FAIL + 1))
        printf 'FAIL %s — want %q got %q\n' "${name}" "${want}" "${got}"
    fi
}

# The real shape, copied from the live hosts: [cli.target] first, then two
# other tables that ALSO carry a url. This is the case that matters.
check "real layout: picks cli.target, not server.api/web" \
    "http://127.0.0.1:32276" \
'_version = 1

[cli.target]
type = "http"
url = "http://127.0.0.1:32276"

[server.api]
url = "https://hp-xubuntu.perch-rudd.ts.net:32276/api/v1"

[server.web]
enabled = true
url = "https://hp-xubuntu.perch-rudd.ts.net:32276"
'

# A url in an EARLIER table must not be picked up.
check "sibling url before cli.target is ignored" \
    "http://127.0.0.1:32276" \
'[server.web]
url = "https://example.ts.net:32276"

[cli.target]
url = "http://127.0.0.1:32276"
'

# A later url does not win. NOTE this passes on the `exit` after the first
# match, NOT on the table-disarm rule — mutation-checked, see the note below.
# It documents the real layout's behaviour; it does not guard the disarm.
check "sibling url after cli.target does not win" \
    "http://127.0.0.1:32276" \
'[cli.target]
url = "http://127.0.0.1:32276"

[server.api]
url = "https://example.ts.net:32276/api/v1"
'

# A missing table yields empty, which the caller renders as <<missing>>.
check "absent cli.target yields empty" \
    "" \
'[server.web]
url = "https://example.ts.net:32276"
'

# THIS is the case that guards the table-disarm rule. With [cli.target] present
# but carrying no url, only the disarm stops the NEXT table's url leaking in.
# Deleting `/^\[/ { in_table = 0 }` makes exactly this test fail — verified.
check "cli.target without a url yields empty (guards the disarm rule)" \
    "" \
'[cli.target]
type = "http"

[server.web]
url = "https://example.ts.net:32276"
'

# Whitespace around the assignment.
check "tolerates whitespace around =" \
    "http://127.0.0.1:32276" \
'[cli.target]
url   =   "http://127.0.0.1:32276"
'

# A dotted SUBTABLE is a different table and must disarm the match.
check "cli.target.retry subtable does not supply the url" \
    "" \
'[cli.target.retry]
url = "http://wrong:1"
'

# --- the parser agrees with the live hosts ---------------------------------
# Not a fixture: if a real settings.toml is readable, the function must return
# what that host's own hosts/<name>.env declares.
for env_file in "${SCRIPT_DIR}"/hosts/*.env; do
    name="$(basename "${env_file}" .env)"
    home_dir="$(grep -E '^FABRO_HOST_HOME=' "${env_file}" | cut -d= -f2-)"
    want="$(grep -E '^FABRO_CLI_TARGET_URL=' "${env_file}" | cut -d= -f2-)"
    toml="${home_dir}/.fabro/settings.toml"
    if [[ -r "${toml}" ]]; then
        got="$(read_cli_target_url "${toml}")"
        if [[ "${got}" == "${want}" ]]; then
            PASS=$((PASS + 1)); printf 'ok   %s: live settings.toml agrees (%s)\n' "${name}" "${got}"
        else
            FAIL=$((FAIL + 1))
            printf 'FAIL %s: live settings.toml — want %q got %q\n' "${name}" "${want}" "${got}"
        fi
    else
        printf 'skip %s: %s not readable from here\n' "${name}" "${toml}"
    fi
done

printf '\n%d passed, %d failed\n' "${PASS}" "${FAIL}"
[[ "${FAIL}" -eq 0 ]]
