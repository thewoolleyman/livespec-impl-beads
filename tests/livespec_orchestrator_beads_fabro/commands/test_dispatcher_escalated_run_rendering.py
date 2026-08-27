"""An ENGINE-ESCALATED run must not be rendered to the operator as a human gate.

When a Fabro run fails non-retryably, the engine routes it to the workflow's
`escalate` node. That routing is CORRECT and is not what these tests are about:
the defect is purely the Dispatcher's RENDERING of it, which used to announce
"parked at the in-loop human gate (needs-human); answer with `fabro attach` …"
for a run where no agent had asked anything. The wording sent a triager hunting
for a question that did not exist and invited an attach that could not help,
because the failure is deterministic and its retry budget is already spent.

The payload fixtures below carry the two tells measured on the real incident —
this repo, run 01M10CYZ8S9TNPZ2MW096NJW7V (work-item bd-ib-utq7b4), 2026-08-27,
read structurally out of the run's own record:

    checkpoints[4].checkpoint.next_node_id            = "escalate"
    checkpoints[4].checkpoint.loop_failure_signatures =
        {"review|deterministic|acp turn failed": 1}

and the genuine-gate fixture is the same shape with the second tell absent,
which is what an agent-reported needs-human ending leaves behind: it rides an
ordinary conditional edge off a node that SUCCEEDED, so the loop records no
failure signature. That pair of tells is the whole discriminator, and it is
deliberately the cheap one — no ACP adapter knowledge, no stderr dump.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_terminal import (
    fabro_run_terminal_outcome,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan
from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroInspectResult

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ESCALATION_MODULE_PATH = (
    _REPO_ROOT
    / ".claude-plugin"
    / "scripts"
    / "livespec_orchestrator_beads_fabro"
    / "commands"
    / "_fabro_escalation.py"
)
_ESCALATION_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._fabro_escalation"
_RUN_ID = "01M10CYZ8S9TNPZ2MW096NJW7V"
_MEASURED_SIGNATURE = "review|deterministic|acp turn failed"


@dataclass(frozen=True, kw_only=True)
class _CommandResult:
    exit_code: int
    stdout: str
    stderr: str


def _escalation_module() -> Any:
    """Import the escalation reader lazily.

    A top-level import would make the Red commit a COLLECTION error rather than
    a failing assertion, which proves only that the module is missing.
    """
    return importlib.import_module(_ESCALATION_MODULE_NAME)


def _record(*, checkpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A `fabro inspect --json` payload: a single-element LIST, as fabro returns."""
    return [
        {
            "run_id": _RUN_ID,
            "status": {"kind": "blocked"},
            "checkpoints": checkpoints,
        }
    ]


_ESCALATED_PAYLOAD = _record(
    checkpoints=[
        {"checkpoint": {"next_node_id": "review"}},
        {
            "checkpoint": {
                "next_node_id": "escalate",
                "loop_failure_signatures": {_MEASURED_SIGNATURE: 1},
            }
        },
    ]
)
_AGENT_GATE_PAYLOAD = _record(
    checkpoints=[{"checkpoint": {"next_node_id": "escalate"}}],
)
_MID_LOOP_GATE_PAYLOAD = _record(
    checkpoints=[{"checkpoint": {"next_node_id": "implement"}}],
)


def _plan(*, tmp_path: Path) -> DispatchPlan:
    return DispatchPlan(
        repo=tmp_path,
        work_item_id="bd-ib-utq7b4",
        branch="feat/bd-ib-utq7b4",
        workflow_toml=tmp_path / "workflow.toml",
        goal_file=tmp_path / "goal.txt",
        fabro_bin="fabro",
        fabro_factory_name="hp",
        fabro_factory_server=None,
        fabro_factory_dev_token=None,
        janitor=("just", "check"),
        janitor_checkout=tmp_path / ".janitor",
        janitor_core_checkout=tmp_path / ".janitor" / ".livespec-core",
        janitor_core_repo_url="https://github.com/thewoolleyman/livespec.git",
        janitor_core_ref="master",
        review_fix_visit_cap=3,
        merge_on_review_cap_outcome="succeeded",
    )


def _detail(*, tmp_path: Path, payload: list[dict[str, Any]]) -> str:
    outcome = fabro_run_terminal_outcome(
        outcome_type=DispatchOutcome,
        plan=_plan(tmp_path=tmp_path),
        run_id=_RUN_ID,
        inspect=FabroInspectResult(
            command=_CommandResult(exit_code=0, stdout="", stderr=""),
            payload=payload,
            status_kind="blocked",
            failure=None,
        ),
        exit_code=1,
        stderr="",
    )
    assert outcome is not None
    assert outcome.status == "blocked"
    return outcome.detail


