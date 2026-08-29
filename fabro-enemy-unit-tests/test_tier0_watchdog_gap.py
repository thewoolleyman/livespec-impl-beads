"""Enemy Unit Test for a KNOWN GAP: the watchdog's fallback field is absent.

Separate from `test_tier0_fabro.py` because this file asserts what the
dependency does NOT provide, rather than a contract we rely on. Same tier 0
rules apply: real calls, no workflow run launched, and it must not be run with
a linked git worktree as the working directory.
"""

from __future__ import annotations

from _tier0_support import (
    TIMEOUT_SECONDS,
    _assert_success,
    _completed_run_id,
    _FabroTier0Config,
    _inspect_record,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port import FabroPort

__all__: list[str] = []

_WATCHDOG_FALLBACK_FIELD = "updated_at"


def test_inspect_record_still_lacks_updated_at(
    *,
    config: _FabroTier0Config,
    port: FabroPort,
) -> None:
    """The pinned build never emits the field the watchdog fallback once read.

    `_dispatcher_watchdog.py` used to fall back to `updated_at` from
    `fabro inspect --json`, but no real payload carries it, so that fallback
    was dead code in production. Measured 2026-08-20 against fabro 0.254.0: a
    real inspect record carries `checkpoint`, `conclusion`, `parent_id`,
    `run_id`, `run_spec`, `sandbox`, `start_record`, and `status` -- and
    nothing else. The fallback has since been REMOVED rather than repointed
    (bd-ib-tec5sz); `fabro events` is the watchdog's sole coarse source.

    This asserts the ABSENCE deliberately, so that the day a future fabro build
    starts emitting `updated_at` this test fails loudly and any decision to
    reintroduce an inspect-based fallback is taken on purpose rather than by
    accident.
    """
    run_id = config.completed_run_id or _completed_run_id(port=port)
    inspect = port.inspect(run_id=run_id, timeout_seconds=TIMEOUT_SECONDS)

    _assert_success(command=inspect.command)
    record = _inspect_record(value=inspect.payload)
    assert _WATCHDOG_FALLBACK_FIELD not in record
