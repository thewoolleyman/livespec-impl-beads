"""Edge coverage for stranded-dispatch attention derivation."""

import json
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands import _needs_attention_work_items
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._needs_attention_stranded_dispatch import (
    stranded_dispatch_items,
)
from livespec_orchestrator_beads_fabro.types import WorkItem


def _item(*, id_: str, status: str = "active") -> WorkItem:
    return WorkItem(
        id=id_,
        type="task",
        status=status,  # type: ignore[arg-type]
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
    )


def _write_journal_lines(project_root: Path, *, records: list[object]) -> None:
    journal = project_root / "tmp" / "fabro-dispatch-journal.jsonl"
    journal.parent.mkdir(parents=True)
    lines = [record if isinstance(record, str) else json.dumps(record) for record in records]
    _ = journal.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _no_live_lock(*, repo: Path, work_item_id: str) -> None:
    _ = (repo, work_item_id)


def test_stranded_dispatch_items_ignore_live_lock(tmp_path: Path) -> None:
    _write_journal_lines(
        tmp_path,
        records=[{"stage": "dispatch-id", "work_item_id": "bd-active"}],
    )

    def _live_lock(*, repo: Path, work_item_id: str) -> object:
        _ = (repo, work_item_id)
        return object()

    attention = stranded_dispatch_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-active")],
        live_lock_lookup=_live_lock,
    )

    assert attention == []


def test_stranded_dispatch_items_parse_embedded_outcome_payload(tmp_path: Path) -> None:
    _write_journal_lines(
        tmp_path,
        records=[
            {
                "stage": "legacy-wrapper",
                "outcome": {
                    "work_item_id": "bd-active",
                    "status": "failed",
                    "stage": "janitor-post-merge",
                    "pr_number": 836,
                    "merge_sha": "ba9fdafef895",
                },
            }
        ],
    )

    attention = stranded_dispatch_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-active")],
        live_lock_lookup=_no_live_lock,
    )

    assert [item.id for item in attention] == ["host-only:stranded-dispatch:bd-active"]


def test_stranded_dispatch_items_embedded_green_outcome_clears_prior_opening(
    tmp_path: Path,
) -> None:
    _write_journal_lines(
        tmp_path,
        records=[
            {"stage": "dispatch-id", "work_item_id": "bd-active"},
            {
                "stage": "legacy-wrapper",
                "outcome": {
                    "work_item_id": "bd-active",
                    "status": "green",
                    "stage": "done",
                    "pr_number": 836,
                    "merge_sha": "ba9fdafef895",
                },
            },
        ],
    )

    attention = stranded_dispatch_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-active")],
        live_lock_lookup=_no_live_lock,
    )

    assert attention == []


def test_stranded_dispatch_items_ignore_invalid_opening_and_outcome_edges(
    tmp_path: Path,
) -> None:
    _write_journal_lines(
        tmp_path,
        records=[
            {"stage": "dispatch-id", "work_item_id": ""},
            [],
            {"stage": "ignored", "work_item_id": "bd-active"},
            {"stage": "outcome", "outcome": "nope"},
            {
                "stage": "outcome",
                "outcome": {
                    "work_item_id": "bd-active",
                    "status": "cancelled",
                    "stage": "review",
                    "pr_number": None,
                    "merge_sha": None,
                },
            },
            {
                "stage": "outcome",
                "outcome": {
                    "work_item_id": "bd-active",
                    "status": "failed",
                    "stage": "review",
                    "pr_number": None,
                    "merge_sha": 123,
                },
            },
        ],
    )

    attention = stranded_dispatch_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-active")],
        live_lock_lookup=_no_live_lock,
    )

    assert attention == []


