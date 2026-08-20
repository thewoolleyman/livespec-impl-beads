"""Unattended plan resume takes the single recorded next action without a picker."""

from __future__ import annotations

from livespec_orchestrator_beads_fabro._beads_client import (
    FakeBeadsClient,
    IssueDraft,
    make_beads_client,
    reset_fake_singleton,
)
from livespec_orchestrator_beads_fabro.commands._plan_timeline import (
    UNATTENDED_ENV_VAR,
    is_unattended_session,
    recorded_next_actions,
    resume_directive,
)
from livespec_orchestrator_beads_fabro.commands.plan import (
    PlanTimelineEntry,
    append_handoff,
    read_timeline,
    record_scope_event,
)
from livespec_orchestrator_beads_fabro.types import StoreConfig

_HANDOFF_ONE_ACTION = (
    "Thread reopened after a context-threshold restart.\n"
    "\n"
    "NEXT ACTION (exactly one): implement bd-ib-idgwyk.1.\n"
)


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


def _seed_epic(*, epic_id: str) -> None:
    reset_fake_singleton()
    _ = _fake().create_issue(
        draft=IssueDraft(
            issue_id=epic_id,
            issue_type="epic",
            title="plan",
            description="plan",
            assignee=None,
            created_at="2026-08-20T00:00:00Z",
            metadata={"rank": "a1"},
            labels=["origin:freeform"],
        )
    )


def _entry(*, kind: str, body: str) -> PlanTimelineEntry:
    return PlanTimelineEntry(
        kind=kind,
        body=body,
        author="unattended-plan-operation-plan",
        created_at="2026-08-20T00:00:00Z",
    )


def test_unattended_marker_is_read_from_the_session_environment() -> None:
    assert is_unattended_session(env={UNATTENDED_ENV_VAR: "1"})
    assert is_unattended_session(env={UNATTENDED_ENV_VAR: " TRUE "})
    assert is_unattended_session(env={UNATTENDED_ENV_VAR: "yes"})
    assert is_unattended_session(env={UNATTENDED_ENV_VAR: "on"})
    assert not is_unattended_session(env={UNATTENDED_ENV_VAR: "0"})
    assert not is_unattended_session(env={UNATTENDED_ENV_VAR: ""})
    assert not is_unattended_session(env={})


def test_recorded_next_actions_reads_the_marker_line() -> None:
    assert recorded_next_actions(body=_HANDOFF_ONE_ACTION) == ("implement bd-ib-idgwyk.1.",)


def test_recorded_next_actions_reads_every_marker_line() -> None:
    body = "NEXT ACTION: implement bd-ib-idgwyk.1.\n- next action: file bd-ib-idgwyk.5.\n"

    assert recorded_next_actions(body=body) == (
        "implement bd-ib-idgwyk.1.",
        "file bd-ib-idgwyk.5.",
    )


def test_recorded_next_actions_ignores_a_marker_that_names_nothing() -> None:
    assert recorded_next_actions(body="NEXT ACTION\nNEXT ACTION:   \nprose about the plan.\n") == ()


def test_unattended_resume_with_one_recorded_next_action_does_not_ask() -> None:
    directive = resume_directive(
        entries=(_entry(kind="handoff", body=_HANDOFF_ONE_ACTION),),
        unattended=True,
    )

    assert not directive.ask
    assert directive.next_action == "implement bd-ib-idgwyk.1."


def test_unattended_resume_with_several_recorded_next_actions_still_asks() -> None:
    body = "NEXT ACTION: implement bd-ib-idgwyk.1.\nNEXT ACTION: implement bd-ib-idgwyk.2.\n"

    directive = resume_directive(entries=(_entry(kind="handoff", body=body),), unattended=True)

    assert directive.ask
    assert directive.next_action is None
    assert "2 next actions" in directive.reason


def test_unattended_resume_with_no_recorded_next_action_still_asks() -> None:
    directive = resume_directive(
        entries=(_entry(kind="handoff", body="Research updated; nothing named.\n"),),
        unattended=True,
    )

    assert directive.ask
    assert directive.next_action is None


def test_unattended_resume_with_an_empty_timeline_still_asks() -> None:
    directive = resume_directive(entries=(), unattended=True)

    assert directive.ask
    assert "no handoff entry" in directive.reason


def test_interactive_resume_always_asks() -> None:
    directive = resume_directive(
        entries=(_entry(kind="handoff", body=_HANDOFF_ONE_ACTION),),
        unattended=False,
    )

    assert directive.ask
    assert directive.next_action is None
    assert directive.reason == "interactive resume"


def test_resume_reads_the_newest_handoff_not_a_newer_scope_event() -> None:
    stale = "NEXT ACTION: implement bd-ib-idgwyk.1.\n"
    newest = "NEXT ACTION: implement bd-ib-idgwyk.2.\n"

    directive = resume_directive(
        entries=(
            _entry(kind="handoff", body=stale),
            _entry(kind="handoff", body=newest),
            _entry(kind="scope", body="Requirement carriers:\n- bd-ib-idgwyk.2\n"),
        ),
        unattended=True,
    )

    assert directive.next_action == "implement bd-ib-idgwyk.2."


def test_read_timeline_labels_each_entry_with_its_kind() -> None:
    _seed_epic(epic_id="bd-ib-plan")
    record_scope_event(
        config=_config(),
        epic_id="bd-ib-plan",
        requirements=("bd-ib-plan.1",),
        deferrals=("nothing",),
        author="unattended-plan-operation-plan",
        now="2026-08-20T00:00:00Z",
    )
    append_handoff(
        config=_config(),
        epic_id="bd-ib-plan",
        body=_HANDOFF_ONE_ACTION,
        author="unattended-plan-operation-plan",
        now="2026-08-20T00:00:01Z",
    )

    entries = read_timeline(config=_config(), epic_id="bd-ib-plan")

    assert [entry.kind for entry in entries] == ["scope", "handoff"]
    assert not resume_directive(entries=entries, unattended=True).ask
