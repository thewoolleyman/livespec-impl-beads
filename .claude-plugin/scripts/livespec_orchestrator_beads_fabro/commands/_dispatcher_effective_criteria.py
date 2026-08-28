"""The one public primitive resolving a work-item's effective acceptance criteria.

The effective-acceptance-criteria clause of `SPECIFICATION/contracts.md`
requires exactly ONE public primitive here, used by every producer and consumer
gate: the capture and groom front-ends' parse display, the entry-to-`ready` wall
(the human `approve` transition), the pre-dispatch wall, and the post-merge
acceptance pass. No surface may re-derive criteria by another path. Before this
module the acceptance pass owned a PRIVATE resolution and no other gate had one
at all, so "the criteria" meant a different thing at each wall — and the two
walls the spec ratifies had nothing to be implemented against.

The resolution order, which is the spec's:

1. The item's MATERIALIZED criteria value — the merged store read in which the
   native `acceptance_criteria` field wins over a metadata-held one, so a
   criteria field written into metadata by an older writer is NOT read as
   absent — when it yields gradeable content. That materialization IS the
   merged read; nothing here re-reads raw metadata separately.
2. Otherwise the item description's "Exit criteria" section (a heading whose
   title case-insensitively equals "Exit criteria"; the section body is the
   criteria text).

The resolved source is reported as exactly one of the two ratified values,
`criteria-field` or `description-exit-criteria`. Gradeability is defined at the
ASSERTION level, so an effective-criteria set is empty when the shipped parser
(`criteria_lines`) yields no assertion — never when a physical-line count
happens to reach zero.

The two walls share `ungradeable_criteria_refusal` deliberately. An item that
the approve valve refuses and an item the pre-dispatch gate refuses are the
same item failing the same test, and a second copy of that test is how the two
gates drift into disagreeing about what "ungradeable" means.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from returns.unsafe import unsafe_perform_io

from livespec_orchestrator_beads_fabro.commands._dispatcher_acceptance_criteria import (
    criteria_lines,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_policy_settings import (
    DEFAULT_ACCEPTANCE_POLICY,
    effective_acceptance_policy,
)

if TYPE_CHECKING:
    from pathlib import Path

    from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "CRITERIA_FIELD_SOURCE",
    "DESCRIPTION_EXIT_CRITERIA_SOURCE",
    "EffectiveCriteria",
    "effective_criteria",
    "pre_dispatch_criteria_refusal",
    "ungradeable_criteria_refusal",
]

CRITERIA_FIELD_SOURCE = "criteria-field"
DESCRIPTION_EXIT_CRITERIA_SOURCE = "description-exit-criteria"

# The two effective `acceptance_policy` values under which a machine grades the
# item. `human-only` is deliberately outside the walls: a human judgement call
# is exactly the case where machine-gradeable criteria are inapplicable.
_AI_DISPOSITIVE_POLICIES = frozenset({"ai-only", "ai-then-human"})
_EXIT_CRITERIA_TITLE = "exit criteria"
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True, kw_only=True)
class EffectiveCriteria:
    """One work-item's resolved criteria text, its source, and its assertions."""

    text: str | None
    source: str
    assertions: tuple[str, ...]

    @property
    def gradeable(self) -> bool:
        """Whether the set carries at least one gradeable assertion."""
        return bool(self.assertions)

    def parse_display(self) -> str:
        """The one-line parse result the capture and groom front-ends display."""
        return (
            f"effective acceptance criteria: {len(self.assertions)} gradeable"
            f" assertion(s) resolved from {self.source}"
        )

    def as_record(self) -> dict[str, object]:
        """The leak-free projection of the parse for a journal or JSON envelope."""
        return {
            "source": self.source,
            "gradeable_assertions": len(self.assertions),
            "gradeable": self.gradeable,
        }


def effective_criteria(*, item: WorkItem) -> EffectiveCriteria:
    """Resolve one item's effective acceptance criteria and report the source.

    The merged criteria value wins whenever it yields gradeable content;
    otherwise the description's "Exit criteria" section is the fallback, and it
    is reported as the source even when that section is absent — the fallback is
    the step that was resolved, and an absent section is an ungradeable result
    rather than a third source value.
    """
    field_assertions = criteria_lines(criteria_text=item.acceptance_criteria)
    if field_assertions:
        return EffectiveCriteria(
            text=item.acceptance_criteria,
            source=CRITERIA_FIELD_SOURCE,
            assertions=field_assertions,
        )
    text = _description_exit_criteria(description=item.description)
    return EffectiveCriteria(
        text=text,
        source=DESCRIPTION_EXIT_CRITERIA_SOURCE,
        assertions=criteria_lines(criteria_text=text),
    )


def ungradeable_criteria_refusal(*, item: WorkItem, cwd: Path) -> str | None:
    """The refusal detail for an AI-dispositive item with no gradeable assertions.

    `None` means the item clears the wall — either it has gradeable criteria, or
    its effective `acceptance_policy` is `human-only` and no machine grades it.
    The detail names the item, states that the effective criteria are empty or
    ungradeable, carries the parse, and gives the remedy, exactly as the two
    ratified walls require.
    """
    resolved = effective_criteria(item=item)
    if resolved.gradeable or not _is_ai_dispositive(item=item, cwd=cwd):
        return None
    return (
        f"work-item {item.id}: effective acceptance criteria are empty or"
        f" ungradeable ({resolved.parse_display()}); author criteria via groom"
        " or edit, or set the item's acceptance_policy to human-only where"
        " machine grading is genuinely inapplicable"
    )


def pre_dispatch_criteria_refusal(*, items: Sequence[WorkItem], cwd: Path) -> str | None:
    """The pre-dispatch wall's operator-facing refusal, or `None` to proceed.

    Applied to the SELECTED candidates of both dispatch paths — the hand-picked
    `dispatch --item` target and the `loop` drain's wave — before any factory
    run is created, so a refused item is never claimed, never admitted, and
    never leaves a run behind to reap.
    """
    details = [
        detail
        for detail in (ungradeable_criteria_refusal(item=item, cwd=cwd) for item in items)
        if detail is not None
    ]
    if not details:
        return None
    lines = "".join(f"  {detail}\n" for detail in details)
    return f"ERROR: refusing to dispatch; no factory run was created:\n{lines}"


def _is_ai_dispositive(*, item: WorkItem, cwd: Path) -> bool:
    """Whether a machine grades this item's acceptance.

    ⚠️ `unsafe_perform_io` is not ceremony. `IOResult.value_or` returns
    `IO[value]`, not the value — without it the membership test is against an
    `IO` wrapper and is False for EVERY item, which silently disarms both walls.
    An unreadable config falls back to the `ai-then-human` default, so the walls
    stay armed rather than opening on a config the operator got wrong.
    """
    policy = unsafe_perform_io(
        effective_acceptance_policy(item=item, cwd=cwd).value_or(DEFAULT_ACCEPTANCE_POLICY)
    )
    return policy in _AI_DISPOSITIVE_POLICIES


def _description_exit_criteria(*, description: str) -> str | None:
    lines = description.splitlines()
    section_lines: list[str] = []
    in_section = False
    section_level = 0
    for raw in lines:
        heading = _HEADING.match(raw)
        if heading is not None:
            level = len(heading.group(1))
            title = heading.group(2).strip().casefold()
            if in_section and level <= section_level:
                break
            if title == _EXIT_CRITERIA_TITLE:
                in_section = True
                section_level = level
                continue
        if in_section:
            section_lines.append(raw)
    text = "\n".join(section_lines).strip()
    if not text:
        return None
    return text
