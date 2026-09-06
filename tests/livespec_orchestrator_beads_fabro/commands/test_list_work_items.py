"""Tests for the list-work-items thin-transport command (beads substrate).

The hermetic `FakeBeadsClient` is the backend (autouse fixture sets
`LIVESPEC_BEADS_FAKE=1` and resets the singleton). Work-items are seeded
into the same in-memory tenant the command reads by calling
`append_work_item` with a `fake=True` connection descriptor; the
process-singleton fake makes the seeded writes visible to `main`.
"""

import json
from dataclasses import fields
from unittest.mock import Mock

import pytest
from livespec_orchestrator_beads_fabro import _store_dispatch_factory
from livespec_orchestrator_beads_fabro._beads_client import fake_singleton
from livespec_orchestrator_beads_fabro.commands.list_work_items import main
from livespec_orchestrator_beads_fabro.store import append_work_item, record_dispatch_factory
from livespec_orchestrator_beads_fabro.types import AuditRecord, StoreConfig, WorkItem


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="livespec-impl-beads",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _seed(item: WorkItem) -> None:
    # `append_work_item` now sets the work-item's status during the write
    # (2-step `bd create` + `bd update --status` for live states; close-in-place
    # for `done`), so no follow-up status transition is needed here.
    append_work_item(path=_config(), item=item)


def _item(
    *,
    id_: str,
    status: str = "ready",
    origin: str = "freeform",
    gap_id: str | None = None,
    depends_on: tuple[str, ...] = (),
    rank: str = "a2",
    spec_commitment_hint: str | None = None,
    blocked_reason: str | None = None,
    awaits_scope_override: bool = False,
    rework_pending: bool = False,
) -> WorkItem:
    return WorkItem(
        id=id_,
        type="task",
        status=status,  # type: ignore[arg-type]
        title=f"{id_} title",
        description="d",
        origin=origin,  # type: ignore[arg-type]
        gap_id=gap_id,
        rank=rank,
        assignee=None,
        depends_on=depends_on,
        captured_at="2026-05-19T00:00:00Z",
        resolution="completed" if status == "done" else None,
        reason="done" if status == "done" else None,
        audit=AuditRecord(
            verification_timestamp="2026-05-19T01:00:00Z",
            commits=("c",),
            files_changed=("f",),
            merge_sha="abc123",
            pr_number=None,
        )
        if status == "done"
        else None,
        superseded_by=None,
        spec_commitment_hint=spec_commitment_hint,
        blocked_reason=blocked_reason,  # type: ignore[arg-type]
        awaits_scope_override=awaits_scope_override,
        rework_pending=rework_pending,
    )


