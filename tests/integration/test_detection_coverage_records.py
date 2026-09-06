"""Integration-tier acceptance for detection coverage records and staleness facts.

Drives the detection coverage-record contract in `SPECIFICATION/contracts.md`
end to end rather than against hand-built fixtures:

- The RECORD half runs through the real store/client seam against the in-memory
  `FakeBeadsClient`, so the attempt and completed records are the ones a real
  detection run would append to a real anchor.
- The STALENESS half composes the actual `needs-attention` snapshot through
  `build_attention`, so the two facts are read back off the wire the operator
  actually receives — not from the lane function in isolation.

That pairing is the point. The all-or-nothing rule is only meaningful if a
withheld completed record actually leaves the derived fact standing, and only a
test that writes the records and THEN composes the snapshot can observe both
halves of that.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._beads_client import make_beads_client, reset_fake_singleton
from livespec_orchestrator_beads_fabro.commands import needs_attention
from livespec_orchestrator_beads_fabro.commands._detection_coverage import (
    ATTEMPT_MARKER_PREFIX,
    COMPLETED_MARKER_PREFIX,
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
from livespec_orchestrator_beads_fabro.commands.needs_attention import build_attention
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem
from livespec_runtime.needs_attention import SpecNextOutput

_ANCHOR = "bd-ib-anchor"
_GAP_FACT_ID = "hygiene:gap-capture-staleness:repo"
_DRIFT_FACT_ID = "hygiene:drift-staleness:repo"
_RATIFIED_VERSIONS = 83


@dataclass(kw_only=True)
class _StubRunner:
    """A CommandRunner answering the two git reads the drift lane makes."""

    merge_count: str
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
        if argv[1] == "symbolic-ref":
            return CommandResult(exit_code=0, stdout="origin/master\n", stderr="")
        return CommandResult(exit_code=0, stdout=self.merge_count, stderr="")


@pytest.fixture(autouse=True)
def _hermetic_fake_backend() -> object:
    reset_fake_singleton()
    yield
    reset_fake_singleton()


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-orch-beads-fabro",
        prefix="bd-ib",
        server_user="livespec-orch-beads-fabro",
        database="livespec-orch-beads-fabro",
        bd_path="bd",
        fake=True,
    )


def _seed(*, id_: str, title: str) -> None:
    append_work_item(
        path=_config(),
        item=WorkItem(
            id=id_,
            type="task",
            status="backlog",
            title=title,
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


def _write_project(*, root: Path, threshold: int = 1) -> None:
    for version in range(1, _RATIFIED_VERSIONS + 1):
        (root / "SPECIFICATION" / "history" / f"v{version:03d}").mkdir(parents=True)
    (root / ".livespec.jsonc").write_text(
        json.dumps(
            {
                "livespec-orchestrator-beads-fabro": {
                    "connection": {
                        "tenant": "livespec-orch-beads-fabro",
                        "prefix": "bd-ib",
                        "server_user": "livespec-orch-beads-fabro",
                        "database": "livespec-orch-beads-fabro",
                        "bd_path": "bd",
                        "fake": True,
                    },
                    "dispatcher": {
                        "detection_coverage_anchor": _ANCHOR,
                        "drift_capture_merge_threshold": threshold,
                    },
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _gap_run(**overrides: object) -> DetectionRun:
    fields: dict[str, object] = {
        "operation": GAP_CAPTURE_OPERATION,
        "scope": f"v{_RATIFIED_VERSIONS:03d}",
        "invoker": "human:maintainer",
        "outcome": "succeeded",
        "exit_code": 0,
        "surfaced_candidates": ("gap-aaaa", "gap-bbbb"),
        "disposed_candidates": ("gap-aaaa", "gap-bbbb"),
        "coverage_point": f"v{_RATIFIED_VERSIONS:03d}",
    }
    fields.update(overrides)
    return DetectionRun(**fields)  # pyright: ignore[reportArgumentType]


def _anchor_bodies() -> list[str]:
    return [
        str(comment["text"])
        for comment in make_beads_client(config=_config()).list_comments(issue_id=_ANCHOR)
    ]


def _no_spec_next(*, project_root: Path) -> SpecNextOutput | None:
    _ = project_root
    return None


def _snapshot_ids(*, root: Path, monkeypatch: pytest.MonkeyPatch) -> set[str]:
    """Compose the real needs-attention snapshot and return its stable ids."""
    monkeypatch.setattr(needs_attention, "spec_next", _no_spec_next)
    return {
        item.id
        for item in build_attention(project_root=root, repo_name="repo", include_hygiene=False)
    }


def _staleness_items(*, root: Path, merge_count: str = "4") -> dict[str, str]:
    composed = detection_staleness_items(
        project_root=root,
        repo="repo",
        config=_config(),
        seams=DetectionStalenessSeams(runner=_StubRunner(merge_count=merge_count)),
    )
    return {item.id: item.summary + "\n" + item.handoff.command for item in composed}


def test_a_complete_pass_writes_both_records_and_clears_the_gap_staleness_fact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project(root=tmp_path)
    _seed(id_=_ANCHOR, title="detection coverage anchor")
    assert _GAP_FACT_ID in _staleness_items(root=tmp_path)

    outcome = record_detection_run(path=_config(), anchor=_ANCHOR, run=_gap_run())

    records = outcome.unwrap()
    bodies = _anchor_bodies()
    assert records.withheld_reason is None
    assert [body.split(":")[0] for body in bodies] == [
        ATTEMPT_MARKER_PREFIX.rstrip(": "),
        COMPLETED_MARKER_PREFIX.rstrip(": "),
    ]
    assert _GAP_FACT_ID not in _snapshot_ids(root=tmp_path, monkeypatch=monkeypatch)


@pytest.mark.parametrize(
    ("overrides", "case"),
    [
        ({"exit_code": 1, "outcome": "failed"}, "a non-zero exit"),
        ({"outcome": "interrupted"}, "an interruption"),
        ({"disposed_candidates": ("gap-aaaa",)}, "an unresolved candidate"),
        ({"partial_range": True}, "a partial range"),
    ],
)
def test_an_aborted_or_partial_pass_writes_no_completed_record_and_leaves_the_point_standing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, overrides: dict[str, object], case: str
) -> None:
    _write_project(root=tmp_path)
    _seed(id_=_ANCHOR, title="detection coverage anchor")
    _ = record_detection_run(
        path=_config(),
        anchor=_ANCHOR,
        run=_gap_run(coverage_point="v080", scope="v080"),
    )

    outcome = record_detection_run(path=_config(), anchor=_ANCHOR, run=_gap_run(**overrides))

    records = outcome.unwrap()
    completed = [body for body in _anchor_bodies() if body.startswith(COMPLETED_MARKER_PREFIX)]
    assert records.completed is None, case
    assert records.withheld_reason is not None, case
    # The prior completed point stands: exactly one completed record exists and
    # it still carries v080, so the derived fact is unchanged and still live.
    assert len(completed) == 1, case
    assert '"coverage_point": "v080"' in completed[0], case
    assert _GAP_FACT_ID in _snapshot_ids(root=tmp_path, monkeypatch=monkeypatch), case


def test_recording_a_run_touches_nothing_in_the_ledger_but_the_anchor(tmp_path: Path) -> None:
    _write_project(root=tmp_path)
    _seed(id_=_ANCHOR, title="detection coverage anchor")
    _seed(id_="bd-ib-bystander", title="an unrelated work-item")
    client = make_beads_client(config=_config())
    before = json.dumps(client.list_issues(), sort_keys=True)

    _ = record_detection_run(path=_config(), anchor=_ANCHOR, run=_gap_run())

    assert json.dumps(client.list_issues(), sort_keys=True) == before
    assert client.list_comments(issue_id="bd-ib-bystander") == []
    assert len(_anchor_bodies()) == 2


def test_the_gap_staleness_fact_hands_off_to_capture_impl_gaps(tmp_path: Path) -> None:
    _write_project(root=tmp_path)
    _seed(id_=_ANCHOR, title="detection coverage anchor")
    _ = record_detection_run(
        path=_config(), anchor=_ANCHOR, run=_gap_run(coverage_point="v080", scope="v080")
    )

    rendered = _staleness_items(root=tmp_path)[_GAP_FACT_ID]

    assert "capture-impl-gaps" in rendered
    assert "v081..v083" in rendered


def test_merges_at_the_threshold_hand_off_to_capture_spec_drift(tmp_path: Path) -> None:
    _write_project(root=tmp_path, threshold=4)
    _seed(id_=_ANCHOR, title="detection coverage anchor")
    _ = record_detection_run(
        path=_config(),
        anchor=_ANCHOR,
        run=_gap_run(
            operation=DRIFT_CAPTURE_OPERATION, coverage_point="deadbeef", scope="whole tree"
        ),
    )

    rendered = _staleness_items(root=tmp_path, merge_count="4")[_DRIFT_FACT_ID]

    assert "capture-spec-drift" in rendered
    assert "deadbeef" in rendered
    assert "no class of commit excluded" in rendered


def test_merges_below_the_threshold_surface_no_drift_fact(tmp_path: Path) -> None:
    _write_project(root=tmp_path, threshold=9)
    _seed(id_=_ANCHOR, title="detection coverage anchor")

    assert _DRIFT_FACT_ID not in _staleness_items(root=tmp_path, merge_count="4")


def test_composing_the_snapshot_invokes_no_detector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project(root=tmp_path)
    _seed(id_=_ANCHOR, title="detection coverage anchor")
    runner = _StubRunner(merge_count="4")

    _ = detection_staleness_items(
        project_root=tmp_path,
        repo="repo",
        config=_config(),
        seams=DetectionStalenessSeams(runner=runner),
    )

    # The lane's ONLY subprocess reads are the two git lookups. Nothing it runs
    # is a detection skill: both facts are surfaced triggers, never runs.
    assert [argv[0] for argv in runner.argvs] == ["git", "git"]
    assert _GAP_FACT_ID in _snapshot_ids(root=tmp_path, monkeypatch=monkeypatch)
    assert _anchor_bodies() == []
