"""Pure classification tests for the Claude OAuth credential pre-flight."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from livespec_orchestrator_beads_fabro.commands._dispatcher_claude_credential import (
    ClaudeProbeObservation,
    classify_claude_probe,
)


@pytest.mark.parametrize(
    ("http_status", "error_type", "condition", "remedy_fragment"),
    [
        (401, "authentication_error", "revoked", "claude setup-token"),
        (402, "billing_error", "exhausted", "billing"),
        (403, "permission_error", "permission-denied", "access"),
        (429, "rate_limit_error", "exhausted", "wait"),
        (500, "api_error", "unavailable", "retry"),
        (None, None, "unavailable", "retry"),
    ],
)
def test_probe_failures_are_distinguished_with_actionable_remedies(
    *,
    http_status: int | None,
    error_type: str | None,
    condition: str,
    remedy_fragment: str,
) -> None:
    status = classify_claude_probe(
        observation=ClaudeProbeObservation(
            http_status=http_status,
            error_type=error_type,
            input_tokens=None,
            output_tokens=None,
        )
    )

    assert status.present is True
    assert status.usable is False
    assert status.condition == condition
    assert status.http_status == http_status
    assert status.error_type == error_type
    assert "CLAUDE_CODE_OAUTH_TOKEN" in status.message
    assert remedy_fragment in status.remedy


@given(
    input_tokens=st.integers(min_value=0, max_value=1_000_000),
    output_tokens=st.integers(min_value=0, max_value=1),
)
def test_success_preserves_measured_usage_and_is_usable(
    *,
    input_tokens: int,
    output_tokens: int,
) -> None:
    status = classify_claude_probe(
        observation=ClaudeProbeObservation(
            http_status=200,
            error_type=None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    )

    assert status.present is True
    assert status.usable is True
    assert status.condition == "usable"
    assert status.input_tokens == input_tokens
    assert status.output_tokens == output_tokens
    assert "CLAUDE_CODE_OAUTH_TOKEN" in status.message
    assert "No action" in status.remedy
