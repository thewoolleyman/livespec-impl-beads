"""Tests for the loop probe's ordered drive and its confinement gate (v076).

EVERY case runs against an injected `_RecordingCycle`; nothing reaches the live
Dispatcher. That recorder is the instrument that makes the confinement contract
checkable rather than merely asserted: it records each stage it is asked for, so
"fails WITHOUT merging" is verified by the ABSENCE of `merge` from that list,
not by reading the implementation and believing it.

The source-unavailability group is separate because it fails at three different
points -- the before-snapshot, the published change, and the after-snapshot --
and the contract's refusal to read an unread surface as clear has to hold at
each of them independently.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_confinement import (
    PROBE_DIRECTORY,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_cycle import (
    ProbeMerge,
    ProbeObservation,
    ProbePublish,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_drive import run_probe_cycle
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_report import (
    CONFINEMENT_ESCAPE_OUTCOME,
    MERGED_ESCAPE_OUTCOME,
    PASSED_OUTCOME,
    STAGE_FAILED_OUTCOME,
    ProbeResult,
    probe_run_identifier,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_residue import (
    SOURCE_UNAVAILABLE_OUTCOME,
    ResidueSnapshot,
    ResidueSource,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

_ITEM = "bd-ib-probe"
_ARTIFACT = f"{PROBE_DIRECTORY}/latest.md"
_TWO_ASSERTIONS = "The probe refuses without an item.\nThe probe never files one.\n"
_EXIT_PRECONDITION_ERROR = 3
_EXIT_FAILURE = 1
_INVOKER = "operator:probe-test"


def _item(**overrides: object) -> WorkItem:
    base = WorkItem(
        id=_ITEM,
        type="task",
        status="ready",
        title="A probe fixture",
        description="Drive the loop.",
        origin="freeform",
        gap_id=None,
        rank="a2",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-28T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy="ai-only",
        acceptance_criteria=_TWO_ASSERTIONS,
    )
    return replace(base, **overrides)


class _StaticSource:
    """A residue source answering with one fixed snapshot per call."""

    def __init__(self, *, snapshots: list[ResidueSnapshot]) -> None:
        self.snapshots: list[ResidueSnapshot] = snapshots

    def snapshot(self) -> ResidueSnapshot:
        return self.snapshots.pop(0) if len(self.snapshots) > 1 else self.snapshots[0]


class _RecordingCycle:
    """A `ProbeCycle` recording which stages the probe actually asked it for."""

    def __init__(
        self,
        *,
        published: ProbePublish | None = None,
        merged: ProbeMerge | None = None,
        observation: ProbeObservation | None = None,
        status: str = "done",
    ) -> None:
        self.calls: list[str] = []
        self.status: str = status
        self.published: ProbePublish = published or ProbePublish(
            branch=f"feat/{_ITEM}", paths=(_ARTIFACT,)
        )
        self.merged: ProbeMerge = merged or ProbeMerge(
            merged=True, merge_commit="abc1234", merged_paths=(_ARTIFACT,)
        )
        self.observation: ProbeObservation = observation or ProbeObservation(
            step_outcomes=({"step": "master-ci", "status": "passed"},),
            verdict="PASS",
            absent_evidence=(),
            item_status=status,
        )

    def publish(self, *, work_item_id: str) -> ProbePublish:
        self.calls.append(f"publish:{work_item_id}")
        return self.published

    def merge(self, *, published: ProbePublish) -> ProbeMerge:
        _ = published
        self.calls.append("merge")
        return self.merged

    def observe(self, *, work_item_id: str) -> ProbeObservation:
        _ = work_item_id
        self.calls.append("observe")
        return self.observation

    def item_status(self, *, work_item_id: str) -> str:
        _ = work_item_id
        return self.status


def _clean_sources() -> tuple[ResidueSource, ...]:
    return (_StaticSource(snapshots=[ResidueSnapshot(source="attention", available=True)]),)


def _probe(
    *,
    cycle: _RecordingCycle,
    sources: Sequence[ResidueSource] | None = None,
    item: WorkItem | None = None,
) -> ProbeResult:
    return run_probe_cycle(
        item=item if item is not None else _item(),
        cycle=cycle,
        sources=sources if sources is not None else _clean_sources(),
        probe_run_id=probe_run_identifier(work_item_id=_ITEM, started_at="2026-08-28T00:00:00Z"),
    )


# --- the driven cycle -------------------------------------------------------


def test_a_clean_cycle_passes_every_stage_assertion() -> None:
    cycle = _RecordingCycle()

    result = _probe(cycle=cycle)

    assert result.passed
    assert result.outcome == PASSED_OUTCOME
    assert result.item_status == "done"
    assert cycle.calls == [f"publish:{_ITEM}", "merge", "observe"]


def test_ungradeable_criteria_fail_before_the_cycle_is_driven_at_all() -> None:
    cycle = _RecordingCycle()

    result = _probe(cycle=cycle, item=_item(acceptance_criteria=None))

    assert not result.passed
    assert result.stage == "effective-criteria"
    assert cycle.calls == []


def test_an_escaping_change_fails_the_probe_without_merging() -> None:
    cycle = _RecordingCycle(
        published=ProbePublish(branch=f"feat/{_ITEM}", paths=(_ARTIFACT, "justfile"))
    )

    result = _probe(cycle=cycle)

    assert result.outcome == CONFINEMENT_ESCAPE_OUTCOME
    assert "justfile" in result.detail
    assert "merge" not in cycle.calls


def test_a_merged_escape_fails_naming_the_commit_and_the_revert_obligation() -> None:
    cycle = _RecordingCycle(
        published=ProbePublish(branch=f"feat/{_ITEM}", paths=("justfile",), merge_commit="abc1234")
    )

    result = _probe(cycle=cycle)

    assert result.outcome == MERGED_ESCAPE_OUTCOME
    assert "abc1234" in result.detail
    assert "revert" in result.remedy
    assert "merge" not in cycle.calls


def test_an_already_merged_confined_change_proceeds_to_the_merge_disposition() -> None:
    cycle = _RecordingCycle(
        published=ProbePublish(branch=f"feat/{_ITEM}", paths=(_ARTIFACT,), merge_commit="abc1234")
    )

    result = _probe(cycle=cycle)

    assert result.passed
    assert "merge" in cycle.calls


def test_the_post_merge_backstop_catches_an_escape_the_disposition_merged() -> None:
    cycle = _RecordingCycle(
        merged=ProbeMerge(merged=True, merge_commit=None, merged_paths=("justfile",))
    )

    result = _probe(cycle=cycle)

    assert result.outcome == MERGED_ESCAPE_OUTCOME
    assert "<unknown commit>" in result.detail


def test_a_disposition_that_did_not_merge_fails_at_the_merge_stage() -> None:
    cycle = _RecordingCycle(merged=ProbeMerge(merged=False, detail="exit 3"), status="active")

    result = _probe(cycle=cycle)

    assert result.stage == "merge"
    assert result.item_status == "active"
    assert "exit 3" in result.detail


def test_a_degraded_step_outcome_fails_the_probe() -> None:
    cycle = _RecordingCycle(
        observation=ProbeObservation(
            step_outcomes=({"step": "master-ci", "status": "warn"},),
            verdict="PASS",
            absent_evidence=(),
            item_status="done",
        )
    )

    result = _probe(cycle=cycle)

    assert result.stage == "step-outcomes"
    assert "master-ci=warn" in result.detail


def test_an_ungrounded_verdict_fails_the_probe() -> None:
    cycle = _RecordingCycle(
        observation=ProbeObservation(
            step_outcomes=(),
            verdict="PASS",
            absent_evidence=("telemetry",),
            item_status="done",
        )
    )

    result = _probe(cycle=cycle)

    assert result.stage == "acceptance-verdict"
    assert "telemetry" in result.detail


def test_an_item_short_of_done_fails_the_residue_stage() -> None:
    cycle = _RecordingCycle(
        observation=ProbeObservation(
            step_outcomes=(), verdict="PASS", absent_evidence=(), item_status="acceptance"
        )
    )

    result = _probe(cycle=cycle)

    assert result.stage == "residue"
    assert result.outcome == STAGE_FAILED_OUTCOME
    assert "acceptance" in result.detail


def test_the_unrelated_delta_rides_a_passing_result_without_failing_it() -> None:
    source = _StaticSource(
        snapshots=[
            ResidueSnapshot(source="attention", available=True, identifiers=("valve:other:a",)),
            ResidueSnapshot(source="attention", available=True, identifiers=("valve:other:b",)),
        ]
    )

    result = _probe(cycle=_RecordingCycle(), sources=(source,))

    assert result.passed
    assert result.unrelated_delta == (
        "appeared attention:valve:other:b",
        "resolved attention:valve:other:a",
    )


# --- source unavailability, at each snapshot --------------------------------


def test_an_unreadable_before_snapshot_fails_source_unavailable_without_driving() -> None:
    cycle = _RecordingCycle(status="ready")
    source = _StaticSource(
        snapshots=[ResidueSnapshot(source="ledger", available=False, detail="refused")]
    )

    result = _probe(cycle=cycle, sources=(source,))

    assert result.outcome == SOURCE_UNAVAILABLE_OUTCOME
    assert result.item_status == "ready"
    assert cycle.calls == []


def test_an_unreadable_after_snapshot_fails_source_unavailable() -> None:
    source = _StaticSource(
        snapshots=[
            ResidueSnapshot(source="attention", available=True),
            ResidueSnapshot(source="attention", available=False, detail="refused"),
        ]
    )

    result = _probe(cycle=_RecordingCycle(), sources=(source,))

    assert result.outcome == SOURCE_UNAVAILABLE_OUTCOME
    assert "refused" in result.detail


def test_an_unreadable_published_change_fails_source_unavailable() -> None:
    cycle = _RecordingCycle(
        published=ProbePublish(
            branch=f"feat/{_ITEM}", paths=(), readable=False, detail="git diff exited 128"
        )
    )

    result = _probe(cycle=cycle)

    assert result.outcome == SOURCE_UNAVAILABLE_OUTCOME
    assert result.stage == "publish"
    assert "merge" not in cycle.calls
