"""The workflow-variant registry policy: what the table means, and which name wins.

`_workflow_variants` is the pure half of the named-variant registry —
`dispatcher.workflows`, `dispatcher.default_workflow`, and the reserved
`implement-work-item` name. It is deliberately TOTAL: every precedence arm
returns a `WorkflowVariant`, and the three faults that must refuse a dispatch
are the dispatch-time seam's job (`test_dispatcher_workflow_variant.py`), not
this module's. What is asserted here is therefore the precedence itself, plus
the two properties the refusals depend on being able to observe:

- the reserved name ALWAYS resolves with `directory is None`, whatever the
  registry says — the mechanical half of "never read from the registry"; and
- any OTHER name resolving with `directory is None` means the registry does
  not define it, which is the signal the unregistered-name refusal reads.
"""

from __future__ import annotations

from typing import Any

from livespec_orchestrator_beads_fabro.commands._workflow_variants import (
    RESERVED_WORKFLOW_NAME,
    WorkflowVariant,
    workflow_registry,
    workflow_variant_from_block,
)

_CODEX_FIRST = ".fabro/workflows/codex-first"
_REVIEW_HEAVY = ".fabro/workflows/review-heavy"


def _block(**keys: Any) -> dict[str, Any]:
    return dict(keys)


def test_reserved_name_is_the_shipped_workflow_directory_name() -> None:
    """The reserved name is the one `_dispatcher_paths` builds its subpath from."""
    assert RESERVED_WORKFLOW_NAME == "implement-work-item"


def test_registry_is_empty_for_a_target_that_declares_none() -> None:
    """An absent `dispatcher.workflows` is an answer, not a fault."""
    assert workflow_registry(block={}) == {}


def test_registry_is_empty_for_a_non_table_value() -> None:
    """A `workflows` key that is not a table declares no variants."""
    assert workflow_registry(block=_block(workflows="codex-first")) == {}


def test_registry_drops_entries_with_unusable_directories() -> None:
    """A non-string or empty directory is indistinguishable from an absent entry.

    Dropping it here is what lets the refusal name the SELECTED variant rather
    than a table row the operator may never have selected.
    """
    registry = workflow_registry(
        block=_block(
            workflows={
                "codex-first": _CODEX_FIRST,
                "empty": "",
                "numeric": 7,
                "nested": {"directory": _REVIEW_HEAVY},
            }
        )
    )

    assert registry == {"codex-first": _CODEX_FIRST}


def test_no_configuration_selects_the_reserved_variant() -> None:
    """The overwhelmingly common case: no registry, no default, reserved name."""
    assert workflow_variant_from_block(block={}) == WorkflowVariant(
        name=RESERVED_WORKFLOW_NAME, directory=None
    )


def test_explicit_name_wins_over_the_configured_default() -> None:
    """An explicitly selected variant outranks `dispatcher.default_workflow`."""
    variant = workflow_variant_from_block(
        block=_block(
            workflows={"codex-first": _CODEX_FIRST, "review-heavy": _REVIEW_HEAVY},
            default_workflow="codex-first",
        ),
        name="review-heavy",
    )

    assert variant == WorkflowVariant(name="review-heavy", directory=_REVIEW_HEAVY)


def test_an_empty_explicit_name_is_no_selection_at_all() -> None:
    """An empty string is an unset argument, not a variant named ``""``."""
    variant = workflow_variant_from_block(
        block=_block(workflows={"codex-first": _CODEX_FIRST}, default_workflow="codex-first"),
        name="",
    )

    assert variant == WorkflowVariant(name="codex-first", directory=_CODEX_FIRST)


def test_configured_default_selects_a_registered_entry() -> None:
    """With no explicit name, a registered `default_workflow` is the selection."""
    variant = workflow_variant_from_block(
        block=_block(workflows={"codex-first": _CODEX_FIRST}, default_workflow="codex-first")
    )

    assert variant == WorkflowVariant(name="codex-first", directory=_CODEX_FIRST)


def test_configured_default_naming_nothing_registered_falls_through() -> None:
    """A default naming an unregistered variant yields the reserved workflow.

    The same shape as `_config`'s `default_factory`: a stale default must not
    fail every dispatch the target makes.
    """
    variant = workflow_variant_from_block(
        block=_block(workflows={"codex-first": _CODEX_FIRST}, default_workflow="retired")
    )

    assert variant == WorkflowVariant(name=RESERVED_WORKFLOW_NAME, directory=None)


def test_configured_default_of_the_wrong_type_falls_through() -> None:
    """A non-string `default_workflow` selects nothing."""
    variant = workflow_variant_from_block(
        block=_block(workflows={"codex-first": _CODEX_FIRST}, default_workflow=["codex-first"])
    )

    assert variant == WorkflowVariant(name=RESERVED_WORKFLOW_NAME, directory=None)


def test_an_unregistered_explicit_name_resolves_without_a_directory() -> None:
    """The signal the unregistered-name refusal reads, produced without refusing."""
    variant = workflow_variant_from_block(
        block=_block(workflows={"codex-first": _CODEX_FIRST}), name="typo-first"
    )

    assert variant == WorkflowVariant(name="typo-first", directory=None)


def test_the_reserved_name_is_never_read_from_the_registry() -> None:
    """A registry entry claiming the reserved name cannot move where it resolves.

    Selected explicitly or reached as the fallback, the reserved variant comes
    back with no directory, so `workflow_toml` still applies its
    target-local-then-bundle rule. The entry itself is refused by the
    dispatch-time seam; this asserts it is INERT even if it were not.
    """
    block = _block(
        workflows={RESERVED_WORKFLOW_NAME: ".fabro/workflows/hijacked"},
        default_workflow=RESERVED_WORKFLOW_NAME,
    )

    explicit = workflow_variant_from_block(block=block, name=RESERVED_WORKFLOW_NAME)
    fallback = workflow_variant_from_block(block=block)

    assert explicit == WorkflowVariant(name=RESERVED_WORKFLOW_NAME, directory=None)
    assert fallback == explicit
