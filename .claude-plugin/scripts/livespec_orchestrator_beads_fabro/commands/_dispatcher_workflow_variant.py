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

THE FOURTH REFUSAL, ratified in v100, is about the ITEM rather than the
registry: an apply dispatch of a work-item carrying an approved groom draft,
resolving to anything other than a registered groom variant. It belongs here
rather than beside the groom door because the door and the apply dispatch are
two SEPARATE dispatches of the same item, and every route between them can
change which graph runs -- an explicit `--workflow-name` naming the reserved
workflow or an implement variant, or a pin cleared so the selection falls
through to `dispatcher.default_workflow`. The consequence of not refusing is
the expensive one: the implement graph would run against a groomed epic
carrying an approved cut in place of an acceptance, and would try to build it.

WHY THE ITEM'S OWN DRAFT COMMENT IS WHAT ARMS IT, and not the item's pin. The
pin is exactly what the third route above CLEARS, so a gate keyed on the pin
would be disarmed by one of the three substitutions it exists to refuse. The
draft comment cannot be cleared -- a ledger comment is append-only -- so it is
the one signal that survives every route.

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
from livespec_orchestrator_beads_fabro.commands._workflow_variant_kind import (
    groom_variant_names,
    is_groom_variant,
)
from livespec_orchestrator_beads_fabro.commands._workflow_variants import (
    RESERVED_WORKFLOW_NAME,
    WorkflowVariant,
    workflow_registry,
)

__all__: list[str] = [
    "WORKFLOW_VARIANT_INCOMPLETE_STAGE",
    "WORKFLOW_VARIANT_NOT_GROOM_STAGE",
    "WORKFLOW_VARIANT_RESERVED_NAME_STAGE",
    "WORKFLOW_VARIANT_UNREGISTERED_STAGE",
    "WorkflowVariantRefusal",
    "prepare_workflow_variant",
]

# One stage per cause, so the journal names WHICH fault refused the dispatch
# without a reader having to parse the detail string back out.
WORKFLOW_VARIANT_UNREGISTERED_STAGE = "workflow-variant-unregistered"
WORKFLOW_VARIANT_INCOMPLETE_STAGE = "workflow-variant-incomplete"
WORKFLOW_VARIANT_RESERVED_NAME_STAGE = "workflow-variant-reserved-name"
WORKFLOW_VARIANT_NOT_GROOM_STAGE = "workflow-variant-not-groom"

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
    approved_groom_draft: str | None = None,
) -> WorkflowVariant | WorkflowVariantRefusal:
    """Resolve the variant this dispatch runs, or refuse before any run exists.

    Returns the resolved variant, or a refusal the caller reports as a failed
    dispatch under the refusal's own stage. The reserved-name conflict is
    checked FIRST because it is a fault of the registry itself: it holds
    however the selection resolves, and reporting it as "variant X is
    unregistered" would name the wrong entry.

    `approved_groom_draft` names the variant that drafted the approved cut this
    work-item carries, when it carries one; the caller reads it off the item's
    ledger comments. The apply gate it arms is checked LAST, after the
    selection has been proved registered and complete, because an incomplete
    directory reads as an `implement` variant -- so checking the kind first
    would report "not a groom variant" for a directory whose real fault is that
    half of it is missing.
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
    selection = _selection_refusal(repo=repo, variant=variant, registry=registry)
    if selection is not None:
        return selection
    if approved_groom_draft is not None and not is_groom_variant(repo=repo, variant=variant):
        return WorkflowVariantRefusal(
            stage=WORKFLOW_VARIANT_NOT_GROOM_STAGE,
            detail=(
                f"the work-item carries an approved groom draft from variant "
                f"{approved_groom_draft!r} awaiting its apply dispatch, and the selected "
                f"workflow {variant.name!r} is not a registered groom variant "
                f"(groom variants: {_names(names=groom_variant_names(repo=repo))})"
            ),
        )
    return variant


def _selection_refusal(
    *,
    repo: Path,
    variant: WorkflowVariant,
    registry: Mapping[str, str],
) -> WorkflowVariantRefusal | None:
    """The two faults of the SELECTION, in order; None when it resolves cleanly.

    The reserved variant resolves no registry directory and is therefore never
    either of these faults -- it is the one name that is always defined -- so it
    falls straight through to the apply gate the caller checks next.
    """
    if variant.directory is None:
        if variant.name == RESERVED_WORKFLOW_NAME:
            return None
        return WorkflowVariantRefusal(
            stage=WORKFLOW_VARIANT_UNREGISTERED_STAGE,
            detail=(
                f"workflow variant {variant.name!r} is not defined by dispatcher.workflows "
                f"(registered: {_names(names=tuple(sorted(registry)))})"
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
    return None


def _missing_variant_files(*, directory: Path) -> tuple[str, ...]:
    return tuple(name for name in _REQUIRED_VARIANT_FILES if not (directory / name).is_file())


def _names(*, names: tuple[str, ...]) -> str:
    """Render a name list for a refusal, saying `none` rather than nothing at all."""
    return ", ".join(names) if names != () else "none"
