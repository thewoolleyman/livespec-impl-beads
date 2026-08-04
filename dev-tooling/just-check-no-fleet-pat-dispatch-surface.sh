#!/usr/bin/env bash
set -euo pipefail

token='LIVESPEC_FAMILY_GITHUB_TOKEN'
hits="$(git grep -n -F "$token" -- orchestrator-image .claude-plugin/scripts .claude-plugin/.fabro .github/workflows || true)"
if [[ -n "$hits" ]]; then
    printf 'ERROR: retired fleet PAT env name found in dispatch surface(s):\n' >&2
    printf '%s\n' "$hits" >&2
    exit 1
fi
