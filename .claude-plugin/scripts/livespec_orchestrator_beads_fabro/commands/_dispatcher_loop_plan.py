"""Per-item `DispatchPlan` construction for the dispatch loop.

Split out of `_dispatcher_loop` by cohesion: everything here answers "what
does THIS item's run look like" — where its per-dispatch scratch files live,
which janitor checkout it gets, which factory it goes to, its effective
review-fix policy, and the subprocess ceiling derived from its resolved node
timeouts. `_dispatcher_loop` is left with the other concern, driving the
dispatch and routing each pre-run refusal to its own journal stage.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import cast

from returns.unsafe import unsafe_perform_io

from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_selection import janitor_core_ref
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    build_plan,
    janitor_checkout_path,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan_build import DispatchPlan
from livespec_orchestrator_beads_fabro.commands._dispatcher_policy_settings import (
    DEFAULT_MERGE_ON_REVIEW_CAP,
    DEFAULT_REVIEW_FIX_CAP,
    effective_merge_on_review_cap,
    effective_review_fix_cap,
)
from livespec_orchestrator_beads_fabro.commands._node_timeouts import (
    NodeTimeouts,
    derive_fabro_timeout_seconds,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "dispatch_plan_for_item",
    "goal_file_path",
    "overlay_file_path",
    "workflow_payload_dir",
]


def goal_file_path(*, work_item_id: str) -> Path:
    """The per-dispatch rendered run goal (`--goal-file`)."""
    return Path(tempfile.gettempdir()) / f"fabro-goal-{work_item_id}.md"


def overlay_file_path(*, work_item_id: str) -> Path:
    """The per-dispatch uncommitted run-config overlay (mode 600)."""
    return Path(tempfile.gettempdir()) / f"fabro-run-config-{work_item_id}.toml"


def workflow_payload_dir(*, work_item_id: str) -> Path:
    """The per-dispatch workflow payload (rendered graph plus its prompts)."""
    return Path(tempfile.gettempdir()) / f"fabro-workflow-{work_item_id}"


def dispatch_plan_for_item(
    *,
    args: argparse.Namespace,
    repo: Path,
    item: WorkItem,
    janitor: tuple[str, ...] | None,
    raw_labels: tuple[str, ...],
    timeouts: NodeTimeouts,
) -> DispatchPlan:
    """Resolve one item's dispatch plan from its args, labels and timeouts."""
    factory_target = cast("FactoryTarget", args.fabro_factory_target)
    return build_plan(
        repo=repo,
        work_item_id=item.id,
        workflow_toml=overlay_file_path(work_item_id=item.id),
        goal_file=goal_file_path(work_item_id=item.id),
        fabro_bin=args.fabro_bin,
        fabro_factory_name=factory_target.name,
        fabro_factory_server=factory_target.server,
        fabro_factory_dev_token=factory_target.dev_token,
        janitor=janitor,
        janitor_checkout=janitor_checkout_path(repo=repo, work_item_id=item.id),
        janitor_core_ref=janitor_core_ref(repo=repo),
        # An unreadable `.livespec.jsonc` falls back to the documented
        # defaults, visibly and here rather than inside the reader.
        # `unsafe_perform_io` is required: `IOResult.value_or` returns
        # `IO[value]`, not the value.
        review_fix_cap=unsafe_perform_io(
            effective_review_fix_cap(item=item, cwd=repo, raw_labels=raw_labels).value_or(
                DEFAULT_REVIEW_FIX_CAP
            )
        ),
        merge_on_review_cap=unsafe_perform_io(
            effective_merge_on_review_cap(item=item, cwd=repo, raw_labels=raw_labels).value_or(
                DEFAULT_MERGE_ON_REVIEW_CAP
            )
        ),
        # The `fabro run` subprocess ceiling FOLLOWS the resolved graph rather
        # than a constant, so lengthening a node cannot outrun the poller and
        # shortening one is not masked.
        fabro_timeout_seconds=derive_fabro_timeout_seconds(timeouts=timeouts),
    )
