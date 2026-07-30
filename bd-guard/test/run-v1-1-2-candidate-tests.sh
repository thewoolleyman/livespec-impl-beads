#!/usr/bin/env bash
# run-v1-1-2-candidate-tests.sh - qualify the tracked bd guard against the
# official Beads v1.1.2 Linux amd64 binary without installing it.
#
# The harness downloads the release into a temporary directory, verifies the
# upstream tarball checksum and the derived binary hash, then runs bd-guard.sh
# with LIVESPEC_BD_REAL pointed at that temporary binary. All Beads state lives
# under temporary git repositories and a temporary HOME/XDG_CONFIG_HOME; nothing
# is copied to /usr/local/bin, no production tenant is contacted, and no Fabro
# server or image state is touched.

set -euo pipefail

VERSION="1.1.2"
RELEASE_BASE="https://github.com/gastownhall/beads/releases/download/v${VERSION}"
TARBALL="beads_${VERSION}_linux_amd64.tar.gz"
SPDX="beads-v${VERSION}.spdx.json"
EXPECTED_BIN_SHA="6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82"
EXPECTED_SPDX_SHA="b05ca7f525f05e50691a4329b13aa87f10bc93160fe8d4d1ca371867701b58e6"
EXPECTED_VERSION="bd version 1.1.2 (20e493e56: HEAD@20e493e569c9)"

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd -P)"
WRAPPER="${SCRIPT_DIR}/../bd-guard.sh"

WORK="$(mktemp -d)"
cleanup() {
    chmod -R u+w "$WORK" 2>/dev/null || true
    rm -rf "$WORK"
}
trap cleanup EXIT

HOME_T="${WORK}/home"
XDG_T="${WORK}/xdg"
mkdir -p "$HOME_T" "$XDG_T"

pass() { printf '  ok:   %s\n' "$1"; }
fail() {
    printf '  FAIL: %s\n' "$1" >&2
    exit 1
}

run_bd() {
    HOME="$HOME_T" \
    XDG_CONFIG_HOME="$XDG_T" \
    BEADS_ACTOR="E2E Test" \
    "$BD" "$@"
}

run_guard() {
    HOME="$HOME_T" \
    XDG_CONFIG_HOME="$XDG_T" \
    BEADS_ACTOR="E2E Test" \
    LIVESPEC_BD_REAL="$BD" \
    LIVESPEC_BD_GUARD_OTLP=off \
    LIVESPEC_BD_GUARD_MODE_FILE="${WORK}/no-such-mode-file" \
    "$WRAPPER" "$@"
}

status_of() {
    python3 - "$1" "$2" <<'PY'
import json
import sys

path, issue_id = sys.argv[1], sys.argv[2]
for item in json.load(open(path, encoding="utf-8")):
    if item["id"] == issue_id:
        print(item["status"])
        raise SystemExit(0)
raise SystemExit(f"missing issue {issue_id}")
PY
}

field_of_object() {
    python3 - "$1" "$2" <<'PY'
import json
import sys

path, field = sys.argv[1], sys.argv[2]
obj = json.load(open(path, encoding="utf-8"))
if isinstance(obj, list):
    obj = obj[0]
print(obj[field])
PY
}

setup_repo() {
    local name="$1"
    local repo="${WORK}/${name}"
    mkdir -p "$repo"
    git -C "$repo" init -q
    (
        cd "$repo"
        BD_NON_INTERACTIVE=1 run_bd init \
            --prefix q \
            --skip-agents \
            --skip-hooks \
            --setup-exclude \
            --role maintainer \
            --quiet >/dev/null 2>"${WORK}/${name}-init.err"
        run_bd config set status.custom \
            "backlog,pending-approval,ready,active,acceptance" >/dev/null
    )
    printf '%s\n' "$repo"
}

download_and_verify_candidate() {
    (
        cd "$WORK"
        curl -fsSLO "${RELEASE_BASE}/checksums.txt"
        curl -fsSLO "${RELEASE_BASE}/${TARBALL}"
        curl -fsSLO "${RELEASE_BASE}/${SPDX}"

        grep "  ${TARBALL}\$" checksums.txt > "${TARBALL}.sha256"
        sha256sum -c "${TARBALL}.sha256" >/dev/null
        printf '%s  %s\n' "$EXPECTED_SPDX_SHA" "$SPDX" | sha256sum -c - >/dev/null

        tar -xzf "$TARBALL"
        printf '%s  bd\n' "$EXPECTED_BIN_SHA" | sha256sum -c - >/dev/null
    )
    BD="${WORK}/bd"
    export BD

    version_out="$(cd "$WORK" && run_bd version)"
    [ "$version_out" = "$EXPECTED_VERSION" ] \
        || fail "candidate version mismatch: ${version_out}"
    pass "downloaded official v${VERSION} candidate and verified tarball, SPDX, binary hash, and version"
}

