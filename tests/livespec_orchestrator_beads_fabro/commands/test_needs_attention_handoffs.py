"""Coverage for needs-attention handoff helpers."""

from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._needs_attention_handoffs import plan_threads
from livespec_orchestrator_beads_fabro.types import WorkItem


def _epic(*, spec_commitment_hint: str | None) -> WorkItem:
    return WorkItem(
        id="bd-epic",
        type="epic",
        status="backlog",
        title="Planning epic",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-11T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        spec_commitment_hint=spec_commitment_hint,
    )


def test_plan_threads_ignores_epics_without_plan_commitment(tmp_path: Path) -> None:
    assert (
        plan_threads(
            project_root=tmp_path,
            items=[_epic(spec_commitment_hint="SPECIFICATION/contracts.md")],
        )
        == []
    )
