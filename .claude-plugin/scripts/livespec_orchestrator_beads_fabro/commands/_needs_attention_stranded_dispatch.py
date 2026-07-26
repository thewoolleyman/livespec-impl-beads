"""Stranded merged-dispatch attention lanes."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from livespec_runtime.attention_item import AttentionItem, Handoff, SourceRef

from livespec_orchestrator_beads_fabro.commands._needs_attention_handoffs import (
    reconcile_merged_command,
)
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt, parse_json
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "stranded_dispatch_items",
]

_DISPATCHER_JOURNAL_PATH = Path("tmp") / "fabro-dispatch-journal.jsonl"
_STRANDED_REASON = "stranded-dispatch"


class _LiveLockLookup(Protocol):
    def __call__(self, *, repo: Path, work_item_id: str) -> object | None: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class _TerminalOutcome:
    work_item_id: str
    status: str
    stage: str
    pr_number: int
    merge_sha: str


@dataclass(frozen=True, slots=True, kw_only=True)
class _StrandedDispatch:
    outcome: _TerminalOutcome
    attempts: int


def stranded_dispatch_items(
    *,
    project_root: Path,
    repo: str,
    items: list[WorkItem],
    live_lock_lookup: _LiveLockLookup,
) -> list[AttentionItem]:
    active_items = {item.id: item for item in items if item.status == "active"}
    stranded = _stranded_dispatches(project_root=project_root, active_item_ids=active_items.keys())
    attention: list[AttentionItem] = []
    for item_id, dispatch in stranded.items():
        if live_lock_lookup(repo=project_root, work_item_id=item_id) is not None:
            continue
        attention.append(
            _stranded_dispatch_item(
                project_root=project_root,
                repo=repo,
                work_item=active_items[item_id],
                stranded_dispatch=dispatch,
            )
        )
    return attention


def _stranded_dispatches(
    *, project_root: Path, active_item_ids: Collection[str]
) -> dict[str, _StrandedDispatch]:
    active_ids = frozenset(active_item_ids)
    journal = project_root / _DISPATCHER_JOURNAL_PATH
    if not journal.is_file():
        return {}
    loaded = attempt(action=lambda: journal.read_text(encoding="utf-8"), exceptions=(OSError,))
    if isinstance(loaded, AttemptFailure):
        return {}
    attempts: dict[str, int] = {}
    latest: dict[str, _TerminalOutcome] = {}
    for line in loaded.splitlines():
        outcome = _terminal_outcome(line=line)
        if outcome is None or outcome.work_item_id not in active_ids:
            continue
        attempts[outcome.work_item_id] = attempts.get(outcome.work_item_id, 0) + 1
        latest[outcome.work_item_id] = outcome
    return {
        item_id: _StrandedDispatch(outcome=outcome, attempts=attempts[item_id])
        for item_id, outcome in latest.items()
    }


def _terminal_outcome(*, line: str) -> _TerminalOutcome | None:
    parsed = parse_json(text=line)
    if not isinstance(parsed, dict):
        return None
    record = cast("dict[str, Any]", parsed)
    if record.get("stage") != "outcome":
        return None
    outcome = record.get("outcome")
    if not isinstance(outcome, dict):
        return None
    return _terminal_outcome_payload(payload=cast("dict[str, Any]", outcome))


def _terminal_outcome_payload(*, payload: dict[str, Any]) -> _TerminalOutcome | None:
    work_item_id = payload.get("work_item_id")
    status = payload.get("status")
    stage = payload.get("stage")
    pr_number = payload.get("pr_number")
    merge_sha = payload.get("merge_sha")
    if status != "failed":
        return None
    if not isinstance(work_item_id, str) or not work_item_id:
        return None
    if not isinstance(stage, str) or not stage:
        return None
    if not isinstance(pr_number, int) or isinstance(pr_number, bool):
        return None
    if not isinstance(merge_sha, str) or not merge_sha:
        return None
    return _TerminalOutcome(
        work_item_id=work_item_id,
        status=status,
        stage=stage,
        pr_number=pr_number,
        merge_sha=merge_sha,
    )


def _stranded_dispatch_item(
    *,
    project_root: Path,
    repo: str,
    work_item: WorkItem,
    stranded_dispatch: _StrandedDispatch,
) -> AttentionItem:
    outcome = stranded_dispatch.outcome
    return AttentionItem(
        id=f"host-only:{_STRANDED_REASON}:{work_item.id}",
        kind="host-only",
        urgency="high",
        summary=(
            f"Reconcile merged active work-item {work_item.id}: PR #{outcome.pr_number} "
            f"merged at {outcome.merge_sha}; {outcome.stage} failed across "
            f"{stranded_dispatch.attempts} prior attempts."
        ),
        source_ref=SourceRef(repo=repo, work_item=work_item.id),
        handoff=Handoff(
            kind="shell",
            command=reconcile_merged_command(project_root=project_root, work_item=work_item.id),
        ),
    )
