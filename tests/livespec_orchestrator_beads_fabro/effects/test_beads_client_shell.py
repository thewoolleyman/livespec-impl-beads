"""Paired coverage for shell-backed beads client effects."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.effects import _beads_client_shell as shell
from livespec_orchestrator_beads_fabro.errors import BeadsConnectionError
from livespec_orchestrator_beads_fabro.types import StoreConfig


def test_raise_for_status_maps_connection_refused() -> None:
    completed = subprocess.CompletedProcess(
        args=["bd", "list"],
        returncode=1,
        stdout="",
        stderr="connection refused",
    )

    with pytest.raises(BeadsConnectionError):
        shell.raise_for_status(completed=completed, argv=["bd", "list"], tenant="tenant")


def _tenant_config(*, repo_root: Path) -> StoreConfig:
    return StoreConfig(
        tenant="tenant-db",
        prefix="td",
        server_user="tenant-db",
        database="tenant-db",
        bd_path="/nonexistent/bd",
        repo_root=repo_root,
    )


def _fake_bd_config_get(counter: list[str]) -> object:
    """A subprocess.run stand-in answering `bd config get <key>` correctly."""

    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        counter.append(argv[-1])
        value = "tenant-db"
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout=value + "\n", stderr="")

    return run


def test_repeat_tenant_verification_reuses_memo_until_config_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A re-verify of an unchanged repo tenant must not re-spawn `bd config get`.

    First verification runs the two config reads; a second verification of the
    SAME repo root with an UNCHANGED `.beads/config.yaml` reuses the memoized
    positive result (zero new subprocess spawns); touching the config file
    invalidates the memo and the next verification re-reads both keys
    (work-item livespec-dev-tooling-yilyxr.6).
    """
    repo_root = tmp_path / "repo"
    config_path = repo_root / ".beads" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    _ = config_path.write_text("dolt:\n  mode: server\n", encoding="utf-8")
    config = _tenant_config(repo_root=repo_root)
    calls: list[str] = []
    monkeypatch.setattr(shell.subprocess, "run", _fake_bd_config_get(calls))
    shell.reset_tenant_verification_memo()

    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)
    assert len(calls) == 2

    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)
    assert len(calls) == 2

    stat = config_path.stat()
    os.utime(config_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)
    assert len(calls) == 4
