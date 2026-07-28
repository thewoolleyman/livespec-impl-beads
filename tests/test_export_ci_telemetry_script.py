"""Static regression tests for the CI telemetry export shell script."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / ".github" / "scripts" / "export-ci-telemetry.sh"


def test_growing_run_payload_reaches_jq_on_stdin() -> None:
    script = _SCRIPT.read_text(encoding="utf-8")

    assert '--argjson run "$run_json"' not in script
    assert ". as $run |" in script
    assert '\' <<<"$run_json")"' in script


def test_growing_job_accumulator_reaches_payload_jq_on_stdin() -> None:
    script = _SCRIPT.read_text(encoding="utf-8")

    assert '--argjson jobs "$job_spans"' not in script
    assert ". as $jobs |" in script
    assert '\' <<<"$job_spans" > "$payload_file"' in script


def test_bounded_run_span_stays_on_argv() -> None:
    script = _SCRIPT.read_text(encoding="utf-8")

    assert '--argjson run "$run_span"' in script
    assert "spans:([$run] + $jobs)" in script
