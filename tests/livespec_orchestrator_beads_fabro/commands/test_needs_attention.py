"""Tests for the needs-attention thin binding."""

import json
import shlex
from pathlib import Path
from typing import Any

import pytest
from livespec_orchestrator_beads_fabro._beads_client import IssueDraft, make_beads_client
from livespec_orchestrator_beads_fabro.commands import needs_attention
from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_lock import (
    write_dispatch_lock,
)
from livespec_orchestrator_beads_fabro.commands.needs_attention import (
    SpecNextSeam,
    _spec_next,
    _SpecNextResult,
    build_attention,
    main,
    render_json,
    render_markdown,
)
from livespec_orchestrator_beads_fabro.commands.plan import append_handoff
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem
from livespec_runtime.needs_attention import SpecNextOutput


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
    append_work_item(path=_config(), item=item)


def _seed_raw(
    *,
    id_: str,
    status: str,
    priority: int,
    labels: list[str] | None = None,
    title: str | None = None,
) -> None:
    """Seed an issue straight through the client seam — the raw `bd create` path.

    `append_work_item` is the capture front-ends' filing path; an agent or
    script that files with a bare `bd create` bypasses it, so the intake
    Definition-of-Ready gate never runs and the record lands WITHOUT the
    `intake:triaged` marker. That is exactly the population the un-triaged
    backlog lane must surface, so these cases seed it the way it really
    arrives. `priority` is the beads-native column (lower = more urgent),
    which `append_work_item` always writes as the neutral default.
    """
    client = make_beads_client(config=_config())
    _ = client.create_issue(
        draft=IssueDraft(
            issue_id=id_,
            issue_type="task",
            title=title if title is not None else f"{id_} title",
            description="d",
            priority=priority,
            assignee=None,
            created_at="2026-05-19T00:00:00Z",
            labels=list(labels) if labels is not None else [],
            metadata={},
            spec_id=None,
            parent_id=None,
        )
    )
    client.update_issue(issue_id=id_, status=status)


def _write_config(
    project_root: Path, *, auto_approve_ready: bool = False, wip_cap: int | None = None
) -> None:
    dispatcher_items = []
    if auto_approve_ready:
        dispatcher_items.append(f'      "auto_approve_ready": {str(auto_approve_ready).lower()}')
    if wip_cap is not None:
        dispatcher_items.append(f'      "wip_cap": {wip_cap}')
    dispatcher_body = ",\n".join(dispatcher_items)
    dispatcher = (
        f""",
    \"dispatcher\": {{
{dispatcher_body}
    }}"""
        if dispatcher_items
        else ""
    )
    (project_root / ".livespec.jsonc").write_text(
        """{
  \"livespec-orchestrator-beads-fabro\": {
    \"connection\": {
      \"tenant\": \"livespec-impl-beads\",
      \"prefix\": \"bd\",
      \"server_user\": \"livespec-impl-beads\",
      \"database\": \"livespec-impl-beads\",
      \"bd_path\": \"bd\",
      \"fake\": true
    }
"""
        + dispatcher
        + """
  }
}
""",
        encoding="utf-8",
    )


def _stub_spec_output() -> SpecNextOutput:
    """A deterministic spec-`next` adaptation used to keep composition tests hermetic."""
    return SpecNextOutput(
        op="revise",
        spec_target="SPECIFICATION",
        summary="Revise a pending proposed change.",
        command="codex exec livespec:revise --project-root /workspace/livespec",
        urgency="medium",
    )


def _stub_spec_next(monkeypatch: pytest.MonkeyPatch, *, output: SpecNextOutput | None) -> None:
    """Replace `_spec_next` so `build_attention` never touches a live CORE checkout."""

    def _fake(*, project_root: Path) -> SpecNextOutput | None:
        _ = project_root
        return output

    monkeypatch.setattr(needs_attention, "_spec_next", _fake)


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


def _item(
    *,
    id_: str,
    status: str,
    type_: str = "task",
    rank: str = "a2",
    blocked_reason: str | None = None,
    factory_safety: str | None = None,
    admission_policy: str | None = None,
    acceptance_policy: str | None = None,
    spec_commitment_hint: str | None = None,
) -> WorkItem:
    return WorkItem(
        id=id_,
        type=type_,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        title=f"{id_} title",
        description="d",
        origin="freeform",
        gap_id=None,
        rank=rank,
        assignee=None,
        depends_on=(),
        captured_at="2026-05-19T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        blocked_reason=blocked_reason,  # type: ignore[arg-type]
        factory_safety=factory_safety,  # type: ignore[arg-type]
        admission_policy=admission_policy,  # type: ignore[arg-type]
        acceptance_policy=acceptance_policy,  # type: ignore[arg-type]
        spec_commitment_hint=spec_commitment_hint,
    )


