"""The master-CI pipeline AS THE PREFLIGHT READS IT: two resolved names and their origin.

This is a PROJECTION of the typed repository-integration contract, not a
resolver. `_dispatcher_integration_resolver` answers what
`dispatcher.master_ci.workflow` and `.job` resolve to; this module shapes those
two answers into the pair the preflight looks up and the sentence a refusal
prints. The split is the point of the whole contract: what an integration point
RESOLVES TO is one generic rule, and what one consumer needs it SHAPED AS is that
consumer's own business.

WHY THE PIPELINE IS DECLARED AT ALL. The shipped preflight hard-coded the
workflow display name `CI` and the aggregate job `ci-green` -- this fleet's own
naming convention, silently assumed of every adopter. A conforming repository
whose aggregate workflow is named anything else was therefore PERMANENTLY
unprovable, and the retired fail-open branches hid that by proceeding unchecked.
The committed `dispatcher.master_ci` key makes the topology a DECLARATION and the
convention a DECLARED DEFAULT rather than a silent assumption: every
unresolvable-pipeline refusal names which of the two resolutions was attempted
and names the key that declares it, so an adopter can tell "your pipeline is red"
apart from "I looked for a workflow you do not have".

ONLY AN ABSENT KEY FALLS BACK, and BOTH HALVES ARE REQUIRED ONCE THE BLOCK IS
DECLARED. A key that is PRESENT but unusable -- not a mapping, or naming only
half the pipeline, or carrying a non-string or empty name -- is a DEFECT, never a
silent slide onto the convention. Falling back there takes the adopter's own
statement that `CI`/`ci-green` is the wrong target and proves that target green
anyway, so a typo in a declared workflow name would admit a dispatch on an
UNRELATED pipeline's evidence. That rule is no longer written here: it is the
schema's `parent_key` on both halves, applied by the one generic resolver.

Declaration changes WHAT is looked up, never WHETHER absence of proof refuses
(`SPECIFICATION/contracts.md`, the master-CI pipeline resolution clause).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from livespec_orchestrator_beads_fabro.commands._config import dispatcher_block
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_declaration import (
    declaration_from_dispatcher_block,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    MASTER_CI_JOB_DEFAULT,
    MASTER_CI_WORKFLOW_DEFAULT,
    UNRESOLVED_NAME,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Defective,
    is_declared,
    resolve_integration_field,
    resolved_name,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    MASTER_CI_JOB_FIELD,
    MASTER_CI_KEY,
    MASTER_CI_WORKFLOW_FIELD,
)

__all__: list[str] = [
    "DECLARED_RESOLUTION",
    "DEFAULT_JOB",
    "DEFAULT_RESOLUTION",
    "DEFAULT_WORKFLOW",
    "MASTER_CI_KEY",
    "UNRESOLVED_NAME",
    "MasterCiPipeline",
    "master_ci_pipeline_from_block",
    "pipeline_resolution_sentence",
    "resolve_master_ci_pipeline",
]

DEFAULT_WORKFLOW = MASTER_CI_WORKFLOW_DEFAULT
DEFAULT_JOB = MASTER_CI_JOB_DEFAULT

DECLARED_RESOLUTION = "declared"
DEFAULT_RESOLUTION = "default"


@dataclass(frozen=True, kw_only=True)
class MasterCiPipeline:
    """The workflow and aggregate job the preflight proves green, plus its origin.

    `resolution` is `declared` when the committed key supplied the names and
    `default` when the convention did. It is carried rather than re-derived
    because the refusal text and the journal record both have to say which
    resolution was attempted, and a second derivation could disagree with the
    first.

    `defect` names what is wrong with a PRESENT declaration, and is `None` on
    every usable pipeline. A defective pipeline still reports `declared` as its
    attempted resolution -- the adopter did declare, the declaration is just not
    readable -- so the refusal names the key the operator has to go and fix
    rather than blaming the convention it never chose.
    """

    workflow: str
    job: str
    resolution: str
    defect: str | None = None


def resolve_master_ci_pipeline(*, cwd: Path) -> MasterCiPipeline:
    """Resolve the dispatch target's pipeline from its committed `.livespec.jsonc`.

    An absent key is an ANSWER — this repository uses the convention — so it
    rides the same block reader as every other dispatcher key rather than a
    special absent-file path of its own.
    """
    return master_ci_pipeline_from_block(block=dispatcher_block(cwd=cwd))


def master_ci_pipeline_from_block(*, block: dict[str, Any]) -> MasterCiPipeline:
    """Project a `dispatcher` block's two pipeline fields into the preflight's pair."""
    declaration = declaration_from_dispatcher_block(block=block)
    workflow = resolve_integration_field(field=MASTER_CI_WORKFLOW_FIELD, declaration=declaration)
    job = resolve_integration_field(field=MASTER_CI_JOB_FIELD, declaration=declaration)
    defects = tuple(
        dict.fromkeys(
            resolution.reason for resolution in (workflow, job) if isinstance(resolution, Defective)
        )
    )
    if defects:
        # No names resolved at all: a half-usable declaration is not half a
        # pipeline to prove green, it is a pipeline nobody named.
        return MasterCiPipeline(
            workflow=UNRESOLVED_NAME,
            job=UNRESOLVED_NAME,
            resolution=DECLARED_RESOLUTION,
            defect="; ".join(defects),
        )
    return MasterCiPipeline(
        workflow=resolved_name(resolution=workflow),
        job=resolved_name(resolution=job),
        resolution=DECLARED_RESOLUTION if is_declared(resolution=workflow) else DEFAULT_RESOLUTION,
    )


def pipeline_resolution_sentence(*, pipeline: MasterCiPipeline) -> str:
    """One line naming the attempted resolution and the key that declares it."""
    if pipeline.defect is not None:
        return (
            f"Resolution attempted: declared, from the committed `{MASTER_CI_KEY}` key, "
            f"which is present but unusable: {pipeline.defect}. A present declaration "
            "is never completed from the default convention, because that would prove "
            "a pipeline this repository has said is not its own."
        )
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
