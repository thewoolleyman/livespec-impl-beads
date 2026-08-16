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
if [[ ${#failed[@]} -gt 0 ]]; then
    printf '\nFailed targets (%d):\n' "${#failed[@]}"
    printf '  - %s\n' "${failed[@]}"
    exit 1
fi
printf '\nAll %d doc-only targets passed.\n' "${#targets[@]}"
