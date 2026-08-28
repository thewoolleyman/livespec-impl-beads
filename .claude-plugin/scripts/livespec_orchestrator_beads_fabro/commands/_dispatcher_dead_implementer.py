"""Dead-implementer truncation records for the Dispatcher.

The workflow's dead-implementer circuit breaker (C5) is the CONTAINMENT half:
it routes an unchanged tree to a terminal node before janitor, review and
disposition, so a dead implementer cannot spend a second vendor's allowance.
This module is the OBSERVABILITY half required by the provider-spend-containment
contract in `SPECIFICATION/contracts.md` — a truncation is an auto-disposition
and MUST NOT be silent.

The obligation is deliberately narrower than the containment-refusal one. A
refusal is governed by an exhaustion record, so it always has a provider and
an expiry to name. A truncation fires on ANY implementer termination that
produced no change to the worktree — a provider ceiling, a crash, a malformed
configuration — so no record need exist and the minimum is the work-item id
plus the governing condition.

The breaker announces itself through a stderr SENTINEL rather than through a
typed field, because a Fabro node script's only channel back to the Dispatcher
is its output. Two conditions reach the same terminal node, and they are not
the same fact: an unchanged tree is a proven absence of work, while a failed
diff command is an INABILITY TO PROVE either way that the breaker fails closed
on. Journaling one condition for both would report a measurement where only a
refusal to guess exists, so the two are named separately. The check-failed
sentinel is matched FIRST because the unchanged-tree sentinel is its prefix.
"""

from __future__ import annotations

from typing import Protocol

__all__: list[str] = [
    "DEAD_IMPLEMENTER_SENTINEL",
    "DEAD_IMPLEMENTER_TRUNCATION_STAGE",
    "dead_implementer_condition_from_text",
    "record_dead_implementer_truncation_if_observed",
]

DEAD_IMPLEMENTER_SENTINEL = "LIVESPEC_DEAD_IMPLEMENTER"
DEAD_IMPLEMENTER_TRUNCATION_STAGE = "dead-implementer-truncation"

_CHECK_FAILED_SENTINEL = "LIVESPEC_DEAD_IMPLEMENTER_CHECK_FAILED"
_UNCHANGED_TREE_CONDITION = "dead_implementer_unchanged_tree"
_DIFF_UNPROVABLE_CONDITION = "dead_implementer_diff_unprovable"


class _Journal(Protocol):
    def append(self, *, record: dict[str, object]) -> None:
        """Persist one journal record."""
        ...


class _Outcome(Protocol):
    @property
    def work_item_id(self) -> str:
        """Ledger id for the dispatch outcome."""
        ...

    @property
    def dead_implementer_condition(self) -> str | None:
        """Governing condition of a dead-implementer truncation, else None."""
        ...

    @property
    def fabro_run_id(self) -> str | None:
        """Fabro run the truncation happened in, when one was parsed."""
        ...


def dead_implementer_condition_from_text(*, text: str) -> str | None:
    """The governing condition a run's output announces, or None for no truncation."""
    if _CHECK_FAILED_SENTINEL in text:
        return _DIFF_UNPROVABLE_CONDITION
    if DEAD_IMPLEMENTER_SENTINEL in text:
        return _UNCHANGED_TREE_CONDITION
    return None


def record_dead_implementer_truncation_if_observed(
    *,
    outcome: _Outcome,
    journal: _Journal,
) -> None:
    """Journal the truncation under its own stage, so it is not an ordinary failure.

    A truncated run and an ordinary implementer failure share the `fabro-run`
    stage and a `failed` status, so the generic outcome record cannot tell them
    apart. This second record carries a stage of its own and the governing
    condition, which is what makes the containment auditable.
    """
    condition = outcome.dead_implementer_condition
    if condition is None:
        return
    journal.append(
        record={
            "stage": DEAD_IMPLEMENTER_TRUNCATION_STAGE,
            "work_item_id": outcome.work_item_id,
            "governing_condition": condition,
            "fabro_run_id": outcome.fabro_run_id,
        }
    )
