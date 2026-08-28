"""Unit-tier cover for the detection-coverage record surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._beads_client import make_beads_client, reset_fake_singleton
from livespec_orchestrator_beads_fabro.commands._detection_coverage import (
    ATTEMPT_MARKER_PREFIX,
    COMPLETED_MARKER_PREFIX,
    DRIFT_CAPTURE_OPERATION,
    GAP_CAPTURE_OPERATION,
    AnchorNotConfigured,
    DetectionRun,
    completed_coverage_is_claimable,
    completed_coverage_point,
    detection_coverage_anchor,
    record_detection_run,
    undisposed_candidates,
)
from livespec_orchestrator_beads_fabro.errors import BeadsMappingError
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem
from returns.result import Failure, Success

_ANCHOR = "bd-ib-anchor"


@pytest.fixture(autouse=True)
def _hermetic_fake_backend() -> object:
    reset_fake_singleton()
    yield
    reset_fake_singleton()


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="t",
        prefix="bd",
        server_user="t",
        database="t",
        bd_path="bd",
        fake=True,
    )


def _seed_anchor() -> None:
    from livespec_orchestrator_beads_fabro.store import append_work_item

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


def _write_config(*, root: Path, dispatcher: dict[str, object]) -> None:
    (root / ".livespec.jsonc").write_text(
        json.dumps({"livespec-orchestrator-beads-fabro": {"dispatcher": dispatcher}}),
        encoding="utf-8",
    )


def _run(**overrides: object) -> DetectionRun:
    fields: dict[str, object] = {
        "operation": GAP_CAPTURE_OPERATION,
        "scope": "v083",
        "invoker": "human:cw",
        "outcome": "succeeded",
        "exit_code": 0,
        "coverage_point": "v083",
    }
    fields.update(overrides)
    return DetectionRun(**fields)  # pyright: ignore[reportArgumentType]


def test_anchor_reads_the_committed_id(tmp_path: Path) -> None:
    _write_config(root=tmp_path, dispatcher={"detection_coverage_anchor": "  bd-ib-x  "})

    assert detection_coverage_anchor(cwd=tmp_path) == "bd-ib-x"


@pytest.mark.parametrize("dispatcher", [{}, {"detection_coverage_anchor": ""}])
def test_an_unprovisioned_anchor_answers_none(
    tmp_path: Path, dispatcher: dict[str, object]
) -> None:
    _write_config(root=tmp_path, dispatcher=dispatcher)

    assert detection_coverage_anchor(cwd=tmp_path) is None


def test_a_non_string_anchor_is_not_an_anchor(tmp_path: Path) -> None:
    _write_config(root=tmp_path, dispatcher={"detection_coverage_anchor": 7})

    assert detection_coverage_anchor(cwd=tmp_path) is None


def test_undisposed_candidates_preserves_surfaced_order() -> None:
    run = _run(surfaced_candidates=("gap-a", "gap-b", "gap-c"), disposed_candidates=("gap-b",))

    assert undisposed_candidates(run=run) == ("gap-a", "gap-c")


def test_a_complete_successful_pass_is_claimable() -> None:
    run = _run(surfaced_candidates=("gap-a",), disposed_candidates=("gap-a",))

    assert completed_coverage_is_claimable(run=run) is None


@pytest.mark.parametrize(
    ("overrides", "expected_fragment"),
    [
        ({"outcome": "interrupted"}, "outcome is 'interrupted'"),
        ({"exit_code": 1}, "exit code is 1"),
        ({"partial_range": True}, "covered only partially"),
        (
            {"surfaced_candidates": ("gap-a",), "disposed_candidates": ()},
            "1 surfaced candidate(s) undisposed: gap-a",
        ),
        ({"coverage_point": None}, "no coverage point to claim"),
    ],
)
def test_each_disqualifying_condition_names_itself(
    overrides: dict[str, object], expected_fragment: str
) -> None:
    reason = completed_coverage_is_claimable(run=_run(**overrides))

    assert reason is not None
    assert expected_fragment in reason


def test_a_complete_pass_appends_both_records() -> None:
    _seed_anchor()

    result = record_detection_run(path=_config(), anchor=_ANCHOR, run=_run())

    assert isinstance(result, Success)
    records = result.unwrap()
    assert records.attempt.startswith(ATTEMPT_MARKER_PREFIX)
    assert records.completed is not None
    assert records.completed.startswith(COMPLETED_MARKER_PREFIX)
    assert records.withheld_reason is None


def test_an_aborted_pass_appends_only_the_attempt_and_says_why() -> None:
    _seed_anchor()

    result = record_detection_run(path=_config(), anchor=_ANCHOR, run=_run(exit_code=2))

    records = result.unwrap()
    bodies = [
        str(comment["text"])
        for comment in make_beads_client(config=_config()).list_comments(issue_id=_ANCHOR)
    ]
    assert records.completed is None
    assert records.withheld_reason is not None
    assert [body.startswith(ATTEMPT_MARKER_PREFIX) for body in bodies] == [True]


@pytest.mark.parametrize("anchor", [None, "   "])
def test_an_unconfigured_anchor_refuses_the_write(anchor: str | None) -> None:
    result = record_detection_run(path=_config(), anchor=anchor, run=_run())

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), AnchorNotConfigured)
    assert "capture-work-item" in result.failure().detail


def test_the_newest_completed_point_for_the_operation_wins() -> None:
    _seed_anchor()
    _ = record_detection_run(path=_config(), anchor=_ANCHOR, run=_run(coverage_point="v080"))
    _ = record_detection_run(path=_config(), anchor=_ANCHOR, run=_run(coverage_point="v083"))
    _ = record_detection_run(
        path=_config(),
        anchor=_ANCHOR,
        run=_run(operation=DRIFT_CAPTURE_OPERATION, coverage_point="deadbee"),
    )

    assert (
        completed_coverage_point(path=_config(), anchor=_ANCHOR, operation=GAP_CAPTURE_OPERATION)
        == "v083"
    )
    assert (
        completed_coverage_point(path=_config(), anchor=_ANCHOR, operation=DRIFT_CAPTURE_OPERATION)
        == "deadbee"
    )


def test_an_aborted_pass_leaves_the_prior_completed_point_standing() -> None:
    _seed_anchor()
    _ = record_detection_run(path=_config(), anchor=_ANCHOR, run=_run(coverage_point="v080"))
    _ = record_detection_run(
        path=_config(),
        anchor=_ANCHOR,
        run=_run(coverage_point="v083", surfaced_candidates=("gap-a",)),
    )

    assert (
        completed_coverage_point(path=_config(), anchor=_ANCHOR, operation=GAP_CAPTURE_OPERATION)
        == "v080"
    )


@pytest.mark.parametrize("anchor", [None, "  "])
def test_no_anchor_means_no_completed_point(anchor: str | None) -> None:
    assert (
        completed_coverage_point(path=_config(), anchor=anchor, operation=GAP_CAPTURE_OPERATION)
        is None
    )


def test_an_anchor_naming_no_live_row_reads_as_no_completed_point() -> None:
    assert (
        completed_coverage_point(
            path=_config(), anchor="bd-ib-typo", operation=GAP_CAPTURE_OPERATION
        )
        is None
    )


def test_the_write_half_refuses_loudly_when_the_anchor_names_no_live_row() -> None:
    with pytest.raises(BeadsMappingError):
        _ = record_detection_run(path=_config(), anchor="bd-ib-typo", run=_run())


@pytest.mark.parametrize(
    "body",
    [
        "an unrelated operator rider",
        COMPLETED_MARKER_PREFIX + "not json at all",
        COMPLETED_MARKER_PREFIX + '["a list, not an object"]',
        COMPLETED_MARKER_PREFIX + json.dumps({"operation": GAP_CAPTURE_OPERATION}),
        COMPLETED_MARKER_PREFIX
        + json.dumps({"operation": GAP_CAPTURE_OPERATION, "coverage_point": ""}),
        COMPLETED_MARKER_PREFIX
        + json.dumps({"operation": GAP_CAPTURE_OPERATION, "coverage_point": 83}),
    ],
)
def test_an_unusable_record_is_skipped_rather_than_blinding_the_read(body: str) -> None:
    _seed_anchor()
    make_beads_client(config=_config()).add_comment(issue_id=_ANCHOR, body=body)

    assert (
        completed_coverage_point(path=_config(), anchor=_ANCHOR, operation=GAP_CAPTURE_OPERATION)
        is None
    )
