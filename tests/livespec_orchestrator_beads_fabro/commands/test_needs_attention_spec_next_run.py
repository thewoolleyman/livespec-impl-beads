"""Tests for the cross-plane spec-`next` runner behind the attention snapshot."""

import json
import shlex
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._needs_attention_spec_next_run import (
    SpecNextSeam,
    _SpecNextResult,
    spec_next,
)


def _seam(
    *,
    command: list[str] | None,
    result: _SpecNextResult | None = None,
    raises: Exception | None = None,
    calls: dict[str, object] | None = None,
) -> SpecNextSeam:
    """Build an injectable spec-`next` seam with a fake resolver + runner."""

    def _resolve(*, project_root: Path) -> list[str] | None:
        _ = project_root
        return command

    def _run(*, argv: list[str]) -> _SpecNextResult:
        if calls is not None:
            calls["argv"] = argv
            calls["run"] = True
        if raises is not None:
            raise raises
        assert result is not None
        return result

    return SpecNextSeam(resolve_command=_resolve, run=_run)


# --------------------------------------------------------------------------
# `spec_next` — invoke CORE spec-`next` cross-plane via an injected seam,
# adapt the top candidate, and fail soft (never emit a pointer).
# --------------------------------------------------------------------------


def test_spec_next_inlines_top_actionable_candidate(tmp_path) -> None:
    stdout = json.dumps(
        {
            "candidates": [
                {
                    "action": "revise",
                    "reason": "proposed change pending; queue depth 1",
                    "urgency": "high",
                    "target": "proposed_changes/owned-heading-coverage-todos.md",
                },
                {"action": "prune-history", "reason": "many versions", "urgency": "low"},
            ]
        }
    )
    calls: dict[str, object] = {}
    seam = _seam(
        command=["python3", "/core/scripts/bin/next.py"],
        result=_SpecNextResult(stdout=stdout, returncode=0),
        calls=calls,
    )

    output = spec_next(project_root=tmp_path, seam=seam)

    assert output is not None
    assert output.op == "revise"
    assert output.spec_target == "proposed_changes/owned-heading-coverage-todos.md"
    assert output.summary == "proposed change pending; queue depth 1"
    assert output.urgency == "high"
    assert output.command == (
        f"codex exec livespec:revise --project-root {shlex.quote(str(tmp_path))} < /dev/null"
    )
    assert calls["argv"] == [
        "python3",
        "/core/scripts/bin/next.py",
        "--project-root",
        str(tmp_path),
    ]


def test_spec_next_returns_none_when_candidates_empty(tmp_path) -> None:
    seam = _seam(
        command=["python3", "/core/next.py"],
        result=_SpecNextResult(stdout=json.dumps({"candidates": []}), returncode=0),
    )
    assert spec_next(project_root=tmp_path, seam=seam) is None


def test_spec_next_returns_none_when_seam_run_raises(tmp_path) -> None:
    import subprocess

    seam = _seam(
        command=["python3", "/core/next.py"],
        raises=subprocess.SubprocessError("boom"),
    )
    assert spec_next(project_root=tmp_path, seam=seam) is None


def test_spec_next_returns_none_when_cli_exits_nonzero(tmp_path) -> None:
    seam = _seam(
        command=["python3", "/core/next.py"],
        result=_SpecNextResult(stdout="", returncode=2),
    )
    assert spec_next(project_root=tmp_path, seam=seam) is None


def test_spec_next_returns_none_when_stdout_unparseable(tmp_path) -> None:
    seam = _seam(
        command=["python3", "/core/next.py"],
        result=_SpecNextResult(stdout="not json at all", returncode=0),
    )
    assert spec_next(project_root=tmp_path, seam=seam) is None


def test_spec_next_does_not_run_cli_when_unresolvable(tmp_path) -> None:
    calls: dict[str, object] = {}
    seam = _seam(command=None, result=_SpecNextResult(stdout="{}", returncode=0), calls=calls)

    assert spec_next(project_root=tmp_path, seam=seam) is None
    assert "run" not in calls
