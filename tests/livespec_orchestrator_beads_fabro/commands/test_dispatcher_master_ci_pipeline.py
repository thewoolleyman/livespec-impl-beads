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


class _PipelineModule(Protocol):
    MASTER_CI_KEY: str
    DEFAULT_WORKFLOW: str
    DEFAULT_JOB: str
    DECLARED_RESOLUTION: str
    DEFAULT_RESOLUTION: str

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


def test_a_non_mapping_key_resolves_the_default_convention() -> None:
    """A malformed declaration is not a declaration — it falls to the convention."""
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(block={"master_ci": "CI"})

    assert (pipeline.workflow, pipeline.job) == ("CI", "ci-green")
    assert pipeline.resolution == module.DEFAULT_RESOLUTION


def test_a_declared_key_resolves_both_declared_names() -> None:
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(
        block={"master_ci": {"workflow": "build.yml", "job": "all-green"}}
    )

    assert pipeline.workflow == "build.yml"
    assert pipeline.job == "all-green"
    assert pipeline.resolution == module.DECLARED_RESOLUTION


def test_a_partial_declaration_defaults_the_missing_half_but_stays_declared() -> None:
    module = _module()

    pipeline = module.master_ci_pipeline_from_block(
        block={"master_ci": {"workflow": "", "job": "all-green"}}
    )

    assert pipeline.workflow == module.DEFAULT_WORKFLOW
    assert pipeline.job == "all-green"
    assert pipeline.resolution == module.DECLARED_RESOLUTION


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
