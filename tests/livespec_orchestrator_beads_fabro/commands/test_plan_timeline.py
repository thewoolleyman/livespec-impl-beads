"""Additional plan timeline coverage."""

from __future__ import annotations

from livespec_orchestrator_beads_fabro._beads_client import (
    FakeBeadsClient,
    IssueDraft,
    make_beads_client,
    reset_fake_singleton,
)
from livespec_orchestrator_beads_fabro.commands.plan import append_handoff, read_timeline
from livespec_orchestrator_beads_fabro.types import StoreConfig


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd-ib",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _fake() -> FakeBeadsClient:
    client = make_beads_client(config=_config())
    assert isinstance(client, FakeBeadsClient)
    return client


def test_timeline_ignores_non_plan_comments() -> None:
    reset_fake_singleton()
    _ = _fake().create_issue(
        draft=IssueDraft(
            issue_id="bd-ib-plan",
            issue_type="epic",
            title="plan",
            description="plan",
            assignee=None,
            created_at="2026-08-11T00:00:00Z",
            metadata={"rank": "a1"},
            labels=["origin:freeform"],
        )
    )

    _fake().seed_comment(issue_id="bd-ib-plan", text="ordinary ledger note")
    append_handoff(
        config=_config(),
        epic_id="bd-ib-plan",
        body="Continue with the scoped child.",
        author="factory-test",
        now="2026-08-11T01:02:03Z",
    )

    [entry] = read_timeline(config=_config(), epic_id="bd-ib-plan")
    assert entry.body == "Continue with the scoped child."
