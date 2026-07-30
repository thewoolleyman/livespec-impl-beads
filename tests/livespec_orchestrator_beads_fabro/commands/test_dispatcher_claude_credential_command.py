"""Tests for the operator-facing Claude credential status command."""

from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock

import pytest
from livespec_orchestrator_beads_fabro.commands import (
    _dispatcher_claude_credential_command as command,
)
from livespec_orchestrator_beads_fabro.commands import (
    dispatcher,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_claude_credential import (
    ClaudeCredentialStatus,
)

_TEST_TOKEN = "test-oauth-token"


def _status(*, usable: bool) -> ClaudeCredentialStatus:
    return ClaudeCredentialStatus(
        condition="usable" if usable else "exhausted",
        present=True,
        usable=usable,
        http_status=200 if usable else 429,
        error_type=None if usable else "rate_limit_error",
        input_tokens=9 if usable else None,
        output_tokens=1 if usable else None,
        message="CLAUDE_CODE_OAUTH_TOKEN is usable." if usable else "Capacity is exhausted.",
        remedy="No action required." if usable else "Wait before retrying.",
    )


def _status_for_token(*, token: str, usable: bool) -> ClaudeCredentialStatus:
    assert token == _TEST_TOKEN
    return _status(usable=usable)


def test_assess_distinguishes_absence_without_calling_probe() -> None:
    probe = MagicMock(return_value=_status(usable=True))

    status = command.assess_claude_credential(
        token=None,
        probe=probe,
        wrapper_text="['with-project-env.sh', '--']",
    )

    probe.assert_not_called()
    assert status.condition == "absent"
    assert status.present is False
    assert status.usable is False
    assert "CLAUDE_CODE_OAUTH_TOKEN" in status.message
    assert "with-project-env.sh" in status.remedy


def test_assess_passes_only_the_present_token_to_the_probe() -> None:
    calls: list[str] = []

    def recording_probe(*, token: str) -> ClaudeCredentialStatus:
        calls.append(token)
        return _status(usable=True)

    status = command.assess_claude_credential(
        token=_TEST_TOKEN,
        probe=recording_probe,
        wrapper_text="unused",
    )

    assert calls == [_TEST_TOKEN]
    assert status.usable is True


def test_status_json_reports_probe_bound_and_measured_usage(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", _TEST_TOKEN)
    monkeypatch.setattr(
        command,
        "probe_claude_credential",
        lambda *, token: _status_for_token(token=token, usable=True),
    )

    exit_code = command.run_claude_cred_status(args=argparse.Namespace(as_json=True))

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload == {
        "condition": "usable",
        "credential_env": "CLAUDE_CODE_OAUTH_TOKEN",
        "error_type": None,
        "http_status": 200,
        "input_tokens": 9,
        "max_output_tokens": 1,
        "message": "CLAUDE_CODE_OAUTH_TOKEN is usable.",
        "model": "claude-haiku-4-5-20251001",
        "output_tokens": 1,
        "present": True,
        "probe_timeout_seconds": 20.0,
        "remedy": "No action required.",
        "usable": True,
    }


def test_status_human_refuses_an_exhausted_token(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", _TEST_TOKEN)
    monkeypatch.setattr(
        command,
        "probe_claude_credential",
        lambda *, token: _status_for_token(token=token, usable=False),
    )

    exit_code = command.run_claude_cred_status(args=argparse.Namespace(as_json=False))

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "credential_env: CLAUDE_CODE_OAUTH_TOKEN" in out
    assert "present: true" in out
    assert "usable: false" in out
    assert "condition: exhausted" in out
    assert "http_status: 429" in out
    assert "error_type: rate_limit_error" in out
    assert "input_tokens: null" in out
    assert "remedy: Wait before retrying." in out


def test_dispatcher_routes_claude_status_command(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)

    exit_code = dispatcher.main(argv=["claude-cred-status", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["credential_env"] == "CLAUDE_CODE_OAUTH_TOKEN"
    assert payload["condition"] == "absent"
    assert payload["present"] is False
    assert payload["usable"] is False
