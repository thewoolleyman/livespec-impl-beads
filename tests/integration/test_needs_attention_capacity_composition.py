"""Integration-tier acceptance for capacity truth composed from the accounting.

Binds `SPECIFICATION/scenarios.md` "Scenario 83 — Capacity truth is composed
from the accounting, never re-derived" through the real `build_attention`
composition and the real store/client seam against the in-memory
`FakeBeadsClient`.

The point of driving the whole snapshot rather than `capacity_items` alone is
that the scenario's guarantees are NEGATIVE across lanes: the live-lock holder
must not surface as a stale claim, and the rework-pending park must not surface
as an abandoned one. A test that called the capacity lane in isolation could not
observe either, because the lane that would wrongly report them is a different
lane. Only the composed snapshot can prove they are absent from ALL of it.

The two control cases are what keep the positive case honest. A cap backed
entirely by live watchable runs emits nothing, and a green-terminal claim under
a readable journal is not counted at all — so no capacity item exists to
advertise a status move for it. Without those, "the fact appeared" could not be
told apart from "the fact always appears".
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._beads_client import make_beads_client, reset_fake_singleton
from livespec_orchestrator_beads_fabro.commands import needs_attention
from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_lock import (
    write_dispatch_lock,
)
from livespec_orchestrator_beads_fabro.commands.needs_attention import build_attention
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem
from livespec_runtime.attention_item import AttentionItem
from livespec_runtime.needs_attention import SpecNextOutput

_JOURNAL = Path("tmp") / "fabro-dispatch-journal.jsonl"
_REWORK_PENDING_LABEL = "rework:pending"
_CAPACITY_FACT_ID = "hygiene:capacity:repo"


@pytest.fixture(autouse=True)
def _hermetic_fake_backend(monkeypatch: pytest.MonkeyPatch) -> object:
    monkeypatch.setenv("LIVESPEC_BEADS_FAKE", "1")
    reset_fake_singleton()
    yield
    reset_fake_singleton()


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _item(*, id_: str, status: str, rank: str = "a2") -> WorkItem:
    base = WorkItem(
        id=id_,
        type="task",
        status="active",
        title=f"{id_} title",
        description="d",
        origin="freeform",
        gap_id=None,
        rank=rank,
        assignee=None,
        depends_on=(),
        captured_at="2026-08-24T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )
    return replace(base, status=status)  # pyright: ignore[reportArgumentType]


def _seed(*, id_: str, status: str = "active", rework_pending: bool = False) -> None:
    append_work_item(path=_config(), item=_item(id_=id_, status=status))
    if rework_pending:
        make_beads_client(config=_config()).update_issue(
            issue_id=id_, add_labels=[_REWORK_PENDING_LABEL]
        )


def _write_project(*, root: Path, wip_cap: int) -> None:
    (root / ".livespec.jsonc").write_text(
        json.dumps(
            {
                "livespec-orchestrator-beads-fabro": {
                    "connection": {
                        "tenant": "livespec-impl-beads",
                        "prefix": "bd",
                        "server_user": "livespec-impl-beads",
                        "database": "livespec-impl-beads",
                        "bd_path": "bd",
                        "fake": True,
                    },
                    "dispatcher": {"wip_cap": wip_cap},
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _unreadable_journal(*, root: Path) -> Path:
    """Make the dispatch journal unreadable the way a real corruption reads.

    A directory at the journal path makes `read_text` raise `OSError`, which is
    the one condition the accounting classifies as `journal-unreadable`.
    """
    journal = root / _JOURNAL
    journal.mkdir(parents=True)
    return journal


def _readable_journal(*, root: Path, records: list[dict[str, object]]) -> Path:
    journal = root / _JOURNAL
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return journal


def _no_spec_next(*, project_root: Path) -> SpecNextOutput | None:
    _ = project_root
    return None


def _snapshot(*, root: Path, monkeypatch: pytest.MonkeyPatch) -> list[AttentionItem]:
    monkeypatch.setattr(needs_attention, "_spec_next", _no_spec_next)
    return build_attention(project_root=root, repo_name="repo", include_hygiene=False)


def test_a_reached_cap_with_an_unreadable_hold_composes_the_capacity_residue_fact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project(root=tmp_path, wip_cap=2)
    _seed(id_="bd-live")
    _seed(id_="bd-unreadable")
    _seed(id_="bd-rework", rework_pending=True)
    _ = write_dispatch_lock(repo=tmp_path, work_item_id="bd-live", dispatch_id="run-live")
    journal = _unreadable_journal(root=tmp_path)

    attention = _snapshot(root=tmp_path, monkeypatch=monkeypatch)

    capacity = [item for item in attention if item.id.startswith("hygiene:capacity")]
    assert [item.id for item in capacity] == [
        _CAPACITY_FACT_ID,
        "hygiene:capacity-hold:bd-unreadable",
    ]
    assert "2 counted claims, 0 free slots" in capacity[0].summary
    # The hold names its holder and hands off to an inspection, not a mutation.
    assert capacity[1].source_ref.work_item == "bd-unreadable"
    assert "journal-unreadable" in capacity[1].summary
    assert "inspect-capacity-hold bd-unreadable" in capacity[1].handoff.command
    # No capacity item advertises a status move for any claim it reports.
    assert all("release-to-ready" not in item.handoff.command for item in capacity)
    assert all("do not move status" in item.handoff.command for item in capacity[1:])
    # The live-lock holder and the rework park are absent from the WHOLE
    # snapshot, not merely from the capacity lane: neither reads as stale,
    # abandoned, or stranded anywhere.
    referenced = {item.source_ref.work_item for item in attention}
    assert "bd-live" not in referenced
    assert "bd-rework" not in referenced
    # Composing the snapshot is a read: the accounting's abandonment-recording
    # sibling is the writer, and this path is not it.
    assert journal.is_dir()
    assert list(journal.iterdir()) == []


def test_a_green_terminal_claim_is_not_counted_and_composes_no_capacity_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project(root=tmp_path, wip_cap=2)
    _seed(id_="bd-live")
    _seed(id_="bd-green")
    _ = write_dispatch_lock(repo=tmp_path, work_item_id="bd-live", dispatch_id="run-live")
    _ = _readable_journal(
        root=tmp_path,
        records=[
            {"stage": "ledger-admit", "work_item_id": "bd-green"},
            {
                "stage": "outcome",
                "outcome": {
                    "work_item_id": "bd-green",
                    "status": "green",
                    "stage": "done",
                    "pr_number": 41,
                    "merge_sha": "feed01",
                    "detail": "merged",
                },
            },
        ],
    )

    attention = _snapshot(root=tmp_path, monkeypatch=monkeypatch)

    # A green terminal after the last admit is reclaimable, so it is not a
    # counted hold: one live claim against a cap of 2 leaves a slot free and no
    # capacity item exists at all — which is why none can advertise a status
    # move for that claim.
    assert [item for item in attention if item.id.startswith("hygiene:capacity")] == []


def test_a_busy_cap_backed_entirely_by_live_runs_emits_no_capacity_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project(root=tmp_path, wip_cap=2)
    _seed(id_="bd-live-one")
    _seed(id_="bd-live-two")
    for work_item_id in ("bd-live-one", "bd-live-two"):
        _ = write_dispatch_lock(
            repo=tmp_path, work_item_id=work_item_id, dispatch_id=f"run-{work_item_id}"
        )
    _ = _unreadable_journal(root=tmp_path)

    attention = _snapshot(root=tmp_path, monkeypatch=monkeypatch)

    # The cap is full and every hold is backed by a live watchable run, so
    # there is nothing actionable to surface. A capacity item here would be
    # noise an operator cannot act on.
    assert [item for item in attention if item.id.startswith("hygiene:capacity")] == []
