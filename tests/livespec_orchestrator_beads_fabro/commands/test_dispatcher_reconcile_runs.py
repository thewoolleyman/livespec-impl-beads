"""Tests for the whole-inventory reconciliation pass over every factory."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from livespec_orchestrator_beads_fabro.commands import _dispatcher_reconcile_runs as reconcile
from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_preserve_reference_body import (
    PRESERVE_POINTER_MARKER,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_export import (
    ExportOutcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_join import (
    journaled_runs,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port_http import FabroHttpResult
from livespec_orchestrator_beads_fabro.commands._fabro_port_types import FabroTarget
from livespec_orchestrator_beads_fabro.commands._run_attribution import (
    GOAL_TEXT_ONLY,
    RunAttribution,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

_HP_DEV_TOKEN_VALUE = "hp-fixture-dev-token"
_VPS_DEV_TOKEN_VALUE = "vps-fixture-dev-token"
_HP = FactoryTarget(name="hp", server="https://hp.example:32276", dev_token=_HP_DEV_TOKEN_VALUE)
_VPS = FactoryTarget(name="vps", server="https://vps.example:32276", dev_token=_VPS_DEV_TOKEN_VALUE)
# The factory an operator host has NOT exported a dev token for, and which no
# `~/.fabro/auth.json` entry covers either: every HTTP route it offers is 401.
_UNAUTHENTICATED = FactoryTarget(name="hp", server="https://hp.example:32276", dev_token=None)
_QUESTIONS_BODY = json.dumps(
    {
        "data": [
            {
                "id": "q-1",
                "options": [{"key": "A", "label": "[A] Abandon (leave open for triage)"}],
                "stage": "escalate",
            }
        ],
        "meta": {"has_more": False},
    }
)


@dataclass(kw_only=True)
class _Runner:
    """One fake `fabro` CLI, keyed by the server the argv names."""

    ps_by_server: dict[str, str] = field(default_factory=dict)
    failing_servers: frozenset[str] = frozenset()
    calls: list[list[str]] = field(default_factory=list)

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
        self.calls.append(argv)
        server = argv[argv.index("--server") + 1] if "--server" in argv else ""
        if argv[1] == "ps":
            if server in self.failing_servers:
                return CommandResult(exit_code=7, stdout="", stderr="unreachable")
            return CommandResult(exit_code=0, stdout=self.ps_by_server.get(server, "[]"), stderr="")
        return CommandResult(exit_code=0, stdout="", stderr="")


@dataclass(kw_only=True)
class _Transport:
    calls: list[str] = field(default_factory=list)

    def send(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout_seconds: float,
    ) -> FabroHttpResult:
        _ = (headers, body, timeout_seconds)
        self.calls.append(f"{method} {url}")
        answered = _QUESTIONS_BODY if url.endswith("/questions") else "{}"
        return FabroHttpResult(
            status=200,
            body=answered,
            error=None,
            payload=None,
            succeeded=True,
        )


@dataclass(kw_only=True)
class _RefusingTransport:
    """What an unauthenticated port meets on every route: 401, no body."""

    calls: list[str] = field(default_factory=list)

    def send(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout_seconds: float,
    ) -> FabroHttpResult:
        _ = (body, timeout_seconds)
        self.calls.append(f"{method} {url}")
        assert "Authorization" not in headers
        return FabroHttpResult(status=401, body="", error=None, payload=None, succeeded=False)


@dataclass(kw_only=True)
class _Journal:
    written: list[dict[str, object]] = field(default_factory=list)

    def append(self, *, record: dict[str, object]) -> None:
        self.written.append(record)


@dataclass(kw_only=True)
class _Ledger:
    comments: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    verbs: list[str] = field(default_factory=list)

    def list_comments(self, *, issue_id: str) -> list[dict[str, Any]]:
        self.verbs.append(f"list_comments:{issue_id}")
        return list(self.comments.get(issue_id, []))

    def add_comment(self, *, issue_id: str, body: str) -> None:
        self.verbs.append(f"add_comment:{issue_id}")
        self.comments.setdefault(issue_id, []).append({"id": f"c-{issue_id}", "text": body})


def test_a_closed_item_run_is_exported_then_terminated_and_journaled(tmp_path: Path) -> None:
    runner = _Runner(ps_by_server={_HP.server or "": _ps(run_id="01ORPHAN", kind="blocked")})
    transport = _Transport()
    journal = _Journal()
    ledger = _Ledger()

    summary = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=runner,
            transport=transport,
            journal=journal,
            ledger=ledger,
            items=[_item(id="bd-ib-orphan", status="closed")],
        ),
        factories=[_HP],
    )

    assert [
        (run.run_id, run.orphan_reason, run.termination_route) for run in summary.reconciled
    ] == [("01ORPHAN", "item-not-active", "questions-answer")]
    # The export precedes the termination: the comment verbs are recorded
    # before any HTTP verb reaches the factory.
    assert ledger.verbs[0] == "list_comments:bd-ib-orphan"
    assert "add_comment:bd-ib-orphan" in ledger.verbs
    assert transport.calls[0].startswith(
        "GET https://hp.example:32276/api/v1/runs/01ORPHAN/questions"
    )
    assert [record["stage"] for record in journal.written] == ["orphan-run-reconciled"]
    assert journal.written[0]["export_comment_id"] == "c-bd-ib-orphan"


def test_an_unresolved_credential_is_journaled_before_the_rm_fallback(tmp_path: Path) -> None:
    runner = _Runner(
        ps_by_server={_UNAUTHENTICATED.server or "": _ps(run_id="01ORPHAN", kind="blocked")}
    )
    transport = _RefusingTransport()
    journal = _Journal()

    summary = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=runner,
            transport=transport,
            journal=journal,
            ledger=_Ledger(),
            items=[_item(id="bd-ib-orphan", status="closed")],
        ),
        factories=[_UNAUTHENTICATED],
    )

    assert [run.termination_route for run in summary.reconciled] == ["rm-force"]
    # The unauthenticated record is written BEFORE the reconciled one, so the
    # degrade is legible as this host carrying no credential rather than as the
    # factory having refused each route on its merits.
    assert [record["stage"] for record in journal.written] == [
        "terminate-route-unauthenticated",
        "orphan-run-reconciled",
        "orphan-run-reconcile-rm-fallback",
    ]
    assert journal.written[0]["run_id"] == "01ORPHAN"
    assert "~/.fabro/auth.json" in str(journal.written[0]["detail"])


def test_a_failing_factory_is_journaled_and_the_other_still_reconciles(tmp_path: Path) -> None:
    runner = _Runner(
        ps_by_server={_VPS.server or "": _ps(run_id="01ORPHAN", kind="running")},
        failing_servers=frozenset({_HP.server or ""}),
    )
    journal = _Journal()

    summary = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=runner,
            transport=_Transport(),
            journal=journal,
            ledger=_Ledger(),
            items=[_item(id="bd-ib-orphan", status="done")],
        ),
        factories=[_HP, _VPS],
    )

    assert [(error.factory_name, error.reason) for error in summary.errors] == [
        ("hp", "factory-ps-failed")
    ]
    assert [(run.factory_name, run.termination_route) for run in summary.reconciled] == [
        ("vps", "cancel")
    ]
    assert [record["stage"] for record in journal.written] == [
        "orphan-run-reconciled",
        "orphan-run-reconcile-error",
    ]


def test_a_factory_without_a_server_url_is_refused_rather_than_surveyed(tmp_path: Path) -> None:
    runner = _Runner()

    summary = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=runner,
            transport=_Transport(),
            journal=_Journal(),
            ledger=_Ledger(),
            items=[],
        ),
        factories=[FactoryTarget(name="implicit", server=None, dev_token=None)],
    )

    assert runner.calls == []
    assert [error.reason for error in summary.errors] == ["factory-server-url-missing"]


def test_no_bare_fabro_target_is_ever_constructed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built: list[FabroTarget] = []

    def _record(**kwargs: object) -> FabroTarget:
        target = FabroTarget(**kwargs)  # pyright: ignore[reportArgumentType]
        built.append(target)
        return target

    monkeypatch.setattr(reconcile, "FabroTarget", _record)

    _ = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=_Runner(),
            transport=_Transport(),
            journal=_Journal(),
            ledger=_Ledger(),
            items=[],
        ),
        factories=[_HP, _VPS, FactoryTarget(name="implicit", server=None, dev_token=None)],
    )

    assert [target.server_url for target in built] == [_HP.server, _VPS.server]
    assert all(target.server_url is not None for target in built)


def test_a_dry_run_emits_the_orphan_set_and_mutates_nothing(tmp_path: Path) -> None:
    runner = _Runner(ps_by_server={_HP.server or "": _ps(run_id="01ORPHAN", kind="blocked")})
    transport = _Transport()
    journal = _Journal()
    ledger = _Ledger()

    summary = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=runner,
            transport=transport,
            journal=journal,
            ledger=ledger,
            items=[_item(id="bd-ib-orphan", status="closed")],
        ),
        factories=[_HP, FactoryTarget(name="implicit", server=None, dev_token=None)],
        dry_run=True,
    )

    assert [run.run_id for run in summary.reconciled] == ["01ORPHAN"]
    assert summary.dry_run is True
    assert journal.written == []
    assert ledger.verbs == []
    assert transport.calls == []
    assert [call[1] for call in runner.calls] == ["ps"]


def test_an_item_missing_orphan_preserves_its_pointer_in_the_journal(tmp_path: Path) -> None:
    runner = _Runner(
        ps_by_server={
            _HP.server or "": _ps(run_id="01GONE", kind="starting", work_item_id="bd-ib-gone")
        }
    )
    journal = _Journal()
    ledger = _Ledger()

    summary = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=runner,
            transport=_Transport(),
            journal=journal,
            ledger=ledger,
            items=[],
        ),
        factories=[_HP],
    )

    assert [run.orphan_reason for run in summary.reconciled] == ["item-missing"]
    assert [record["stage"] for record in journal.written] == [
        "orphan-run-reconcile-export",
        "orphan-run-reconciled",
    ]
    body = journal.written[0]["pointer_body"]
    assert isinstance(body, str)
    assert body.startswith(PRESERVE_POINTER_MARKER)
    assert ledger.verbs == []


def test_an_unverified_export_leaves_the_run_untouched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        reconcile,
        "export_orphan_reference",
        lambda **_: ExportOutcome(
            exported=False,
            comment_id=None,
            journal_body=None,
            detail="read-back failed",
        ),
    )
    runner = _Runner(ps_by_server={_HP.server or "": _ps(run_id="01ORPHAN", kind="blocked")})
    transport = _Transport()
    journal = _Journal()

    summary = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=runner,
            transport=transport,
            journal=journal,
            ledger=_Ledger(),
            items=[_item(id="bd-ib-orphan", status="closed")],
        ),
        factories=[_HP],
    )

    assert summary.reconciled == ()
    assert [error.reason for error in summary.errors] == ["export-not-verified"]
    assert transport.calls == []
    assert [call[1] for call in runner.calls] == ["ps"]
    assert [record["stage"] for record in journal.written] == ["orphan-run-reconcile-error"]


def test_the_ledger_attribution_reaches_the_join_and_spares_a_stamped_run(tmp_path: Path) -> None:
    """`ReconcileInputs.attribution` is threaded to the join, not merely stored.

    The run's goal text names `bd-ib-orphan`, which is `closed` — the shape the
    regex-only join reconciles. The ledger stamps the same run onto the ACTIVE
    `bd-ib-live`, so nothing may be terminated.
    """
    runner = _Runner(ps_by_server={_HP.server or "": _ps(run_id="01ORPHAN", kind="running")})
    journal = _Journal()

    summary = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=runner,
            transport=_Transport(),
            journal=journal,
            ledger=_Ledger(),
            items=[
                _item(id="bd-ib-orphan", status="closed"),
                _item(id="bd-ib-live", status="active"),
            ],
            attribution=RunAttribution(metadata_run_ids={"01ORPHAN": "bd-ib-live"}),
        ),
        factories=[_HP],
    )

    assert summary.reconciled == ()
    assert summary.errors == ()
    assert journal.written == []


def test_the_reconciler_is_handed_no_ledger_status_write_seam(tmp_path: Path) -> None:
    ledger = _Ledger()

    _ = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=_Runner(ps_by_server={_HP.server or "": _ps(run_id="01ORPHAN", kind="blocked")}),
            transport=_Transport(),
            journal=_Journal(),
            ledger=ledger,
            items=[_item(id="bd-ib-orphan", status="closed")],
        ),
        factories=[_HP],
    )

    assert {verb.split(":", maxsplit=1)[0] for verb in ledger.verbs} == {
        "list_comments",
        "add_comment",
    }


def test_a_targeted_pass_leaves_every_other_items_orphan_alone(tmp_path: Path) -> None:
    """`only_work_item_id` narrows what is ACTED ON, not what is classified."""
    runner = _Runner(
        ps_by_server={
            _HP.server or "": json.dumps(
                [
                    _run(run_id="01MINE", kind="blocked", work_item_id="bd-ib-mine"),
                    _run(run_id="01THEIRS", kind="blocked", work_item_id="bd-ib-theirs"),
                ]
            )
        }
    )

    summary = reconcile.reconcile_runs(
        inputs=_inputs(
            tmp_path=tmp_path,
            runner=runner,
            transport=_Transport(),
            journal=_Journal(),
            ledger=_Ledger(),
            items=[
                _item(id="bd-ib-mine", status="closed"),
                _item(id="bd-ib-theirs", status="closed"),
            ],
            only_work_item_id="bd-ib-mine",
        ),
        factories=[_HP],
    )

    assert [run.run_id for run in summary.reconciled] == ["01MINE"]
    assert summary.errors == ()


def _inputs(
    *,
    tmp_path: Path,
    runner: _Runner,
    transport: _Transport,
    journal: _Journal,
    ledger: _Ledger,
    items: list[WorkItem],
    only_work_item_id: str | None = None,
    attribution: RunAttribution = GOAL_TEXT_ONLY,
) -> reconcile.ReconcileInputs:
    return reconcile.ReconcileInputs(
        repo=tmp_path,
        fabro_bin="fabro",
        id_prefix="bd-ib",
        items=items,
        only_work_item_id=only_work_item_id,
        journaled=journaled_runs(text=""),
        runner=runner,
        journal=journal,
        ledger=ledger,
        attribution=attribution,
        http=transport,
    )


def _ps(*, run_id: str, kind: str, work_item_id: str = "bd-ib-orphan") -> str:
    return json.dumps([_run(run_id=run_id, kind=kind, work_item_id=work_item_id)])


def _run(*, run_id: str, kind: str, work_item_id: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "goal": f"Work-item: {work_item_id}\nRepo: /tmp/repo",
        "status": {"kind": kind},
    }


def _item(*, id: str, status: str) -> WorkItem:
    return WorkItem(
        id=id,
        type="task",
        status=status,
        title=id,
        description=id,
        origin="freeform",
        gap_id=None,
        rank="a0",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-30T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )
