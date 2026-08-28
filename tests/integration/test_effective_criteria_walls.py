"""Integration-tier acceptance for the effective-acceptance-criteria walls.

Binds two `SPECIFICATION/scenarios.md` headings through the real
`dispatcher.main(argv=[...])` and `drive.run_action` surfaces and the real
store/client seam against the in-memory `FakeBeadsClient`, with `run_dispatch`
replaced by a recording stand-in so no fabro sandbox launches:

- "Scenario 69 — Zero-criteria AI-dispositive work is walled before any spend":
  the pre-dispatch wall refuses with exit 5 on BOTH dispatch paths, the approve
  valve refuses and leaves the item where it stood, and criteria that reach the
  primitive only through a description `Exit criteria` section clear both walls.
- "Scenario 71 — One effective-criteria authority for every gate": one criteria
  text is followed through all four gates — the capture front-end's parse, the
  entry-to-`ready` wall, the pre-dispatch wall, and the post-merge acceptance
  pass — and the assertions each resolves are compared for equality.

The recording stand-in is what makes "before any spend" checkable rather than
asserted: a refusal that still created a run would show up as a recorded launch,
and the exit code alone could not tell the two apart. The exit code is compared
against the precondition code as well as the expected one, because the whole
point of a dedicated code is that it is DISTINCT — asserting only `!= 0` would
pass for either.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest
from livespec_orchestrator_beads_fabro._beads_client import reset_fake_singleton
from livespec_orchestrator_beads_fabro.commands import _dispatcher_completion, _dispatcher_loop
from livespec_orchestrator_beads_fabro.commands._dispatcher_acceptance_ai import (
    AcceptancePassResult,
    run_acceptance_pass,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    CommandResult,
    DispatchOutcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan
from livespec_orchestrator_beads_fabro.commands.dispatcher import main
from livespec_orchestrator_beads_fabro.commands.drive import run_action
from livespec_orchestrator_beads_fabro.commands.groom import (
    CandidateSlice,
    file_approved_slices,
)
from livespec_orchestrator_beads_fabro.store import (
    append_work_item,
    materialize_work_items,
    read_work_items,
)
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

_EXIT_PRECONDITION_ERROR = 3
_EXIT_UNGRADEABLE_CRITERIA = 5
_LOCAL_REPO = "livespec-orchestrator-beads-fabro"

# The one criteria text this file follows across every gate. It lives ONLY in a
# description section, so a gate that reads the criteria field alone resolves
# nothing and the comparison below cannot pass by accident.
_CRITERION = "The dispatched slice is verified green by the check suite."
_EXIT_CRITERIA_BODY = (
    "Implement the slice.\n"
    "\n"
    "## Exit criteria\n"
    "\n"
    f"{_CRITERION}\n"
    "\n"
    "## Notes\n"
    "\n"
    "Anything appended below this heading is outside the criteria section.\n"
)

# A merged diff carrying the criterion's own vocabulary, so the criteria leg
# grades cleanly and the acceptance pass reaches a judged verdict.
_READABLE_DIFF = "diff --git a/impl.py b/impl.py\n+the dispatched slice is verified green\n"

_FLEET_MANIFEST_TEXT = (
    "// .livespec-fleet-manifest.jsonc — canned test copy\n"
    "{\n"
    '  "owner": "thewoolleyman",\n'
    '  "members": [\n'
    '    { "repo": "livespec", "class": "core" },\n'
    '    { "repo": "repo", "class": "impl-plugin" }\n'
    "  ]\n"
    "}\n"
)

_COMMITTED_WORKFLOW_TOML = (
    '[workflow]\ngraph = "graph.toml"\n\n[run.environment]\nid = "fabro-sandbox"\n'
)

_MINIMAL_GRAPH = (
    "digraph ImplementWorkItem {\n"
    "    graph [\n"
    '        stall_timeout="7200s"\n'
    "    ]\n"
    "\n"
    "    implement [\n"
    '        timeout="1800s"\n'
    "    ]\n"
    "}\n"
)


@dataclass(kw_only=True)
class _StubRunner:
    """The acceptance pass's command seam, standing in for `gh` / `git`."""

    stdout: str

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
    ) -> CommandResult:
        _ = (argv, cwd, timeout_seconds, env)
        return CommandResult(exit_code=0, stdout=self.stdout, stderr="")


