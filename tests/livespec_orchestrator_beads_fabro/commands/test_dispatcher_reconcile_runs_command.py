"""CLI wiring tests for `reconcile-runs` and its `stale-run-sweep` alias."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from livespec_orchestrator_beads_fabro.commands import _dispatcher_reconcile_runs_command as cli
from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_grace import HeldRun
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_runs_records import (
    ReconciledRun,
    ReconcileError,
    ReconcileRunsSummary,
)
from livespec_orchestrator_beads_fabro.commands.dispatcher import main
from livespec_orchestrator_beads_fabro.types import WorkItem


def test_reconcile_runs_emits_a_json_projection_and_wires_every_input(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = _stub(monkeypatch=monkeypatch, summary=_summary(reconciled=(_run(),)))

    exit_code = main(
        argv=[
            "reconcile-runs",
            "--repo",
            str(tmp_path),
            "--fabro-bin",
            "fabro",
            "--invoker",
            "agent:test",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["dry_run"] is False
    assert payload["reconciled"][0]["run_id"] == "01ORPHAN"
    assert payload["reconciled"][0]["orphan_reason"] == "item-not-active"
    assert calls["factories"] == (tmp_path, None)
    inputs = calls["inputs"]
    assert isinstance(inputs, dict)
    assert inputs["fabro_bin"] == "fabro"
    assert inputs["repo"] == tmp_path
    assert inputs["journal_path"] == tmp_path / "tmp" / "fabro-dispatch-journal.jsonl"
    assert inputs["invoker"] == "agent:test"


def test_the_stale_run_sweep_alias_resolves_to_the_same_handler(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = _stub(monkeypatch=monkeypatch, summary=_summary())

    exit_code = main(argv=["stale-run-sweep", "--repo", str(tmp_path), "--factory", "hp"])

    assert exit_code == 0
    assert capsys.readouterr().out == "(no orphaned fabro runs found)\n"
    assert calls["factories"] == (tmp_path, "hp")


def test_a_dry_run_reaches_the_reconciler_as_a_dry_run(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = _stub(monkeypatch=monkeypatch, summary=_summary(dry_run=True))

    exit_code = main(argv=["reconcile-runs", "--repo", str(tmp_path), "--dry-run", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["dry_run"] is True
    assert calls["dry_run"] is True
    assert calls["fabro_bin_cwd"] == tmp_path


def test_a_failure_on_either_leg_sets_the_nonzero_exit(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _ = _stub(
        monkeypatch=monkeypatch,
        summary=_summary(
            errors=(
                ReconcileError(
                    factory_name="hp",
                    factory_server_url=None,
                    run_id=None,
                    work_item_id=None,
                    reason="factory-ps-failed",
                    detail="fabro ps exited 7",
                ),
            )
        ),
    )
    errored = main(argv=["reconcile-runs", "--repo", str(tmp_path)])
    error_output = capsys.readouterr().out

    _ = _stub(
        monkeypatch=monkeypatch,
        summary=_summary(reconciled=(_run(termination_succeeded=False),)),
    )
    unterminated = main(argv=["reconcile-runs", "--repo", str(tmp_path)])
    orphan_output = capsys.readouterr().out

    assert errored == 1
    assert error_output == "ERROR   hp  factory-ps-failed: fabro ps exited 7\n"
    assert unterminated == 1
    assert orphan_output == (
        "ORPHAN  bd-ib-orphan  01ORPHAN  factory=hp run=blocked item=closed "
        "reason=item-not-active route=cancel\n"
    )


def test_an_omitted_repo_defaults_to_the_working_directory(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    calls = _stub(monkeypatch=monkeypatch, summary=_summary())

    exit_code = main(argv=["reconcile-runs", "--journal", str(tmp_path / "own.jsonl")])

    assert exit_code == 0
    assert capsys.readouterr().out == "(no orphaned fabro runs found)\n"
    inputs = calls["inputs"]
    assert isinstance(inputs, dict)
    assert inputs["repo"] == tmp_path
    assert inputs["journal_path"] == tmp_path / "own.jsonl"


def test_a_held_parked_run_is_projected_with_the_time_it_has_left(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _ = _stub(monkeypatch=monkeypatch, summary=_summary(held=(_held(),)))

    exit_code = main(argv=["reconcile-runs", "--repo", str(tmp_path), "--dry-run", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["held"][0]["hold_reason"] == "blocked-within-grace"
    assert payload["held"][0]["seconds_remaining"] == 1500.0
    assert payload["held"][0]["grace_seconds"] == 1800


def test_a_held_parked_run_renders_a_human_line_rather_than_reading_as_empty(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _ = _stub(monkeypatch=monkeypatch, summary=_summary(held=(_held(),)))

    exit_code = main(argv=["reconcile-runs", "--repo", str(tmp_path)])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "HELD    bd-ib-parked  01YOUNG  factory=hp run=blocked item=blocked "
        "reason=blocked-within-grace remaining=1500.0\n"
    )


def test_the_committed_grace_setting_reaches_the_reconciler(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = _stub(monkeypatch=monkeypatch, summary=_summary())
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps(
            {"livespec-orchestrator-beads-fabro": {"dispatcher": {"blocked_run_grace_seconds": 0}}}
        ),
        encoding="utf-8",
    )

    exit_code = main(argv=["reconcile-runs", "--repo", str(tmp_path)])

    inputs = calls["inputs"]
    assert exit_code == 0
    assert capsys.readouterr().out == "(no orphaned fabro runs found)\n"
    assert isinstance(inputs, dict)
    assert inputs["blocked_run_grace_seconds"] == 0


def test_an_unconfigured_grace_reaches_the_reconciler_as_the_documented_default(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = _stub(monkeypatch=monkeypatch, summary=_summary())

    exit_code = main(argv=["reconcile-runs", "--repo", str(tmp_path)])

    inputs = calls["inputs"]
    assert exit_code == 0
    assert capsys.readouterr().out == "(no orphaned fabro runs found)\n"
    assert isinstance(inputs, dict)
    assert inputs["blocked_run_grace_seconds"] == 1800


def _stub(
    *,
    monkeypatch: pytest.MonkeyPatch,
    summary: ReconcileRunsSummary,
) -> dict[str, object]:
    calls: dict[str, object] = {}

    def _load_items(*, repo: Path) -> list[WorkItem]:
        calls["items_repo"] = repo
        return []

    def _store_config(*, repo: Path) -> Any:
        calls["store_repo"] = repo
        return _StoreConfig()

    def _factories(*, repo: Path, factory: str | None = None) -> tuple[FactoryTarget, ...]:
        calls["factories"] = (repo, factory)
        return ()

    def _fabro_bin(*, cwd: Path) -> str:
        calls["fabro_bin_cwd"] = cwd
        return "resolved-fabro"

    def _reconcile(*, inputs: Any, factories: Any, dry_run: bool) -> ReconcileRunsSummary:
        calls["inputs"] = {
            "repo": inputs.repo,
            "fabro_bin": inputs.fabro_bin,
            "id_prefix": inputs.id_prefix,
            "journal_path": inputs.journal.path,
            "invoker": inputs.journal.identity.invoker,
            "blocked_run_grace_seconds": inputs.blocked_run_grace_seconds,
        }
        calls["factory_targets"] = factories
        calls["dry_run"] = dry_run
        return summary

    monkeypatch.setattr(cli, "load_items", _load_items)
    monkeypatch.setattr(cli, "store_config", _store_config)
    monkeypatch.setattr(cli, "make_beads_client", lambda **_: object())
    monkeypatch.setattr(cli, "reconcile_factory_targets", _factories)
    monkeypatch.setattr(cli, "resolve_fabro_bin", _fabro_bin)
    monkeypatch.setattr(cli, "reconcile_runs", _reconcile)
    return calls


class _StoreConfig:
    prefix = "bd-ib"


def _held() -> HeldRun:
    return HeldRun(
        run_id="01YOUNG",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
        status_kind="blocked",
        work_item_id="bd-ib-parked",
        work_item_status="blocked",
        hold_reason="blocked-within-grace",
        parked_seconds=300.0,
        seconds_remaining=1500.0,
        grace_seconds=1800,
    )


def _summary(
    *,
    reconciled: tuple[ReconciledRun, ...] = (),
    errors: tuple[ReconcileError, ...] = (),
    dry_run: bool = False,
    held: tuple[HeldRun, ...] = (),
) -> ReconcileRunsSummary:
    return ReconcileRunsSummary(reconciled=reconciled, errors=errors, dry_run=dry_run, held=held)


def _run(*, termination_succeeded: bool = True) -> ReconciledRun:
    return ReconciledRun(
        run_id="01ORPHAN",
        factory_name="hp",
        factory_server_url="https://hp.example:32276",
        status_kind="blocked",
        work_item_id="bd-ib-orphan",
        work_item_status="closed",
        orphan_reason="item-not-active",
        termination_route="cancel",
        termination_succeeded=termination_succeeded,
        termination_detail="cancel route returned 200",
        export_comment_id="c-1",
    )
