"""The operator-clearance leg of the provider-exhaustion reverse scan.

The scan already walks the journal newest-first for one named provider. These
tests pin the third retirement route onto that walk: a
`provider-exhaustion-cleared` line met BEFORE any observation for the same
provider means an operator has already retired the newest observation, so
nothing is held even though the recorded expiry is still in the future.
"""

from __future__ import annotations

from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.commands._dispatcher_provider_exhaustion import (
    active_provider_exhaustion,
)

_RECORD_EXPIRES_AT = "2026-08-30T10:15:00Z"
_WHILE_STILL_UNEXPIRED = "2026-08-30T10:05:00Z"


def test_operator_clearance_retires_the_newest_record_before_its_expiry(tmp_path: Path) -> None:
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    journal.append(record=_observed(provider="codex"))
    journal.append(record=_observed(provider="anthropic"))
    journal.append(record=_cleared(provider="codex"))

    cleared = active_provider_exhaustion(
        provider="codex",
        journal_path=journal.path,
        now_iso=_WHILE_STILL_UNEXPIRED,
    )
    untouched = active_provider_exhaustion(
        provider="anthropic",
        journal_path=journal.path,
        now_iso=_WHILE_STILL_UNEXPIRED,
    )

    # The cleared vendor holds nothing; clearing one vendor never reaches another.
    assert cleared is None
    assert untouched is not None
    assert untouched.provider == "anthropic"


def test_an_observation_after_a_clearance_is_held_again(tmp_path: Path) -> None:
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    journal.append(record=_observed(provider="codex"))
    journal.append(record=_cleared(provider="codex"))
    journal.append(record=_observed(provider="codex"))

    held = active_provider_exhaustion(
        provider="codex",
        journal_path=journal.path,
        now_iso=_WHILE_STILL_UNEXPIRED,
    )

    # A clearance retires the observations BEHIND it, never the ones ahead of it.
    assert held is not None
    assert held.record_expires_at == _RECORD_EXPIRES_AT


def _observed(*, provider: str) -> dict[str, object]:
    return {
        "stage": "provider-exhaustion-observed",
        "work_item_id": "bd-ib-observed",
        "provider": provider,
        "governing_condition": "provider_usage_limit",
        "record_expires_at": _RECORD_EXPIRES_AT,
    }


def _cleared(*, provider: str) -> dict[str, object]:
    return {
        "stage": "provider-exhaustion-cleared",
        "provider": provider,
        "governing_condition": "provider_usage_limit",
        "reason": "restarted the self-hosted model; it answers again",
    }
