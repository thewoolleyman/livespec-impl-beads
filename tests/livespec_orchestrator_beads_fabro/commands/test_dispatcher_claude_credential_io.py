"""Tests for the bounded Claude OAuth credential probe."""

from __future__ import annotations

import io
import json
from typing import Any
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest
from livespec_orchestrator_beads_fabro.commands import (
    _dispatcher_claude_credential_io as credential_io,
)

_TEST_TOKEN = "oauth-secret"


def _response(*, status: int, body: bytes) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.read.return_value = body
    response.__enter__.return_value = response
    return response


def test_probe_uses_exact_oauth_path_with_a_one_token_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Request, float]] = []
    response = _response(
        status=200,
        body=json.dumps({"usage": {"input_tokens": 9, "output_tokens": 1}}).encode(),
    )

    def fake_urlopen(request: Request, *, timeout: float) -> MagicMock:
        calls.append((request, timeout))
        return response

    monkeypatch.setattr(credential_io, "urlopen", fake_urlopen)

    status = credential_io.probe_claude_credential(token=_TEST_TOKEN)

    assert status.usable is True
    assert status.input_tokens == 9
    assert status.output_tokens == 1
    assert len(calls) == 1
    request, timeout = calls[0]
    assert request.full_url == "https://api.anthropic.com/v1/messages"
    assert request.method == "POST"
    assert request.get_header("Authorization") == f"Bearer {_TEST_TOKEN}"
    assert request.get_header("Anthropic-beta") == "oauth-2025-04-20"
    assert request.get_header("Anthropic-version") == "2023-06-01"
    assert timeout == credential_io.CLAUDE_CREDENTIAL_PROBE_TIMEOUT_SECONDS
    assert json.loads(request.data or b"") == {
        "model": credential_io.CLAUDE_CREDENTIAL_PROBE_MODEL,
        "max_tokens": credential_io.CLAUDE_CREDENTIAL_PROBE_MAX_OUTPUT_TOKENS,
        "messages": [{"role": "user", "content": "hi"}],
    }
    assert credential_io.CLAUDE_CREDENTIAL_PROBE_MAX_OUTPUT_TOKENS == 1


def test_probe_classifies_http_error_body_without_leaking_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = HTTPError(
        url="https://api.anthropic.com/v1/messages",
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=io.BytesIO(b'{"error":{"type":"authentication_error","message":"secret detail"}}'),
    )

    def fake_urlopen(request: Request, *, timeout: float) -> Any:
        _ = (request, timeout)
        raise error

    monkeypatch.setattr(credential_io, "urlopen", fake_urlopen)

    status = credential_io.probe_claude_credential(token=_TEST_TOKEN)

    assert status.condition == "revoked"
    assert status.error_type == "authentication_error"
    assert "secret detail" not in status.message
    assert _TEST_TOKEN not in status.message


@pytest.mark.parametrize(
    "body",
    [
        b"{",
        b"\xff",
        b"[]",
        b'{"error":{"type":123},"usage":{"input_tokens":true,"output_tokens":-1}}',
        b'{"usage":{"input_tokens":"nine","output_tokens":null}}',
    ],
)
def test_probe_treats_untrusted_response_shapes_as_non_secret_metadata(
    *,
    body: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: Request, *, timeout: float) -> MagicMock:
        _ = (request, timeout)
        return _response(status=500, body=body)

    monkeypatch.setattr(credential_io, "urlopen", fake_urlopen)

    status = credential_io.probe_claude_credential(token=_TEST_TOKEN)

    assert status.condition == "unavailable"
    assert status.error_type is None
    assert status.input_tokens is None
    assert status.output_tokens is None


def test_probe_transport_failure_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: Request, *, timeout: float) -> Any:
        _ = (request, timeout)
        raise URLError("network unavailable")

    monkeypatch.setattr(credential_io, "urlopen", fake_urlopen)

    status = credential_io.probe_claude_credential(token=_TEST_TOKEN)

    assert status.condition == "unavailable"
    assert status.http_status is None
    assert status.usable is False
