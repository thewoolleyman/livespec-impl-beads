"""Read-only-cache guards for the dark-factory Dispatcher (Slice 3).

One cache-hostile behavior is hardened into a CLEAN no-op so the
dispatcher runs correctly from a read-only, flattened plugin cache (the
adopter path), per the self-contained plugin dispatch contract in
SPECIFICATION/contracts.md:

(a) The fleet-manifest sibling-clone projection renders an EMPTY sibling
    set when no fleet manifest is fetchable (no `gh`, no manifest, a
    non-fleet adopter), so the dispatch PROCEEDS rather than refusing it.

This file also preserves the regression shape for the retired self-update
writable-checkout guard: a flattened cache must not skip the canary merely
because it has no `.git`.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_credentials import (
    resolve_sibling_clones,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import SiblingClones
from livespec_orchestrator_beads_fabro.commands._dispatcher_self_update import (
    canary_self_check_argv,
    released_payload_version,
    running_release_version,
    self_update_after_release,
)


@dataclass(kw_only=True)
class _RecordingJournal:
    records: list[dict[str, object]] = field(default_factory=list)

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


@dataclass(kw_only=True)
class _QueueRunner:
    seen_argv: list[list[str]] = field(default_factory=list)

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
        self.seen_argv.append(list(argv))
        return CommandResult(exit_code=0, stdout="[]", stderr="")


@dataclass(kw_only=True)
class _RecordingPoster:
    bodies: list[str] = field(default_factory=list)

    def post(self, *, url: str, body: str, title: str, timeout_seconds: float) -> bool:
        _ = (url, title, timeout_seconds)
        self.bodies.append(body)
        return True


def test_self_update_canaries_on_a_read_only_plugin_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A flattened read-only plugin cache has no `.git`; that must not be a
    # reason to skip the release canary.
    cache_root = tmp_path / "cache"
    cache_root.mkdir()
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(cache_root))
    monkeypatch.setenv("CLAUDE_NTFY_DISPATCHER_TOPIC", "livespec-dispatcher-test")
    journal = _RecordingJournal()
    runner = _QueueRunner()
    poster = _RecordingPoster()
    candidate_bin = str(cache_root / "scripts" / "bin" / "dispatcher.py")
    self_update_after_release(
        work_item_id="livespec-impl-beads-roc",
        candidate_bin=candidate_bin,
        scratch_root=str(tmp_path / "scratch"),
        repo=tmp_path,
        journal=journal,
        runner=runner,
        poster=poster,
    )
    assert runner.seen_argv == [
        canary_self_check_argv(candidate_bin=candidate_bin, scratch_root=str(tmp_path / "scratch"))
    ]
    stages = [record["stage"] for record in journal.records]
    assert "self-update-restart-due" in stages
    assert "self-update-error" not in stages
    assert "self-update-promoted" not in stages
    assert "self-update-kept-last-known-good" not in stages
    assert len(poster.bodies) == 1


def test_released_payload_version_is_absent_for_unusable_plugin_json(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin"
    plugin.mkdir()

    (plugin / "plugin.json").write_text("not json", encoding="utf-8")
    assert released_payload_version(root=plugin) is None

    (plugin / "plugin.json").write_text("[]", encoding="utf-8")
    assert released_payload_version(root=plugin) is None


def test_running_release_version_is_absent_when_import_marker_is_absent() -> None:
    assert running_release_version(running_release=None) is None


def test_resolve_sibling_clones_is_empty_when_no_fleet_manifest_is_fetchable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No fleet manifest is fetchable (no `gh`, no manifest, a non-fleet
    # adopter): the projection renders an EMPTY sibling set rather than
    # an actionable-refusal string the dispatch aborts on.
    monkeypatch.setattr(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_sibling_clones.fetch_fleet_manifest_text",
        lambda: None,
    )
    resolved = resolve_sibling_clones(repo=tmp_path / "adopter-repo")
    assert isinstance(resolved, SiblingClones)
    assert resolved.repos == ()


def test_scripted_gh_fixture_records_invocations(scripted_gh) -> None:
    scripted_gh.script(exit_code=3, stdout="stubbed")

    result = subprocess.run(
        ["gh", "repo", "view"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 3
    assert result.stdout == "stubbed"
    assert scripted_gh.argv_lines() == ["repo view"]


def test_absent_gh_fixture_replaces_path(absent_gh: None) -> None:
    assert absent_gh is None
    assert os.environ["PATH"].endswith("empty-bin")
