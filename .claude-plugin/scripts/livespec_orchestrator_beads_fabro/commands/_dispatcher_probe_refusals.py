"""The three refusals that bracket every loop-probe invocation.

They are grouped because they share one property the rest of the probe does
not: each must fire BEFORE any store mutation, journal write, or driven cycle.
A refusal that fired later would itself have performed the act it exists to
prevent, so their position in the entry point is as load-bearing as their text.

IT TAKES; IT NEVER FILES. The probe refuses without `--item` and creates,
files, or clones NOTHING under any circumstances. The designated item is filed
by the operator through `capture-work-item`, where consent and
Definition-of-Ready evaluation are native. A health command that could file its
own fixture would be an unconsented intake path wearing a diagnostic's name --
which is why this refusal sits above even identity resolution.

IT REFUSES AN ITEM IT CANNOT DRIVE TO DONE. Under the default `ai-then-human`
policy a passing item PARKS in `acceptance` awaiting the human valve, so
terminal `done` is machine-reachable only for an `ai-only` item. Refusing early
and NAMING THE LABEL is the difference between an operator fixing one label at
filing time and an operator watching a probe hang on a gate it can never open.
The probe sets nothing itself: granting that policy is the operator's act.

AN UNATTRIBUTED PROBE PROVES NOTHING ABOUT ATTRIBUTION. A probe is an operator
act, so a fallback-derived identity fails it rather than being journaled as
though someone had claimed it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.unsafe import unsafe_perform_io

from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import (
    FALLBACK_SOURCE,
    INVOKER_ENV_VAR,
    INVOKER_FLAG,
    InvokerIdentity,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_policy_settings import (
    DEFAULT_ACCEPTANCE_POLICY,
    effective_acceptance_policy,
)

if TYPE_CHECKING:
    from pathlib import Path

    from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "AI_ONLY_POLICY",
    "PROBE_ACCEPTANCE_LABEL",
    "acceptance_policy_refusal",
    "designated_item_refusal",
    "fallback_invoker_refusal",
]

AI_ONLY_POLICY = "ai-only"
PROBE_ACCEPTANCE_LABEL = "acceptance:ai-only"


def designated_item_refusal(*, item_id: str | None) -> str | None:
    """Refuse a probe invocation that designates no item, before anything else runs."""
    if item_id is not None and item_id.strip():
        return None
    return (
        "ERROR: probe requires --item <work-item-id>; the probe TAKES a"
        " pre-filed item and never creates, files, or clones one.\n"
        "File the probe item through capture-work-item, where consent and"
        " Definition-of-Ready evaluation are native, then designate it.\n"
    )


def acceptance_policy_refusal(*, item: WorkItem, cwd: Path) -> str | None:
    """Refuse a designated item whose effective acceptance policy is not `ai-only`."""
    policy = unsafe_perform_io(
        effective_acceptance_policy(item=item, cwd=cwd).value_or(DEFAULT_ACCEPTANCE_POLICY)
    )
    if policy == AI_ONLY_POLICY:
        return None
    return (
        f"ERROR: work-item {item.id} has effective acceptance_policy {policy};"
        f" terminal done is machine-reachable only under {AI_ONLY_POLICY}, so a"
        " passing item would park in acceptance awaiting the human valve.\n"
        f"Set the {PROBE_ACCEPTANCE_LABEL} label at filing; the probe sets nothing"
        " itself.\n"
    )


def fallback_invoker_refusal(*, identity: InvokerIdentity) -> str | None:
    """Refuse a probe whose journaled records would carry a fallback-derived identity."""
    if identity.invoker_source != FALLBACK_SOURCE:
        return None
    return (
        "ERROR: the probe asserted no invoker identity (resolved"
        f" {identity.invoker} as {FALLBACK_SOURCE}); a probe is an operator act,"
        " and an unattributed probe proves nothing about attribution.\n"
        f"Pass {INVOKER_FLAG} <id> or set the {INVOKER_ENV_VAR} environment"
        " variable.\n"
    )
