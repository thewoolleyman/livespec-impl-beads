"""Tests for dispatcher Fabro failure-detail parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_failure import (
    FabroFailureDetail,
    fabro_failure_outcome_detail,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroPort, FabroTarget


@dataclass(kw_only=True)
class _Runner:
    stdout: str

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (argv, cwd, timeout_seconds, env, stdin)
        return CommandResult(exit_code=0, stdout=self.stdout, stderr="")


def test_fabro_port_inspect_extracts_nested_failure_block(tmp_path: Path) -> None:
    detail = _inspect_failure(
        tmp_path=tmp_path,
        stdout=(
            '{"events": [{"payload": {"failure": {'
            '"causes": [7, "script failed with exit 2"], '
            '"category": "deterministic", '
            '"signature": "fix|deterministic|script failed"}}}]}'
        ),
    )

    assert detail == FabroFailureDetail(
        cause="script failed with exit 2",
        category="deterministic",
        signature="fix|deterministic|script failed",
    )


def test_fabro_port_inspect_returns_none_for_unusable_payloads(tmp_path: Path) -> None:
    assert _inspect_failure(tmp_path=tmp_path, stdout="not json") is None
    assert _inspect_failure(tmp_path=tmp_path, stdout="[]") is None
    assert _inspect_failure(tmp_path=tmp_path, stdout='{"failure": {"causes": [7, "  "]}}') is None
    assert _inspect_failure(tmp_path=tmp_path, stdout='{"failure": "not an object"}') is None


def test_fabro_port_inspect_accepts_category_without_causes(tmp_path: Path) -> None:
    detail = _inspect_failure(
        tmp_path=tmp_path, stdout='{"failure": {"causes": "not a list", "category": "infra"}}'
    )

    assert detail == FabroFailureDetail(cause=None, category="infra", signature=None)


def test_fabro_failure_outcome_detail_formats_available_fields() -> None:
    assert (
        fabro_failure_outcome_detail(
            failure=FabroFailureDetail(
                cause=None,
                category="deterministic",
                signature="fix|deterministic|script failed",
            ),
            fallback="ACP turn failed",
        )
        == "category=deterministic; signature=fix|deterministic|script failed"
    )
    assert (
        fabro_failure_outcome_detail(failure=None, fallback="ACP turn failed") == "ACP turn failed"
    )
    assert (
        fabro_failure_outcome_detail(
            failure=FabroFailureDetail(cause=None, category=None, signature=None),
            fallback="ACP turn failed",
        )
        == "ACP turn failed"
    )


def _inspect_failure(*, tmp_path: Path, stdout: str) -> FabroFailureDetail | None:
    return (
        FabroPort(
            fabro_bin="fabro",
            target=FabroTarget(),
            runner=_Runner(stdout=stdout),
            cwd=tmp_path,
        )
        .inspect(run_id="01RUN", timeout_seconds=1)
        .failure
    )
