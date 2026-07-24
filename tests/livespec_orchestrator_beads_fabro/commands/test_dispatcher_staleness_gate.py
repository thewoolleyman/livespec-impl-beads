"""Tests for the dispatcher's release-based plugin staleness gate."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult

_MODULE_PATH = Path(
    ".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/"
    "_dispatcher_staleness_gate.py"
)
_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._dispatcher_staleness_gate"
_RELEASE_SHA = "9532efb793bc1d2c3a4b5c6d7e8f901234567890"
_MASTER_SHA = "8eb81fae1234567890abcdefabcdefabcdefabcd"


@dataclass(kw_only=True)
class _Runner:
    results: dict[tuple[str, ...], CommandResult]
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env)
        key = tuple(argv)
        self.calls.append(key)
        return self.results.get(key, CommandResult(exit_code=1, stdout="", stderr="missing"))


def _module() -> ModuleType:
    assert _MODULE_PATH.is_file()
    return importlib.import_module(_MODULE_NAME)


def _ls_remote(*, ref: str, sha: str) -> CommandResult:
    return CommandResult(exit_code=0, stdout=f"{sha}\t{ref}\n", stderr="")


def test_read_only_cache_build_predating_latest_release_refuses_with_performable_remedy(
    tmp_path: Path,
) -> None:
    module = _module()
    cache_root = tmp_path / "b6e4012cafed"
    cache_root.mkdir()
    runner = _Runner(
        results={
            module.latest_release_ref_argv(): _ls_remote(
                ref="refs/heads/release",
                sha=_RELEASE_SHA,
            ),
            module.master_ref_argv(): _ls_remote(ref="refs/heads/master", sha=_RELEASE_SHA),
        }
    )

    decision = module.dispatcher_staleness_decision(plugin_root=cache_root, runner=runner)

    assert decision.refusal is not None
    assert "b6e4012cafed" in decision.refusal.detail
    assert _RELEASE_SHA[:12] in decision.refusal.detail
    assert (
        "claude plugin update "
        "livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro"
        in decision.refusal.detail
    )
    assert decision.warnings == ()


def test_current_release_build_proceeds_when_master_is_ahead_and_warns_with_commit(
    tmp_path: Path,
) -> None:
    module = _module()
    cache_root = tmp_path / _RELEASE_SHA[:12]
    cache_root.mkdir()
    runner = _Runner(
        results={
            module.latest_release_ref_argv(): _ls_remote(
                ref="refs/heads/release",
                sha=_RELEASE_SHA,
            ),
            module.master_ref_argv(): _ls_remote(ref="refs/heads/master", sha=_MASTER_SHA),
            module.unreleased_dispatcher_commits_argv(
                release_sha=_RELEASE_SHA,
                master_sha=_MASTER_SHA,
            ): CommandResult(
                exit_code=0,
                stdout="8eb81fa chore: refactor dispatcher admission\n",
                stderr="",
            ),
        }
    )

    decision = module.dispatcher_staleness_decision(plugin_root=cache_root, runner=runner)

    assert decision.refusal is None
    assert len(decision.warnings) == 1
    warning = decision.warnings[0].detail
    assert "8eb81fa chore: refactor dispatcher admission" in warning
    assert "a release must be cut before this code takes effect" in warning


def test_current_release_build_with_no_newer_release_does_not_fire(tmp_path: Path) -> None:
    module = _module()
    cache_root = tmp_path / _RELEASE_SHA[:12]
    cache_root.mkdir()
    runner = _Runner(
        results={
            module.latest_release_ref_argv(): _ls_remote(
                ref="refs/heads/release",
                sha=_RELEASE_SHA,
            ),
            module.master_ref_argv(): _ls_remote(ref="refs/heads/master", sha=_RELEASE_SHA),
        }
    )

    decision = module.dispatcher_staleness_decision(plugin_root=cache_root, runner=runner)

    assert decision.refusal is None
    assert decision.warnings == ()


def test_unobservable_latest_release_probe_warns_without_refusing(tmp_path: Path) -> None:
    module = _module()
    cache_root = tmp_path / "cache-without-ref"
    cache_root.mkdir()
    runner = _Runner(results={})

    decision = module.dispatcher_staleness_decision(plugin_root=cache_root, runner=runner)

    assert decision.refusal is None
    assert len(decision.warnings) == 1
    assert "could not inspect latest release" in decision.warnings[0].detail