def _write_journal_record(project_root: Path, *, record: dict[str, Any]) -> None:
    journal = project_root / "tmp" / "fabro-dispatch-journal.jsonl"
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as handle:
        _ = handle.write(json.dumps(record, sort_keys=True) + "\n")


def _write_dispatch_lock(project_root: Path, *, work_item_id: str) -> None:
    _ = write_dispatch_lock(
        repo=project_root,
        work_item_id=work_item_id,
        dispatch_id=f"run-{work_item_id}",
    )


def test_build_attention_composes_impl_human_valves_plan_threads_and_spec_next(
    tmp_path, monkeypatch
) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=_stub_spec_output())
    _ = (tmp_path / "plan" / "needs-attention").mkdir(parents=True)
    _seed(_item(id_="bd-ready", status="ready", rank="a1"))
    _seed(_item(id_="bd-approval", status="pending-approval", rank="a2"))
    _seed(_item(id_="bd-accept", status="acceptance", rank="a3"))
    _seed(_item(id_="bd-block", status="blocked", rank="a4", blocked_reason="needs-human"))

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [item.id for item in attention] == [
        "valve:approve:bd-approval",
        "valve:accept:bd-accept",
        "valve:resolve-blocked:bd-block",
        "impl:bd-ready",
        "spec:revise:SPECIFICATION",
        "plan:needs-attention",
    ]
    assert attention[0].handoff.action_id == "approve:bd-approval"
    assert attention[1].handoff.command.endswith("--action accept:bd-accept --json")
    assert attention[3].handoff.command.endswith("--action impl:bd-ready --json")
    assert attention[-1].source_ref.path == "plan/needs-attention/"


def test_build_attention_reads_ledger_held_plan_without_handoff_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)
    _seed(
        _item(
            id_="bd-plan",
            type_="epic",
            status="backlog",
            rank="a1",
            spec_commitment_hint="plan:ledger-held",
        )
    )
    append_handoff(
        config=_config(),
        epic_id="bd-plan",
        body="Next action: keep driving bd-plan from the ledger.",
        author="factory-test",
        now="2026-08-11T01:02:03Z",
    )

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert not (tmp_path / "plan" / "ledger-held" / "handoff.md").exists()
    [plan_item] = [item for item in attention if item.id == "plan:ledger-held"]
    assert plan_item.summary == "Review plan ledger-held."
    assert plan_item.source_ref.path == "plan/ledger-held/"


def test_build_attention_surfaces_a_live_plan_with_an_insufficient_newest_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)
    _seed(
        _item(
            id_="bd-plan",
            type_="epic",
            status="backlog",
            rank="a1",
            spec_commitment_hint="plan:bad-handoff",
        )
    )
    append_handoff(
        config=_config(),
        epic_id="bd-plan",
        body="Current state cites bd-ib-qfv9.1.\n\n== EXACTLY ONE NEXT ACTION ==\nImplement it.",
        author="factory-test",
        now="2026-08-11T01:02:03Z",
    )

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    [plan_item] = [item for item in attention if item.id == "plan:bad-handoff"]
    assert plan_item.urgency == "high"
    assert (
        plan_item.summary
        == "Repair plan bad-handoff handoff: newest handoff records 0 next actions, not exactly one."
    )


def test_build_attention_advertises_approve_only_for_effective_manual_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path, auto_approve_ready=True)
    _stub_spec_next(monkeypatch, output=None)
    _seed(_item(id_="bd-auto", status="pending-approval", rank="a1"))
    _seed(
        _item(
            id_="bd-manual",
            status="pending-approval",
            rank="a2",
            admission_policy="manual",
        )
    )

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [item.id for item in attention] == [
        "valve:approve:bd-manual",
        "internal:awaiting-admission:bd-auto",
    ]
    assert attention[0].handoff.action_id == "approve:bd-manual"
    assert attention[1].kind == "internal"
    assert "Dispatcher admission pass" in attention[1].summary


