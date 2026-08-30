"""Tests for Fabro bearer-credential resolution from env and `~/.fabro/auth.json`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands import _fabro_port_auth
from livespec_orchestrator_beads_fabro.commands._fabro_port_auth import resolve_bearer_token
from livespec_orchestrator_beads_fabro.commands._fabro_port_types import FabroTarget

# Captured before any fixture runs, so the HOME-resolution test can exercise
# the real seam that `tests/conftest.py` autouse-replaces for every other test.
_REAL_AUTH_FILE = _fabro_port_auth.fabro_auth_file

_SERVER = "https://hp-xubuntu.perch-rudd.ts.net:32276"
_ENV_TOKEN_VALUE = "env-token"

# The shape `fabro auth login` writes, recorded from a live operator host.
_AUTH_JSON = json.dumps(
    {
        "servers": {
            _SERVER: {
                "kind": "dev_token",
                "logged_in_at": "2026-08-29T22:14:03.117Z",
                "token": "auth-json-token",
            }
        }
    }
)


def test_the_env_dev_token_wins_over_the_auth_file(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _point_at(monkeypatch=monkeypatch, tmp_path=tmp_path, text=_AUTH_JSON)

    resolved = resolve_bearer_token(
        target=FabroTarget(server_url=_SERVER, dev_token=_ENV_TOKEN_VALUE)
    )

    assert resolved == _ENV_TOKEN_VALUE


def test_the_auth_file_token_is_resolved_when_no_env_token_is_set(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _point_at(monkeypatch=monkeypatch, tmp_path=tmp_path, text=_AUTH_JSON)

    resolved = resolve_bearer_token(target=FabroTarget(server_url=_SERVER))

    assert resolved == "auth-json-token"


def test_a_trailing_slash_or_a_cased_host_still_matches_the_logged_in_server(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _point_at(monkeypatch=monkeypatch, tmp_path=tmp_path, text=_AUTH_JSON)

    trailing = resolve_bearer_token(target=FabroTarget(server_url=f"{_SERVER}/"))
    cased = resolve_bearer_token(
        target=FabroTarget(server_url="HTTPS://HP-XUBUNTU.PERCH-RUDD.TS.NET:32276")
    )

    assert (trailing, cased) == ("auth-json-token", "auth-json-token")


def test_a_different_server_a_bare_url_and_a_bare_target_resolve_nothing(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _point_at(monkeypatch=monkeypatch, tmp_path=tmp_path, text=_AUTH_JSON)

    assert resolve_bearer_token(target=FabroTarget(server_url="https://vps.example:32276")) is None
    assert resolve_bearer_token(target=FabroTarget(server_url="hp-xubuntu")) is None
    assert resolve_bearer_token(target=FabroTarget()) is None


def test_an_entry_that_carries_no_usable_token_is_skipped_for_a_later_match(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _point_at(
        monkeypatch=monkeypatch,
        tmp_path=tmp_path,
        text=json.dumps(
            {
                "servers": {
                    f"{_SERVER}/": {"kind": "dev_token", "token": ""},
                    f"{_SERVER}//": "not-an-object",
                    _SERVER.upper(): {"token": "late-match"},
                }
            }
        ),
    )

    assert resolve_bearer_token(target=FabroTarget(server_url=_SERVER)) == "late-match"


def test_an_unreadable_or_unshaped_auth_file_resolves_nothing(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = FabroTarget(server_url=_SERVER)
    monkeypatch.setattr(_fabro_port_auth, "fabro_auth_file", lambda: tmp_path / "absent.json")
    absent = resolve_bearer_token(target=target)

    _point_at(monkeypatch=monkeypatch, tmp_path=tmp_path, text="not json")
    unparsable = resolve_bearer_token(target=target)

    _point_at(monkeypatch=monkeypatch, tmp_path=tmp_path, text=json.dumps(["not", "a", "mapping"]))
    unshaped = resolve_bearer_token(target=target)

    _point_at(monkeypatch=monkeypatch, tmp_path=tmp_path, text=json.dumps({"servers": []}))
    serverless = resolve_bearer_token(target=target)

    assert (absent, unparsable, unshaped, serverless) == (None, None, None, None)


def test_the_auth_file_resolves_under_the_home_directory(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    assert _REAL_AUTH_FILE() == tmp_path / ".fabro" / "auth.json"


def _point_at(*, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, text: str) -> None:
    auth_file = tmp_path / ".fabro" / "auth.json"
    auth_file.parent.mkdir(parents=True, exist_ok=True)
    _ = auth_file.write_text(text, encoding="utf-8")
    monkeypatch.setattr(_fabro_port_auth, "fabro_auth_file", lambda: auth_file)
