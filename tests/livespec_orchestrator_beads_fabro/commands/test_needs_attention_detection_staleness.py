"""Unit-tier cover for the two detection-staleness attention lanes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._beads_client import reset_fake_singleton
from livespec_orchestrator_beads_fabro.commands._detection_coverage import (
    DRIFT_CAPTURE_OPERATION,
    GAP_CAPTURE_OPERATION,
    DetectionRun,
    record_detection_run,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._needs_attention_detection_staleness import (
    DetectionStalenessSeams,
    detection_staleness_items,
)
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

_ANCHOR = "bd-ib-anchor"
_GAP_ID = "hygiene:gap-capture-staleness:repo"
_DRIFT_ID = "hygiene:drift-staleness:repo"


@dataclass(kw_only=True)
class _StubRunner:
    """A CommandRunner whose answers are keyed by the first two argv words."""

    answers: dict[str, CommandResult]
    argvs: list[list[str]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env, stdin)
        self.argvs.append(argv)
        return self.answers.get(argv[1], CommandResult(exit_code=1, stdout="", stderr=""))


@pytest.fixture(autouse=True)
def _hermetic_fake_backend() -> object:
    reset_fake_singleton()
    yield
    reset_fake_singleton()


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="t", prefix="bd", server_user="t", database="t", bd_path="bd", fake=True
    )


def _seed_anchor() -> None:
    append_work_item(
        path=_config(),
        item=WorkItem(
            id=_ANCHOR,
            type="task",
            status="backlog",
            title="detection coverage anchor",
            description="d",
            origin="freeform",
            gap_id=None,
            rank="a0",
            assignee=None,
            depends_on=(),
            captured_at="2026-08-01T00:00:00Z",
            resolution=None,
            reason=None,
            audit=None,
            superseded_by=None,
            blocked_reason=None,
            factory_safety=None,
            admission_policy=None,
            acceptance_policy=None,
            spec_commitment_hint=None,
        ),
    )


def _record(*, operation: str, coverage_point: str) -> None:
    _ = record_detection_run(
        path=_config(),
        anchor=_ANCHOR,
        run=DetectionRun(
            operation=operation,
            scope="whole tree",
            invoker="human:cw",
            outcome="succeeded",
            exit_code=0,
            coverage_point=coverage_point,
        ),
    )


def _project(*, root: Path, versions: int, anchor: str = _ANCHOR, threshold: int = 1) -> None:
    for version in range(1, versions + 1):
        (root / "SPECIFICATION" / "history" / f"v{version:03d}").mkdir(parents=True)
    (root / ".livespec.jsonc").write_text(
        json.dumps(
            {
                "livespec-orchestrator-beads-fabro": {
                    "dispatcher": {
                        "detection_coverage_anchor": anchor,
                        "drift_capture_merge_threshold": threshold,
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def _runner(*, branch: str = "master", count: str = "0", count_exit: int = 0) -> _StubRunner:
    return _StubRunner(
        answers={
            "symbolic-ref": CommandResult(exit_code=0, stdout=f"origin/{branch}\n", stderr=""),
            "rev-list": CommandResult(exit_code=count_exit, stdout=count, stderr=""),
        }
    )


def _items(*, root: Path, runner: _StubRunner) -> dict[str, str]:
    composed = detection_staleness_items(
        project_root=root,
        repo="repo",
        config=_config(),
        seams=DetectionStalenessSeams(runner=runner),
    )
    return {item.id: item.handoff.command for item in composed}


def test_a_ratified_revision_past_the_covered_point_surfaces_the_gap_backstop(
    tmp_path: Path,
) -> None:
    _seed_anchor()
    _record(operation=GAP_CAPTURE_OPERATION, coverage_point="v080")
    _project(root=tmp_path, versions=83)

    commands = _items(root=tmp_path, runner=_runner())

    assert "capture-impl-gaps" in commands[_GAP_ID]
    assert "--since-version v080" in commands[_GAP_ID]


def test_the_gap_backstop_names_the_stale_range_it_covers(tmp_path: Path) -> None:
    _seed_anchor()
    _record(operation=GAP_CAPTURE_OPERATION, coverage_point="v080")
    _project(root=tmp_path, versions=83)

    composed = detection_staleness_items(
        project_root=tmp_path,
        repo="repo",
        config=_config(),
        seams=DetectionStalenessSeams(runner=_runner()),
    )

    gap = next(item for item in composed if item.id == _GAP_ID)
    assert "v081..v083" in gap.summary
    assert gap.kind == "hygiene"


def test_an_unprovisioned_anchor_still_surfaces_the_gap_backstop(tmp_path: Path) -> None:
    _project(root=tmp_path, versions=2, anchor="")

    commands = _items(root=tmp_path, runner=_runner())

    assert "--since-version" not in commands[_GAP_ID]


def test_a_completed_pass_at_the_ratified_revision_clears_the_gap_backstop(
    tmp_path: Path,
) -> None:
    _seed_anchor()
    _record(operation=GAP_CAPTURE_OPERATION, coverage_point="v083")
    _project(root=tmp_path, versions=83)

    assert _GAP_ID not in _items(root=tmp_path, runner=_runner())


def test_a_repository_with_no_ratified_revision_surfaces_no_gap_backstop(tmp_path: Path) -> None:
    _project(root=tmp_path, versions=0)

    assert _GAP_ID not in _items(root=tmp_path, runner=_runner())


def test_an_unparseable_recorded_point_reads_as_no_coverage(tmp_path: Path) -> None:
    _seed_anchor()
    _record(operation=GAP_CAPTURE_OPERATION, coverage_point="not-a-version")
    _project(root=tmp_path, versions=2)

    assert "--since-version" not in _items(root=tmp_path, runner=_runner())[_GAP_ID]


def test_merges_at_the_threshold_surface_the_drift_fact(tmp_path: Path) -> None:
    _seed_anchor()
    _record(operation=DRIFT_CAPTURE_OPERATION, coverage_point="deadbee")
    _project(root=tmp_path, versions=1, threshold=2)
    runner = _runner(count="2")

    commands = _items(root=tmp_path, runner=runner)

    assert "capture-spec-drift" in commands[_DRIFT_ID]
    assert ["git", "rev-list", "--count", "deadbee..origin/master"] in runner.argvs


def test_the_drift_fact_states_that_merge_counting_excludes_nothing(tmp_path: Path) -> None:
    _project(root=tmp_path, versions=1, anchor="")

    composed = detection_staleness_items(
        project_root=tmp_path,
        repo="repo",
        config=_config(),
        seams=DetectionStalenessSeams(runner=_runner(count="9")),
    )

    drift = next(item for item in composed if item.id == _DRIFT_ID)
    assert "no class of commit excluded" in drift.summary
    assert "none on record" in drift.summary


def test_merges_below_the_threshold_surface_no_drift_fact(tmp_path: Path) -> None:
    _project(root=tmp_path, versions=1, threshold=5)

    assert _DRIFT_ID not in _items(root=tmp_path, runner=_runner(count="4"))


@pytest.mark.parametrize(
    "symbolic_ref",
    [
        CommandResult(exit_code=128, stdout="", stderr="not a git repository"),
        CommandResult(exit_code=0, stdout="  \n", stderr=""),
    ],
)
def test_an_unresolvable_default_branch_surfaces_no_drift_fact(
    tmp_path: Path, symbolic_ref: CommandResult
) -> None:
    _project(root=tmp_path, versions=1)
    runner = _StubRunner(answers={"symbolic-ref": symbolic_ref})

    assert _DRIFT_ID not in _items(root=tmp_path, runner=runner)


def test_the_drift_lane_never_falls_back_to_the_forge(tmp_path: Path) -> None:
    _project(root=tmp_path, versions=1)
    runner = _StubRunner(answers={"symbolic-ref": CommandResult(exit_code=1, stdout="", stderr="")})

    _ = _items(root=tmp_path, runner=runner)

    assert [argv[0] for argv in runner.argvs] == ["git"]


@pytest.mark.parametrize(
    ("count", "count_exit"),
    [("3", 128), ("not a number", 0)],
)
def test_an_unusable_merge_count_surfaces_no_drift_fact(
    tmp_path: Path, count: str, count_exit: int
) -> None:
    _project(root=tmp_path, versions=1)

    assert _DRIFT_ID not in _items(
        root=tmp_path, runner=_runner(count=count, count_exit=count_exit)
    )
