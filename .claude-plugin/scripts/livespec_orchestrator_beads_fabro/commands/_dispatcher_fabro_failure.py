"""Fabro failure-detail parsing for dispatcher failed-run outcomes."""

from __future__ import annotations

from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroFailureDetail

__all__: list[str] = [
    "FabroFailureDetail",
    "fabro_failure_outcome_detail",
]


def fabro_failure_outcome_detail(
    *,
    failure: FabroFailureDetail | None,
    fallback: str,
) -> str:
    """Human-readable failed-run detail, preferring Fabro's structured cause."""
    if failure is None:
        return fallback
    parts: list[str] = []
    if failure.cause is not None:
        parts.append(failure.cause)
    if failure.category is not None:
        parts.append(f"category={failure.category}")
    if failure.signature is not None:
        parts.append(f"signature={failure.signature}")
    return "; ".join(parts) if parts else fallback