@pytest.fixture(autouse=True)
def _hermetic_dispatch_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> object:
    """Hermetic dispatch environment + a fresh in-memory tenant per case."""
    scratch = tmp_path_factory.mktemp("fabro-effective-criteria")
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(scratch))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "test-oauth-token")
    monkeypatch.setattr(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_loop.selfup.github_token_supplier",
        lambda: (lambda: "test-github-token"),
    )
    monkeypatch.setenv("LIVESPEC_BEADS_FAKE", "1")
    for _ntfy_env in ("CLAUDE_NTFY_DISPATCHER_TOPIC", "CLAUDE_NTFY_TOPIC", "CLAUDE_NTFY_SERVER"):
        monkeypatch.delenv(_ntfy_env, raising=False)
    monkeypatch.setattr(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_sibling_clones.fetch_fleet_manifest_text",
        lambda: _FLEET_MANIFEST_TEXT,
    )
    reset_fake_singleton()
    yield
    reset_fake_singleton()


def _config(*, repo_root: Path | None = None) -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd-ib",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
        repo_root=repo_root,
    )


def _item(**overrides: object) -> WorkItem:
    base = WorkItem(
        id="bd-ib-crit",
        type="task",
        status="ready",
        title="A dispatched slice",
        description="Implement the slice.",
        origin="freeform",
        gap_id=None,
        rank="a2",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-24T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy="ai-only",
    )
    return replace(base, **overrides)


def _repo_with_workflow(*, tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib"},'
        ' "dispatcher": {"wip_cap": 3, "acceptance_mode": "ai-only"}}}',
        encoding="utf-8",
    )
    workflow = tmp_path / "workflow.toml"
    _ = workflow.write_text(_COMMITTED_WORKFLOW_TOML, encoding="utf-8")
    _ = (workflow.parent / "graph.toml").write_text(_MINIMAL_GRAPH, encoding="utf-8")
    return repo, workflow


def _stored() -> dict[str, WorkItem]:
    return materialize_work_items(records=read_work_items(path=_config()))


def _recording(*, calls: list[str]) -> Callable[..., DispatchOutcome]:
    """A `run_dispatch` stand-in recording every launch, in launch order."""

    def _run_dispatch(**kwargs: object) -> DispatchOutcome:
        plan = kwargs["plan"]
        assert isinstance(plan, DispatchPlan)
        calls.append(plan.work_item_id)
        return DispatchOutcome(
            work_item_id=plan.work_item_id,
            status="green",
            stage="done",
            pr_number=11,
            merge_sha="feed01",
            detail="merged",
        )

    return _run_dispatch


def _real_acceptance_pass() -> Callable[..., AcceptancePassResult]:
    """The REAL acceptance pass, with only its command seam stood in."""
    runner = _StubRunner(stdout=_READABLE_DIFF)

    def _call(*, repo: Path, item: WorkItem, outcome: DispatchOutcome) -> AcceptancePassResult:
        return run_acceptance_pass(repo=repo, item=item, outcome=outcome, runner=runner)

    return _call


