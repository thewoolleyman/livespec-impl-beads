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

ONLY AN ABSENT KEY FALLS BACK. A key that is PRESENT but unusable -- not a
mapping, or naming only half the pipeline, or carrying a non-string or empty
name -- is a DEFECT, never a silent slide onto the convention. The two readings
are not interchangeable: an absent key says "this repository uses the
convention", while a present one says "this repository's pipeline is NOT the
convention" and then fails to say which. Falling back on the second reading
takes the adopter's own statement that `CI`/`ci-green` is the wrong target and
proves that target green anyway -- so a typo in a declared workflow name admits
a dispatch on an UNRELATED pipeline's evidence, which is the fail-open this
clause exists to retire wearing a declaration's clothes. A defective
declaration therefore resolves no names at all and refuses as unprovable.

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
    "UNRESOLVED_NAME",
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

# What a defective declaration resolves its names to. It is a sentinel rather
# than the convention's names precisely because the convention is the wrong
# answer here: a journal record reading `CI` would tell the operator the lookup
# targeted a pipeline they never declared.
UNRESOLVED_NAME = "<unresolved>"

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
    """Resolve the pipeline from a `dispatcher` block; ABSENT key -> the convention.

    Presence is tested with `in` rather than a `get` sentinel because a key
    written as JSON `null` is a present declaration that names nothing, and
    reading it as absent is exactly the fallback this refuses.
    """
    if _MASTER_CI_BLOCK not in block:
        return MasterCiPipeline(
            workflow=DEFAULT_WORKFLOW,
            job=DEFAULT_JOB,
            resolution=DEFAULT_RESOLUTION,
        )
    raw = block[_MASTER_CI_BLOCK]
    if not isinstance(raw, dict):
        return _defective(
            defect=(
                f"`{MASTER_CI_KEY}` is present but is not a mapping naming "
                f"`{_WORKFLOW_KEY}` and `{_JOB_KEY}`"
            )
        )
    declared = cast("dict[str, Any]", raw)
    workflow = declared.get(_WORKFLOW_KEY)
    if not isinstance(workflow, str) or workflow == "":
        return _defective(defect=_name_defect(declared=declared, key=_WORKFLOW_KEY))
    job = declared.get(_JOB_KEY)
    if not isinstance(job, str) or job == "":
        return _defective(defect=_name_defect(declared=declared, key=_JOB_KEY))
    return MasterCiPipeline(workflow=workflow, job=job, resolution=DECLARED_RESOLUTION)


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


def _defective(*, defect: str) -> MasterCiPipeline:
    """A present-but-unusable declaration: no names resolved, and the reason carried."""
    return MasterCiPipeline(
        workflow=UNRESOLVED_NAME,
        job=UNRESOLVED_NAME,
        resolution=DECLARED_RESOLUTION,
        defect=defect,
    )


def _name_defect(*, declared: dict[str, Any], key: str) -> str:
    """Why one declared name is unusable, distinguishing absent from malformed."""
    qualified = f"`{MASTER_CI_KEY}.{key}`"
    if key not in declared:
        return (
            f"{qualified} is absent; a declared pipeline names BOTH `{_WORKFLOW_KEY}` "
            f"and `{_JOB_KEY}`, since defaulting the missing half would prove part of "
            "a pipeline the repository never named"
        )
    return f"{qualified} is present but is not a non-empty string"
