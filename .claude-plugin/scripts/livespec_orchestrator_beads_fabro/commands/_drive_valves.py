"""Human-valve actions for the drive operator surface."""

from collections.abc import Callable
from pathlib import Path
from subprocess import run
from typing import Any, Protocol, cast

from livespec_orchestrator_beads_fabro import store
from livespec_orchestrator_beads_fabro.commands._config import resolve_store_config
from livespec_orchestrator_beads_fabro.commands._dispatcher_effective_criteria import (
    ungradeable_criteria_refusal,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import (
    InvokerIdentity,
    default_invoker_identity,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.commands._drive_policy_valves import (
    CAP_ACTION_VERBS,
    move_item,
    resolve_blocked_item,
    set_cap,
    set_policy,
    set_workflow_scope_override,
)
from livespec_orchestrator_beads_fabro.commands._drive_valve_predicates import can_approve_item
from livespec_orchestrator_beads_fabro.commands._drive_valve_result import (
    invalid_source_state,
    valve_refusal,
    valve_success,
)
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

__all__: list[str] = ["is_human_valve_action", "run_human_valve_action"]


class HumanValveCommandRun(Protocol):
    @property
    def returncode(self) -> int: ...

    @property
    def stderr(self) -> str: ...


HumanValveRunner = Callable[..., object]
_REWORK_REJECT_KIND = "rework"
ACTION_WITH_ITEM_PARTS = 2
ACTION_WITH_VALUE_PARTS = 3
APPROVAL_ACTIONS = frozenset({"approve", "accept"})
VALUE_ALLOWLISTS = {
    "reject": frozenset({"rework", "regroom"}),
    "resolve-blocked": frozenset({"ready", "backlog"}),
    "set-admission": frozenset({"auto", "manual"}),
    "set-acceptance": frozenset({"ai-only", "human-only", "ai-then-human"}),
    "set-workflow-scope-override": frozenset({"citation-only"}),
}


def run_human_valve_action(
    *,
    repo: Path,
    action_id: str,
    runner: HumanValveRunner | None = None,
    identity: InvokerIdentity | None = None,
) -> dict[str, Any]:
    """Run one human-valve action, attributing whatever it journals.

    `identity` is the invocation's resolved invoker; `None` means "resolve it
    from the environment here", so a direct caller is still attributed rather
    than unattributed.
    """
    resolved_identity = default_invoker_identity() if identity is None else identity
    parsed = _parse_human_valve_action(action_id=action_id)
    if parsed is None:
        return valve_refusal(
            aid=action_id,
            err="invalid-action-id",
            msg="Unsupported human valve action id.",
        )
    action, item_id, action_value = parsed
    config = resolve_store_config(cwd=repo, work_items_arg=None)
    item = _find_item(items=list(store.read_work_items(path=config)), item_id=item_id)
    if item is None:
        return valve_refusal(
            aid=action_id,
            err="work-item-not-found",
            msg=f"work-item not found: {item_id}",
        )
    value = cast("str", action_value)
    if action == "resolve-blocked":
        result = resolve_blocked_item(config=config, item=item, aid=action_id, target_status=value)
    elif action == "approve":
        result = _approve_item(repo=repo, config=config, item=item, action_id=action_id)
    elif action == "accept":
        result = _accept_item(config=config, item=item, action_id=action_id)
    elif action in {"set-admission", "set-acceptance"}:
        result = set_policy(config=config, item=item, aid=action_id, action=action, value=value)
    elif action == "set-workflow-scope-override":
        result = set_workflow_scope_override(config=config, item=item, aid=action_id, value=value)
    elif action in CAP_ACTION_VERBS:
        result = set_cap(config=config, item=item, aid=action_id, action=action, value=value)
    elif action == "move":
        result = move_item(config=config, item=item, aid=action_id, target_status=value)
    else:
        result = _reject_item(
            repo=repo, config=config, item=item, aid=action_id, reject_kind=value, runner=runner
        )
        _journal_rework_return(
            repo=repo, identity=resolved_identity, reject_kind=value, result=result
        )
    return result


def is_human_valve_action(*, action_id: str) -> bool:
    return action_id.startswith(
        (
            "approve:",
            "accept:",
            "reject:",
            "resolve-blocked:",
            "set-admission:",
            "set-acceptance:",
            "set-workflow-scope-override:",
            "set-merge-on-review-cap:",
            "set-review-fix-cap:",
            "set-acceptance-rework-cap:",
            "move:",
        )
    )


def _parse_human_valve_action(*, action_id: str) -> tuple[str, str, str | None] | None:
    parts = action_id.split(":")
    parsed = _parse_action_with_item(parts=parts)
    if parsed is not None:
        return parsed
    return _parse_action_with_value(parts=parts)


def _parse_action_with_item(*, parts: list[str]) -> tuple[str, str, str | None] | None:
    if len(parts) != ACTION_WITH_ITEM_PARTS:
        return None
    action, item = parts
    if item == "" or action not in APPROVAL_ACTIONS:
        return None
    return (action, item, None)


def _parse_action_with_value(*, parts: list[str]) -> tuple[str, str, str | None] | None:
    if len(parts) != ACTION_WITH_VALUE_PARTS:
        return None
    action, item, value = parts
    if item == "":
        return None
    if action in CAP_ACTION_VERBS:
        return (action, item, value)
    if action == "move":
        return ("move", item, value)
    allowed_values = VALUE_ALLOWLISTS.get(action)
    if allowed_values is None or value not in allowed_values:
        return None
    return (action, item, value)


def _find_item(*, items: list[WorkItem], item_id: str) -> WorkItem | None:
    return next((item for item in items if item.id == item_id), None)


def _approve_item(
    *, repo: Path, config: StoreConfig, item: WorkItem, action_id: str
) -> dict[str, Any]:
    if item.status != "pending-approval":
        return invalid_source_state(aid=action_id, item=item, expected="pending-approval")
    if not can_approve_item(item=item, cwd=repo):
        return valve_refusal(
            aid=action_id,
            wid=item.id,
            err="invalid-source-state",
            msg="approve requires an effective-manual pending-approval item.",
        )
    # The entry-to-`ready` wall (the effective-acceptance-criteria clause of contracts.md).
    # The refusal writes NOTHING: the item rests at `pending-approval` rather
    # than being routed to `backlog` or `blocked` on these grounds.
    ungradeable = ungradeable_criteria_refusal(item=item, cwd=repo)
    if ungradeable is not None:
        return valve_refusal(
            aid=action_id,
            wid=item.id,
            err="ungradeable-acceptance-criteria",
            msg=f"approve refused: {ungradeable}.",
        )
    store.update_work_item_status(path=config, item_id=item.id, status="ready")
    return valve_success(
        aid=action_id,
        wid=item.id,
        stage="human-valve-approve",
        status="ready",
        assignee=None,
        msg=f"Approved {item.id}: pending-approval -> ready.",
    )


def _accept_item(*, config: StoreConfig, item: WorkItem, action_id: str) -> dict[str, Any]:
    if item.status != "acceptance":
        return invalid_source_state(aid=action_id, item=item, expected="acceptance")
    store.update_work_item_status(path=config, item_id=item.id, status="done")
    return valve_success(
        aid=action_id,
        wid=item.id,
        stage="human-valve-accept",
        status="done",
        assignee=None,
        msg=f"Accepted {item.id}: acceptance -> done.",
    )


def _reject_item(
    *,
    repo: Path,
    config: StoreConfig,
    item: WorkItem,
    aid: str,
    reject_kind: str,
    runner: HumanValveRunner | None,
) -> dict[str, Any]:
    if item.status != "acceptance":
        return invalid_source_state(aid=aid, item=item, expected="acceptance")
    target_status = "active" if reject_kind == "rework" else "backlog"
    if reject_kind == "regroom":
        refusal = _revert_merged_change(repo=repo, item=item, aid=aid, runner=runner)
        if refusal is not None:
            return refusal
    store.update_work_item_status(path=config, item_id=item.id, status=target_status)
    return valve_success(
        aid=aid,
        wid=item.id,
        stage=f"human-valve-reject-{reject_kind}",
        status=target_status,
        assignee=None,
        msg=f"Rejected {item.id}: acceptance -> {target_status}.",
    )


def _journal_rework_return(
    *, repo: Path, identity: InvokerIdentity, reject_kind: str, result: dict[str, Any]
) -> None:
    """Journal a SUCCESSFUL REWORK return through the single append layer.

    Lifted out of `_reject_item` so the invocation's identity reaches the write
    without pushing that function past the argument ceiling, and it owns BOTH
    guards rather than splitting them with its caller. A `regroom` return is not
    journaled here, and a refusal payload carries no `journal` key — so that
    key's absence is the success discriminator.
    """
    record = result.get("journal")
    if reject_kind != _REWORK_REJECT_KIND or record is None:
        return
    JournalFile(path=repo / "tmp" / "fabro-dispatch-journal.jsonl", identity=identity).append(
        record=cast("dict[str, object]", record)
    )


def _revert_merged_change(
    *, repo: Path, item: WorkItem, aid: str, runner: HumanValveRunner | None
) -> dict[str, Any] | None:
    merge_sha = item.audit.merge_sha if item.audit is not None else None
    if not merge_sha:
        return valve_refusal(
            aid=aid,
            wid=item.id,
            err="missing-merge-evidence",
            msg="reject:regroom refused: no merged change recorded to revert.",
        )
    argv = ("git", "revert", "--no-edit", merge_sha)
    if runner is None:
        result = run(argv, check=False, cwd=repo, text=True, capture_output=True)  # noqa: S603
    else:
        result = cast("HumanValveCommandRun", runner(argv=argv, cwd=repo))
    if result.returncode == 0:
        return None
    return valve_refusal(
        aid=aid,
        wid=item.id,
        err="revert-failed",
        msg=f"reject:regroom refused: git revert {merge_sha} failed: {result.stderr}",
    )