def test_build_attention_surfaces_ready_factory_safety_item_as_host_only(
    tmp_path, monkeypatch
) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)
    _seed(
        _item(
            id_="bd-host",
            status="ready",
            rank="a1",
            factory_safety="needs-host-secrets",
        )
    )
    _seed(_item(id_="bd-ready", status="ready", rank="a2"))

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [(item.id, item.kind, item.handoff.kind) for item in attention] == [
        ("impl:bd-ready", "impl", "drive"),
        ("host-only:needs-host-secrets:bd-host", "host-only", "shell"),
    ]
    host_only = attention[1]
    assert host_only.source_ref.work_item == "bd-host"
    assert "bd-host" in host_only.summary
    assert str(tmp_path) in host_only.handoff.command
    assert "< /dev/null" in host_only.handoff.command


def test_build_attention_surfaces_recorded_factory_safety_refusal(tmp_path, monkeypatch) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)
    _write_journal_record(
        tmp_path,
        record={
            "stage": "outcome",
            "outcome": {
                "work_item_id": "bd-recorded",
                "status": "failed",
                "stage": "host-only-refused",
                "pr_number": None,
                "merge_sha": None,
                "detail": "factory-safety refusal",
            },
        },
    )

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [(item.id, item.kind, item.handoff.kind) for item in attention] == [
        ("host-only:recorded-refusal:bd-recorded", "host-only", "shell")
    ]


def test_build_attention_surfaces_unexpired_provider_exhaustion_hold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)
    _seed(_item(id_="bd-held", status="ready", rank="a1"))
    _write_journal_record(
        tmp_path,
        record={
            "stage": "provider-exhaustion-observed",
            "work_item_id": "bd-prior",
            "provider": "codex",
            "governing_condition": "provider_usage_limit",
            "record_expires_at": "2099-01-01T00:00:00Z",
        },
    )

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [(item.id, item.kind, item.handoff.kind) for item in attention] == [
        ("provider-exhaustion:codex:bd-held", "internal", "shell")
    ]
    [held] = attention
    assert held.source_ref.work_item == "bd-held"
    assert "provider=codex" in held.summary
    assert "record_expires_at=2099-01-01T00:00:00Z" in held.summary
    assert "Dispatcher admission pass" in held.handoff.command


def test_build_attention_enriches_needs_attention_parked_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)
    _seed(
        _item(
            id_="bd-parked",
            status="acceptance",
            rank="a1",
            acceptance_policy="human-only",
        )
    )
    _write_journal_record(
        tmp_path,
        record={
            "stage": "acceptance-ai-pass",
            "work_item_id": "bd-parked",
            "verdict": "NEEDS_ATTENTION",
            "acceptance_policy": "human-only",
            "diff": {"observed": False, "reason": "missing-merge-evidence"},
            "criteria": {"observed": True, "checks": []},
            "telemetry": {"observed": False, "reason": "missing-run-turn"},
        },
    )
    _write_journal_record(
        tmp_path,
        record={
            "stage": "acceptance-parked",
            "work_item_id": "bd-parked",
            "policy": "human-only",
            "advisory": True,
            "acceptance_verdict": "NEEDS_ATTENTION",
        },
    )

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [item.id for item in attention] == ["valve:accept:bd-parked"]
    [parked] = attention
    assert parked.kind == "human-valve"
    assert parked.handoff.action_id == "accept:bd-parked"
    assert "reject:bd-parked:rework" in parked.summary
    assert "reject:bd-parked:regroom" in parked.summary
    assert "NEEDS_ATTENTION" in parked.summary
    assert "absent evidence: diff, telemetry" in parked.summary


def test_build_attention_surfaces_stranded_merged_dispatch(tmp_path, monkeypatch) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)
    _seed(_item(id_="bd-active", status="active"))
    _write_journal_record(
        tmp_path,
        record={
            "stage": "outcome",
            "outcome": {
                "work_item_id": "bd-active",
                "status": "failed",
                "stage": "janitor-post-merge",
                "pr_number": 836,
                "merge_sha": "ba9fdafef895",
                "detail": "post-merge janitor red",
            },
        },
    )

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [(item.id, item.kind, item.handoff.kind) for item in attention] == [
        ("host-only:stranded-dispatch:bd-active", "host-only", "shell")
    ]
    stranded = attention[0]
    assert "PR #836" in stranded.summary
    assert "janitor-post-merge" in stranded.summary
    assert "reconcile-merged" in stranded.handoff.command
    assert "--item bd-active" in stranded.handoff.command


