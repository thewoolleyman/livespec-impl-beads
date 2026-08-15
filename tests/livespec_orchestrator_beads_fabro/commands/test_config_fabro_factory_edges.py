"""Edge coverage for Fabro factory target resolution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands import _config

_CONFIG_NAME = ".livespec.jsonc"


def _write_config(*, cwd: Path, body: str) -> None:
    _ = (cwd / _CONFIG_NAME).write_text(body, encoding="utf-8")


def test_missing_configured_default_factory_falls_back_to_implicit_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing `default_factory` entry does not invent a server target."""
    monkeypatch.delenv("LIVESPEC_FABRO_FACTORY", raising=False)
    _write_config(
        cwd=tmp_path,
        body=json.dumps(
            {
                "livespec-orchestrator-beads-fabro": {
                    "dispatcher": {
                        "default_factory": "missing",
                        "factories": {
                            "remote": {"server": "https://remote.example.test"},
                        },
                    }
                }
            }
        ),
    )
    target = _config.resolve_fabro_factory(cwd=tmp_path)
    assert target.name == "default"
    assert target.server is None
    assert target.dev_token is None


def test_cli_factory_argument_selects_configured_factory_over_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit dispatcher CLI selection wins over the host env default."""
    monkeypatch.setenv("LIVESPEC_FABRO_FACTORY", "env-default")
    _write_config(
        cwd=tmp_path,
        body=json.dumps(
            {
                "livespec-orchestrator-beads-fabro": {
                    "dispatcher": {
                        "factories": {
                            "cli": {"server": "https://cli.example.test"},
                            "env-default": {"server": "https://env.example.test"},
                        },
                    }
                }
            }
        ),
    )

    target = _config.resolve_fabro_factory(cwd=tmp_path, factory="cli")

    assert target.name == "cli"
    assert target.server == "https://cli.example.test"
