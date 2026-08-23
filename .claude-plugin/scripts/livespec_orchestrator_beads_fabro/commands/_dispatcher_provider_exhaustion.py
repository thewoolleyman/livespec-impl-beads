"""Provider-exhaustion admission records for the Dispatcher."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol, cast

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import DispatchOutcome
from livespec_orchestrator_beads_fabro.effects import parse_iso_datetime

__all__: list[str] = [
    "ProviderExhaustionRecord",
    "active_provider_exhaustion",
    "provider_exhaustion_refusal",
    "record_provider_exhaustion_if_observed",
]

_GOVERNING_CONDITION = "provider_usage_limit"
_PROVIDER_CODEX = "codex"
_RECORD_STAGE = "provider-exhaustion-observed"
_REFUSAL_STAGE = "provider-exhaustion-refusal"
_HOLD_INTERVAL = timedelta(minutes=15)


class _Journal(Protocol):
    def append(self, *, record: dict[str, object]) -> None:
        """Persist one journal record."""
        ...


class _Outcome(Protocol):
    @property
    def work_item_id(self) -> str:
        """Ledger id for the dispatch outcome."""
        ...

    @property
    def provider_usage_limit(self) -> bool:
        """Whether the completed Fabro run observed a provider limit."""
        ...


@dataclass(frozen=True, kw_only=True)
class ProviderExhaustionRecord:
    provider: str
    governing_condition: str
    record_expires_at: str
    work_item_id: str


def record_provider_exhaustion_if_observed(
    *,
    outcome: _Outcome,
    journal: _Journal,
    now_iso: str,
) -> None:
    """Persist a short dispatcher-owned hold from a typed provider limit outcome."""
    if not outcome.provider_usage_limit:
        return
    now = _parse_journal_iso(text=now_iso)
    expires_at = (now + _HOLD_INTERVAL).strftime("%Y-%m-%dT%H:%M:%SZ")
    journal.append(
        record={
            "at": now_iso,
            "stage": _RECORD_STAGE,
            "work_item_id": outcome.work_item_id,
            "provider": _PROVIDER_CODEX,
            "governing_condition": _GOVERNING_CONDITION,
            "record_expires_at": expires_at,
        }
    )


def active_provider_exhaustion(
    *,
    provider: str,
    journal_path: Path | None,
    now_iso: str,
) -> ProviderExhaustionRecord | None:
    now = _parse_journal_iso(text=now_iso)
    if journal_path is None or not journal_path.is_file():
        return None
    for record in reversed(_records(text=journal_path.read_text(encoding="utf-8"))):
        parsed = _provider_record(record=record)
        if parsed.provider != provider:
            continue
        expiry = _parse_journal_iso(text=parsed.record_expires_at)
        if expiry > now:
            return parsed
    return None


def provider_exhaustion_refusal(
    *,
    work_item_id: str,
    journal: _Journal,
    journal_path: Path | None,
    now_iso: str,
) -> DispatchOutcome | None:
    record = active_provider_exhaustion(
        provider=_PROVIDER_CODEX,
        journal_path=journal_path,
        now_iso=now_iso,
    )
    if record is None:
        return None
    outcome = DispatchOutcome(
        work_item_id=work_item_id,
        status="provider-exhaustion",
        stage="provider-exhaustion",
        pr_number=None,
        merge_sha=None,
        detail=(
            "provider exhaustion refusal: "
            f"provider={record.provider} "
            f"governing_condition={record.governing_condition} "
            f"record_expires_at={record.record_expires_at}"
        ),
    )
    journal.append(record={"stage": "outcome", "outcome": _outcome_record(outcome=outcome)})
    journal.append(
        record={
            "stage": _REFUSAL_STAGE,
            "work_item_id": work_item_id,
            "provider": record.provider,
            "governing_condition": record.governing_condition,
            "record_expires_at": record.record_expires_at,
        }
    )
    return outcome


def _outcome_record(*, outcome: DispatchOutcome) -> dict[str, object]:
    record: dict[str, object] = {
        "work_item_id": outcome.work_item_id,
        "status": outcome.status,
        "stage": outcome.stage,
        "pr_number": outcome.pr_number,
        "merge_sha": outcome.merge_sha,
        "detail": outcome.detail,
        "fabro_run_id": outcome.fabro_run_id,
    }
    return record


def _records(*, text: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for line in text.splitlines():
        parsed_record = cast("dict[object, object]", json.loads(line))
        record = {str(key): value for key, value in parsed_record.items()}
        if record.get("stage") == _RECORD_STAGE:
            records.append(record)
    return records


def _parse_journal_iso(*, text: str) -> datetime:
    return cast("datetime", parse_iso_datetime(text=text.removesuffix("Z") + "+00:00"))


def _provider_record(*, record: dict[str, object]) -> ProviderExhaustionRecord:
    provider = record.get("provider")
    condition = record.get("governing_condition")
    expires_at = record.get("record_expires_at")
    work_item_id = record.get("work_item_id")
    return ProviderExhaustionRecord(
        provider=cast("str", provider),
        governing_condition=cast("str", condition),
        record_expires_at=cast("str", expires_at),
        work_item_id=cast("str", work_item_id),
    )
