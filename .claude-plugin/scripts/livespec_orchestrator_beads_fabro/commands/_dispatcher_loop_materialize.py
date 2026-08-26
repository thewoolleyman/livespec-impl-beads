"""Materialize WHAT one dispatch will run, before any Fabro run exists.

Split out of `_dispatcher_loop` by cohesion. Two questions share one
answer here and nowhere else: which committed workflow config governs this
dispatch, and what does that workflow resolve to once this target's
configuration is applied to it -- the graph with its node timeouts written
in as literal durations, and every ACP node's adapter resolved through the
three configuration layers. `_dispatcher_loop` is left with the other
concern, driving the dispatch and routing each pre-run refusal.

BOTH STEPS REFUSE BEFORE ANY RUN EXISTS, which is why they belong
together. A non-positive timeout and a node named in `dispatcher.acp_nodes`
that the workflow does not declare are the same KIND of fault -- a config
typo whose only honest discovery point is the dispatch that would
otherwise have gone out carrying a value nobody chose. Each refusal keeps
its own journal stage, so the record still says which of the two failed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._acp_node_layers import AcpNodeResolution
from livespec_orchestrator_beads_fabro.commands._dispatcher_acp_nodes import (
    ACP_NODES_STAGE,
    prepare_acp_nodes,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import JournalWriter
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_plan import (
    workflow_payload_dir,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import workflow_toml
from livespec_orchestrator_beads_fabro.commands._dispatcher_payload import (
    WorkflowPayload,
    prepare_workflow_payload,
)

__all__: list[str] = [
    "MaterializationRefusal",
    "MaterializedDispatch",
    "materialize_dispatch",
]

_WORKFLOW_PAYLOAD_STAGE = "workflow-payload"


@dataclass(frozen=True, kw_only=True)
class MaterializedDispatch:
    """Everything one dispatch runs, resolved from the committed workflow."""

    committed_workflow: Path
    payload: WorkflowPayload
    acp_nodes: AcpNodeResolution


@dataclass(frozen=True, kw_only=True)
class MaterializationRefusal:
    """A pre-run refusal, carrying the journal stage that produced it."""

    stage: str
    detail: str


def materialize_dispatch(
    *,
    args: argparse.Namespace,
    repo: Path,
    work_item_id: str,
    journal: JournalWriter,
) -> MaterializedDispatch | MaterializationRefusal:
    """Resolve this dispatch's workflow payload and ACP adapters, or refuse."""
    # Resolved once and journaled: `workflow_toml` now picks the dispatch
    # target's OWN committed workflow over the plugin's bundled default, and
    # that config carries the sandbox image pin — so which file won is the
    # first thing to read when a dispatch dies on a missing toolchain. The
    # payload materializer then renders THIS dispatch's resolved node
    # timeouts into a per-run copy of that workflow's graph as literal
    # durations; a config typo refuses here, before any Fabro run exists.
    committed_workflow = workflow_toml(args=args)
    payload = prepare_workflow_payload(
        repo=repo,
        committed=committed_workflow,
        payload_dir=workflow_payload_dir(work_item_id=work_item_id),
        journal=journal,
        work_item_id=work_item_id,
    )
    if isinstance(payload, str):
        return MaterializationRefusal(stage=_WORKFLOW_PAYLOAD_STAGE, detail=payload)
    # Every ACP node's adapter, resolved through the workflow's own declared
    # defaults, the target's `dispatcher.acp_nodes` / `codex_models` block and
    # this dispatch's `--acp-node` arguments, then journaled with the layer
    # behind each field. A node named in configuration but absent from the
    # workflow refuses HERE, before any Fabro run exists — the alternative is
    # a run that silently carries the default the operator meant to replace.
    #
    # `acp_node` is read defensively: only the dispatching subparsers define
    # it, and the reconcile and check subcommands reach this code with a
    # Namespace that never carried the argument.
    acp_nodes = prepare_acp_nodes(
        repo=repo,
        committed=committed_workflow,
        overrides=tuple(getattr(args, "acp_node", None) or ()),
        journal=journal,
        work_item_id=work_item_id,
    )
    if isinstance(acp_nodes, str):
        return MaterializationRefusal(stage=ACP_NODES_STAGE, detail=acp_nodes)
    return MaterializedDispatch(
        committed_workflow=committed_workflow,
        payload=payload,
        acp_nodes=acp_nodes,
    )
