#!/usr/bin/env bash
# Deliberately omit errexit so the doc-only subset reports every failing target.
set -uo pipefail

targets=(
    check-heading-coverage
    check-agents-ai-references-resolve
    check-claude-md-coverage
    check-handoff-dispatch-routing
    check-plan-anchor-declared
    check-vendor-manifest
    check-no-direct-tool-invocation
    check-check-tools
)
failed=()
for target in "${targets[@]}"; do
    printf '\n::: just %s\n' "$target"
    if ! just "$target"; then
        failed+=("$target")
    fi
done
# check-no-todo-registry (work-item livespec-dev-tooling-yilyxr.10): the
# per-commit tier is warn-only everywhere; the release tier is armed only
# for the commit that itself edits tests/heading-coverage.json, because
# authoring an UNOWNED TODO entry is never valid per the check's contract.
printf '\n::: just check-no-todo-registry\n'
if git diff --cached --name-only | grep -qx 'tests/heading-coverage.json'; then
    echo ":: staged changeset edits tests/heading-coverage.json — arming the TODO-ownership release tier"
    if ! LIVESPEC_FAIL_IF_HEADING_COVERAGE_TODOS_EXIST=true just check-no-todo-registry; then
        failed+=(check-no-todo-registry)
    fi
elif ! just check-no-todo-registry; then
    failed+=(check-no-todo-registry)
fi
if [[ ${#failed[@]} -gt 0 ]]; then
    printf '\nFailed targets (%d):\n' "${#failed[@]}"
    printf '  - %s\n' "${failed[@]}"
    exit 1
fi
printf '\nAll doc-only targets passed.\n' 
