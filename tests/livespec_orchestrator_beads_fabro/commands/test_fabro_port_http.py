"""Tests for the Fabro server-API HTTP port and its urllib transport."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType

import pytest
from livespec_orchestrator_beads_fabro.commands import _fabro_port_http
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroPort
from livespec_orchestrator_beads_fabro.commands._fabro_port_http import (
    FabroHttpPort,
    FabroHttpResult,
    UrllibFabroHttpTransport,
    fabro_http_request,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port_types import FabroTarget

_DEV_TOKEN_VALUE = "fixture-dev-token"


@dataclass(kw_only=True)
class _RecordingTransport:
    result: FabroHttpResult
    calls: list[dict[str, object]] = field(default_factory=list)

    def send(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout_seconds: float,
    ) -> FabroHttpResult:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.result


@dataclass(kw_only=True)
class _FakeResponse:
    status: int
    payload: bytes

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        _ = (exc_type, exc, traceback)


def test_questions_and_answer_and_cancel_hit_the_documented_routes() -> None:
    transport = _RecordingTransport(result=_ok(body='{"questions": []}'))
    port = FabroHttpPort(
        target=FabroTarget(server_url="https://hp.example:32276/", dev_token=_DEV_TOKEN_VALUE),
        transport=transport,
    )

    listed = port.questions(run_id="01RUN", timeout_seconds=5.0)
    _ = port.answer_question(
        run_id="01RUN",
        question_id="q1",
        answer="[A] Abandon",
        timeout_seconds=5.0,
    )
    _ = port.cancel(run_id="01RUN", timeout_seconds=5.0)

    assert listed.payload == {"questions": []}
    assert [(call["method"], call["url"]) for call in transport.calls] == [
        ("GET", "https://hp.example:32276/runs/01RUN/questions"),
        ("POST", "https://hp.example:32276/runs/01RUN/questions/q1/answer"),
        ("POST", "https://hp.example:32276/runs/01RUN/cancel"),
    ]
    assert transport.calls[0]["headers"] == {
        "Accept": "application/json",
        "Authorization": f"Bearer {_DEV_TOKEN_VALUE}",
    }
    assert transport.calls[1]["body"] == json.dumps({"answer": "[A] Abandon"}).encode("utf-8")
    assert transport.calls[1]["headers"] == {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_DEV_TOKEN_VALUE}",
    }


def test_a_target_without_a_server_url_never_sends_a_request() -> None:
    transport = _RecordingTransport(result=_ok(body="{}"))

    result = fabro_http_request(
        target=FabroTarget(),
        transport=transport,
        method="POST",
        path="/runs/01RUN/cancel",
        payload=None,
        timeout_seconds=5.0,
    )

    assert transport.calls == []
    assert result.succeeded is False
    assert result.error is not None
    assert "no server url" in result.error


def test_an_unparsable_body_leaves_the_payload_empty_without_failing() -> None:
    transport = _RecordingTransport(result=_ok(body="not json"))

    result = fabro_http_request(
        target=FabroTarget(server_url="https://hp.example:32276"),
        transport=transport,
        method="GET",
        path="/runs/01RUN/questions",
        payload=None,
        timeout_seconds=5.0,
    )

    assert result.payload is None
    assert result.succeeded is True
    assert transport.calls[0]["headers"] == {"Accept": "application/json"}


def test_the_urllib_transport_reports_a_2xx_and_a_transport_fault(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: _FakeResponse(status=202, payload=b'{"ok": true}'),  # noqa: ARG005
    )
    ok = UrllibFabroHttpTransport().send(
        method="POST",
        url="https://hp.example:32276/runs/01RUN/cancel",
        headers={},
        body=None,
        timeout_seconds=1.0,
    )

    def _refuse(request: object, timeout: float) -> _FakeResponse:
        _ = (request, timeout)
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", _refuse)
    failed = UrllibFabroHttpTransport().send(
        method="POST",
        url="https://hp.example:32276/runs/01RUN/cancel",
        headers={},
        body=None,
        timeout_seconds=1.0,
    )

    assert (ok.status, ok.succeeded, ok.body) == (202, True, '{"ok": true}')
    assert (failed.status, failed.succeeded) == (0, False)
    assert failed.error is not None
    assert "URLError" in failed.error


def test_a_non_2xx_status_is_reported_as_not_succeeded(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: _FakeResponse(status=404, payload=b""),  # noqa: ARG005
    )

    result = UrllibFabroHttpTransport().send(
        method="GET",
        url="https://hp.example:32276/runs/01RUN/questions",
        headers={},
        body=None,
        timeout_seconds=1.0,
    )

    assert (result.status, result.succeeded) == (404, False)


def test_the_cli_port_builds_its_server_api_face_from_its_own_target(tmp_path: Path) -> None:
    transport = _RecordingTransport(result=_ok(body="{}"))
    runner = _RecordingRunner()
    port = FabroPort(
        fabro_bin="fabro",
        target=FabroTarget(server_url="https://vps.example:32276", dev_token=_DEV_TOKEN_VALUE),
        runner=runner,
        cwd=tmp_path,
        http=transport,
    )

    server_api = port.server_api()

    assert server_api.target is port.target
    assert server_api.transport is transport
    assert runner.calls == []


def test_the_module_default_transport_is_the_urllib_one() -> None:
    port = FabroHttpPort(target=FabroTarget(server_url="https://hp.example:32276"))

    assert isinstance(port.transport, _fabro_port_http.UrllibFabroHttpTransport)


@dataclass(kw_only=True)
class _RecordingRunner:
    calls: list[list[str]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env, stdin)
        self.calls.append(argv)
        return CommandResult(exit_code=0, stdout="", stderr="")


def test_the_recording_runner_would_have_reported_a_shell_out(tmp_path: Path) -> None:
    runner = _RecordingRunner()

    result = runner.run(argv=["fabro", "ps"], cwd=tmp_path, timeout_seconds=1.0)

    assert result.exit_code == 0
    assert runner.calls == [["fabro", "ps"]]


def _ok(*, body: str) -> FabroHttpResult:
    return FabroHttpResult(status=200, body=body, error=None, payload=None, succeeded=True)
