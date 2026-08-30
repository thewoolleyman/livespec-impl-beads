"""Scenario 103 — A needs-human outcome terminates the run and routes the decision to the ledger.

Binds the SPECIFICATION/contracts.md rule that a factory run never awaits a human (v093):
the `implement-work-item` graph carries NO interactive human-decision node.
Every outcome the loop cannot auto-resolve routes to a `needs_human` terminal
SCRIPT node that preserves the tree on a run-scoped ref, emits the
`LIVESPEC_NEEDS_HUMAN` sentinel, and exits non-zero with no outgoing edge —
the same dead-end shape as `non_converged`. The Dispatcher maps that sentinel
onto its existing `blocked` outcome, so the item rests at
`blocked / needs-human` in the ledger while the run itself is already gone.
"""

from __future__ import annotations

import re
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands import _dispatcher_plan as plan_module
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_terminal import (
    fabro_run_terminal_outcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan
from livespec_orchestrator_beads_fabro.commands._fabro_escalation import ESCALATION_NODE_ID

_WORKFLOW_DOT = Path(".claude-plugin/.fabro/workflows/implement-work-item/workflow.fabro")
_SENTINEL = "LIVESPEC_NEEDS_HUMAN"
_FORMER_GATE_SOURCES = ("implement", "review", "disposition", "pr")


def _dot() -> str:
    assert _WORKFLOW_DOT.is_file()
    return _WORKFLOW_DOT.read_text(encoding="utf-8")


def _code_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if not line.strip().startswith("//")]


def _node_body(text: str, node: str) -> str | None:
    match = re.search(rf"^\s*{node}\s*\[(?P<body>.*?)^\s*\]", text, re.DOTALL | re.MULTILINE)
    return None if match is None else match.group("body")


def test_graph_has_no_interactive_human_decision_node() -> None:
    """No hexagon, no `escalate`, no `abandon`: nothing in the graph waits for a human."""
    text = _dot()
    lines = _code_lines(text)

    assert not any("shape=hexagon" in line for line in lines)
    assert _node_body(text, "escalate") is None
    assert _node_body(text, "abandon") is None
    assert not any(re.match(r"^escalate\s*->", line) for line in lines)


def test_needs_human_is_a_terminal_script_node_that_preserves_then_exits_non_green() -> None:
    text = _dot()
    body = _node_body(text, "needs_human")

    assert body is not None
    assert "script=" in body
    assert "shape=parallelogram" in body
    assert _SENTINEL in body
    assert "exit 1" in body
    assert "refs/heads/needs-human/" in body
    assert "FABRO_RUN_ID" in body
    assert "feat/" not in body
    assert not any(re.match(r"^needs_human\s*->", line) for line in _code_lines(text))


def test_every_former_gate_edge_targets_needs_human() -> None:
    lines = _code_lines(_dot())
    for source in _FORMER_GATE_SOURCES:
        assert any(re.match(rf"^{source}\s*->\s*needs_human\b", line) for line in lines), source
    assert 'review -> needs_human [label="unmatched review outcome"]' in lines
    assert 'disposition -> needs_human [label="unmatched disposition outcome"]' in lines


def test_escalation_node_id_follows_the_rename() -> None:
    assert ESCALATION_NODE_ID == "needs_human"


def test_needs_human_marker_is_shared_between_dot_and_dispatcher() -> None:
    marker = getattr(plan_module, "NEEDS_HUMAN_MARKER", None)
    predicate = getattr(plan_module, "is_needs_human_outcome", None)

    assert marker == _SENTINEL
    assert predicate is not None
    assert predicate(outcome=_outcome(status="failed", detail=f"stage needs_human: {_SENTINEL}: x"))
    assert not predicate(outcome=_outcome(status="failed", detail="ordinary failure"))
    assert not predicate(outcome=_outcome(status="green", detail=_SENTINEL))


def test_dispatcher_maps_the_sentinel_onto_the_blocked_outcome(tmp_path: Path) -> None:
    outcome = fabro_run_terminal_outcome(
        outcome_type=DispatchOutcome,
        plan=_plan(tmp_path=tmp_path),
        run_id="01NEEDSHUMAN",
        inspect=None,
        exit_code=1,
        stderr=(
            f"{_SENTINEL}: loop cannot auto-resolve; work preserved by reference; "
            "decision routed to the ledger\n"
        ),
    )

    assert outcome is not None
    assert outcome.status == "blocked"
    assert outcome.stage == "fabro-run"
    assert outcome.fabro_run_id == "01NEEDSHUMAN"
    assert "refs/heads/needs-human/01NEEDSHUMAN" in outcome.detail
    assert "resolve-blocked:bd-ib-8nnu:ready" in outcome.detail
    assert "fabro attach" not in outcome.detail


def _outcome(*, status: str, detail: str) -> DispatchOutcome:
    return DispatchOutcome(
        work_item_id="bd-ib-8nnu",
        status=status,
        stage="fabro-run",
        pr_number=None,
        merge_sha=None,
        detail=detail,
    )


def _plan(*, tmp_path: Path) -> DispatchPlan:
    return DispatchPlan(
        repo=tmp_path,
        work_item_id="bd-ib-8nnu",
        branch="feat/bd-ib-8nnu",
        workflow_toml=tmp_path / "workflow.toml",
        goal_file=tmp_path / "goal.txt",
        fabro_bin="fabro",
        fabro_factory_name="hp",
        fabro_factory_server="https://hp.example:32276",
        fabro_factory_dev_token=None,
        janitor=("just", "check"),
        janitor_checkout=tmp_path / ".janitor",
        janitor_core_checkout=tmp_path / ".janitor" / ".livespec-core",
        janitor_core_repo_url="https://github.com/thewoolleyman/livespec.git",
        janitor_core_ref="master",
        review_fix_visit_cap=3,
        merge_on_review_cap_outcome="succeeded",
    )
