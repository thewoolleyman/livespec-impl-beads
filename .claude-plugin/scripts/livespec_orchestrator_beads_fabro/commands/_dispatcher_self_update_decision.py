"""Release-triggered self-update decisions and canary verdicts for Dispatcher."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__: list[str] = [
    "SELF_UPDATE_BREACH_CLASS",
    "CanaryVerdict",
    "PromotionDecision",
    "ReleaseUpdateDecision",
    "canary_self_check_argv",
    "canary_verdict",
    "promotion_decision",
    "release_below_floor",
    "release_update_decision",
]

# The alarm class a failed-canary self-update breach fires through h1p's
# `notify_terminal` seam. NOT a `DispatchOutcome.status`, so (like y0m's
# `spend-cap-breach`) it is built as its own `NotifyEvent` rather than
# flowing through `terminal_events`.
SELF_UPDATE_BREACH_CLASS = "self-update-canary-failed"


@dataclass(frozen=True, kw_only=True, slots=True)
class CanaryVerdictValue:
    """Enum-like verdict value without subclassing."""

    value: str


class CanaryVerdict:
    """The canary's pass/fail decision over the candidate self-check."""

    PASS: Final = CanaryVerdictValue(value="pass")
    FAIL: Final = CanaryVerdictValue(value="fail")


@dataclass(frozen=True, kw_only=True)
class PromotionDecision:
    """Whether a canary verdict should swap code or alarm."""

    promote: bool
    alarm: bool
    reason: str


@dataclass(frozen=True, kw_only=True)
class ReleaseUpdateDecision:
    """Whether the available released artifact should replace the running one."""

    update_required: bool
    reason: str


def release_update_decision(
    *,
    running_release: str | None,
    available_release: str | None,
) -> ReleaseUpdateDecision:
    """Compare the running release with the available released artifact."""
    if running_release is None:
        return ReleaseUpdateDecision(
            update_required=False,
            reason="running release could not be determined",
        )
    if available_release is None:
        return ReleaseUpdateDecision(
            update_required=False,
            reason="available release could not be determined",
        )
    if _version_key(version=available_release) > _version_key(version=running_release):
        return ReleaseUpdateDecision(
            update_required=True,
            reason=(
                f"available release {available_release} is newer than "
                f"running release {running_release}"
            ),
        )
    return ReleaseUpdateDecision(
        update_required=False,
        reason=f"running release is current ({running_release})",
    )


def canary_self_check_argv(*, candidate_bin: str, scratch_root: str) -> list[str]:
    """The argv for the candidate dispatcher's cheap, side-effect-free canary.

    Runs the CANDIDATE's OWN `dispatcher.py ledger-check --json` against a
    throwaway `--project-root` (`scratch_root`, a freshly-created empty
    directory with no `.livespec.jsonc` / ledger). This exercises the
    candidate end-to-end — its module import graph, its argument parsing,
    and its check pipeline — while touching NO real ledger, NO fabro, and
    NO network.
    """
    return [
        "python3",
        candidate_bin,
        "ledger-check",
        "--project-root",
        scratch_root,
        "--json",
    ]


def canary_verdict(*, exit_code: int) -> CanaryVerdictValue:
    """Map a candidate self-check exit code to the canary verdict."""
    return CanaryVerdict.PASS if exit_code == 0 else CanaryVerdict.FAIL


def promotion_decision(*, verdict: CanaryVerdictValue) -> PromotionDecision:
    """Decide the post-canary action. Never swap code; alarm on every verdict."""
    if verdict is CanaryVerdict.PASS:
        return PromotionDecision(
            promote=False,
            alarm=True,
            reason="canary passed; restart is due for the validated released payload",
        )
    return PromotionDecision(
        promote=False,
        alarm=True,
        reason=(
            "canary FAILED; keeping the last-known-good pinned copy and alarming "
            "(the staged self-update is NOT promoted)"
        ),
    )


def release_below_floor(*, release: str, floor: str) -> bool | None:
    """Whether `release` orders below a deliberate operator floor.

    `None` means the comparison COULD NOT BE MADE — either side carries no
    orderable released-version identifier — and it is deliberately distinct
    from `False`. The dispatch-admission currency check turns that `None` into
    a recorded "currency could not be determined" rather than into a silent
    pass, per the self-update contract in SPECIFICATION/contracts.md: an
    unobservable release must never fail open into a false refusal nor be
    silenced into a satisfied floor.
    """
    release_key = _version_key(version=release)
    floor_key = _version_key(version=floor)
    if not release_key or not floor_key:
        return None
    return release_key < floor_key


def _version_key(*, version: str) -> tuple[int, ...]:
    normalized = version.strip().removeprefix("v")
    release, _, _suffix = normalized.partition("-")
    return tuple(int(part) for part in release.split(".") if part.isdigit())
