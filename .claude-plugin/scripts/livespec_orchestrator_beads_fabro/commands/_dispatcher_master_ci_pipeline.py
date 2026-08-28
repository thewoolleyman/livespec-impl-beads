"""What the master-CI preflight looks up: the pipeline the repository DECLARES.

Split out of `_dispatcher_master_ci_preflight` for the same reason
`_node_timeouts` is split out of `_config`: WHAT is looked up is a declared
property of the repository, and the record of why a default exists belongs
beside its own resolver rather than inside the classification that consumes it.

WHY THE PIPELINE IS DECLARED AT ALL. The shipped preflight hard-coded the
workflow display name `CI` and the aggregate job `ci-green` -- this repo's own
naming convention, silently assumed of every adopter. A conforming repository
whose aggregate workflow is named anything else was therefore PERMANENTLY
unprovable, and the retired fail-open branches hid that by proceeding unchecked.
The committed `dispatcher.master_ci` key makes the topology a DECLARATION and
the convention a DECLARED DEFAULT rather than a silent assumption: every
unresolvable-pipeline refusal names which of the two resolutions was attempted
and names the key that declares it, so an adopter can tell "your pipeline is
red" apart from "I looked for a workflow you do not have".

Declaration changes WHAT is looked up, never WHETHER absence of proof refuses
(`SPECIFICATION/contracts.md`, the master-CI pipeline resolution clause).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from livespec_orchestrator_beads_fabro.commands._config import dispatcher_block

__all__: list[str] = [
    "DECLARED_RESOLUTION",
    "DEFAULT_JOB",
    "DEFAULT_RESOLUTION",
    "DEFAULT_WORKFLOW",
    "MASTER_CI_KEY",
    "MasterCiPipeline",
    "master_ci_pipeline_from_block",
    "pipeline_resolution_sentence",
    "resolve_master_ci_pipeline",
]

# The committed key that declares the topology, named verbatim in every
# unresolvable-pipeline refusal so the reader knows where to write the answer.
MASTER_CI_KEY = "dispatcher.master_ci"

DEFAULT_WORKFLOW = "CI"
DEFAULT_JOB = "ci-green"

DECLARED_RESOLUTION = "declared"
DEFAULT_RESOLUTION = "default"

_MASTER_CI_BLOCK = "master_ci"
_WORKFLOW_KEY = "workflow"
_JOB_KEY = "job"


@dataclass(frozen=True, kw_only=True)
class MasterCiPipeline:
    """The workflow and aggregate job the preflight proves green, plus its origin.

    `resolution` is `declared` when the committed key supplied the names and
    `default` when the convention did. It is carried rather than re-derived
    because the refusal text and the journal record both have to say which
    resolution was attempted, and a second derivation could disagree with the
    first.
    """

    workflow: str
    job: str
    resolution: str


def resolve_master_ci_pipeline(*, cwd: Path) -> MasterCiPipeline:
    """Resolve the dispatch target's pipeline from its committed `.livespec.jsonc`.

    An absent key is an ANSWER — this repository uses the convention — so it
    rides the same block reader as every other dispatcher key rather than a
    special absent-file path of its own.
    """
    return master_ci_pipeline_from_block(block=dispatcher_block(cwd=cwd))


def master_ci_pipeline_from_block(*, block: dict[str, Any]) -> MasterCiPipeline:
    """Resolve the pipeline from a `dispatcher` block; absent key -> the convention."""
    raw = block.get(_MASTER_CI_BLOCK)
    if not isinstance(raw, dict):
        return MasterCiPipeline(
            workflow=DEFAULT_WORKFLOW,
            job=DEFAULT_JOB,
            resolution=DEFAULT_RESOLUTION,
        )
    declared = cast("dict[str, Any]", raw)
    return MasterCiPipeline(
        workflow=_declared_name(block=declared, key=_WORKFLOW_KEY, default=DEFAULT_WORKFLOW),
        job=_declared_name(block=declared, key=_JOB_KEY, default=DEFAULT_JOB),
        resolution=DECLARED_RESOLUTION,
    )


def pipeline_resolution_sentence(*, pipeline: MasterCiPipeline) -> str:
    """One line naming the attempted resolution and the key that declares it."""
    if pipeline.resolution == DECLARED_RESOLUTION:
        return (
            f"Resolution attempted: declared, from the committed `{MASTER_CI_KEY}` key "
            f"(workflow `{pipeline.workflow}`, aggregate job `{pipeline.job}`)."
        )
    return (
        f"Resolution attempted: default convention (workflow `{pipeline.workflow}`, "
        f"aggregate job `{pipeline.job}`); declare this repository's own pipeline "
        f"under the committed `{MASTER_CI_KEY}` key."
    )


def _declared_name(*, block: dict[str, Any], key: str, default: str) -> str:
    value = block.get(key)
    if isinstance(value, str) and value != "":
        return value
    return default
