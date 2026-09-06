"""Select one dispatch's workflow variant, refusing before any Fabro run exists.

`_workflow_variants` owns the precedence and stays total; this module is where
a registry that cannot be honoured becomes a REFUSAL. It sits beside
`_dispatcher_acp_nodes` and the payload materializer in
`_dispatcher_loop_materialize`, and takes the same shape they do: a pre-run
refusal carrying its own journal stage, so the dispatch record says which of
the resolution steps failed rather than reporting one undifferentiated
"dispatch did not start".

THE THREE REFUSALS, and why each is a refusal rather than a fallback:

- A selected name no registry entry defines. Falling back to the reserved
  workflow would run a DIFFERENT graph under the name the operator asked for,
  and nothing in the run would say so.
- A registered directory missing `workflow.toml` or `workflow.fabro`. A
  variant is a whole directory, never a partial overlay merged with the
  bundle, so an incomplete one has no honest completion.
- A registry entry named `implement-work-item`. The reserved name resolves
  through the target-local-then-bundle rule and never from the registry, so
  such an entry is silently inert -- the operator's edit would have no effect
  at all, which is the failure mode hardest to discover from a run.

These are NOT `Defective` schema points and deliberately do not take the
schema-validation exit-3 path: `dispatcher.workflows` and
`dispatcher.default_workflow` are optional target-declared capabilities in the
class of `dispatcher.acp_nodes`, not fields of the repository integration
contract's closed schema.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._config import (
    dispatcher_block,
    resolve_workflow_variant,
)
from livespec_orchestrator_beads_fabro.commands._workflow_variants import (
    RESERVED_WORKFLOW_NAME,
    WorkflowVariant,
    workflow_registry,
)

__all__: list[str] = [
    "WORKFLOW_VARIANT_INCOMPLETE_STAGE",
    "WORKFLOW_VARIANT_RESERVED_NAME_STAGE",
    "WORKFLOW_VARIANT_UNREGISTERED_STAGE",
    "WorkflowVariantRefusal",
    "prepare_workflow_variant",
]

# One stage per cause, so the journal names WHICH registry fault refused the
# dispatch without a reader having to parse the detail string back out.
WORKFLOW_VARIANT_UNREGISTERED_STAGE = "workflow-variant-unregistered"
WORKFLOW_VARIANT_INCOMPLETE_STAGE = "workflow-variant-incomplete"
WORKFLOW_VARIANT_RESERVED_NAME_STAGE = "workflow-variant-reserved-name"

# What makes a registered directory a COMPLETE workflow rather than a partial
# overlay. The prompt files are not listed: the graph references them
# relatively and a missing one surfaces as the graph's own unresolved
# reference, whereas a missing graph or manifest has no such downstream report.
_REQUIRED_VARIANT_FILES = ("workflow.toml", "workflow.fabro")


@dataclass(frozen=True, kw_only=True)
class WorkflowVariantRefusal:
    """A pre-run refusal, carrying the journal stage that names its cause."""

    stage: str
    detail: str


def prepare_workflow_variant(
    *,
    repo: Path,
    name: str | None = None,
) -> WorkflowVariant | WorkflowVariantRefusal:
    """Resolve the variant this dispatch runs, or refuse before any run exists.

    Returns the resolved variant, or a refusal the caller reports as a failed
    dispatch under the refusal's own stage. The reserved-name conflict is
    checked FIRST because it is a fault of the registry itself: it holds
    however the selection resolves, and reporting it as "variant X is
    unregistered" would name the wrong entry.
    """
    registry = workflow_registry(block=dispatcher_block(cwd=repo))
    if RESERVED_WORKFLOW_NAME in registry:
        return WorkflowVariantRefusal(
            stage=WORKFLOW_VARIANT_RESERVED_NAME_STAGE,
            detail=(
                f"dispatcher.workflows registers {RESERVED_WORKFLOW_NAME!r}, which is the "
                "reserved workflow name and cannot be redefined; rename the entry"
            ),
        )
    variant = resolve_workflow_variant(cwd=repo, name=name)
    if variant.directory is None:
        if variant.name == RESERVED_WORKFLOW_NAME:
            return variant
        return WorkflowVariantRefusal(
            stage=WORKFLOW_VARIANT_UNREGISTERED_STAGE,
            detail=(
                f"workflow variant {variant.name!r} is not defined by dispatcher.workflows "
                f"(registered: {_registered_names(registry=registry)})"
            ),
        )
    missing = _missing_variant_files(directory=repo / variant.directory)
    if missing != ():
        return WorkflowVariantRefusal(
            stage=WORKFLOW_VARIANT_INCOMPLETE_STAGE,
            detail=(
                f"workflow variant {variant.name!r} at {variant.directory} is not a complete "
                f"workflow: missing {', '.join(missing)}"
            ),
        )
    return variant


def _missing_variant_files(*, directory: Path) -> tuple[str, ...]:
    return tuple(name for name in _REQUIRED_VARIANT_FILES if not (directory / name).is_file())


def _registered_names(*, registry: Mapping[str, str]) -> str:
    return ", ".join(sorted(registry)) if registry != {} else "none"
