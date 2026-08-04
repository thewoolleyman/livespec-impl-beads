#!/usr/bin/env bash
# Deliberately omit errexit: a non-zero live ledger gate can be a fail-soft
# could-not-check path, and this wrapper must inspect the marker before blocking.
set -uo pipefail

if [[ ! -f .beads/config.yaml ]]; then
    echo ":: check-ledger-conformance-live: no .beads/config.yaml (repo has no tenant); skipping"
    exit 0
fi
mapfile -t wrapper < <(uv run python -c 'import sys; sys.path.insert(0, ".claude-plugin/scripts"); from pathlib import Path; from livespec_orchestrator_beads_fabro.commands._config import resolve_credential_wrapper; w = resolve_credential_wrapper(cwd=Path(".")); w and print("\n".join(w))' 2>/dev/null) || wrapper=()
if [[ ${#wrapper[@]} -eq 0 ]]; then
    echo ":: check-ledger-conformance-live: no credential_wrapper resolved; skipping (fail-soft)"
    exit 0
fi
out=$("${wrapper[@]}" python3 .claude-plugin/scripts/bin/dispatcher.py ledger-normalize --project-root . --gate 2>&1)
rc=$?
printf '%s\n' "$out"
if [[ $rc -eq 1 ]] && grep -q 'LIVESPEC_LEDGER_GATE: DRIFT' <<<"$out"; then
    echo ":: check-ledger-conformance-live: RESIDUAL out-of-lifecycle work-item status needs a human lane decision; blocking push (set each to a lifecycle status per the message above, then re-push)"
    exit 1
fi
echo ":: check-ledger-conformance-live: no residual drift (gate exit $rc); allowing push (any safe transient drift was auto-healed in place and printed above; a tenant it could not verify is SKIPPED, never blocked)"
exit 0