def test_stranded_dispatch_items_count_opening_attempt_shapes(tmp_path: Path) -> None:
    _write_journal_lines(
        tmp_path,
        records=[
            {"stage": "dispatch-id", "work_item_id": "bd-active", "dispatch_id": "dispatch-1"},
            {"stage": "dispatch-id", "work_item_id": "bd-active", "dispatch_id": "dispatch-2"},
        ],
    )

    attention = stranded_dispatch_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-active")],
        live_lock_lookup=_no_live_lock,
    )

    assert [item.id for item in attention] == ["host-only:stranded-dispatch:bd-active"]
    assert "2 prior attempts" in attention[0].summary


def test_stranded_dispatch_items_count_failed_outcomes(tmp_path: Path) -> None:
    _write_journal_lines(
        tmp_path,
        records=[
            {
                "stage": "outcome",
                "outcome": {
                    "work_item_id": "bd-active",
                    "status": "failed",
                    "stage": "review",
                    "pr_number": None,
                    "merge_sha": None,
                },
            },
            {
                "stage": "outcome",
                "outcome": {
                    "work_item_id": "bd-active",
                    "status": "failed",
                    "stage": "merge-poll",
                    "pr_number": 2018,
                    "merge_sha": None,
                },
            },
        ],
    )

    attention = stranded_dispatch_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-active")],
        live_lock_lookup=_no_live_lock,
    )

    assert [item.id for item in attention] == ["host-only:stranded-dispatch:bd-active"]
    assert "2 prior attempts" in attention[0].summary
    assert "gh pr view 2018" in attention[0].handoff.command


def test_stranded_dispatch_items_green_outcome_clears_prior_opening(
    tmp_path: Path,
) -> None:
    _write_journal_lines(
        tmp_path,
        records=[
            {"stage": "ledger-admit", "work_item_id": "bd-active"},
            {"stage": "ledger-admit", "work_item_id": "bd-active"},
            {
                "stage": "outcome",
                "outcome": {
                    "work_item_id": "bd-active",
                    "status": "green",
                    "stage": "done",
                    "pr_number": 836,
                    "merge_sha": "ba9fdafef895",
                },
            },
        ],
    )

    attention = stranded_dispatch_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-active")],
        live_lock_lookup=_no_live_lock,
    )

    assert attention == []


def test_work_items_watchable_run_fails_soft_on_nonzero_ps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_journal_lines(
        tmp_path,
        records=[{"stage": "dispatch-id", "work_item_id": "bd-active"}],
    )

    class _Runner:
        def run(
            self,
            *,
            argv: list[str],
            cwd: Path,
            timeout_seconds: float,
            env: dict[str, str] | None = None,
            stdin: int | None = None,
        ) -> CommandResult:
            _ = (argv, cwd, timeout_seconds, env, stdin)
            return CommandResult(exit_code=9, stdout="", stderr="boom")

    monkeypatch.setattr(_needs_attention_work_items, "ShellCommandRunner", _Runner)

    attention = _needs_attention_work_items.stranded_dispatch_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-active")],
    )

    assert [item.id for item in attention] == ["host-only:stranded-dispatch:bd-active"]


def test_work_items_watchable_run_suppresses_stranded_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_journal_lines(
        tmp_path,
        records=[{"stage": "dispatch-id", "work_item_id": "bd-active"}],
    )

    class _Runner:
        def run(
            self,
            *,
            argv: list[str],
            cwd: Path,
            timeout_seconds: float,
            env: dict[str, str] | None = None,
            stdin: int | None = None,
        ) -> CommandResult:
            _ = (argv, cwd, timeout_seconds, env, stdin)
            stdout = json.dumps(
                {
                    "runs": [
                        {
                            "run_id": "01RUN",
                            "goal": "Work-item: bd-active",
                            "status": {"kind": "running"},
                        }
                    ]
                }
            )
            return CommandResult(exit_code=0, stdout=stdout, stderr="")

    monkeypatch.setattr(_needs_attention_work_items, "ShellCommandRunner", _Runner)

    attention = _needs_attention_work_items.stranded_dispatch_items(
        project_root=tmp_path,
        repo="repo",
        items=[_item(id_="bd-active")],
    )

    assert attention == []
