"""Declared janitor-core provisioning: the ref and repository a repo must name.

The contract under test is `SPECIFICATION/contracts.md`'s janitor-core
provisioning resolution clause: `compat.pinned` resolves the livespec-core ref
and a missing one is REFUSED rather than completed from a moving `master` tip,
while `compat.core_repo` resolves the clone repository, absent meaning the fleet
repository and present-but-unusable meaning refuse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_janitor import post_merge
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_selection import (
    janitor_core_ref,
    janitor_core_repo_url,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    FLEET_JANITOR_CORE_REPO_URL,
    JANITOR_CORE_PINNED_KEY,
    JANITOR_CORE_REPO_KEY,
    DispatchPlan,
    PrView,
    build_plan,
    janitor_core_ref_from_config,
    janitor_core_repo_url_from_config,
)

_MIRROR = "https://git.example.invalid/adopter/livespec-core.git"


@dataclass(kw_only=True)
class _Runner:
    queue: list[CommandResult] = field(default_factory=list)
    calls: list[tuple[list[str], Path]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        _ = (env, timeout_seconds)
        self.calls.append((argv, cwd))
        return self.queue.pop(0) if self.queue else CommandResult(exit_code=0, stdout="", stderr="")


@dataclass(kw_only=True)
class _Journal:
    records: list[dict[str, object]] = field(default_factory=list)

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


def _config(*, compat: str) -> str:
    return '{"livespec-orchestrator-beads-fabro": {"compat": {' + compat + "}}}"


def _plan(*, repo: Path, ref: str | None, repo_url: str | None) -> DispatchPlan:
    return build_plan(
        repo=repo,
        work_item_id="x-1",
        workflow_toml=repo / "wf.toml",
        goal_file=repo / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=repo / "janitor-co",
        janitor_core_ref=ref,
        janitor_core_repo_url=repo_url,
    )


def _merged() -> PrView:
    return PrView(
        number=11,
        state="MERGED",
        auto_merge_armed=True,
        merge_state_status="CLEAN",
        merge_sha="cafe11",
        terminal_required_check_failures=(),
    )


def test_declared_core_ref_is_honored_including_the_bootstrap_master_value() -> None:
    assert janitor_core_ref_from_config(config_text=_config(compat='"pinned": "v0.38.1"')) == (
        "v0.38.1"
    )
    # `master` is the ratified bootstrap value of the `compat` block: a value
    # the repository explicitly chose, which is exactly what distinguishes it
    # from the silent default the clause forbids.
    assert (
        janitor_core_ref_from_config(config_text=_config(compat='"pinned": "master"')) == "master"
    )
    assert janitor_core_ref_from_config(config_text=_config(compat='"pinned": "  v1  "')) == "v1"


def test_absent_or_unreadable_core_pin_resolves_no_ref_at_all() -> None:
    assert janitor_core_ref_from_config(config_text="{}") is None
    assert janitor_core_ref_from_config(config_text="not-jsonc") is None
    assert janitor_core_ref_from_config(config_text="[]") is None
    assert janitor_core_ref_from_config(config_text='{"livespec-orchestrator-beads-fabro": 7}') is (
        None
    )
    assert (
        janitor_core_ref_from_config(
            config_text='{"livespec-orchestrator-beads-fabro": {"compat": 7}}'
        )
        is None
    )
    assert janitor_core_ref_from_config(config_text=_config(compat='"pinned": ""')) is None
    assert janitor_core_ref_from_config(config_text=_config(compat='"pinned": null')) is None


def test_core_repository_resolves_from_the_declaration_and_defaults_when_absent() -> None:
    assert (
        janitor_core_repo_url_from_config(config_text=_config(compat=f'"core_repo": "{_MIRROR}"'))
        == _MIRROR
    )
    assert (
        janitor_core_repo_url_from_config(config_text=_config(compat='"pinned": "v1"'))
        == FLEET_JANITOR_CORE_REPO_URL
    )
    assert janitor_core_repo_url_from_config(config_text="{}") == FLEET_JANITOR_CORE_REPO_URL


def test_present_but_unusable_core_repository_refuses_rather_than_defaulting() -> None:
    assert (
        janitor_core_repo_url_from_config(config_text=_config(compat='"core_repo": null')) is None
    )
    assert (
        janitor_core_repo_url_from_config(config_text=_config(compat='"core_repo": "  "')) is None
    )
    assert janitor_core_repo_url_from_config(config_text=_config(compat='"core_repo": 7')) is None


def test_repo_resolution_reads_the_committed_config_and_survives_its_absence(
    tmp_path: Path,
) -> None:
    declared = tmp_path / "declared"
    declared.mkdir()
    _ = (declared / ".livespec.jsonc").write_text(
        _config(compat=f'"pinned": "v2", "core_repo": "{_MIRROR}"'), encoding="utf-8"
    )
    assert janitor_core_ref(repo=declared) == "v2"
    assert janitor_core_repo_url(repo=declared) == _MIRROR

    assert janitor_core_ref(repo=tmp_path / "missing") is None
    assert janitor_core_repo_url(repo=tmp_path / "missing") == FLEET_JANITOR_CORE_REPO_URL


def test_build_plan_carries_no_moving_ref_default_and_the_fleet_core_repository(
    tmp_path: Path,
) -> None:
    plan = build_plan(
        repo=tmp_path,
        work_item_id="x-1",
        workflow_toml=tmp_path / "wf.toml",
        goal_file=tmp_path / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=tmp_path / "janitor-co",
    )

    assert plan.janitor_core_ref is None
    assert plan.janitor_core_repo_url == FLEET_JANITOR_CORE_REPO_URL


def test_post_merge_degrades_naming_the_pin_instead_of_cloning_a_moving_tip(
    tmp_path: Path,
) -> None:
    runner = _Runner(queue=[CommandResult(exit_code=0, stdout="", stderr="")])

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=_plan(repo=tmp_path, ref=None, repo_url=FLEET_JANITOR_CORE_REPO_URL),
        runner=runner,
        journal=_Journal(),
        merged=_merged(),
    )

    assert (outcome.status, outcome.stage) == ("green", "janitor-env-degraded")
    assert JANITOR_CORE_PINNED_KEY in outcome.detail
    assert "moving" in outcome.detail
    # Only the primary pull ran: the refusal lands before any venue is
    # provisioned for a clone that must not happen.
    assert [argv[0] for argv, _ in runner.calls] == ["mise"]


def test_post_merge_degrades_naming_an_unusable_core_repository_declaration(
    tmp_path: Path,
) -> None:
    runner = _Runner(queue=[CommandResult(exit_code=0, stdout="", stderr="")])

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=_plan(repo=tmp_path, ref="v1", repo_url=None),
        runner=runner,
        journal=_Journal(),
        merged=_merged(),
    )

    assert (outcome.status, outcome.stage) == ("green", "janitor-env-degraded")
    assert JANITOR_CORE_REPO_KEY in outcome.detail
    assert len(runner.calls) == 1


def test_post_merge_clones_core_from_the_declared_repository_at_the_declared_ref(
    tmp_path: Path,
) -> None:
    runner = _Runner()

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=_plan(repo=tmp_path, ref="v2", repo_url=_MIRROR),
        runner=runner,
        journal=_Journal(),
        merged=_merged(),
    )

    assert (outcome.status, outcome.stage) == ("green", "done")
    clone = next(argv for argv, _ in runner.calls if argv[:2] == ["git", "clone"])
    assert clone[-3:] == ["v2", _MIRROR, str(tmp_path / "janitor-co" / ".livespec-core")]
