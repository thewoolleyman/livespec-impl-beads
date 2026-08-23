"""Comment-body builders for Fabro preserve-by-reference records."""

from __future__ import annotations

import hashlib
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_overlay import (
    escape_minijinja_literal,
)

__all__: list[str] = [
    "FABRO_DIFF_ARTIFACT_GLOB",
    "artifact_pointer_body",
    "dump_failed_body",
    "error_pointer_body",
    "missing_artifact_body",
]

FABRO_DIFF_ARTIFACT_GLOB = "stages/*/diff.patch"
_MAX_STDERR_CHARS = 1000


def artifact_pointer_body(
    *,
    run_id: str,
    server_url: str,
    artifacts: tuple[Path, ...],
    export_dir: Path,
) -> tuple[str, str]:
    artifact_lines: list[str] = []
    verification_lines: list[str] = []
    digests: list[str] = []
    for artifact in artifacts:
        data = artifact.read_bytes()
        relative_path = artifact.relative_to(export_dir).as_posix()
        digest = hashlib.sha256(data).hexdigest()
        digests.append(digest)
        artifact_lines.append(f"stage artifact path: {relative_path}")
        artifact_lines.append(f"byte size: {len(data)}")
        artifact_lines.append(f"sha256: {digest}")
        verification_lines.append(f"sha256sum <export-dir>/{relative_path} # must equal {digest}")
    return (
        "\n".join(
            [
                "livespec-preserve-by-reference",
                "",
                f"run id: {run_id}",
                f"factory server url: {server_url}",
                *artifact_lines,
                "",
                "retrieval command:",
                f"fabro dump {run_id} --server {server_url} -o <export-dir>",
                "",
                "After retrieval, verify:",
                *verification_lines,
                "",
                (
                    "If the dump no longer resolves, the factory run storage may have "
                    "been pruned or the factory may be temporarily unreachable; the "
                    "recorded sha256 is the integrity check for any recovered artifact."
                ),
            ]
        ),
        ",".join(digests),
    )


def missing_artifact_body(*, run_id: str, server_url: str) -> tuple[str, str]:
    digest = "(not recorded; artifact missing)"
    return (
        "\n".join(
            [
                "livespec-preserve-by-reference",
                "",
                f"run id: {run_id}",
                f"factory server url: {server_url}",
                f"stage artifact path: {FABRO_DIFF_ARTIFACT_GLOB} (none found)",
                "artifact: run produced no checkpointed diff artifact",
                "byte size: (not recorded; artifact missing)",
                f"sha256: {digest}",
                "",
                "retrieval command:",
                f"fabro dump {run_id} --server {server_url} -o <export-dir>",
            ]
        ),
        digest,
    )


def dump_failed_body(
    *,
    run_id: str,
    server_url: str,
    command: CommandResult,
) -> tuple[str, str]:
    digest = "(not recorded; dump failed)"
    return (
        "\n".join(
            [
                "livespec-preserve-by-reference",
                "",
                f"run id: {run_id}",
                f"factory server url: {server_url}",
                f"stage artifact path: {FABRO_DIFF_ARTIFACT_GLOB} (unverified)",
                f"artifact: fabro dump failed with exit code {command.exit_code}",
                f"stderr: {comment_safe_external_text(text=command.stderr)}",
                "byte size: (not recorded; dump failed)",
                f"sha256: {digest}",
                (
                    "resolution: retry the command below; if the same run/path remains "
                    "unavailable while the factory is reachable, treat the reference as dangling."
                ),
                "",
                "retrieval command:",
                f"fabro dump {run_id} --server {server_url} -o <export-dir>",
            ]
        ),
        digest,
    )


def error_pointer_body(
    *,
    run_id: str,
    server_url: str,
    error: Exception,
) -> tuple[str, str]:
    digest = "(not recorded; preserve step failed)"
    return (
        "\n".join(
            [
                "livespec-preserve-by-reference",
                "",
                f"run id: {run_id}",
                f"factory server url: {server_url}",
                f"stage artifact path: {FABRO_DIFF_ARTIFACT_GLOB} (unverified)",
                f"artifact: preserve reference failed with {type(error).__name__}",
                f"error: {comment_safe_external_text(text=str(error))}",
                "byte size: (not recorded; preserve step failed)",
                f"sha256: {digest}",
            ]
        ),
        digest,
    )


def comment_safe_external_text(*, text: str) -> str:
    stripped = text.strip()
    bounded = stripped
    if len(stripped) > _MAX_STDERR_CHARS:
        bounded = f"{stripped[:_MAX_STDERR_CHARS]}\n[truncated]"
    escaped = escape_minijinja_literal(text=bounded)
    return escaped.replace("{{", "[[").replace("{%", "[%").replace("{#", "[#")
