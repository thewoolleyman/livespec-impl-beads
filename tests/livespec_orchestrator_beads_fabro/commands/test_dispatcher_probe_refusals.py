"""Tests for the three refusals bracketing every loop-probe invocation (v076).

Each refusal is tested for its TEXT as well as its verdict, because each one's
text is the whole remedy an operator gets: the take-never-file refusal has to
route them to `capture-work-item`, the policy refusal has to name the label, and
the attribution refusal has to name both accepted identity inputs. A refusal
that fired correctly and said nothing useful would leave the operator with a
failed probe and no next move.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import (
    ENV_SOURCE,
    FALLBACK_SOURCE,
    FLAG_SOURCE,
    InvokerIdentity,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_refusals import (
    AI_ONLY_POLICY,
    PROBE_ACCEPTANCE_LABEL,
    acceptance_policy_refusal,
    designated_item_refusal,
    fallback_invoker_refusal,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

_ITEM = "bd-ib-probe"


def _item(**overrides: object) -> WorkItem:
    base = WorkItem(
        id=_ITEM,
        type="task",
        status="ready",
        title="A probe fixture",
        description="Drive the loop.",
        origin="freeform",
        gap_id=None,
        rank="a2",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-28T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy=AI_ONLY_POLICY,
    )
    return replace(base, **overrides)


def _repo(*, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib",'
        ' "fake": true}}}',
        encoding="utf-8",
    )
    return repo


# --- it takes; it never files -----------------------------------------------


@pytest.mark.parametrize("designated", [None, "", "   "])
def test_the_probe_refuses_without_a_designated_item(designated: str | None) -> None:
    refusal = designated_item_refusal(item_id=designated)

    assert refusal is not None
    assert "--item" in refusal
    assert "never creates, files, or clones" in refusal
    assert "capture-work-item" in refusal


def test_a_designated_item_clears_the_take_never_file_refusal() -> None:
    assert designated_item_refusal(item_id=_ITEM) is None


# --- it refuses an item it cannot drive to done -----------------------------


def test_an_ai_only_item_clears_the_acceptance_policy_refusal(tmp_path: Path) -> None:
    assert acceptance_policy_refusal(item=_item(), cwd=_repo(tmp_path=tmp_path)) is None


@pytest.mark.parametrize("policy", ["ai-then-human", "human-only"])
def test_a_non_ai_only_item_is_refused_naming_the_label_to_set(tmp_path: Path, policy: str) -> None:
    refusal = acceptance_policy_refusal(
        item=_item(acceptance_policy=policy), cwd=_repo(tmp_path=tmp_path)
    )

    assert refusal is not None
    assert policy in refusal
    assert PROBE_ACCEPTANCE_LABEL in refusal


# --- an unattributed probe proves nothing about attribution -----------------


@pytest.mark.parametrize("source", [FLAG_SOURCE, ENV_SOURCE])
def test_an_asserted_invoker_clears_the_attribution_refusal(source: str) -> None:
    identity = InvokerIdentity(invoker="operator:probe-test", invoker_source=source)

    assert fallback_invoker_refusal(identity=identity) is None


def test_a_fallback_derived_invoker_fails_the_probe() -> None:
    identity = InvokerIdentity(invoker="unattributed:me@host", invoker_source=FALLBACK_SOURCE)

    refusal = fallback_invoker_refusal(identity=identity)

    assert refusal is not None
    assert "unattributed:me@host" in refusal
    assert "--invoker" in refusal
    assert "LIVESPEC_INVOKER" in refusal
