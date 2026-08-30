"""DispatchPlan dataclass and per-item plan construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._acp_node_layers import AcpNodeResolution
from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_argv import (
    janitor_argv,
    janitor_core_checkout_path,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_check_suite import (
    resolve_janitor_check_suite,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_policy_settings import (
    DEFAULT_MERGE_ON_REVIEW_CAP,
    DEFAULT_REVIEW_FIX_CAP,
)
from livespec_orchestrator_beads_fabro.commands._node_timeouts import (
    DEFAULT_FABRO_TIMEOUT_SECONDS,
)

__all__: list[str] = [
    "DispatchPlan",
    "build_plan",
]

_DEFAULT_JANITOR_CORE_REPO_URL = "https://github.com/thewoolleyman/livespec.git"
_DEFAULT_JANITOR_CORE_REF = "master"
_MERGE_ON_REVIEW_CAP_DISABLED_OUTCOME = "__merge_on_review_cap_disabled__"


@dataclass(frozen=True, kw_only=True)
class DispatchPlan:
    """Everything one work-item dispatch needs, resolved up front.

    `branch` is the PUBLISH branch (`feat/<work-item-id>`) the phase
    graph's pr stage pushes and the engine polls — the Fabro-managed
    run branch inside the sandbox is run-internal and never leaves it.
    `workflow_toml` is the MATERIALIZED run-config overlay path (the
    committed config plus the credential env table), not the committed
    file itself. `janitor_checkout` is the path the engine provisions
    as a FRESH detached worktree of the merged ref and runs the
    post-merge janitor in — never the host primary's working tree,
    whose environment rot (stale `.venv` shebangs, stale `.coverage`,
    ghost `__pycache__` dirs) once false-redded a confirmed-green
    merge (work-item livespec-impl-beads-cgd).
    """

    repo: Path
    work_item_id: str
    branch: str
    workflow_toml: Path
    goal_file: Path
    fabro_bin: str
    fabro_factory_name: str
    fabro_factory_server: str | None
    fabro_factory_dev_token: str | None
    janitor: tuple[str, ...]
    janitor_checkout: Path
    janitor_core_checkout: Path
    janitor_core_repo_url: str
    janitor_core_ref: str
    review_fix_visit_cap: int
    merge_on_review_cap_outcome: str
    # Every ACP node's adapter, already resolved through the workflow /
    # repository / per-dispatch layers (`_acp_node_layers`). It rides the
    # plan rather than being re-resolved at launch because BOTH launchers
    # render the `--input` pairs from it, and because the resolution is
    # what the dispatch record already journaled -- re-deriving it at
    # launch is how the record and the run come to disagree.
    #
    # None is NOT a provider fallback: it means this plan carried no
    # resolution, so the dispatch passes NO adapter `--input` at all and
    # the workflow's own declared defaults stand. That is layer 1 doing
    # its job through fabro rather than through us, which is why no
    # adapter string survives anywhere in this package as a literal.
    acp_nodes: AcpNodeResolution | None = None
    # The `fabro run` subprocess ceiling, DERIVED from this dispatch's
    # resolved node timeouts and stall timeout rather than fixed by a
    # constant — so lengthening a node cannot outrun the poller and
    # shortening one is not masked. Both launchers read it from here, which
    # is what keeps the watched and synchronous paths on one number.
    fabro_timeout_seconds: float = DEFAULT_FABRO_TIMEOUT_SECONDS


def build_plan(  # noqa: PLR0913 — kw-only plan resolver; each field is an independent caller input.
    *,
    repo: Path,
    work_item_id: str,
    workflow_toml: Path,
    goal_file: Path,
    fabro_bin: str,
    fabro_factory_name: str = "default",
    fabro_factory_server: str | None = None,
    fabro_factory_dev_token: str | None = None,
    janitor: tuple[str, ...] | None,
    janitor_checkout: Path,
    janitor_core_repo_url: str = _DEFAULT_JANITOR_CORE_REPO_URL,
    janitor_core_ref: str = _DEFAULT_JANITOR_CORE_REF,
    review_fix_cap: int = DEFAULT_REVIEW_FIX_CAP,
    merge_on_review_cap: bool = DEFAULT_MERGE_ON_REVIEW_CAP,
    fabro_timeout_seconds: float = DEFAULT_FABRO_TIMEOUT_SECONDS,
    acp_nodes: AcpNodeResolution | None = None,
) -> DispatchPlan:
    """Resolve the per-item dispatch plan (publish branch, argv config)."""
    return DispatchPlan(
        repo=repo,
        work_item_id=work_item_id,
        branch=f"feat/{work_item_id}",
        workflow_toml=workflow_toml,
        goal_file=goal_file,
        fabro_bin=fabro_bin,
        fabro_factory_name=fabro_factory_name,
        fabro_factory_server=fabro_factory_server,
        fabro_factory_dev_token=fabro_factory_dev_token,
        janitor=janitor_argv(check_suite=resolve_janitor_check_suite(cwd=repo, janitor=janitor)),
        janitor_checkout=janitor_checkout,
        janitor_core_checkout=janitor_core_checkout_path(janitor_checkout=janitor_checkout),
        janitor_core_repo_url=janitor_core_repo_url,
        janitor_core_ref=janitor_core_ref,
        review_fix_visit_cap=review_fix_cap + 1,
        merge_on_review_cap_outcome=(
            "succeeded" if merge_on_review_cap else _MERGE_ON_REVIEW_CAP_DISABLED_OUTCOME
        ),
        fabro_timeout_seconds=fabro_timeout_seconds,
        acp_nodes=acp_nodes,
    )
