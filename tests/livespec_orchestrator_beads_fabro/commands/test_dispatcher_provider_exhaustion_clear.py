"""The `clear-provider-exhaustion` operator valve, driven through the CLI.

The scan half of the mechanism is pinned by
`test_dispatcher_provider_exhaustion_clearance_scan`; this file covers the
subcommand that writes the clearance, its two human-only refusals, and the
end-to-end claim that matters: a dispatch attempted right after a clearance is
admitted against that provider exactly as if the record had expired.
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


def test_clearance_admits_a_dispatch_immediately_and_journals_who_and_why(
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
    written = _records(path=journal.path)[-1]
    assert written["stage"] == "provider-exhaustion-cleared"
    assert written["provider"] == "codex"
    assert written["reason"] == _REASON
    # Who, and when, ride the same unforgeable stamp the observation carries.
    assert written["invoker"] == "operator:cwoolley"
    assert written["invoker_source"] == "flag"
    assert isinstance(written["at"], str)
    # The observation line itself is untouched: the store is append-only.
    assert _records(path=journal.path)[0]["stage"] == "provider-exhaustion-observed"
    # And the admission gate now admits, without any dispatch having happened.
    assert (
        dispatch_provider_exhaustion(
            journal_path=journal.path,
            now_iso="2026-08-30T10:05:00Z",
        )
        is None
    )


def test_clearance_refuses_an_unattributed_invocation(
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
    # Nothing was appended, so the record still holds.
    assert len(_records(path=journal.path)) == 1


def test_clearance_refuses_a_blank_reason(
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


def test_clearance_refuses_a_provider_holding_no_unexpired_record(
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
    assert len(_records(path=journal.path)) == 1


def test_clearance_defaults_the_journal_under_the_current_directory(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    default_journal = JournalFile(path=tmp_path / "tmp" / "fabro-dispatch-journal.jsonl")
    default_journal.append(record=_observed(provider="codex"))
    monkeypatch.setenv("LIVESPEC_INVOKER", "operator:from-env")
    monkeypatch.chdir(tmp_path)

    exit_code = main(argv=["clear-provider-exhaustion", "--provider", "codex", "--reason", _REASON])

    assert exit_code == 0
    assert "by operator:from-env" in capsys.readouterr().out
    written = _records(path=default_journal.path)[-1]
    assert written["stage"] == "provider-exhaustion-cleared"
    assert written["invoker_source"] == "env"


def _journal_holding_codex(*, tmp_path: Path) -> JournalFile:
    journal = JournalFile(path=tmp_path / "journal.jsonl")
    journal.append(record=_observed(provider="codex"))
    return journal


def _observed(*, provider: str) -> dict[str, object]:
    return {
        "stage": "provider-exhaustion-observed",
        "work_item_id": "bd-ib-observed",
        "provider": provider,
        "governing_condition": "provider_usage_limit",
        "record_expires_at": _RECORD_EXPIRES_AT,
    }


def _records(*, path: Path) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]