def test_escalated_run_is_surfaced_as_an_escalation_not_as_a_human_gate(
    tmp_path: Path,
) -> None:
    """A run whose next node is the escalation node reads as an escalation."""
    detail = _detail(tmp_path=tmp_path, payload=_ESCALATED_PAYLOAD)

    assert "ESCALATED by the engine" in detail
    assert "`escalate` node" in detail
    assert "parked at the in-loop human gate" not in detail


def test_escalated_run_message_does_not_tell_the_operator_to_answer_a_gate(
    tmp_path: Path,
) -> None:
    """There is no question, so the message must not offer a way to answer one."""
    detail = _detail(tmp_path=tmp_path, payload=_ESCALATED_PAYLOAD)

    assert "answer with" not in detail
    assert "needs-human" not in detail
    assert f"fabro attach {_RUN_ID}" not in detail
    assert f"fabro resume {_RUN_ID}" not in detail


def test_escalated_run_message_names_the_recorded_loop_failure_signature(
    tmp_path: Path,
) -> None:
    """The signature is the thing actually worth triaging, so it is surfaced."""
    detail = _detail(tmp_path=tmp_path, payload=_ESCALATED_PAYLOAD)

    assert _MEASURED_SIGNATURE in detail


def test_run_genuinely_awaiting_human_input_still_reads_as_a_human_gate(
    tmp_path: Path,
) -> None:
    """An agent-reported needs-human ending records no loop failure signature."""
    detail = _detail(tmp_path=tmp_path, payload=_AGENT_GATE_PAYLOAD)

    assert "parked at the in-loop human gate (needs-human)" in detail
    assert f"answer with `fabro attach {_RUN_ID}`" in detail
    assert "ESCALATED by the engine" not in detail


def test_gate_outside_the_escalation_node_still_reads_as_a_human_gate(
    tmp_path: Path,
) -> None:
    """A run parked anywhere but the escalation node is untouched by the split."""
    detail = _detail(tmp_path=tmp_path, payload=_MID_LOOP_GATE_PAYLOAD)

    assert "parked at the in-loop human gate (needs-human)" in detail


def test_unusable_payload_falls_back_to_the_human_gate_wording(tmp_path: Path) -> None:
    """An unreadable record must not invent an escalation it cannot see."""
    assert "parked at the in-loop human gate" in _detail(tmp_path=tmp_path, payload=[])


def test_escalation_reader_module_exists_and_reads_both_tells() -> None:
    assert _ESCALATION_MODULE_PATH.is_file()
    module = _escalation_module()

    escalation = module.fabro_escalation_from_payload(payload=_ESCALATED_PAYLOAD)

    assert module.ESCALATION_NODE_ID == "escalate"
    assert escalation is not None
    assert escalation.next_node_id == "escalate"
    assert escalation.loop_failure_signatures == (_MEASURED_SIGNATURE,)


def test_escalation_reader_returns_none_without_both_tells() -> None:
    module = _escalation_module()

    assert module.fabro_escalation_from_payload(payload=None) is None
    assert module.fabro_escalation_from_payload(payload=_AGENT_GATE_PAYLOAD) is None
    assert module.fabro_escalation_from_payload(payload=_MID_LOOP_GATE_PAYLOAD) is None


def test_escalation_reader_tolerates_every_malformed_checkpoint_shape() -> None:
    module = _escalation_module()
    unusable = [
        _record(checkpoints=[]),
        _record(checkpoints=["not-a-mapping"]),  # pyright: ignore[reportArgumentType]
        _record(checkpoints=[{"checkpoint": "not-a-mapping"}]),
        _record(checkpoints=[{"next_node_id": 17}]),
        _record(checkpoints=[{"next_node_id": "   "}]),
        [{"run_id": _RUN_ID, "checkpoints": "not-a-list"}],
        [
            {
                "run_id": _RUN_ID,
                "checkpoint": {
                    "next_node_id": "escalate",
                    "loop_failure_signatures": "not-a-mapping",
                },
            }
        ],
        [
            {
                "run_id": _RUN_ID,
                "checkpoint": {
                    "next_node_id": "escalate",
                    "loop_failure_signatures": {"  ": 1, 17: 2},
                },
            }
        ],
    ]

    assert [module.fabro_escalation_from_payload(payload=each) for each in unusable] == [
        None
    ] * len(unusable)


def test_top_level_checkpoint_is_the_newest_state_and_wins() -> None:
    """The record's own `checkpoint` is later than anything in `checkpoints[]`."""
    module = _escalation_module()
    payload = [
        {
            "run_id": _RUN_ID,
            "checkpoints": [
                {
                    "checkpoint": {
                        "next_node_id": "escalate",
                        "loop_failure_signatures": {_MEASURED_SIGNATURE: 1},
                    }
                }
            ],
            "checkpoint": {"next_node_id": "pr"},
        }
    ]

    assert module.fabro_escalation_from_payload(payload=payload) is None
