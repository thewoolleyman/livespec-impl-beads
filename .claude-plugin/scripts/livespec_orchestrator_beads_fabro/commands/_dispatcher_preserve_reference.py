"""Preserve failed/blocked Fabro run work by reference on the ledger."""

from __future__ import annotations

import argparse
import hashlib
import tempfile
from pathlib import Path
from typing import Protocol

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    CommandRunner,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import store_config
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt
from livespec_orchestrator_beads_fabro.errors import (
    BeadsCommandError,
    BeadsConnectionError,
    BeadsMappingError,
    BeadsTenantMissingError,
    ConnectionPrefixMissingError,
    WorkItemNotFoundError,
)
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

__all__: list[str] = ["preserve_checkpointed_work_reference"]

_ARTIFACT_PATH = Path("stages") / "002-implement@1" / "diff.patch"
_DUMP_TIMEOUT_SECONDS = 300.0
_LEDGER_WRITE_ERRORS = (
    WorkItemNotFoundError,
    BeadsCommandError,
    BeadsConnectionError,
    BeadsMappingError,
    BeadsTenantMissingError,
)


class _Journal(Protocol):
    def append(self, *, record: dict[str, object]) -> None:
        """Persist one journal record."""
        ...


def preserve_checkpointed_work_reference(
    *,
    args: argparse.Namespace,
    repo: Path,
    item: WorkItem,
    outcome: DispatchOutcome,
    journal: _Journal,
    runner: CommandRunner | None = None,
) -> None:
    """Write a preserve-by-reference comment for failed/blocked Fabro runs."""
    if outcome.status not in {"blocked", "failed"}:
        return
    run_id = outcome.fabro_run_id
    server_url = _factory_server_url(args=args)
    if run_id is None or server_url is None:
        _write_comment(
            repo=repo,
            item_id=item.id,
            body=_missing_pointer_body(run_id=run_id, server_url=server_url),
            journal=journal,
            artifact_present=False,
        )
        return
    command_runner = runner if runner is not None else ShellCommandRunner()
    with tempfile.TemporaryDirectory(prefix=f"fabro-preserve-{item.id}-") as raw_dir:
        output_dir = Path(raw_dir)
        dumped = command_runner.run(
            argv=[
                str(args.fabro_bin),
                "dump",
                run_id,
                "--server",
                server_url,
                "-o",
                str(output_dir),
            ],
            cwd=repo,
            timeout_seconds=_DUMP_TIMEOUT_SECONDS,
        )
        artifact = output_dir / _ARTIFACT_PATH
        if dumped.exit_code != 0:
            body = _dump_failed_body(
                run_id=run_id,
                server_url=server_url,
                command=dumped,
            )
            artifact_present = False
        elif artifact.is_file():
            body = _artifact_pointer_body(
                run_id=run_id,
                server_url=server_url,
                artifact=artifact,
            )
            artifact_present = True
        else:
            body = _missing_artifact_body(run_id=run_id, server_url=server_url)
            artifact_present = False
    _write_comment(
        repo=repo,
        item_id=item.id,
        body=body,
        journal=journal,
        artifact_present=artifact_present,
    )


def _factory_server_url(*, args: argparse.Namespace) -> str | None:
    target = getattr(args, "fabro_factory_target", None)
    server = getattr(target, "server", None)
    return server if isinstance(server, str) and server else None


def _artifact_pointer_body(*, run_id: str, server_url: str, artifact: Path) -> str:
    data = artifact.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return "\n".join(
        [
            "livespec-preserve-by-reference",
            "",
            f"run id: {run_id}",
            f"factory server url: {server_url}",
            f"stage artifact path: {_ARTIFACT_PATH.as_posix()}",
            f"byte size: {len(data)}",
            f"sha256: {digest}",
            "",
            "retrieval command:",
            f"fabro dump {run_id} --server {server_url} -o <export-dir>",
            "",
            "After retrieval, verify:",
            ("sha256sum <export-dir>/" f"{_ARTIFACT_PATH.as_posix()} # must equal {digest}"),
            "",
            (
                "If the dump no longer resolves, the factory run storage may have "
                "been pruned or the factory may be temporarily unreachable; the "
                "recorded sha256 is the integrity check for any recovered artifact."
            ),
        ]
    )


def _missing_artifact_body(*, run_id: str, server_url: str) -> str:
    return "\n".join(
        [
            "livespec-preserve-by-reference",
            "",
            f"run id: {run_id}",
            f"factory server url: {server_url}",
            f"stage artifact path: {_ARTIFACT_PATH.as_posix()} (missing)",
            "artifact: run produced no checkpointed diff artifact",
            "byte size: (not recorded; artifact missing)",
            "sha256: (not recorded; artifact missing)",
            "",
            "retrieval command:",
            f"fabro dump {run_id} --server {server_url} -o <export-dir>",
        ]
    )


def _dump_failed_body(*, run_id: str, server_url: str, command: CommandResult) -> str:
    return "\n".join(
        [
            "livespec-preserve-by-reference",
            "",
            f"run id: {run_id}",
            f"factory server url: {server_url}",
            f"stage artifact path: {_ARTIFACT_PATH.as_posix()} (unverified)",
            f"artifact: fabro dump failed with exit code {command.exit_code}",
            f"stderr: {command.stderr.strip()}",
            "byte size: (not recorded; dump failed)",
            "sha256: (not recorded; dump failed)",
            (
                "resolution: retry the command below; if the same run/path remains "
                "unavailable while the factory is reachable, treat the reference as dangling."
            ),
            "",
            "retrieval command:",
            f"fabro dump {run_id} --server {server_url} -o <export-dir>",
        ]
    )


def _missing_pointer_body(*, run_id: str | None, server_url: str | None) -> str:
    return "\n".join(
        [
            "livespec-preserve-by-reference",
            "",
            f"run id: {run_id or '(unavailable)'}",
            f"factory server url: {server_url or '(unavailable)'}",
            f"stage artifact path: {_ARTIFACT_PATH.as_posix()} (unverified)",
            (
                "artifact: preserve reference could not be resolved because "
                "required pointer data was missing"
            ),
            "byte size: (not recorded; pointer incomplete)",
            "sha256: (not recorded; pointer incomplete)",
        ]
    )


def _write_comment(
    *,
    repo: Path,
    item_id: str,
    body: str,
    journal: _Journal,
    artifact_present: bool,
) -> None:
    written = attempt(
        action=lambda: make_beads_client(config=_comment_store_config(repo=repo)).add_comment(
            issue_id=item_id,
            body=body,
        ),
        exceptions=(*_LEDGER_WRITE_ERRORS, ConnectionPrefixMissingError),
    )
    if isinstance(written, AttemptFailure):
        journal.append(
            record={
                "stage": "preserve-by-reference-error",
                "work_item_id": item_id,
                "reason": f"{type(written.error).__name__}",
            }
        )
        return
    journal.append(
        record={
            "stage": "preserve-by-reference",
            "work_item_id": item_id,
            "artifact_path": _ARTIFACT_PATH.as_posix(),
            "artifact_present": artifact_present,
        }
    )


def _comment_store_config(*, repo: Path) -> StoreConfig:
    configured = attempt(
        action=lambda: store_config(repo=repo),
        exceptions=(ConnectionPrefixMissingError,),
    )
    if not isinstance(configured, AttemptFailure):
        return configured
    return StoreConfig(
        tenant="livespec-preserve-reference-test",
        prefix="livespec-preserve-reference-test",
        server_user="livespec-preserve-reference-test",
        database="livespec-preserve-reference-test",
        bd_path="bd",
        fake=True,
    )
