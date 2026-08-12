"""Focused coverage for needs-attention handoff rendering helpers."""

from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._needs_attention_handoffs import plans
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _item(*, id_: str, spec_commitment_hint: str) -> WorkItem:
    return WorkItem(
        id=id_,
        type="epic",
        status="backlog",
        title=f"{id_} title",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee=None,
        depends_on=(),
        captured_at="2026-05-19T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        spec_commitment_hint=spec_commitment_hint,
    )


def test_plans_ignore_non_plan_and_empty_plan_hints(tmp_path: Path) -> None:
    assert (
        plans(
            project_root=tmp_path,
            config=_config(),
            items=[
                _item(id_="bd-not-plan", spec_commitment_hint="SPECIFICATION"),
                _item(id_="bd-empty-plan", spec_commitment_hint="plan:"),
            ],
        )
        == []
    )