test_passthrough_streams_and_exit() {
    repo="$(setup_repo passthrough)"
    (
        cd "$repo"
        run_guard create --id q-pass --type task --title Pass --json >create.json
        run_bd list --status all --limit 0 --json >direct-list.json 2>direct-list.err
        run_guard list --status all --limit 0 --json >guard-list.json 2>guard-list.err
        diff -u direct-list.json guard-list.json >/dev/null
        diff -u direct-list.err guard-list.err >/dev/null

        printf 'create task 2 From stdin\n' \
            | run_bd batch --dry-run --json >direct-batch.out 2>direct-batch.err
        printf 'create task 2 From stdin\n' \
            | run_guard batch --dry-run --json >guard-batch.out 2>guard-batch.err
        diff -u direct-batch.out guard-batch.out >/dev/null
        diff -u direct-batch.err guard-batch.err >/dev/null

        set +e
        run_bd show q-missing --json >direct-missing.out 2>direct-missing.err
        direct_rc=$?
        run_guard show q-missing --json >guard-missing.out 2>guard-missing.err
        guard_rc=$?
        set -e
        [ "$direct_rc" -eq "$guard_rc" ] || fail "missing-show exit changed"
        [ "$guard_rc" -ne 0 ] || fail "missing-show unexpectedly succeeded"
        diff -u direct-missing.out guard-missing.out >/dev/null
        diff -u direct-missing.err guard-missing.err >/dev/null
    )
    pass "candidate passthrough preserves JSON stdout, stdin-driven output, stderr, and nonzero exit"
}

test_lifecycle_controls() {
    repo="$(setup_repo lifecycle)"
    (
        cd "$repo"
        run_guard create --id q-life --type task --title Life --json >/dev/null

        run_guard update q-life --status active --json >active.json 2>active.err
        [ ! -s active.err ] || fail "lifecycle status emitted a warning"
        [ "$(field_of_object active.json status)" = "active" ] \
            || fail "lifecycle status did not apply"

        LIVESPEC_BD_GUARD_MODE=warn run_guard update q-life --status in_progress \
            --json >native.json 2>native.err
        grep -qF "bd update --status in_progress' is non-lifecycle" native.err \
            || fail "warn-mode native status did not warn"
        [ "$(field_of_object native.json status)" = "in_progress" ] \
            || fail "warn-mode native status did not pass through"

        set +e
        LIVESPEC_BD_GUARD_MODE=fail run_guard update q-life --claim \
            >claim.out 2>claim.err
        claim_rc=$?
        LIVESPEC_BD_GUARD_MODE=fail run_guard ready --claim \
            >ready.out 2>ready.err
        ready_rc=$?
        LIVESPEC_BD_GUARD_MODE=fail run_guard reopen q-life \
            >reopen.out 2>reopen.err
        reopen_rc=$?
        LIVESPEC_BD_GUARD_MODE=fail run_guard defer q-life \
            >defer.out 2>defer.err
        defer_rc=$?
        set -e
        if ! { [ "$claim_rc" -eq 3 ] && grep -qF "bd update --claim' is non-lifecycle" claim.err; }; then
            fail "fail-mode update --claim was not blocked"
        fi
        if ! { [ "$ready_rc" -eq 3 ] && grep -qF "bd ready --claim' is non-lifecycle" ready.err; }; then
            fail "fail-mode ready --claim was not blocked"
        fi
        if ! { [ "$reopen_rc" -eq 3 ] && grep -qF "bd reopen' is non-lifecycle" reopen.err; }; then
            fail "fail-mode reopen was not blocked"
        fi
        if ! { [ "$defer_rc" -eq 3 ] && grep -qF "bd defer' is non-lifecycle" defer.err; }; then
            fail "fail-mode defer was not blocked"
        fi
    )
    pass "candidate-backed lifecycle writes pass, warn, or fail exactly as guarded"
}

test_create_normalization() {
    repo="$(setup_repo create-normalization)"
    (
        cd "$repo"
        run_guard create --id q-json --type task --title Json --json >create-json.out 2>create-json.err
        [ ! -s create-json.err ] || fail "qualifying JSON create emitted stderr"
        [ "$(field_of_object create-json.out status)" = "open" ] \
            || fail "candidate create output no longer reports native open"
        run_bd list --status all --limit 0 --json >after-json.json
        [ "$(status_of after-json.json q-json)" = "backlog" ] \
            || fail "JSON create was not normalized to backlog"

        run_guard q "Silent item" >silent.out 2>silent.err
        [ ! -s silent.err ] || fail "quick-capture create emitted stderr"
        silent_id="$(tr -d '[:space:]' < silent.out)"
        run_bd list --status all --limit 0 --json >after-silent.json
        [ "$(status_of after-silent.json "$silent_id")" = "backlog" ] \
            || fail "quick-capture create was not normalized to backlog"

        run_guard create --id q-event --type event --title Event --json >event.out 2>event.err
        [ ! -s event.err ] || fail "event create emitted stderr"
        run_bd list --status all --limit 0 --json >after-event.json
        [ "$(status_of after-event.json q-event)" = "open" ] \
            || fail "event create exclusion was normalized"

        run_guard create --id q-dry --title Dry --dry-run --json >dry.out 2>dry.err
        run_bd list --status all --limit 0 --json >after-dry.json
        if python3 - after-dry.json <<'PY'
import json
import sys

raise SystemExit(any(item["id"] == "q-dry" for item in json.load(open(sys.argv[1], encoding="utf-8"))))
PY
        then
            :
        else
            fail "dry-run create created or normalized an issue"
        fi

        run_guard create --help >create-help.out 2>create-help.err
        [ ! -s create-help.err ] || fail "create help emitted stderr"
        if grep -Eq '(^|[[:space:]])(--status|-s)([=,[:space:]]|$)' create-help.out; then
            fail "candidate create help now advertises create-time status; redesign normalizer"
        fi
    )
    pass "candidate create output is normalized for work items and excluded for event/dry-run/help cases"
}

download_and_verify_candidate
test_passthrough_streams_and_exit
test_lifecycle_controls
test_create_normalization

printf 'bd-guard candidate qualification passed in isolated temporary repositories\n'
