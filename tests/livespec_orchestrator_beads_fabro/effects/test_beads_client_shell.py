"""Paired coverage for shell-backed beads client effects."""

from __future__ import annotations

import json
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


def _server_mode_repo(*, tmp_path: Path) -> tuple[Path, Path]:
    """A repo root whose `.beads/config.yaml` declares server mode."""
    repo_root = tmp_path / "repo"
    config_path = repo_root / ".beads" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    _ = config_path.write_text("dolt:\n  mode: server\n", encoding="utf-8")
    return repo_root, config_path


def _cache_path(*, repo_root: Path) -> Path:
    return repo_root / ".beads" / "tenant-verification-cache.json"


def test_fresh_process_reuses_the_file_cached_tenant_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A one-shot CLI process must not re-spawn `bd config get`.

    Clearing the in-process memo stands in for a brand-new wrapper process
    (scripts/bin/list_work_items.py and friends spawn, make one or two bd calls,
    and exit). The tier-2 file cache in `.beads/` must satisfy the verification
    with zero new subprocess spawns.
    """
    repo_root, _ = _server_mode_repo(tmp_path=tmp_path)
    config = _tenant_config(repo_root=repo_root)
    calls: list[str] = []
    monkeypatch.setattr(shell.subprocess, "run", _fake_bd_config_get(calls))
    shell.reset_tenant_verification_memo()

    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)
    assert len(calls) == 2

    shell.reset_tenant_verification_memo()
    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)

    assert len(calls) == 2
    assert _cache_path(repo_root=repo_root).exists()


def test_config_file_change_invalidates_the_file_cached_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root, config_path = _server_mode_repo(tmp_path=tmp_path)
    config = _tenant_config(repo_root=repo_root)
    calls: list[str] = []
    monkeypatch.setattr(shell.subprocess, "run", _fake_bd_config_get(calls))
    shell.reset_tenant_verification_memo()
    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)

    shell.reset_tenant_verification_memo()
    stat = config_path.stat()
    os.utime(config_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)

    assert len(calls) == 4


def test_expired_file_cache_entries_are_reverified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The TTL bounds a positive whose config identity never changed."""
    repo_root, _ = _server_mode_repo(tmp_path=tmp_path)
    config = _tenant_config(repo_root=repo_root)
    calls: list[str] = []
    monkeypatch.setattr(shell.subprocess, "run", _fake_bd_config_get(calls))
    shell.reset_tenant_verification_memo()
    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)

    cache_path = _cache_path(repo_root=repo_root)
    cached: dict[str, float] = json.loads(cache_path.read_text(encoding="utf-8"))
    _ = cache_path.write_text(json.dumps({key: 0.0 for key in cached}), encoding="utf-8")
    shell.reset_tenant_verification_memo()
    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)

    assert len(calls) == 4


def test_corrupt_file_cache_is_treated_as_a_miss_and_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root, _ = _server_mode_repo(tmp_path=tmp_path)
    config = _tenant_config(repo_root=repo_root)
    cache_path = _cache_path(repo_root=repo_root)
    _ = cache_path.write_text("{ not json at all", encoding="utf-8")
    calls: list[str] = []
    monkeypatch.setattr(shell.subprocess, "run", _fake_bd_config_get(calls))
    shell.reset_tenant_verification_memo()

    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)
    assert len(calls) == 2

    shell.reset_tenant_verification_memo()
    shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)

    assert len(calls) == 2
    rewritten: dict[str, float] = json.loads(cache_path.read_text(encoding="utf-8"))
    assert len(rewritten) == 1


def test_tenant_mismatch_without_a_config_file_is_never_file_cached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only POSITIVE verifications are cached; a mismatch keeps raising."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config = _tenant_config(repo_root=repo_root)

    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=argv, returncode=0, stdout="other-tenant\n", stderr=""
        )

    monkeypatch.setattr(shell.subprocess, "run", run)
    shell.reset_tenant_verification_memo()

    with pytest.raises(BeadsConnectionError):
        shell.assert_repo_root_matches_config(config=config, repo_root=repo_root)

    assert not _cache_path(repo_root=repo_root).exists()


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
