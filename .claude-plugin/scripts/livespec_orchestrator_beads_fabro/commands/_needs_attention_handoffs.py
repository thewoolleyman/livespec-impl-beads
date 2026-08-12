"""Handoff command rendering for needs-attention outputs."""

from __future__ import annotations

import shlex
from collections.abc import Iterable
from pathlib import Path

from livespec_runtime.needs_attention import PlanThreadOutput

from livespec_orchestrator_beads_fabro.commands.list_plans import list_plans
from livespec_orchestrator_beads_fabro.commands.plan import read_timeline
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

__all__: list[str] = [
    "dispatcher_loop_command",
    "drive_command",
    "host_only_command",
    "plans",
    "reconcile_merged_command",
    "untriaged_backlog_command",
    "untriaged_backlog_summary_command",
]

_PLUGIN_NAME = "livespec-orchestrator-beads-fabro"
_PLAN_HINT_PREFIX = "plan:"


def plans(
    *,
    project_root: Path,
    config: StoreConfig,
    items: Iterable[WorkItem],
) -> list[PlanThreadOutput]:
    return [
        PlanThreadOutput(
            topic=topic,
            path=f"plan/{topic}/",
            summary=f"Review plan thread {topic}.",
            command=(
                f"codex exec {_PLUGIN_NAME}:plan "
                f"--project-root {_quote(path=project_root)} {shlex.quote(topic)}"
            ),
        )
        for topic in _plan_topics(project_root=project_root, config=config, items=items)
    ]


def _plan_topics(
    *,
    project_root: Path,
    config: StoreConfig,
    items: Iterable[WorkItem],
) -> list[str]:
    return sorted(
        {
            *list_plans(project_root=project_root),
            *_ledger_plan_topics(config=config, items=items),
        }
    )


def _ledger_plan_topics(*, config: StoreConfig, items: Iterable[WorkItem]) -> list[str]:
    topics: list[str] = []
    for item in items:
        topic = _plan_topic(item=item)
        if topic is None:
            continue
        _ = read_timeline(config=config, epic_id=item.id)
        topics.append(topic)
    return topics


def _plan_topic(*, item: WorkItem) -> str | None:
    hint = item.spec_commitment_hint
    if item.type != "epic" or item.status == "done" or hint is None:
        return None
    if not hint.startswith(_PLAN_HINT_PREFIX):
        return None
    topic = hint.removeprefix(_PLAN_HINT_PREFIX)
    if topic == "":
        return None
    return topic


def drive_command(*, project_root: Path, action_id: str) -> str:
    return (
        f"python3 {_quote(path=_wrapper_path(name='drive.py'))} "
        f"--repo {_quote(path=project_root)} --action {shlex.quote(action_id)} --json"
    )


def dispatcher_loop_command(*, project_root: Path) -> str:
    return (
        f"python3 {_quote(path=_wrapper_path(name='dispatcher.py'))} "
        f"loop --repo {_quote(path=project_root)} --budget 1 --parallel 1 --json"
    )


def host_only_command(*, project_root: Path, work_item: str) -> str:
    prompt = (
        f"Host-route work-item {work_item} from repository {project_root}. "
        "Run it on the host with required credentials; do not dispatch it to Fabro."
    )
    return f"cd {_quote(path=project_root)} && codex exec {shlex.quote(prompt)} < /dev/null"


def reconcile_merged_command(*, project_root: Path, work_item: str) -> str:
    return (
        f"python3 {_quote(path=_wrapper_path(name='dispatcher.py'))} "
        f"reconcile-merged --repo {_quote(path=project_root)} "
        f"--item {shlex.quote(work_item)} --json"
    )


def untriaged_backlog_command(*, project_root: Path, work_item: str) -> str:
    """Hand off ONE backlog work-item the intake gate never saw."""
    prompt = (
        f"Triage backlog work-item {work_item} in repository {project_root}. "
        "It was filed without running the intake Definition-of-Ready checklist, "
        "so it carries no intake:triaged label and no surface reports it. Run the "
        "checklist over it and route it to its lifecycle state; if it is "
        "deliberately parked, label it intake:triaged to dismiss it from this lane."
    )
    return f"cd {_quote(path=project_root)} && codex exec {shlex.quote(prompt)} < /dev/null"


def untriaged_backlog_summary_command(*, project_root: Path) -> str:
    """Hand off the lower-priority remainder as ONE item, never one per record.

    The remainder is reported in aggregate on purpose: a repository can carry
    hundreds of un-triaged backlog items, and one attention item per record
    would produce noise rather than signal — an attention list nobody reads
    is worse than none.
    """
    prompt = (
        f"Triage the un-triaged backlog work-items in repository {project_root} — "
        "every item in backlog status without the intake:triaged label. Run the "
        "intake Definition-of-Ready checklist over each and route it to its "
        "lifecycle state; label the deliberately-parked ones intake:triaged."
    )
    return f"cd {_quote(path=project_root)} && codex exec {shlex.quote(prompt)} < /dev/null"


def _wrapper_path(*, name: str) -> Path:
    return Path(__file__).parents[2] / "bin" / name


def _quote(*, path: Path) -> str:
    return shlex.quote(str(path))