def test_build_attention_composes_capacity_residue_from_accounting(tmp_path, monkeypatch) -> None:
    _write_config(tmp_path, auto_approve_ready=True, wip_cap=2)
    _stub_spec_next(monkeypatch, output=None)
    live = _item(id_="bd-live", status="active")
    unreadable = _item(id_="bd-unreadable", status="active")
    for item in (live, unreadable):
        _seed(item)
    _write_dispatch_lock(tmp_path, work_item_id=live.id)
    journal = tmp_path / "tmp" / "fabro-dispatch-journal.jsonl"
    journal.mkdir(parents=True)
    original_journal = b""

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    capacity_items = [item for item in attention if item.id.startswith("hygiene:capacity")]
    assert [item.id for item in capacity_items] == [
        "hygiene:capacity:repo",
        "hygiene:capacity-hold:bd-unreadable",
    ]
    assert (
        capacity_items[0].summary
        == "Capacity reached for repo: 2 counted claims, 0 free slots under per-repo WIP cap 2; host-run concurrency is governed separately."
    )
    assert "codex exec" in capacity_items[0].handoff.command
    assert "inspect-capacity repo" in capacity_items[0].handoff.command
    assert capacity_items[1].source_ref.work_item == unreadable.id
    assert "Inspect capacity hold bd-unreadable" in capacity_items[1].summary
    assert "inspect-capacity-hold" in capacity_items[1].handoff.command
    assert "release-to-ready" not in capacity_items[1].handoff.command
    assert "bd-live" not in [item.id for item in capacity_items]
    assert not any(item.id == "host-only:stranded-dispatch:bd-unreadable" for item in attention)
    assert journal.is_dir()
    assert original_journal == b""


def test_build_attention_omits_capacity_when_all_counted_holds_are_live(
    tmp_path, monkeypatch
) -> None:
    _write_config(tmp_path, auto_approve_ready=True, wip_cap=2)
    _stub_spec_next(monkeypatch, output=None)
    first = _item(id_="bd-live-a", status="active")
    second = _item(id_="bd-live-b", status="active")
    for item in (first, second):
        _seed(item)
        _write_dispatch_lock(tmp_path, work_item_id=item.id)

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert not any(item.id.startswith("hygiene:capacity") for item in attention)


def test_build_attention_reads_capacity_count_from_accounting_verdict(
    tmp_path, monkeypatch
) -> None:
    _write_config(tmp_path, auto_approve_ready=True, wip_cap=2)
    _stub_spec_next(monkeypatch, output=None)
    live = _item(id_="bd-live", status="active")
    no_outcome = _item(id_="bd-no-outcome", status="active")
    for item in (live, no_outcome):
        _seed(item)
    _write_dispatch_lock(tmp_path, work_item_id=live.id)
    journal = tmp_path / "tmp" / "fabro-dispatch-journal.jsonl"
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text("", encoding="utf-8")

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert not any(item.id.startswith("hygiene:capacity") for item in attention)


def test_build_attention_surfaces_untriaged_backlog_and_summarizes_the_remainder(
    tmp_path, monkeypatch
) -> None:
    """The load-bearing case: a backlog item the intake gate never saw is visible.

    `livespec-h95t` — an item filed with a raw `bd create` lands in
    `backlog`, which no dispatch surface admits and no attention lane
    reported, so it was indistinguishable from a deliberately-parked epic.
    The `intake:triaged` marker is the discriminator: gated items carry it,
    this one does not. Noise control is part of the contract — P0/P1 get one
    lane each, everything at P2 or lower collapses into ONE summary lane.
    """
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)
    _seed_raw(id_="bd-p0", status="backlog", priority=0, title="Un-triaged P0")
    _seed_raw(id_="bd-p1", status="backlog", priority=1, title="Un-triaged P1")
    _seed_raw(id_="bd-p2", status="backlog", priority=2, title="Un-triaged P2")
    _seed_raw(id_="bd-p3", status="backlog", priority=3, title="Un-triaged P3")

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [(item.id, item.kind, item.urgency) for item in attention] == [
        ("hygiene:untriaged-backlog:bd-p0", "hygiene", "high"),
        ("hygiene:untriaged-backlog:bd-p1", "hygiene", "high"),
        ("hygiene:untriaged-backlog-remainder:count", "hygiene", "low"),
    ]
    assert attention[0].source_ref.work_item == "bd-p0"
    assert "Un-triaged P0" in attention[0].summary
    remainder = attention[2]
    assert remainder.source_ref.work_item is None
    assert "2 un-triaged backlog work-items at P2 or lower" in remainder.summary


