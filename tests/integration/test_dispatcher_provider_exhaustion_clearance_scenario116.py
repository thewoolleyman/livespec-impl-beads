"""Consumer-tier acceptance for SPECIFICATION/scenarios.md Scenario 116.

Binds "## Scenario 116 — An operator retires an exhaustion record before its
expiry" through the real `dispatcher.main(argv=[...])` CLI against a real
on-disk journal. The clause under test — the operator-clearance clause of
`SPECIFICATION/contracts.md` — is a statement about what the operator-facing
subcommand DOES end to end, so every case here drives the Dispatcher's own
entry point rather than the command helper it calls.

The four cases map 1:1 to the scenario's four Given/When/Then blocks:

- an operator clearance retires the record and admission resumes, journaling the
  provider, the acting identity, the time and the reason while the observation
  line survives (append-only);
- a clearance asserting no identity is refused and nothing is appended;
- a clearance with a blank reason is refused;
- a clearance against a provider holding no unexpired record is refused before
  anything is written.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.commands._dispatcher_provider_exhaustion import (
    dispatch_provider_exhaustion,
)
from livespec_orchestrator_beads_fabro.commands.dispatcher import main

_RECORD_EXPIRES_AT = "2126-01-01T00:00:00Z"
_REASON = "restarted the self-hosted model and confirmed it answers"


def test_scenario116_operator_clearance_retires_and_admits(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    journal = _journal_holding_codex(tmp_path=tmp_path)
    monkeypatch.delenv("LIVESPEC_INVOKER", raising=False)

    exit_code = main(
        argv=[
            "clear-provider-exhaustion",
            "--repo",
            str(tmp_path),
            "--journal",
            str(journal.path),
            "--provider",
            "codex",
            "--reason",
            _REASON,
            "--invoker",
            "operator:cwoolley",
        ]
    )

    assert exit_code == 0
    assert "CLEARED  codex" in capsys.readouterr().out
    # Then the clearance is appended carrying the provider, acting identity, time and reason.
    written = _records(path=journal.path)[-1]
    assert written["stage"] == "provider-exhaustion-cleared"
    assert written["provider"] == "codex"
    assert written["reason"] == _REASON
    assert written["invoker"] == "operator:cwoolley"
    assert written["invoker_source"] == "flag"
    assert isinstance(written["at"], str)
    # And the original observation record remains readable in the journal (append-only).
    assert _records(path=journal.path)[0]["stage"] == "provider-exhaustion-observed"
    # And a dispatch against "codex" is admitted normally, with no dispatch having happened.
    assert (
        dispatch_provider_exhaustion(journal_path=journal.path, now_iso="2026-08-30T10:05:00Z")
        is None
    )


def test_scenario116_a_clearance_asserting_no_identity_is_refused(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    journal = _journal_holding_codex(tmp_path=tmp_path)
    monkeypatch.delenv("LIVESPEC_INVOKER", raising=False)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        argv=[
            "clear-provider-exhaustion",
            "--journal",
            str(journal.path),
            "--provider",
            "codex",
            "--reason",
            _REASON,
        ]
    )

    assert exit_code == 3
    assert "asserted no identity" in capsys.readouterr().err
    # Nothing is appended, and the record continues to refuse admission for "codex".
    assert len(_records(path=journal.path)) == 1
    assert (
        dispatch_provider_exhaustion(journal_path=journal.path, now_iso="2026-08-30T10:05:00Z")
        is not None
    )


def test_scenario116_a_clearance_with_no_stated_reason_is_refused(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    journal = _journal_holding_codex(tmp_path=tmp_path)

    exit_code = main(
        argv=[
            "clear-provider-exhaustion",
            "--repo",
            str(tmp_path),
            "--journal",
            str(journal.path),
            "--provider",
            "codex",
            "--reason",
            "   ",
            "--invoker",
            "operator:cwoolley",
        ]
    )

    assert exit_code == 3
    assert "--reason is blank" in capsys.readouterr().err
    assert len(_records(path=journal.path)) == 1


def test_scenario116_a_clearance_against_a_provider_holding_no_record_is_refused(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    journal = _journal_holding_codex(tmp_path=tmp_path)

    exit_code = main(
        argv=[
            "clear-provider-exhaustion",
            "--repo",
            str(tmp_path),
            "--journal",
            str(journal.path),
            "--provider",
            "anthropic",
            "--reason",
            _REASON,
            "--invoker",
            "operator:cwoolley",
        ]
    )

    assert exit_code == 3
    assert "nothing to clear" in capsys.readouterr().err
    # Refused before anything is written: the codex observation is the only record.
    assert len(_records(path=journal.path)) == 1


def _journal_holding_codex(*, tmp_path: Path) -> JournalFile:
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    journal.append(
        record={
            "stage": "provider-exhaustion-observed",
            "work_item_id": "bd-ib-observed",
            "provider": "codex",
            "governing_condition": "provider_usage_limit",
            "record_expires_at": _RECORD_EXPIRES_AT,
        }
    )
    return journal


def _records(*, path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
