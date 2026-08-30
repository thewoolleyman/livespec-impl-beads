#!/usr/bin/env bash
set -euo pipefail

staged=$(git diff --cached --name-only --diff-filter=AM)
py_staged=$(echo "$staged" | grep -E '\.py$' || true)
test_staged=$(echo "$staged" | grep -E '^tests/.*\.py$' || true)
impl_staged=$(echo "$staged" | grep -E '^(\.claude-plugin/scripts/|dev-tooling/checks/).*\.py$' || true)
test_count=0
impl_count=0
[[ -n "$test_staged" ]] && test_count=$(echo "$test_staged" | wc -l)
[[ -n "$impl_staged" ]] && impl_count=$(echo "$impl_staged" | wc -l)
if [[ -z "$py_staged" ]]; then
    echo ":: doc-only mode detected (zero .py files staged): running just check-pre-commit-doc-only"
    echo ":: pre-push + CI keep the full aggregate as the load-bearing safety net"
    just check-pre-commit-doc-only
    exit $?
fi
if [[ "$test_count" -eq 1 ]] && [[ "$impl_count" -eq 0 ]]; then
    echo ":: Red-mode shape detected: $test_staged"
    echo ":: skipping coverage gates and same-repo live TUI picker gate in pre-commit"
    # check-check-coverage-incremental belongs in this skip list even though it
    # is vacuous on a FRESH branch: on a branch that already carries impl
    # commits, its incremental scope includes those impl files, so it RUNS the
    # branch's tests — the staged Red test among them. That test fails BY
    # DESIGN, which is the whole point of a Red commit, so leaving the gate
    # armed here refuses the ritual's own first step (work-item bd-ib-c4sfpr).
    # No coverage is lost: the Green amend, pre-push, and CI each run the full
    # aggregate on the final commit, which is the load-bearing net.
    just check-skipping \
        check-coverage \
        check-per-file-coverage \
        check-check-coverage-incremental \
        check-codex-skill-picker
    exit $?
fi
head_msg=$(git log -1 --format=%B 2>/dev/null || true)
if [[ "$impl_count" -ge 1 ]] \
    && grep -q 'TDD-Red-Test-File-Checksum:' <<<"$head_msg" \
    && ! grep -q 'TDD-Green-Verified-At:' <<<"$head_msg"; then
    echo ":: Green-amend shape detected (impl staged; HEAD carries Red-only trailers)"
    echo ":: skipping no-arg check-red-green-replay and same-repo live TUI picker gate"
    just check-skipping check-red-green-replay check-codex-skill-picker
    exit $?
fi
echo ":: pre-push: skipping same-repo live TUI picker gate; run just check-codex-skill-picker explicitly for live Codex picker acceptance"
just check-skipping check-codex-skill-picker
