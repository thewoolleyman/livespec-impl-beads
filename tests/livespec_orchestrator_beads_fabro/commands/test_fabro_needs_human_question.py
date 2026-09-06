"""Tests for the needs-human account read off a TERMINATED run's inspect record."""

from __future__ import annotations

import importlib
from pathlib import Path

_MODULE_PATH = (
    Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
    / "_fabro_needs_human_question.py"
)
_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._fabro_needs_human_question"

_PROMPT = (
    "loop cannot auto-resolve this work-item; run terminated, work preserved "
    "by reference, decision routed to the ledger (blocked / needs-human)"
)
_REF = "refs/heads/needs-human/01M10CYZ8S9TNPZ2MW096NJW7V"


def _terminated(*, stderr: str, checkpoints: list[object] | None = None) -> list[object]:
    """A `fabro inspect --json` payload for a run that TERMINATED non-green.

    `status.kind` is `failed`, never a park: under contract v093 a needs-human
    outcome terminates the run. A fixture that parked would be testing a state
    this repository's workflow cannot produce.
    """
    return [
        {
            "run_id": "01M10CYZ8S9TNPZ2MW096NJW7V",
            "status": {"kind": "failed"},
            "checkpoints": checkpoints
            if checkpoints is not None
            else [{"checkpoint": {"next_node_id": "needs_human"}}],
            "nodes": [{"id": "needs_human", "output": {"stderr": stderr}}],
        }
    ]


def test_a_terminated_needs_human_run_yields_why_it_stopped_and_where_work_survived() -> None:
    assert _MODULE_PATH.is_file()
    module = importlib.import_module(_MODULE_NAME)

    question = module.needs_human_question_from_payload(
        payload=_terminated(
            stderr=f"LIVESPEC_NEEDS_HUMAN_PRESERVED: {_REF}\nLIVESPEC_NEEDS_HUMAN: {_PROMPT}\n",
            checkpoints=[
                {"checkpoint": {"next_node_id": "review"}},
                {
                    "checkpoint": {
                        "next_node_id": "needs_human",
                        "loop_failure_signatures": {"review|deterministic|acp turn failed": 1},
                    }
                },
            ],
        )
    )

    assert question is not None
    assert question.prompt == _PROMPT
    assert question.reason == "review|deterministic|acp turn failed"
    assert question.preserved_ref == _REF
    assert question.tree_preserved is True
    assert module.NEEDS_HUMAN_NODE_ID == "needs_human"


def test_a_run_that_did_not_end_at_the_terminal_node_yields_nothing() -> None:
    """`None` is "this run did not route a human decision", nothing else."""
    module = importlib.import_module(_MODULE_NAME)

    assert module.needs_human_question_from_payload(payload=None) is None
    assert module.needs_human_question_from_payload(payload=[]) is None
    assert (
        module.needs_human_question_from_payload(
            payload=[{"run_id": "01OK", "status": {"kind": "succeeded"}}]
        )
        is None
    )
    assert (
        module.needs_human_question_from_payload(
            payload=[{"checkpoints": [{"checkpoint": {"next_node_id": "pr"}}]}]
        )
        is None
    )


def test_the_sentinel_alone_is_enough_wherever_in_the_record_it_sits() -> None:
    """Which field carries a script node's stderr is the unknown; the token is ours."""
    module = importlib.import_module(_MODULE_NAME)

    question = module.needs_human_question_from_payload(
        payload={
            "status": {"kind": "failed"},
            "some": {"unmodelled": ["nesting", {"log": f"LIVESPEC_NEEDS_HUMAN: {_PROMPT}"}]},
        }
    )

    assert question is not None
    assert question.prompt == _PROMPT
    assert question.preserved_ref is None
    # No push-failed sentinel present, so preservation is not contradicted —
    # the ABSENT ref is what the lane reports, not a failed push.
    assert question.tree_preserved is True


def test_the_routing_alone_is_enough_when_no_sentinel_text_is_readable() -> None:
    """A record carrying only the checkpoint still names a real human decision."""
    module = importlib.import_module(_MODULE_NAME)

    question = module.needs_human_question_from_payload(
        payload=_terminated(stderr="no sentinel here at all")
    )

    assert question is not None
    assert question.prompt is None
    assert question.preserved_ref is None
    # An agent-reported ending records no loop failure signature, and that
    # absence is informative rather than a failed read.
    assert question.reason is None


def test_a_failed_push_is_reported_as_a_fact_not_as_a_missing_ref() -> None:
    """A rework decision turns on whether the tree is actually there."""
    module = importlib.import_module(_MODULE_NAME)

    question = module.needs_human_question_from_payload(
        payload=_terminated(
            stderr=(
                "LIVESPEC_NEEDS_HUMAN_PUSH_FAILED: tree not pushed; rely on the "
                "preserve-by-reference dump pointer\n"
                f"LIVESPEC_NEEDS_HUMAN: {_PROMPT}"
            )
        )
    )

    assert question is not None
    assert question.tree_preserved is False
    assert question.preserved_ref is None
    assert question.prompt == _PROMPT


def test_an_empty_or_malformed_sentinel_line_does_not_masquerade_as_content() -> None:
    module = importlib.import_module(_MODULE_NAME)

    question = module.needs_human_question_from_payload(
        payload=_terminated(stderr="LIVESPEC_NEEDS_HUMAN:    \n   \nLIVESPEC_NEEDS_HUMAN")
    )

    assert question is not None
    assert question.prompt is None


def test_a_top_level_checkpoint_and_a_bare_wrapper_are_both_read() -> None:
    """The routing walk covers both checkpoint shapes the records carry."""
    module = importlib.import_module(_MODULE_NAME)

    top_level = module.needs_human_question_from_payload(
        payload=[{"checkpoint": {"next_node_id": "needs_human"}}]
    )
    bare_wrapper = module.needs_human_question_from_payload(
        payload=[{"checkpoints": ["not a mapping", {"next_node_id": " needs_human "}]}]
    )

    assert top_level is not None
    assert bare_wrapper is not None