def _journal_records(*, repo: Path) -> list[dict[str, Any]]:
    text = (repo / "tmp" / "fabro-dispatch-journal.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line]


def test_the_pre_dispatch_wall_refuses_a_targeted_dispatch_with_exit_five(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, workflow = _repo_with_workflow(tmp_path=tmp_path)
    item = _item(acceptance_criteria=None)
    append_work_item(path=_config(), item=item)
    calls: list[str] = []
    monkeypatch.setattr(_dispatcher_loop, "run_dispatch", _recording(calls=calls))

    exit_code = main(
        argv=["dispatch", "--repo", str(repo), "--item", item.id, "--workflow", str(workflow)]
    )

    assert exit_code == _EXIT_UNGRADEABLE_CRITERIA
    assert exit_code != _EXIT_PRECONDITION_ERROR
    # No factory run was created, so no token was spent — the whole point of
    # walling this before the factory rather than failing it after the merge.
    assert calls == []
    stderr = capsys.readouterr().err
    assert item.id in stderr
    assert "empty or ungradeable" in stderr
    assert _stored()[item.id].status == "ready"


def test_the_drain_refuses_the_same_candidate_with_exit_five(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, workflow = _repo_with_workflow(tmp_path=tmp_path)
    item = _item(acceptance_criteria=None)
    append_work_item(path=_config(), item=item)
    calls: list[str] = []
    monkeypatch.setattr(_dispatcher_loop, "run_dispatch", _recording(calls=calls))

    exit_code = main(
        argv=[
            "loop",
            "--repo",
            str(repo),
            "--budget",
            "3",
            "--workflow",
            str(workflow),
            "--no-close-on-merge",
        ]
    )

    # The drain reaches the same wall as `dispatch --item`, so an unverifiable
    # item cannot slip through by being picked automatically instead of by hand.
    assert (exit_code, calls) == (_EXIT_UNGRADEABLE_CRITERIA, [])


def test_the_approve_valve_refuses_and_the_item_rests_at_pending_approval(
    tmp_path: Path,
) -> None:
    repo, _ = _repo_with_workflow(tmp_path=tmp_path)
    item = _item(
        status="pending-approval",
        admission_policy="manual",
        acceptance_criteria=None,
    )
    append_work_item(path=_config(), item=item)

    result = run_action(repo=repo, action_id=f"approve:{item.id}")

    assert result["status"] == "failed"
    assert result["domain_error"] == "ungradeable-acceptance-criteria"
    assert "empty or ungradeable" in result["summary"]
    # Entry to `ready` is withheld and NOTHING is written: the item rests
    # exactly where the operator left it.
    assert _stored()[item.id].status == "pending-approval"


def test_criteria_reaching_the_primitive_only_through_the_description_clear_the_wall(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, workflow = _repo_with_workflow(tmp_path=tmp_path)
    # No criteria FIELD at all: the assertions exist solely in the description's
    # `Exit criteria` section, which is the fallback leg of the resolution order.
    item = _item(acceptance_criteria=None, description=_EXIT_CRITERIA_BODY)
    append_work_item(path=_config(), item=item)
    calls: list[str] = []
    monkeypatch.setattr(_dispatcher_loop, "run_dispatch", _recording(calls=calls))
    monkeypatch.setattr(
        _dispatcher_completion, "run_acceptance_pass", _real_acceptance_pass(), raising=False
    )

    exit_code = main(
        argv=["dispatch", "--repo", str(repo), "--item", item.id, "--workflow", str(workflow)]
    )

    assert (exit_code, calls) == (0, [item.id])


def test_all_four_gates_resolve_the_identical_effective_criteria_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, workflow = _repo_with_workflow(tmp_path=tmp_path)
    item = _item(
        id="bd-ib-fourgates",
        status="pending-approval",
        admission_policy="manual",
        acceptance_criteria=None,
        description=_EXIT_CRITERIA_BODY,
    )
    append_work_item(path=_config(), item=item)
    calls: list[str] = []
    monkeypatch.setattr(_dispatcher_loop, "run_dispatch", _recording(calls=calls))
    monkeypatch.setattr(
        _dispatcher_completion, "run_acceptance_pass", _real_acceptance_pass(), raising=False
    )

    # GATE 1 — the capture front-end's parse, on a slice filed through groom
    # carrying the same criteria section in its description.
    append_work_item(path=_config(), item=_item(id="bd-ib-groomtarget", status="backlog"))
    groomed = file_approved_slices(
        # Groom's intake routing resolves the repo's admission policy, so this
        # leg needs the descriptor's `repo_root`; the tenant is the same one.
        path=_config(repo_root=repo),
        slices=[
            CandidateSlice(
                title="A groomed slice",
                description=_EXIT_CRITERIA_BODY,
                acceptance="folded into the description by groom",
                autonomy_tier="factory",
                repo_target=_LOCAL_REPO,
            )
        ],
        regroom_item_id="bd-ib-groomtarget",
        local_repo=_LOCAL_REPO,
    )
    [parse] = groomed.criteria_parses
    capture_assertions = parse.criteria.assertions

    # GATE 2 — the entry-to-`ready` wall admits it.
    approved = run_action(repo=repo, action_id=f"approve:{item.id}")

    # GATES 3 and 4 — the pre-dispatch wall lets it through and the post-merge
    # acceptance pass grades it.
    exit_code = main(
        argv=["dispatch", "--repo", str(repo), "--item", item.id, "--workflow", str(workflow)]
    )

    assert (approved["status"], _stored()[item.id].status) == ("green", "done")
    assert (exit_code, calls) == (0, [item.id])
    ai_pass = next(
        record for record in _journal_records(repo=repo) if record["stage"] == "acceptance-ai-pass"
    )
    acceptance_assertions = tuple(check["text"] for check in ai_pass["criteria"]["checks"])
    # The capture-side parse and the acceptance-side judgement resolved the SAME
    # assertions from the SAME resolution order, and the two walls between them
    # admitted the item rather than reporting it as absent. One authority.
    assert capture_assertions == (_CRITERION,)
    assert acceptance_assertions == capture_assertions
    assert parse.criteria.source == "description-exit-criteria"
