"""Refusal-path tests for the gh-refresh prepare-step guards (bd-ib-gnli).

Both guards exist to refuse BEFORE submission. A step over the kernel's
per-argument limit does not degrade gracefully: `execve` fails with
"argument list too long", the run dies at launch having done no work and
pushed no branch, and the operator sees a failure that looks nothing like
its cause. An untested refusal path is the same hazard one level up, so
each guard is exercised here on the input it exists to reject.
"""

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_gh_refresh import (
    MAX_PREPARE_STEP_BYTES,
    _assert_shell_safe,  # pyright: ignore[reportPrivateUsage]
    _assert_step_within_limit,  # pyright: ignore[reportPrivateUsage]
)


def test_assert_shell_safe_accepts_the_base64_alphabet() -> None:
    _assert_shell_safe(chunk="AZaz09+/=")


def test_assert_shell_safe_refuses_a_single_quote() -> None:
    """A quote would break out of the single-quoted shell literal."""
    with pytest.raises(ValueError, match="outside the base64 alphabet"):
        _assert_shell_safe(chunk="AAAA'; rm -rf /; echo '")


def test_assert_step_within_limit_accepts_a_step_at_the_cap() -> None:
    _assert_step_within_limit(script="x" * MAX_PREPARE_STEP_BYTES)


def test_assert_step_within_limit_refuses_a_step_over_the_cap() -> None:
    """The refusal must name the cause, not merely fail."""
    with pytest.raises(ValueError, match="argument list too long") as excinfo:
        _assert_step_within_limit(script="x" * (MAX_PREPARE_STEP_BYTES + 1))
    assert str(MAX_PREPARE_STEP_BYTES + 1) in str(excinfo.value)
