"""Producer-side envelope conformance for the needs-attention composition.

The needs-attention machine-envelope contract in `SPECIFICATION/contracts.md`
binds this producer twice over: it MUST NOT emit an item that fails the runtime
validator, and it MUST NOT silently omit a candidate that failed validation — a
composition-time validation failure MUST surface as a visible failure alongside
the valid items. The second half is the load-bearing one: absence of an
attention item reads as RESOLUTION downstream, so a validation failure that
merely shortened the list would manufacture an all-clear.

The shared normalizer `livespec_runtime.needs_attention.compose_needs_attention`
appends a composed item ONLY when the runtime validator accepts its stable id,
and it reports nothing at all when it declines — exactly the silent-omission
shape the clause forbids. The ownership cut puts that validator (and the
normalizer over injected facts) in `livespec-runtime`, whose vendored tree is
read-only here, so the loud half lives on this side of the cut instead.

The mechanism is to route each injected primitive through the runtime normalizer
ON ITS OWN. An empty result then names exactly which candidate the validator
rejected, and that rejection is re-emitted as a visible failure item. Routing one
primitive at a time is what keeps the runtime the single authority on both id
FORMATION and validity: this module never formats a candidate id itself, so it
cannot drift from the grammar it is checking against.
"""

from __future__ import annotations

import shlex
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from livespec_runtime.attention_item import (
    AttentionItem,
    Handoff,
    SourceRef,
    validate_attention_item_id,
)
from livespec_runtime.needs_attention import (
    ImplNextOutput,
    PlanThreadOutput,
    SpecNextOutput,
    WorkItemHumanValveLane,
    compose_needs_attention,
)

__all__: list[str] = [
    "ConformanceContext",
    "composed_conformant",
    "conformant_items",
]

# The failure item is itself an envelope item, so it must clear the very
# validator that rejected the candidate it reports — otherwise the loud half
# would be silently dropped by the same mechanism it exists to expose. The
# runtime grammar accepts `hygiene:<type>:<resource>` when both trailing
# components are non-empty and non-decimal, so the rejected candidate's own key
# is carried behind a fixed literal prefix: that makes the resource component
# unconditionally well-formed no matter how degenerate the rejected key was,
# while still naming it verbatim for the operator.
_FAILURE_TYPE = "attention-invalid"
_FAILURE_KEY_PREFIX = "candidate-"


@dataclass(frozen=True, slots=True, kw_only=True)
class ConformanceContext:
    """The repo identity every conformance decision is reported against."""

    project_root: Path
    repo: str


def composed_conformant(
    *,
    context: ConformanceContext,
    spec_next: SpecNextOutput | None,
    impl_next: ImplNextOutput | None,
    human_valve_lanes: Sequence[WorkItemHumanValveLane],
    plan_threads: Sequence[PlanThreadOutput],
) -> list[AttentionItem]:
    """Normalize each injected primitive alone, surfacing every rejection.

    Equivalent to one `compose_needs_attention` call over all the primitives,
    except that a candidate the runtime validator rejects leaves a visible
    failure item behind instead of leaving nothing behind.
    """
    attention: list[AttentionItem] = []
    for lane in human_valve_lanes:
        attention.extend(
            _normalized(
                context=context,
                subject=f"human-valve lane {lane.verb} for work-item {lane.work_item}",
                key=f"{lane.verb}-{lane.work_item}",
                composed=compose_needs_attention(repo=context.repo, human_valve_lanes=(lane,)),
            )
        )
    if impl_next is not None:
        attention.extend(
            _normalized(
                context=context,
                subject=f"impl-next candidate for work-item {impl_next.work_item}",
                key=impl_next.work_item,
                composed=compose_needs_attention(repo=context.repo, impl_next=impl_next),
            )
        )
    if spec_next is not None:
        attention.extend(
            _normalized(
                context=context,
                subject=f"spec-next candidate {spec_next.op} on {spec_next.spec_target}",
                key=f"{spec_next.op}-{spec_next.spec_target}",
                composed=compose_needs_attention(repo=context.repo, spec_next=spec_next),
            )
        )
    for thread in plan_threads:
        attention.extend(
            _normalized(
                context=context,
                subject=f"plan thread {thread.topic}",
                key=thread.topic,
                composed=compose_needs_attention(repo=context.repo, plan_threads=(thread,)),
            )
        )
    return attention


def conformant_items(
    *,
    context: ConformanceContext,
    candidates: Sequence[AttentionItem],
) -> list[AttentionItem]:
    """Gate directly-built candidates on the runtime validator, loudly.

    The lanes this repository composes as `AttentionItem` values directly never
    pass through the runtime normalizer, so nothing else would apply the
    validator to them at all — a malformed stable id would ship on the wire.
    Each rejected candidate is replaced by a visible failure item rather than
    dropped, so the count of things needing attention never falls silently.
    """
    attention: list[AttentionItem] = []
    for candidate in candidates:
        if validate_attention_item_id(id=candidate.id):
            attention.append(candidate)
        else:
            attention.append(
                _failure_item(
                    context=context,
                    subject=f"{candidate.kind} candidate with stable id {candidate.id!r}",
                    key=candidate.id,
                )
            )
    return attention


def _normalized(
    *,
    context: ConformanceContext,
    subject: str,
    key: str,
    composed: list[AttentionItem],
) -> list[AttentionItem]:
    if composed:
        return composed
    return [_failure_item(context=context, subject=subject, key=key)]


def _failure_item(*, context: ConformanceContext, subject: str, key: str) -> AttentionItem:
    return AttentionItem(
        id=f"hygiene:{_FAILURE_TYPE}:{_FAILURE_KEY_PREFIX}{key}",
        kind="hygiene",
        urgency="high",
        summary=(
            f"Attention candidate rejected by the runtime validator: {subject}. "
            "It is absent from the envelope because composition failed validation, "
            "never because the underlying fact resolved."
        ),
        source_ref=SourceRef(repo=context.repo),
        handoff=Handoff(
            kind="shell",
            command=_failure_command(context=context, subject=subject),
        ),
    )


def _failure_command(*, context: ConformanceContext, subject: str) -> str:
    prompt = (
        f"inspect-attention-validation-failure in repository {context.project_root}. "
        f"The rejected composition candidate is: {subject}. Repair the derivation so "
        "the candidate carries a stable id the runtime validator accepts; never "
        "resolve it by dropping the candidate."
    )
    return (
        f"cd {shlex.quote(str(context.project_root))} && "
        f"codex exec {shlex.quote(prompt)} < /dev/null"
    )