def test_main_empty_store_prints_no_items(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(argv=[])
    captured = capsys.readouterr()
    assert rc == 0
    assert "(no work-items)" in captured.out


def test_main_lists_all_human(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a", origin="gap-tied", gap_id="G1"))
    _seed(_item(id_="li-b"))
    rc = main(argv=[])
    captured = capsys.readouterr()
    assert rc == 0
    assert "li-a" in captured.out
    assert "li-b" in captured.out
    assert "gap=G1" in captured.out


def test_main_lists_dispatch_factory_human(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a"))
    record_dispatch_factory(path=_config(), work_item_id="li-a", factory="remote")
    rc = main(argv=[])
    captured = capsys.readouterr()
    assert rc == 0
    assert "factory=remote" in captured.out


def test_main_filter_gap_tied(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a", origin="gap-tied", gap_id="G1"))
    _seed(_item(id_="li-b"))
    rc = main(argv=["--filter=gap-tied"])
    captured = capsys.readouterr()
    assert "li-a" in captured.out
    assert "li-b" not in captured.out
    assert rc == 0


def test_main_filter_freeform(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a", origin="gap-tied", gap_id="G1"))
    _seed(_item(id_="li-b"))
    rc = main(argv=["--filter=freeform"])
    captured = capsys.readouterr()
    assert "li-b" in captured.out
    assert "li-a" not in captured.out
    assert rc == 0


def test_main_filter_blocked(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a", status="blocked"))
    _seed(_item(id_="li-b"))
    rc = main(argv=["--filter=blocked"])
    captured = capsys.readouterr()
    assert "li-a" in captured.out
    assert "li-b" not in captured.out
    assert rc == 0


def test_main_filter_ready_excludes_open_local_deps(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a"))
    _seed(_item(id_="li-b", depends_on=("li-a",)))
    rc = main(argv=["--filter=ready"])
    captured = capsys.readouterr()
    assert "li-a" in captured.out
    assert "li-b" not in captured.out
    assert rc == 0


def test_main_filter_ready_does_not_exclude_missing_local_dep(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing local ids resolve to UNKNOWN; only OPEN excludes per the v072 contract."""
    _seed(_item(id_="li-c", depends_on=("li-missing",)))
    rc = main(argv=["--filter=ready"])
    captured = capsys.readouterr()
    assert "li-c" in captured.out
    assert rc == 0


def test_main_filter_ready_includes_closed_deps(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a", status="done"))
    _seed(_item(id_="li-b", depends_on=("li-a",)))
    rc = main(argv=["--filter=ready"])
    captured = capsys.readouterr()
    assert "li-b" in captured.out
    assert rc == 0


def test_main_filter_closed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a"))
    _seed(_item(id_="li-b", status="done"))
    rc = main(argv=["--filter=closed"])
    captured = capsys.readouterr()
    assert "li-b" in captured.out
    assert "li-a" not in captured.out
    assert rc == 0


def test_main_with_gap_id_filter(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a", origin="gap-tied", gap_id="G1"))
    _seed(_item(id_="li-b", origin="gap-tied", gap_id="G2"))
    rc = main(argv=["--with-gap-id", "G1"])
    captured = capsys.readouterr()
    assert "li-a" in captured.out
    assert "li-b" not in captured.out
    assert rc == 0


def test_main_json_output_with_audit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a", status="done"))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload[0]["id"] == "li-a"
    assert payload[0]["audit"]["commits"] == ["c"]
    assert set(payload[0]["audit"]) == {field.name for field in fields(AuditRecord)}


def test_main_json_output_key_set_tracks_work_item_dataclass_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The projection must fail if a future WorkItem field is not emitted."""
    _seed(_item(id_="li-a", status="done"))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    expected = {field.name for field in fields(WorkItem)} | {
        "dispatch_factory",
        "labels",
        "lane",
        "lane_reason",
        "merge_hold",
        "parent",
    }
    assert set(payload[0]) == expected


def test_main_json_output_derives_merge_hold_from_the_label(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A held item reads as held without any downstream reader parsing labels."""
    _seed(_item(id_="li-held"))
    _seed(_item(id_="li-free"))
    fake_singleton().update_issue(issue_id="li-held", add_labels=["merge-hold:on"])

    rc = main(argv=["--json"])
    captured = capsys.readouterr()

    assert rc == 0
    payload = _by_id(json.loads(captured.out))
    assert payload["li-held"]["merge_hold"] is True
    assert payload["li-free"]["merge_hold"] is False


def test_main_json_output_includes_parent_and_labels(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-parent"))
    _seed(_item(id_="li-child"))
    fake_singleton().update_issue(
        issue_id="li-child",
        parent_id="li-parent",
        add_labels=["acceptance:human-only", "topic:grooming"],
    )

    rc = main(argv=["--json"])
    captured = capsys.readouterr()

    assert rc == 0
    payload = _by_id(json.loads(captured.out))
    assert payload["li-child"]["parent"] == "li-parent"
    assert payload["li-child"]["labels"] == [
        "origin:freeform",
        "acceptance:human-only",
        "topic:grooming",
    ]
    assert payload["li-parent"]["parent"] is None
    assert payload["li-parent"]["labels"] == ["origin:freeform"]


def test_main_json_parent_unions_implicit_dotted_child_and_explicit_edge(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="bd-ib-mrqoy2", status="done"))
    _seed(_item(id_="bd-ib-mrqoy2.1", status="done"))
    _seed(_item(id_="bd-ib-g4u4xj", status="done"))
    _seed(_item(id_="bd-ib-m36re3", status="done"))
    fake_singleton().update_issue(issue_id="bd-ib-m36re3", parent_id="bd-ib-g4u4xj")
    fake_singleton().children = Mock(
        side_effect=AssertionError("list-work-items must not fan out child reads")
    )

    rc = main(argv=["--json"])
    captured = capsys.readouterr()

    assert rc == 0
    payload = _by_id(json.loads(captured.out))
    assert payload["bd-ib-mrqoy2.1"]["parent"] == "bd-ib-mrqoy2"
    assert payload["bd-ib-m36re3"]["parent"] == "bd-ib-g4u4xj"


def test_substrate_facts_from_records_reads_native_parent_and_labels() -> None:
    from livespec_orchestrator_beads_fabro.commands._list_work_items_projection import (
        substrate_facts_from_records,
    )

    facts = substrate_facts_from_records(
        records=[
            {
                "id": "li-child",
                "parent": "li-parent",
                "labels": ["topic:grooming", 7, "acceptance:human-only"],
            },
            {"id": 7, "parent": "ignored"},
        ]
    )

    assert facts["li-child"].parent == "li-parent"
    assert facts["li-child"].labels == ("topic:grooming", "acceptance:human-only")
    assert set(facts) == {"li-child"}


def test_substrate_facts_from_records_reads_parent_id_and_edge_fallbacks() -> None:
    from livespec_orchestrator_beads_fabro.commands._list_work_items_projection import (
        substrate_facts_from_records,
    )

    facts = substrate_facts_from_records(
        records=[
            {
                "id": "li-parent-id",
                "parent_id": "li-parent",
                "labels": "not-a-list",
                "dependencies": [],
            },
            {
                "id": "li-edge",
                "labels": [],
                "dependencies": [
                    {"depends_on_id": "not-parent", "type": "blocks"},
                    "bad-edge",
                    {"depends_on_id": "li-epic", "type": "parent-child"},
                ],
            },
            {
                "id": "li-none",
                "labels": [],
                "dependencies": "not-a-list",
            },
        ]
    )

    assert facts["li-parent-id"].parent == "li-parent"
    assert facts["li-parent-id"].labels == ()
    assert facts["li-edge"].parent == "li-epic"
    assert facts["li-none"].parent is None


def test_main_json_output_includes_dispatch_factory(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-a"))
    record_dispatch_factory(path=_config(), work_item_id="li-a", factory="remote")
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload[0]["dispatch_factory"] == "remote"


def test_main_json_skips_dispatch_factory_lookup_for_closed_items(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed(_item(id_="li-live"))
    record_dispatch_factory(path=_config(), work_item_id="li-live", factory="remote")
    _seed(_item(id_="li-closed", status="done"))

    monkeypatch.setattr(
        _store_dispatch_factory,
        "read_work_item_comments",
        Mock(side_effect=AssertionError("list-work-items must not read dispatch-factory comments")),
    )

    rc = main(argv=["--json"])
    captured = capsys.readouterr()

    assert rc == 0
    payload = _by_id(json.loads(captured.out))
    assert payload["li-live"]["dispatch_factory"] == "remote"
    assert payload["li-closed"]["dispatch_factory"] is None


def test_main_json_output_depends_on_is_typed_dict_local_entry(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--json` emits each `blocks`-edge dependency as the v072 typed-dict form.

    livespec's `DependsOnEntry` schema and the doctor
    `depends_on-ref-wellformedness` / `no-orphan-dependency` checks require
    the typed-dict `{"kind":"local","work_item_id":...}` shape; the legacy
    bare-string materialization fails wellformedness on every dependency edge.
    """
    _seed(_item(id_="li-dep"))
    _seed(_item(id_="li-blocked", depends_on=("li-dep",)))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    blocked = next(item for item in payload if item["id"] == "li-blocked")
    assert blocked["depends_on"] == [{"kind": "local", "work_item_id": "li-dep"}]


def test_main_json_output_without_audit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-open"))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload[0]["id"] == "li-open"
    assert payload[0]["audit"] is None


def test_main_json_output_includes_awaits_scope_override_boolean(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed(_item(id_="li-awaits", awaits_scope_override=True))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload[0]["awaits_scope_override"] is True


def test_main_json_output_includes_rework_pending_boolean(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pending rework is visible on the listing surface, per the field map."""
    _seed(_item(id_="li-rework", status="active"))
    fake_singleton().update_issue(issue_id="li-rework", add_labels=["rework:pending"])
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload[0]["rework_pending"] is True


# -- spec_commitment_hint surface (livespec PC #4 sub-proposal 3) --------


def test_main_json_output_includes_spec_commitment_hint_when_set(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--json` exposes spec_commitment_hint so the doctor invariant can match."""
    _seed(_item(id_="li-a", spec_commitment_hint="spec-impl-commitment-tracking"))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload[0]["spec_commitment_hint"] == "spec-impl-commitment-tracking"


def test_main_json_output_includes_null_spec_commitment_hint_when_unset(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--json` carries explicit null for freeform work-items (the unset case)."""
    _seed(_item(id_="li-a"))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert "spec_commitment_hint" in payload[0]
    assert payload[0]["spec_commitment_hint"] is None


def test_main_with_spec_commitment_hint_filter(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--with-spec-commitment-hint=<id_hint>` filters to exact hint match."""
    _seed(_item(id_="li-match", spec_commitment_hint="topic-x"))
    _seed(_item(id_="li-other", spec_commitment_hint="topic-y"))
    _seed(_item(id_="li-none"))
    rc = main(argv=["--with-spec-commitment-hint", "topic-x"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "li-match" in captured.out
    assert "li-other" not in captured.out
    assert "li-none" not in captured.out


def test_main_with_spec_commitment_hint_filter_no_matches(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A hint with no matching record yields the empty-listing message."""
    _seed(_item(id_="li-a"))
    rc = main(argv=["--with-spec-commitment-hint", "no-match"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "(no work-items)" in captured.out


def test_main_with_spec_commitment_hint_filter_combines_with_filter_name(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Hint filter composes with --filter (intersect, not union)."""
    _seed(_item(id_="li-open", status="ready", spec_commitment_hint="topic-x"))
    _seed(_item(id_="li-closed", status="done", spec_commitment_hint="topic-x"))
    rc = main(argv=["--filter=closed", "--with-spec-commitment-hint", "topic-x"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "li-closed" in captured.out
    assert "li-open" not in captured.out


def test_main_with_spec_commitment_hint_filter_combines_with_gap_id(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Hint filter composes with --with-gap-id (intersect, not union)."""
    _seed(
        _item(
            id_="li-a",
            origin="gap-tied",
            gap_id="G1",
            spec_commitment_hint="topic-x",
        )
    )
    _seed(_item(id_="li-b", spec_commitment_hint="topic-x"))
    rc = main(argv=["--with-gap-id", "G1", "--with-spec-commitment-hint", "topic-x"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "li-a" in captured.out
    assert "li-b" not in captured.out


# -- lane / lane_reason emission (Scenario 26 — L1a/S4) ------------------


def _by_id(payload: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(entry["id"]): entry for entry in payload}


def test_main_json_emits_lane_active_with_null_reason(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An active item emits lane 'active' and lane_reason null (Scenario 26)."""
    _seed(_item(id_="li-active", status="active"))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    entry = _by_id(json.loads(captured.out))["li-active"]
    assert entry.get("lane") == "active"
    assert entry.get("lane_reason") is None


def test_main_json_emits_lane_blocked_dependency_for_ready_with_open_dep(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A stored-ready item with an open dependency renders lane blocked:dependency."""
    _seed(_item(id_="li-dep"))
    _seed(_item(id_="li-ready", status="ready", depends_on=("li-dep",)))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    entry = _by_id(json.loads(captured.out))["li-ready"]
    assert entry.get("lane") == "blocked"
    assert entry.get("lane_reason") == "dependency"


def test_main_json_emits_lane_blocked_needs_human_for_stored_blocked(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A stored blocked item carries its stored blocked_reason as lane_reason."""
    _seed(_item(id_="li-blk", status="blocked", blocked_reason="needs-human"))
    rc = main(argv=["--json"])
    captured = capsys.readouterr()
    assert rc == 0
    entry = _by_id(json.loads(captured.out))["li-blk"]
    assert entry.get("lane") == "blocked"
    assert entry.get("lane_reason") == "needs-human"


def test_main_filter_blocked_includes_ready_with_open_dependency(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--filter=blocked` is lane semantics: a ready item with an open dep matches."""
    _seed(_item(id_="li-dep"))
    _seed(_item(id_="li-ready", status="ready", depends_on=("li-dep",)))
    rc = main(argv=["--filter=blocked"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "li-ready" in captured.out
    assert "li-dep" not in captured.out
