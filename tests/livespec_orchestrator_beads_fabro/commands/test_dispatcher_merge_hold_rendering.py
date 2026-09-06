"""The per-item merge hold, from the ledger label to the two seams that honor it.

The per-item merge hold `SPECIFICATION/contracts.md` ratified as v101 puts ONE
value in front of two consumers and says neither
is authoritative: the sandbox's pr stage reads it as the `merge_hold` workflow
input, and the host's own auto-merge argv reads it off the plan. A hold that
reached only one of them would silently not hold, so every case here asserts the
CHAIN rather than a value -- the label resolves onto the plan, the plan renders
the input, the record journals what was rendered, and the host arms nothing.

The chain is asserted at its ends, not through a mock: `dispatch_plan_for_item`
is driven with real raw labels, and the argv assertion is made against the whole
list, because the claim is an ABSENCE (`gh pr merge` is never spawned) and a
search for a flag cannot establish one.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from livespec_orchestrator_beads_fabro._store_merge_hold import MERGE_HOLD_LABEL_PREFIX
from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_id_journal import (
    DispatchJournalIdentity,
    append_dispatch_id_record,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    dispatch_fabro_run_inputs,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine_merge import confirm_pr
from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_argv import pr_arm_argv
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_plan import dispatch_plan_for_item
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan, build_plan
from livespec_orchestrator_beads_fabro.commands._node_timeouts import NodeTimeouts
from livespec_orchestrator_beads_fabro.types import WorkItem

_HELD_LABEL = f"{MERGE_HOLD_LABEL_PREFIX}on"
_DECLARED_CONFIG = '{"livespec-orchestrator-beads-fabro": {"compat": {"pinned": "master"}}}'


def _item() -> WorkItem:
    return WorkItem(
        id="bd-ib-held",
        type="task",
        status="active",
        title="held",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee="fabro",
        depends_on=(),
        captured_at="2026-09-06T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )


def _plan(*, repo: Path, merge_hold: bool = False) -> DispatchPlan:
    return build_plan(
        repo=repo,
        work_item_id="bd-ib-held",
        workflow_toml=repo / "wf.toml",
        goal_file=repo / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=repo / "janitor-co",
        config_text=_DECLARED_CONFIG,
        default_branch="master",
        merge_hold=merge_hold,
    )


@dataclass(kw_only=True)
class _Runner:
    queue: list[CommandResult]
    calls: list[list[str]] = field(default_factory=list)

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
        return self.queue.pop(0)


@dataclass(kw_only=True)
class _Journal:
    records: list[dict[str, object]] = field(default_factory=list)

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


def _pr_json(*, armed: bool) -> str:
    return json.dumps(
        {
            "number": 7,
            "state": "OPEN",
            "autoMergeRequest": {"enabledAt": "now"} if armed else None,
            "mergeStateStatus": "CLEAN",
            "mergeCommit": None,
            "statusCheckRollup": [],
        }
    )


def _dispatch_plan(*, repo: Path, raw_labels: tuple[str, ...]) -> DispatchPlan:
    """A plan resolved the way a real dispatch resolves one, from raw labels."""
    args = argparse.Namespace(
        fabro_bin="fabro",
        fabro_factory_target=FactoryTarget(name="default", server=None, dev_token=None),
    )
    return dispatch_plan_for_item(
        args=args,
        repo=repo,
        item=_item(),
        janitor=None,
        raw_labels=raw_labels,
        timeouts=NodeTimeouts(configured={}, stall_seconds=7200, stall_layer="workflow-default"),
        runner=_Runner(queue=[CommandResult(exit_code=1, stdout="", stderr="")] * 4),
        committed_workflow=repo / "absent-workflow.toml",
    )


def test_the_hold_label_resolves_onto_the_plan_and_its_absence_resolves_false(
    tmp_path: Path,
) -> None:
    """The effective hold is the LABEL's presence -- there is no setting behind it.

    Both directions in one case, because the interesting claim is the pairing:
    the hold has no repository-level default, so the same repository, the same
    item and the same configuration must resolve differently on the label alone.
    """
    held = _dispatch_plan(repo=tmp_path, raw_labels=(_HELD_LABEL, "review-fix-cap:2"))
    free = _dispatch_plan(repo=tmp_path, raw_labels=("review-fix-cap:2",))

    assert held.merge_hold is True
    assert free.merge_hold is False
    # The label edit moved ONLY the hold: the cap override beside it is
    # unchanged, so this is a per-field read rather than a plan-shaped one.
    assert held.review_fix_visit_cap == free.review_fix_visit_cap == 3


def test_the_hold_renders_as_a_workflow_input_on_every_dispatch(tmp_path: Path) -> None:
    """`merge_hold` rides EVERY dispatch, spelled as the run config declares it.

    Rendered unconditionally rather than intersected with the payload's declared
    names, exactly as the two cap-shaped policy inputs beside it are: it projects
    the ITEM's effective policy, not the repository's integration contract.
    """
    held = dispatch_fabro_run_inputs(plan=_plan(repo=tmp_path, merge_hold=True))
    free = dispatch_fabro_run_inputs(plan=_plan(repo=tmp_path))

    assert held[-1] == "merge_hold=true"
    assert free[-1] == "merge_hold=false"
    # It sits BESIDE the other two per-item policy inputs, which is the family
    # the ratified seam-equivalence clause names it into.
    assert free[-3:] == (
        "review_fix_visit_cap=4",
        "merge_on_review_cap_outcome=__merge_on_review_cap_disabled__",
        "merge_hold=false",
    )


def test_the_dispatch_record_journals_the_rendered_hold(tmp_path: Path) -> None:
    """The record and the run agree because both project the one resolved value.

    Journaled as what the dispatch RENDERED, never re-read from the ledger: the
    label can be set or released at any moment, so today's labels cannot answer
    "did this dispatch arm auto-merge".
    """
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    plan = _plan(repo=tmp_path, merge_hold=True)

    append_dispatch_id_record(
        journal=journal,
        work_item_id=plan.work_item_id,
        identity=DispatchJournalIdentity(dispatch_id="d-1", dispatch_factory=None),
        started_at_epoch=1.0,
        workflow_toml=tmp_path / "wf.toml",
        workflow_name="implement-work-item",
        integration=plan.integration,
        merge_hold=plan.merge_hold,
    )

    record = json.loads((tmp_path / "journal.jsonl").read_text(encoding="utf-8").strip())
    assert record["merge_hold"] is True
    assert record["stage"] == "dispatch-id"
    assert f"merge_hold={str(record['merge_hold']).lower()}" in dispatch_fabro_run_inputs(plan=plan)


def test_the_host_auto_merge_argv_arms_nothing_for_a_held_item(tmp_path: Path) -> None:
    """The SECOND seam. An empty argv is no forge write at all.

    Asserted against the whole list rather than by searching it for a flag,
    because the claim is an absence. The unheld plan beside it is the control
    that the argv builder still arms when it should -- an argv builder that
    returned nothing unconditionally would pass the held assertion alone.
    """
    assert pr_arm_argv(plan=_plan(repo=tmp_path, merge_hold=True), number=7) == []
    assert pr_arm_argv(plan=_plan(repo=tmp_path), number=7) == [
        "gh",
        "pr",
        "merge",
        "7",
        "--rebase",
        "--auto",
        "--delete-branch",
    ]


def test_the_fallback_arming_never_fires_for_a_held_pull_request(tmp_path: Path) -> None:
    """The path that would silently undo a correctly-unarmed pr stage.

    `confirm_pr` exists to arm when the graph could not, so an unarmed PR is
    exactly the shape it reaches for. The held run must therefore make no `gh pr
    merge` call and journal no arming stage; only the view it already took.
    """
    runner = _Runner(queue=[CommandResult(exit_code=0, stdout=_pr_json(armed=False), stderr="")])
    journal = _Journal()

    view = confirm_pr(plan=_plan(repo=tmp_path, merge_hold=True), runner=runner, journal=journal)

    assert view is not None
    assert view.auto_merge_armed is False
    assert runner.calls == [
        [
            "gh",
            "pr",
            "view",
            "feat/bd-ib-held",
            "--json",
            "number,state,autoMergeRequest,mergeStateStatus,mergeCommit,statusCheckRollup",
        ]
    ]
    assert [record["stage"] for record in journal.records] == ["pr-view"]
