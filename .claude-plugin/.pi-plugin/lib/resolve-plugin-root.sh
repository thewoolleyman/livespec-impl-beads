#!/usr/bin/env bash
#
# resolve-plugin-root.sh — the single realization of the pi bindings'
# plugin-root resolution.
#
# Every one of this package's pi bindings calls this script instead of
# restating the ordered algorithm inline. A sibling Driver learned the cost of
# the alternative: independently-maintained inline copies are kept in agreement
# only by copying, and one positional defect consequently came to live in every
# binding at once.
#
# Ordered algorithm — first hit wins:
#
#   1. $LIVESPEC_ORCH_PLUGIN_ROOT when set and non-empty. The explicit operator
#      override; covers nonstandard dev setups such as driving a sibling
#      checkout's plugin.
#   2. <project-root>/.claude-plugin when that checkout IS this plugin
#      (dogfooding) — identity confirmed from its plugin manifest name, never
#      from the path alone.
#   3. <project-root>/.pi/git/github.com/thewoolleyman/livespec-orchestrator-beads-fabro/.claude-plugin
#      — the PROJECT-scope pi package clone (`pi install ... -l`).
#   4. ~/.pi/agent/git/github.com/thewoolleyman/livespec-orchestrator-beads-fabro/.claude-plugin — the
#      USER-scope pi package clone.
#
# Steps 3 and 4 are pi's own documented git-package clone locations. A candidate
# counts as resolved ONLY when it carries a `scripts/bin` directory: a clone
# that exists but is empty or half-fetched must fail loudly rather than resolve
# to a path whose every subsequent read fails separately and confusingly.
#
# On success: writes the resolved absolute path to stdout, exits 0.
# On failure: writes an install diagnostic to stderr, exits 1. The caller MUST
# surface that diagnostic verbatim and stop — never improvise a path, and never
# run an install command the diagnostic did not ask for.
#
# Usage: resolve-plugin-root.sh [<project-root>]   (default: the current directory)

set -euo pipefail

plugin_name="livespec-orchestrator-beads-fabro"
project_root="${1:-.}"

if ! project_root="$(cd "$project_root" 2>/dev/null && pwd)"; then
    printf 'plugin root resolution failed: project root %s does not exist\n' \
        "${1:-.}" >&2
    exit 1
fi

clone_suffix="git/github.com/thewoolleyman/$plugin_name/.claude-plugin"

candidates=()
if [ -n "${LIVESPEC_ORCH_PLUGIN_ROOT:-}" ]; then
    candidates+=("$LIVESPEC_ORCH_PLUGIN_ROOT")
fi
candidates+=("$project_root/.claude-plugin")
candidates+=("$project_root/.pi/$clone_suffix")
candidates+=("${HOME:-}/.pi/agent/$clone_suffix")

is_this_plugin() {
    manifest="$1/plugin.json"
    [ -f "$manifest" ] || return 1
    python3 - "$manifest" "$plugin_name" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        manifest = json.load(handle)
except (OSError, ValueError):
    sys.exit(1)
sys.exit(0 if manifest.get("name") == sys.argv[2] else 1)
PY
}

for candidate in "${candidates[@]}"; do
    if [ -d "$candidate/scripts/bin" ] && is_this_plugin "$candidate"; then
        printf '%s\n' "$candidate"
        exit 0
    fi
done

{
    printf '%s plugin root could not be resolved.\n' "$plugin_name"
    printf 'A candidate resolves only when it carries scripts/bin AND its\n'
    printf 'plugin.json names this plugin. Searched, in order:\n'
    for candidate in "${candidates[@]}"; do
        printf '    %s\n' "$candidate"
    done
    printf '\n'
    if [ -n "${LIVESPEC_ORCH_PLUGIN_ROOT:-}" ]; then
        printf 'LIVESPEC_ORCH_PLUGIN_ROOT is set to %s but does not resolve.\n' \
            "$LIVESPEC_ORCH_PLUGIN_ROOT"
        printf 'An override that does not resolve is a configuration error, not\n'
        printf 'a missing install — fix or unset it before installing anything.\n\n'
    fi
    printf 'Install this plugin as a project-scope pi package from the repo root:\n'
    printf '    pi install git:github.com/thewoolleyman/%s@release -l\n\n' "$plugin_name"
    printf 'pi resolves project packages only after the project is TRUSTED, so a\n'
    printf 'non-interactive run (-p, --mode json, --mode rpc) in an untrusted\n'
    printf 'project silently loads nothing. Establish trust before driving\n'
    printf 'unattended.\n'
} >&2
exit 1
