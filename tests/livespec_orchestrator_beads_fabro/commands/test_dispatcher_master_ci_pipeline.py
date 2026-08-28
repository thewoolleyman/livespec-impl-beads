"""Focused tests for declared master-CI pipeline resolution.

The module is imported through `importlib` inside each test body, behind a
`is_file()` assertion, so the first failing assertion is a genuine claim about
the extraction rather than a collection-time `ModuleNotFoundError`.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Protocol, cast

_MODULE_PATH = (
    Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
    / "_dispatcher_master_ci_pipeline.py"
)
_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._dispatcher_master_ci_pipeline"


class _Pipeline(Protocol):
    workflow: str
    job: str
    resolution: str
    defect: str | None


class _PipelineModule(Protocol):
    MASTER_CI_KEY: str
    DEFAULT_WORKFLOW: str
    DEFAULT_JOB: str
    DECLARED_RESOLUTION: str
    DEFAULT_RESOLUTION: str
    UNRESOLVED_NAME: str

    def master_ci_pipeline_from_block(self, *, block: dict[str, Any]) -> _Pipeline:
        """Resolve the pipeline from a dispatcher block."""

    def pipeline_resolution_sentence(self, *, pipeline: _Pipeline) -> str:
        """Name the attempted resolution and the declaring key."""


def _module() -> _PipelineModule:
    assert _MODULE_PATH.is_file()
    return cast("_PipelineModule", importlib.import_module(_MODULE_NAME))


def test_an_absent_key_resolves_the_default_convention() -> None:
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(block={"wip_cap": 3})

    assert pipeline.workflow == "CI"
    assert pipeline.job == "ci-green"
    assert pipeline.resolution == module.DEFAULT_RESOLUTION
    assert pipeline.defect is None


def test_a_non_mapping_key_is_a_defect_and_never_the_convention() -> None:
    """ONLY an absent key falls back; a present one that names nothing is a defect.

    The discriminating assertion is on the resolved NAMES, not on the defect
    alone: the retired behaviour returned the convention's `CI`/`ci-green` here,
    so a pipeline still carrying those names would prove an unrelated workflow
    green on the strength of a typo.
    """
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(block={"master_ci": "CI"})

    assert pipeline.defect is not None
    assert (pipeline.workflow, pipeline.job) == (
        module.UNRESOLVED_NAME,
        module.UNRESOLVED_NAME,
    )
    assert pipeline.resolution == module.DECLARED_RESOLUTION


def test_a_null_declaration_is_a_defect_rather_than_an_absent_key() -> None:
    """JSON `null` is a PRESENT declaration naming nothing, not an absent key."""
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(block={"master_ci": None})

    assert pipeline.defect is not None
    assert pipeline.workflow == module.UNRESOLVED_NAME


def test_a_declared_key_resolves_both_declared_names() -> None:
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(
        block={"master_ci": {"workflow": "build.yml", "job": "all-green"}}
    )

    assert pipeline.workflow == "build.yml"
    assert pipeline.job == "all-green"
    assert pipeline.resolution == module.DECLARED_RESOLUTION
    assert pipeline.defect is None


def test_an_empty_declared_workflow_is_a_defect_not_a_defaulted_half() -> None:
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(
        block={"master_ci": {"workflow": "", "job": "all-green"}}
    )

    assert pipeline.defect is not None
    assert "workflow" in pipeline.defect
    assert "not a non-empty string" in pipeline.defect
    assert (pipeline.workflow, pipeline.job) == (
        module.UNRESOLVED_NAME,
        module.UNRESOLVED_NAME,
    )


def test_an_absent_declared_workflow_is_a_defect_naming_the_missing_half() -> None:
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(block={"master_ci": {"job": "all-green"}})

    assert pipeline.defect is not None
    assert "workflow` is absent" in pipeline.defect
    assert pipeline.job == module.UNRESOLVED_NAME


def test_a_non_string_declared_job_is_a_defect() -> None:
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(
        block={"master_ci": {"workflow": "build.yml", "job": 7}}
    )

    assert pipeline.defect is not None
    assert "job` is present but is not a non-empty string" in pipeline.defect
    assert pipeline.workflow == module.UNRESOLVED_NAME


def test_an_absent_declared_job_is_a_defect_naming_the_missing_half() -> None:
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(block={"master_ci": {"workflow": "build.yml"}})

    assert pipeline.defect is not None
    assert "job` is absent" in pipeline.defect


def test_the_defective_sentence_names_the_declared_resolution_the_key_and_the_defect() -> None:
    module = _module()
    pipeline = module.master_ci_pipeline_from_block(block={"master_ci": {"job": "all-green"}})

    sentence = module.pipeline_resolution_sentence(pipeline=pipeline)

    assert "Resolution attempted: declared" in sentence
    assert module.MASTER_CI_KEY in sentence
    assert "unusable" in sentence
    assert module.DEFAULT_WORKFLOW not in sentence
    assert module.DEFAULT_JOB not in sentence


def test_the_declared_sentence_names_the_resolution_and_the_key() -> None:
    module = _module()
    pipeline = module.master_ci_pipeline_from_block(
        block={"master_ci": {"workflow": "build.yml", "job": "all-green"}}
    )

    sentence = module.pipeline_resolution_sentence(pipeline=pipeline)

    assert "declared" in sentence
    assert module.MASTER_CI_KEY in sentence
    assert "build.yml" in sentence
    assert "all-green" in sentence


def test_the_default_sentence_names_the_convention_and_the_key() -> None:
    module = _module()
    pipeline = module.master_ci_pipeline_from_block(block={})

    sentence = module.pipeline_resolution_sentence(pipeline=pipeline)

    assert "default convention" in sentence
    assert module.MASTER_CI_KEY in sentence
    assert "ci-green" in sentence
