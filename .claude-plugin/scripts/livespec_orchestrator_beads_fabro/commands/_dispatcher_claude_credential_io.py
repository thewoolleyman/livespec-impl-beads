"""Bounded network probe for the Claude Code OAuth credential."""

from __future__ import annotations

import json
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from livespec_orchestrator_beads_fabro.commands._dispatcher_claude_credential import (
    ClaudeCredentialStatus,
    ClaudeProbeObservation,
    classify_claude_probe,
)

__all__: list[str] = [
    "CLAUDE_CREDENTIAL_PROBE_MAX_OUTPUT_TOKENS",
    "CLAUDE_CREDENTIAL_PROBE_MODEL",
    "CLAUDE_CREDENTIAL_PROBE_TIMEOUT_SECONDS",
    "probe_claude_credential",
]

CLAUDE_CREDENTIAL_PROBE_MODEL = "claude-haiku-4-5-20251001"
CLAUDE_CREDENTIAL_PROBE_MAX_OUTPUT_TOKENS = 1
CLAUDE_CREDENTIAL_PROBE_TIMEOUT_SECONDS = 20.0
_CLAUDE_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
_CLAUDE_OAUTH_BETA = "oauth-2025-04-20"
_ANTHROPIC_VERSION = "2023-06-01"
_MAX_RESPONSE_BYTES = 65_536


def probe_claude_credential(*, token: str) -> ClaudeCredentialStatus:
    """Spend at most one output token to assess the exact projected OAuth token."""
    request = _probe_request(token=token)
    try:
        with urlopen(  # noqa: S310 - fixed HTTPS endpoint, no caller-controlled URL.
            request,
            timeout=CLAUDE_CREDENTIAL_PROBE_TIMEOUT_SECONDS,
        ) as response:
            observation = _observation(
                http_status=response.status,
                body=response.read(_MAX_RESPONSE_BYTES),
            )
    except HTTPError as error:
        observation = _observation(
            http_status=error.code,
            body=error.read(_MAX_RESPONSE_BYTES),
        )
    except (OSError, TimeoutError, URLError):
        observation = ClaudeProbeObservation(
            http_status=None,
            error_type=None,
            input_tokens=None,
            output_tokens=None,
        )
    return classify_claude_probe(observation=observation)


def _probe_request(*, token: str) -> Request:
    body = json.dumps(
        {
            "model": CLAUDE_CREDENTIAL_PROBE_MODEL,
            "max_tokens": CLAUDE_CREDENTIAL_PROBE_MAX_OUTPUT_TOKENS,
            "messages": [{"role": "user", "content": "hi"}],
        },
        separators=(",", ":"),
    ).encode()
    return Request(  # noqa: S310 - fixed HTTPS endpoint, no caller-controlled URL.
        _CLAUDE_MESSAGES_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": _CLAUDE_OAUTH_BETA,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )


def _observation(*, http_status: int, body: bytes) -> ClaudeProbeObservation:
    payload = _json_object(body=body)
    error = payload.get("error")
    error_object = cast("dict[str, object]", error) if isinstance(error, dict) else {}
    error_type = error_object.get("type")
    usage = payload.get("usage")
    usage_object = cast("dict[str, object]", usage) if isinstance(usage, dict) else {}
    input_tokens = usage_object.get("input_tokens")
    output_tokens = usage_object.get("output_tokens")
    return ClaudeProbeObservation(
        http_status=http_status,
        error_type=error_type if isinstance(error_type, str) else None,
        input_tokens=_token_count(value=input_tokens),
        output_tokens=_token_count(value=output_tokens),
    )


def _json_object(*, body: bytes) -> dict[str, object]:
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    return cast("dict[str, object]", parsed)


def _token_count(*, value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
