"""CLI wiring tests for the stale Fabro run sweep."""

from __future__ import annotations

import json
import runpy
from dataclasses import dataclass
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands import _dispatcher_stale_run_sweep
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands.dispatcher import main
from livespec_orchestrator_beads_fabro.types import WorkItem


@dataclass(kw_only=True)
class _Runner:
    ps_json: str = "[]"
    ps_exit_code: int = 0
    rm_exit_code: int = 0
    calls: list[list[str]]

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env)
        self.calls.append(argv)
        if argv[1] == "ps":
            return CommandResult(exit_code=self.ps_exit_code, stdout=self.ps_json, stderr="")
        if argv[1] == "rm":
            return CommandResult(exit_code=self.rm_exit_code, stdout="", stderr="")
        return CommandResult(exit_code=1, stdout="", stderr="unexpected")


@dataclass(frozen=True, kw_only=True)
class _Factory:
    name: str
    server: str | None
    dev_token: str | None


def test_stale_run_sweep_cli_emits_json_summary(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    item = _item(id="bd-ib-closed", status="done")
    calls: dict[str, object] = {}

    def _load_items(*, repo: Path) -> list[WorkItem]:
        calls["repo"] = repo
        return [item]

    def _resolve_factory(*, cwd: Path, factory: str | None = None) -> _Factory:
        calls["factory"] = (cwd, factory)
        return _Factory(name="host", server="http://127.0.0.1:32276", dev_token=None)

    def _reap(**kwargs: object) -> _dispatcher_stale_run_sweep.StaleFabroRunSweepSummary:
        calls["reap"] = kwargs
        return _dispatcher_stale_run_sweep.StaleFabroRunSweepSummary(
            probe_exit_code=0,
            reaped=(
                _dispatcher_stale_run_sweep.ReapedStaleFabroRun(
                    work_item_id="bd-ib-closed",
                    run_id="01CLOSED",
                    run_status="runnable",
                    item_status="done",
                    rm_exit_code=0,
                ),
            ),
        )

    monkeypatch.setattr(_dispatcher_stale_run_sweep, "load_items", _load_items)
    monkeypatch.setattr(_dispatcher_stale_run_sweep, "resolve_fabro_factory", _resolve_factory)
    monkeypatch.setattr(_dispatcher_stale_run_sweep, "reap_stale_fabro_runs", _reap)

    assert (
        main(
            argv=[
                "stale-run-sweep",
                "--repo",
                str(tmp_path),
                "--factory",
                "host",
                "--fabro-bin",
                "fabro",
                "--json",
            ]
        )
        == 0
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["reaped"][0]["run_id"] == "01CLOSED"
    assert calls["repo"] == tmp_path
    assert calls["factory"] == (tmp_path, "host")
    reap_kwargs = calls["reap"]
    assert isinstance(reap_kwargs, dict)
    assert reap_kwargs["items"] == [item]
    assert reap_kwargs["fabro_bin"] == "fabro"
    assert reap_kwargs["fabro_factory_server"] == "http://127.0.0.1:32276"


def test_stale_run_sweep_skips_unusable_and_dispatchable_runs(tmp_path: Path) -> None:
    runner = _Runner(
        calls=[],
        ps_json=json.dumps(
            {
                "runs": [
                    "not-a-dict",
                    {"run_id": "01MISSINGGOAL", "status": "running"},
                    {"run_id": "01NOMATCH", "goal": "Repo: /tmp/repo", "status": "running"},
                    {
                        "run_id": "01BADSTATUS",
                        "goal": "Work-item: bd-ib-done\nRepo: /tmp/repo",
                        "status": {"phase": "running"},
                    },
                    {
                        "run_id": "01NUMSTATUS",
                        "goal": "Work-item: bd-ib-done\nRepo: /tmp/repo",
                        "status": 7,
                    },
                    {
                        "run_id": "",
                        "goal": "Work-item: bd-ib-done\nRepo: /tmp/repo",
                        "status": "running",
                    },
                    {
                        "goal": "Work-item: bd-ib-done\nRepo: /tmp/repo",
                        "status": "running",
                    },
                    {
                        "run_id": "01SUCCEEDED",
                        "goal": "Work-item: bd-ib-done\nRepo: /tmp/repo",
                        "status": "succeeded",
                    },
                    {
                        "run_id": "01UNKNOWN",
                        "goal": "Work-item: bd-ib-unknown\nRepo: /tmp/repo",
                        "status": "running",
                    },
                    {
                        "run_id": "01ACTIVE",
                        "goal": "Work-item: bd-ib-active\nRepo: /tmp/repo",
                        "status": "running",
                    },
                ]
            }
        ),
    )

    summary = _dispatcher_stale_run_sweep.reap_stale_fabro_runs(
        repo=tmp_path,
        runner=runner,
        items=[_item(id="bd-ib-active", status="active"), _item(id="bd-ib-done", status="done")],
        fabro_bin="fabro",
        fabro_factory_server="http://127.0.0.1:32276",
    )

    assert summary.reaped == ()
    assert [call[1] for call in runner.calls] == ["ps"]
    assert runner.calls[0][-2:] == ["--server", "http://127.0.0.1:32276"]


def test_stale_run_sweep_handles_failed_or_unparseable_ps(tmp_path: Path) -> None:
    failed = _dispatcher_stale_run_sweep.reap_stale_fabro_runs(
        repo=tmp_path,
        runner=_Runner(calls=[], ps_exit_code=7),
        items=[],
        fabro_bin="fabro",
        fabro_factory_server=None,
    )
    malformed = _dispatcher_stale_run_sweep.reap_stale_fabro_runs(
        repo=tmp_path,
        runner=_Runner(calls=[], ps_json="not-json"),
        items=[],
        fabro_bin="fabro",
        fabro_factory_server=None,
    )
    wrong_envelope = _dispatcher_stale_run_sweep.reap_stale_fabro_runs(
        repo=tmp_path,
        runner=_Runner(calls=[], ps_json='{"runs": "nope"}'),
        items=[],
        fabro_bin="fabro",
        fabro_factory_server=None,
    )
    scalar = _dispatcher_stale_run_sweep.reap_stale_fabro_runs(
        repo=tmp_path,
        runner=_Runner(calls=[], ps_json="42"),
        items=[],
        fabro_bin="fabro",
        fabro_factory_server=None,
    )

    assert failed.probe_exit_code == 7
    assert malformed.reaped == ()
    assert wrong_envelope.reaped == ()
    assert scalar.reaped == ()


def test_stale_run_sweep_cli_uses_default_repo_and_fabro_bin(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: dict[str, object] = {}

    def _load_items(*, repo: Path) -> list[WorkItem]:
        calls["repo"] = repo
        return []

    def _resolve_factory(*, cwd: Path, factory: str | None = None) -> _Factory:
        calls["factory"] = (cwd, factory)
        return _Factory(name="default", server=None, dev_token=None)

    def _resolve_fabro_bin(*, cwd: Path) -> str:
        calls["fabro_bin_cwd"] = cwd
        return "resolved-fabro"

    def _reap(**kwargs: object) -> _dispatcher_stale_run_sweep.StaleFabroRunSweepSummary:
        calls["reap"] = kwargs
        return _dispatcher_stale_run_sweep.StaleFabroRunSweepSummary(
            probe_exit_code=0,
            reaped=(),
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_dispatcher_stale_run_sweep, "load_items", _load_items)
    monkeypatch.setattr(_dispatcher_stale_run_sweep, "resolve_fabro_factory", _resolve_factory)
    monkeypatch.setattr(_dispatcher_stale_run_sweep, "resolve_fabro_bin", _resolve_fabro_bin)
    monkeypatch.setattr(_dispatcher_stale_run_sweep, "reap_stale_fabro_runs", _reap)

    assert main(argv=["stale-run-sweep"]) == 0

    assert capsys.readouterr().out == "(no stale fabro runs reaped)\n"
    assert calls["repo"] == tmp_path
    assert calls["factory"] == (tmp_path, None)
    assert calls["fabro_bin_cwd"] == tmp_path
    reap_kwargs = calls["reap"]
    assert isinstance(reap_kwargs, dict)
    assert reap_kwargs["fabro_bin"] == "resolved-fabro"


def test_stale_run_sweep_cli_reports_probe_and_rm_failures(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    summaries = [
        _dispatcher_stale_run_sweep.StaleFabroRunSweepSummary(probe_exit_code=9, reaped=()),
        _dispatcher_stale_run_sweep.StaleFabroRunSweepSummary(
            probe_exit_code=0,
            reaped=(
                _dispatcher_stale_run_sweep.ReapedStaleFabroRun(
                    work_item_id="bd-ib-closed",
                    run_id="01CLOSED",
                    run_status="running",
                    item_status="done",
                    rm_exit_code=4,
                ),
            ),
        ),
    ]

    monkeypatch.setattr(_dispatcher_stale_run_sweep, "load_items", lambda **_: [])
    monkeypatch.setattr(
        _dispatcher_stale_run_sweep,
        "resolve_fabro_factory",
        lambda **_: _Factory(name="default", server=None, dev_token=None),
    )
    monkeypatch.setattr(
        _dispatcher_stale_run_sweep,
        "reap_stale_fabro_runs",
        lambda **_: summaries.pop(0),
    )

    assert main(argv=["stale-run-sweep", "--repo", str(tmp_path), "--fabro-bin", "fabro"]) == 1
    assert capsys.readouterr().out == "fabro ps failed with exit 9\n"
    assert main(argv=["stale-run-sweep", "--repo", str(tmp_path), "--fabro-bin", "fabro"]) == 1
    assert capsys.readouterr().out == (
        "REAPED  bd-ib-closed  01CLOSED  run=running item=done rm_exit=4\n"
    )


def test_red_test_fake_runner_rejects_unexpected_verbs(tmp_path: Path) -> None:
    red_test = runpy.run_path(
        "tests/livespec_orchestrator_beads_fabro/commands/test_dispatcher_stale_run_sweep.py"
    )
    runner_class = red_test["_RecordingRunner"]
    runner = runner_class(ps_json="[]")

    result = runner.run(argv=["fabro", "bogus"], cwd=tmp_path, timeout_seconds=1.0)

    assert result.exit_code == 1
    assert "unexpected argv" in result.stderr


def test_cli_test_runner_covers_rm_and_unexpected_verbs(tmp_path: Path) -> None:
    runner = _Runner(calls=[], rm_exit_code=4)

    rm = runner.run(argv=["fabro", "rm"], cwd=tmp_path, timeout_seconds=1.0)
    unexpected = runner.run(argv=["fabro", "bogus"], cwd=tmp_path, timeout_seconds=1.0)

    assert rm.exit_code == 4
    assert unexpected.exit_code == 1
    assert runner.calls == [["fabro", "rm"], ["fabro", "bogus"]]


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
        captured_at="2026-08-16T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )
