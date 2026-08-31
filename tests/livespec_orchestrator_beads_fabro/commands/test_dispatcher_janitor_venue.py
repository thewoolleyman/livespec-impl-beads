"""The post-merge / reconcile janitor VENUE: the merged default-branch tip.

The venue is the target repository's default-branch tip that CONTAINS the
item's merge -- never the item's historical merge sha. Pinning it to the merge
sha deadlocks every item that merged before a janitor-environment fix landed,
because each reconcile re-provisions a checkout from before the fix existed.

The branch itself is READ OFF THE PLAN'S RESOLVED INTEGRATION CONTRACT, whose
`default_branch` field carries what the ratified two-route resolution answered
at plan build, so these cases declare it on the plan rather than queueing a
probe result for the venue to read.

Every behavioural case is driven through `post_merge`, the published entry
point both the post-merge flow and the reconcile-merged valve call, so the
assertions are about what the janitor actually provisions rather than about a
helper's return value.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field, replace
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands import _dispatcher_engine_janitor
from livespec_orchestrator_beads_fabro.commands._dispatcher_core_provisioning_view import (
    FLEET_JANITOR_CORE_REPO_URL,
    JANITOR_CORE_PINNED_KEY,
    JANITOR_CORE_REPO_KEY,
    UNRESOLVED_JANITOR_CORE,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_janitor import post_merge
from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_venue import (
    fleet_toolchain_is_the_host_janitor_premise,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    DispatchPlan,
    PrView,
    build_plan,
)

_MERGE_SHA = "16fe3ac"


# The venue cases are about WHERE the janitor runs, so every one of them
# declares a janitor-core ref: an undeclared pin degrades before the venue is
# ever resolved.
_DECLARED_CONFIG = '{"livespec-orchestrator-beads-fabro": {"compat": {"pinned": "master"}}}'

# The same repository with BOTH host-janitor points declared, which is what makes
# the fleet toolchain not a premise of its venue.
_ADOPTER_CONFIG = (
    '{"livespec-orchestrator-beads-fabro": {"compat": {"pinned": "master"}, "dispatcher": '
    '{"janitor": {"check_suite": ["make", "verify"]}, '
    '"janitor_bootstrap": {"recipe": ["make", "install-hooks"]}}}}'
)


def _plan(
    *, repo: Path, default_branch: str | None = "master", config_text: str = _DECLARED_CONFIG
) -> DispatchPlan:
    return build_plan(
        repo=repo,
        work_item_id="x-1",
        workflow_toml=repo / "wf.toml",
        goal_file=repo / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=repo / "janitor-co",
        config_text=config_text,
        default_branch=default_branch,
    )


@dataclass(kw_only=True)
class Runner:
    queue: list[CommandResult]
    calls: list[tuple[list[str], Path]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        _ = env
        assert timeout_seconds > 0
        self.calls.append((argv, cwd))
        return self.queue.pop(0)


@dataclass(kw_only=True)
class Journal:
    records: list[dict[str, object]] = field(default_factory=list)

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


def _ok() -> CommandResult:
    return CommandResult(exit_code=0, stdout="", stderr="")


def _err(*, stderr: str = "") -> CommandResult:
    return CommandResult(exit_code=1, stdout="", stderr=stderr)


def _merged(*, merge_sha: str | None = _MERGE_SHA) -> PrView:
    return PrView(
        number=7,
        state="MERGED",
        auto_merge_armed=True,
        merge_state_status="CLEAN",
        merge_sha=merge_sha,
        terminal_required_check_failures=(),
    )


def test_janitor_venue_module_owns_provisioning_and_old_privates_are_gone() -> None:
    module_path = (
        Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
        / "_dispatcher_janitor_venue.py"
    )
    venue_public_names = {
        "UNRESOLVED_VENUE",
        "JanitorVenue",
        "fleet_toolchain_is_the_host_janitor_premise",
        "provision_janitor_checkout",
        "resolve_janitor_venue",
    }

    assert module_path.is_file()
    venue = importlib.import_module(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_venue"
    )
    assert set(venue.__all__) == venue_public_names
    for name in venue_public_names:
        assert hasattr(venue, name)
    # The provisioning moved out of the flow module wholesale, and the shaper
    # both halves need is public on the degraded module rather than duplicated.
    assert not hasattr(_dispatcher_engine_janitor, "_provision_janitor_checkout")
    assert not hasattr(_dispatcher_engine_janitor, "_degraded_step")


def test_post_merge_provisions_the_venue_at_the_merged_default_branch_tip(tmp_path: Path) -> None:
    """The deadlock-cleared case: the venue is the tip, so a later fix is present.

    An item merged before a janitor-environment fix landed is provisioned at the
    CURRENT default-branch tip, which carries both its merge and the later fix --
    where a venue pinned to the item's merge sha could only ever re-fail.
    """
    plan = _plan(repo=tmp_path, default_branch="main")
    runner = Runner(queue=[_ok(), *[_ok() for _ in range(8)]])
    journal = Journal()

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=plan,
        runner=runner,
        journal=journal,
        merged=_merged(),
    )

    assert (outcome.status, outcome.stage) == ("green", "done")
    argvs = [argv for argv, _ in runner.calls]
    assert [
        "git",
        "-C",
        str(tmp_path),
        "merge-base",
        "--is-ancestor",
        _MERGE_SHA,
        "origin/main",
    ] in argvs
    add = next(argv for argv in argvs if argv[3:5] == ["worktree", "add"])
    assert add[-1] == "origin/main"
    # The merge sha is what the venue is PROVEN AGAINST, never what it is pinned
    # to: it appears in the containment probe and nowhere else.
    assert [argv for argv in argvs if _MERGE_SHA in argv] == [
        ["git", "-C", str(tmp_path), "merge-base", "--is-ancestor", _MERGE_SHA, "origin/main"]
    ]


def test_post_merge_emits_no_trust_step_when_the_venue_runs_declared_commands(
    tmp_path: Path,
) -> None:
    """A repository declaring BOTH host-janitor points never gets this fleet's trust step.

    The trust command is a premise of the fleet-default check-suite and bootstrap
    recipe, not something every governed repository owes. Where both resolved
    `Declared` the venue runs the repository's own commands, so imposing a tool it
    does not carry would fail the step and degrade a post-merge outcome for a
    premise nobody declared.

    The member case above is the positive control for this absence: it runs the
    same code path, resolves both points to `FleetDefault`, and DOES emit the
    step -- so an argv list that could never contain it is not what is being read
    here.
    """
    plan = _plan(repo=tmp_path, default_branch="main", config_text=_ADOPTER_CONFIG)
    runner = Runner(queue=[_ok(), *[_ok() for _ in range(8)]])
    journal = Journal()

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=plan,
        runner=runner,
        journal=journal,
        merged=_merged(),
    )

    assert (outcome.status, outcome.stage) == ("green", "done")
    assert fleet_toolchain_is_the_host_janitor_premise(plan=plan) is False
    assert "janitor-checkout-trust" not in [record["stage"] for record in journal.records]
    assert [argv for argv, _ in runner.calls if argv == ["mise", "trust"]] == []


def test_post_merge_degrades_when_the_resolved_tip_does_not_contain_the_merge(
    tmp_path: Path,
) -> None:
    plan = _plan(repo=tmp_path, default_branch="main")
    runner = Runner(queue=[_ok(), _err(), *[_ok() for _ in range(8)]])
    journal = Journal()

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=plan,
        runner=runner,
        journal=journal,
        merged=_merged(),
    )

    assert (outcome.status, outcome.stage) == ("green", "janitor-env-degraded")
    assert "does NOT contain" in outcome.detail
    assert (
        outcome.missing_integration_point
        == f"a origin/main tip containing the item's merge {_MERGE_SHA}"
    )
    assert outcome.remedy is not None
    assert "re-run the reconcile" in outcome.remedy
    # The venue is not a step of the closed vocabulary, so the degradation
    # carries no step id and stands up no pre-dispatch refusal.
    assert outcome.step is None
    # Nothing is provisioned against a tip that cannot prove the merge landed.
    assert [record["stage"] for record in journal.records] == ["pull-primary"]


def test_post_merge_degrades_when_no_default_branch_can_be_resolved(tmp_path: Path) -> None:
    """Both probe routes silent at plan build leaves the REQUIRED field unresolved."""
    plan = _plan(repo=tmp_path, default_branch=None)
    runner = Runner(queue=[_ok(), *[_ok() for _ in range(8)]])
    journal = Journal()

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=plan,
        runner=runner,
        journal=journal,
        merged=_merged(),
    )

    assert (outcome.status, outcome.stage) == ("green", "janitor-env-degraded")
    assert (
        outcome.missing_integration_point == "a resolvable default branch for the target repository"
    )
    assert outcome.remedy is not None
    assert "git remote set-head origin --auto" in outcome.remedy
    assert [record["stage"] for record in journal.records] == ["pull-primary"]


def test_post_merge_venue_skips_the_containment_probe_when_no_merge_sha_is_known(
    tmp_path: Path,
) -> None:
    """No merge sha is nothing to confirm, not a degradation."""
    plan = _plan(repo=tmp_path, default_branch="master")
    runner = Runner(queue=[_ok(), *[_ok() for _ in range(8)]])
    journal = Journal()

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=plan,
        runner=runner,
        journal=journal,
        merged=_merged(merge_sha=None),
    )

    assert (outcome.status, outcome.stage) == ("green", "done")
    argvs = [argv for argv, _ in runner.calls]
    # `origin/master` here is RESOLVED, not a literal fallback: the contract
    # carries a declared branch, and it is the absence of a merge sha -- not of a
    # default branch -- that leaves the containment probe unmade.
    assert plan.integration.contract.default_branch == "master"
    assert not [argv for argv in argvs if "merge-base" in argv]
    add = next(argv for argv in argvs if argv[3:5] == ["worktree", "add"])
    assert add[-1] == "origin/master"


def test_post_merge_degrades_naming_the_undeclared_janitor_core_declaration(
    tmp_path: Path,
) -> None:
    """An unresolved janitor-core pin degrades BEFORE anything is provisioned for it.

    The plan carries the sentinel rather than a moving `master`, and the
    degradation names the committed key the operator has to write -- where the
    clone's own stderr would name a branch the repository never declared.
    """
    plan = replace(_plan(repo=tmp_path), janitor_core_ref=UNRESOLVED_JANITOR_CORE)
    runner = Runner(queue=[_ok(), *[_ok() for _ in range(8)]])
    journal = Journal()

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=plan,
        runner=runner,
        journal=journal,
        merged=_merged(),
    )

    assert (outcome.status, outcome.stage) == ("green", "janitor-env-degraded")
    assert JANITOR_CORE_PINNED_KEY in outcome.detail
    assert (
        outcome.missing_integration_point
        == "a declared livespec-core ref for the target repository"
    )
    assert outcome.remedy is not None
    assert JANITOR_CORE_REPO_KEY.rsplit(".", maxsplit=1)[-1] in outcome.remedy
    # Janitor-core provisioning is not a step of the closed vocabulary.
    assert outcome.step is None
    # Nothing is provisioned, and the venue is never even resolved.
    assert [record["stage"] for record in journal.records] == ["pull-primary"]


def test_post_merge_degrades_naming_an_unusable_core_repo_declaration(tmp_path: Path) -> None:
    """A present-but-unusable `core_repo` refuses instead of sliding onto the fleet default."""
    plan = replace(_plan(repo=tmp_path), janitor_core_repo_url=UNRESOLVED_JANITOR_CORE)
    runner = Runner(queue=[_ok(), *[_ok() for _ in range(8)]])
    journal = Journal()

    outcome = post_merge(
        outcome_type=DispatchOutcome,
        plan=plan,
        runner=runner,
        journal=journal,
        merged=_merged(),
    )

    assert (outcome.status, outcome.stage) == ("green", "janitor-env-degraded")
    assert JANITOR_CORE_REPO_KEY in outcome.detail
    assert FLEET_JANITOR_CORE_REPO_URL not in outcome.detail