def test_build_attention_omits_triaged_backlog_and_non_backlog_items(tmp_path, monkeypatch) -> None:
    """The marker dismisses an item; a non-backlog status is never in this lane.

    A deliberately-parked epic the intake gate routed to `backlog` carries
    `intake:triaged`, so it stays silent — that is the whole point of the
    discriminator. A P0 item in any other status belongs to another lane.
    """
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)
    _seed_raw(id_="bd-parked", status="backlog", priority=0, labels=["intake:triaged"])
    _seed_raw(id_="bd-elsewhere", status="ready", priority=0)

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [item.id for item in attention if item.kind == "hygiene"] == []


def test_build_attention_drops_spec_item_when_spec_next_none(tmp_path, monkeypatch) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=None)

    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    assert [item.kind for item in attention if item.kind == "spec"] == []


def test_render_json_wraps_flat_attention_array(tmp_path, monkeypatch) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=_stub_spec_output())
    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    payload = json.loads(render_json(attention=attention))

    assert list(payload) == ["attention"]
    assert payload["attention"][0]["id"] == "spec:revise:SPECIFICATION"


def test_render_markdown_lists_handoff_commands(tmp_path, monkeypatch) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=_stub_spec_output())
    attention = build_attention(
        project_root=tmp_path,
        repo_name="repo",
        include_hygiene=False,
    )

    rendered = render_markdown(attention=attention)

    assert rendered.startswith("# Needs Attention\n")
    assert "`spec:revise:SPECIFICATION`" in rendered
    assert "codex exec livespec:revise" in rendered


def test_render_markdown_empty_attention() -> None:
    assert render_markdown(attention=[]) == "No attention items.\n"


def test_main_json_output(
    tmp_path,
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=_stub_spec_output())
    rc = main(
        argv=["--json", "--skip-hygiene", "--project-root", str(tmp_path), "--repo-name", "repo"]
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert json.loads(captured.out)["attention"][0]["id"] == "spec:revise:SPECIFICATION"


def test_main_markdown_output(
    tmp_path,
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_config(tmp_path)
    _stub_spec_next(monkeypatch, output=_stub_spec_output())
    rc = main(argv=["--skip-hygiene", "--project-root", str(tmp_path), "--repo-name", "repo"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.startswith("# Needs Attention\n")


# --------------------------------------------------------------------------
# `_spec_next` — invoke CORE spec-`next` cross-plane via an injected seam,
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

    output = _spec_next(project_root=tmp_path, seam=seam)

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
    assert _spec_next(project_root=tmp_path, seam=seam) is None


def test_spec_next_returns_none_when_seam_run_raises(tmp_path) -> None:
    import subprocess

    seam = _seam(
        command=["python3", "/core/next.py"],
        raises=subprocess.SubprocessError("boom"),
    )
    assert _spec_next(project_root=tmp_path, seam=seam) is None


def test_spec_next_returns_none_when_cli_exits_nonzero(tmp_path) -> None:
    seam = _seam(
        command=["python3", "/core/next.py"],
        result=_SpecNextResult(stdout="", returncode=2),
    )
    assert _spec_next(project_root=tmp_path, seam=seam) is None


def test_spec_next_returns_none_when_stdout_unparseable(tmp_path) -> None:
    seam = _seam(
        command=["python3", "/core/next.py"],
        result=_SpecNextResult(stdout="not json at all", returncode=0),
    )
    assert _spec_next(project_root=tmp_path, seam=seam) is None


def test_spec_next_does_not_run_cli_when_unresolvable(tmp_path) -> None:
    calls: dict[str, object] = {}
    seam = _seam(command=None, result=_SpecNextResult(stdout="{}", returncode=0), calls=calls)

    assert _spec_next(project_root=tmp_path, seam=seam) is None
    assert "run" not in calls
