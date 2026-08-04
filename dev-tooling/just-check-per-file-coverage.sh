#!/usr/bin/env bash
# Deliberately omit errexit so the per-file coverage verifier still runs after pytest.
set -uo pipefail

pytest_rc=0
uv run pytest -n "$(bash dev-tooling/just-test-nprocs.sh)" --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing || pytest_rc=$?
uv run python -m livespec_dev_tooling.checks.per_file_coverage
coverage_rc=$?

if [[ "$pytest_rc" -ne 0 ]]; then
    exit "$pytest_rc"
fi
exit "$coverage_rc"
