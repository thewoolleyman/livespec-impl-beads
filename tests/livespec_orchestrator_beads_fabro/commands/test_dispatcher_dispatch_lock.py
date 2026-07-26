"""Dispatch ownership lock tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands import _dispatcher_dispatch_lock as lock
from livespec_orchestrator_beads_fabro.effects import AttemptFailure


def test_write_dispatch_lock_surfaces_non_contention_open_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def deny_open(*args: object) -> int:
        _ = args
        raise PermissionError("blocked")

    monkeypatch.setattr(lock.os, "open", deny_open)

    with pytest.raises(PermissionError):
        _ = lock.write_dispatch_lock(
            repo=tmp_path, work_item_id="bd-ib-lock", dispatch_id="dispatch-new"
        )


def test_write_dispatch_lock_refuses_when_reclaim_mutex_cannot_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    item_id = "bd-ib-lock"
    path = _write_existing_lock(repo=tmp_path, item_id=item_id)

    def mutex_path_that_cannot_open(*, path: Path) -> Path:
        _ = path
        return tmp_path

    monkeypatch.setattr(lock, "_reclaim_mutex_path", mutex_path_that_cannot_open)

    with pytest.raises(FileExistsError):
        _ = lock.write_dispatch_lock(
            repo=tmp_path, work_item_id=item_id, dispatch_id="dispatch-new"
        )

    assert path.is_file()


def test_write_dispatch_lock_refuses_when_reclaim_mutex_cannot_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    item_id = "bd-ib-lock"
    path = _write_existing_lock(repo=tmp_path, item_id=item_id)

    def refuse_flock(*args: object) -> None:
        _ = args
        raise OSError("flock unavailable")

    monkeypatch.setattr(lock.fcntl, "flock", refuse_flock)

    with pytest.raises(FileExistsError):
        _ = lock.write_dispatch_lock(
            repo=tmp_path, work_item_id=item_id, dispatch_id="dispatch-new"
        )

    assert path.is_file()


def test_write_dispatch_lock_surfaces_retry_contention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    failures = [
        AttemptFailure(error=FileExistsError("first")),
        AttemptFailure(error=FileExistsError("retry")),
    ]

    def refuse_open(*, path: Path) -> AttemptFailure:
        _ = path
        return failures.pop(0)

    monkeypatch.setattr(lock, "_open_dispatch_lock", refuse_open)
    monkeypatch.setattr(lock, "_stale_dispatch_lock_reclaimed", lambda **_: True)

    with pytest.raises(FileExistsError, match="retry"):
        _ = lock.write_dispatch_lock(
            repo=tmp_path, work_item_id="bd-ib-lock", dispatch_id="dispatch-new"
        )

    assert failures == []


def _write_existing_lock(*, repo: Path, item_id: str) -> Path:
    path = lock.dispatch_lock_path(repo=repo, work_item_id=item_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"dispatch_id":"dispatch-old","pid":999999999,'
        '"started_at_epoch":1.0,"work_item_id":"bd-ib-lock"}\n',
        encoding="utf-8",
    )
    return path
