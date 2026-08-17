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


def _tenant_config(*, repo_root: Path, tenant: str = "tenant-db") -> StoreConfig:
    return StoreConfig(
        tenant=tenant,
        prefix="td",
        server_user=tenant,
        database=tenant,
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


def test_repeat_tenant_verification_reuses_memo_for_process_lifetime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A re-verify of the same repo tenant must not re-spawn `bd config get`.

    First verification runs the two config reads; a second verification of the
    SAME repo root and tenant identity reuses the memoized positive result
    (zero new subprocess spawns) for process lifetime.
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
    assert len(calls) == 2


def test_invoke_memoizes_tenant_validation_per_process_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    config_a_path = repo_a / ".beads" / "config.yaml"
    config_b_path = repo_b / ".beads" / "config.yaml"
    config_a_path.parent.mkdir(parents=True)
    config_b_path.parent.mkdir(parents=True)
    _ = config_a_path.write_text("dolt.mode: server\n", encoding="utf-8")
    _ = config_b_path.write_text("dolt.mode: server\n", encoding="utf-8")
    config_a = _tenant_config(repo_root=repo_a, tenant="tenant-a")
    config_b = _tenant_config(repo_root=repo_b, tenant="tenant-b")
    tenant_by_repo = {
        repo_a: "tenant-a",
        repo_b: "tenant-b",
    }
    config_get_calls: list[tuple[Path, str]] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        cwd = kwargs["cwd"]
        assert isinstance(cwd, Path)
        if argv[1:3] == ["config", "get"]:
            key = argv[3]
            config_get_calls.append((cwd, key))
            value = tenant_by_repo[cwd]
            return subprocess.CompletedProcess(
                args=argv,
                returncode=0,
                stdout=value + "\n",
                stderr="",
            )
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout="[]\n", stderr="")

    monkeypatch.setenv("BEADS_DOLT_PASSWORD", "present")
    monkeypatch.setattr(shell.subprocess, "run", run)
    shell.reset_tenant_verification_memo()

    for _ in range(3):
        shell.invoke(config=config_a, argv=[config_a.bd_path, "list"])
    for _ in range(2):
        shell.invoke(config=config_b, argv=[config_b.bd_path, "list"])

    stat = config_a_path.stat()
    os.utime(config_a_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    shell.invoke(config=config_a, argv=[config_a.bd_path, "show", "bd-ib-demo"])

    assert config_get_calls == [
        (repo_a, "dolt.server-user"),
        (repo_a, "dolt.database"),
        (repo_b, "dolt.server-user"),
        (repo_b, "dolt.database"),
    ]
