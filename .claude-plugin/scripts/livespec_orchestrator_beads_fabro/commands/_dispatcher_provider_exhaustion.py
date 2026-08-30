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
    "DISPATCH_PROVIDERS",
    "ProviderExhaustionRecord",
    "active_provider_exhaustion",
    "dispatch_provider_exhaustion",
    "provider_exhaustion_clearance_record",
    "provider_exhaustion_refusal",
    "record_provider_exhaustion_if_observed",
]

_GOVERNING_CONDITION = "provider_usage_limit"

# The vendors a dispatch of this repository SPENDS, which is the set the
# admission condition is evaluated over: a record covers this dispatch when its
# provider is one of these. Both are listed because one run spends both — the
# implementer nodes are Anthropic-backed and the publish node is Codex-backed by
# this repository's own `dispatcher` configuration — so a ceiling on either
# vendor is a ceiling this dispatch would run into.
#
# It is NOT the label a record carries: that is read off the observed failure
# (`_fabro_port_records`), which is the whole point of this module's fix. Keying
# the record on the vendor and this gate on the vendors actually spent is what
# lets a record for a provider outside this set refuse nothing, instead of one
# vendor's ceiling silently standing in for another's.
DISPATCH_PROVIDERS: tuple[str, ...] = ("anthropic", "codex")

_RECORD_STAGE = "provider-exhaustion-observed"
_REFUSAL_STAGE = "provider-exhaustion-refusal"
# The operator's early-clearance line. It RETIRES the newest observation for
# its provider instead of rewriting or deleting it: the journal is append-only
# by construction, so what was observed and who overrode it both survive.
_CLEARED_STAGE = "provider-exhaustion-cleared"
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
    def provider_usage_limit_provider(self) -> str | None:
        """The vendor whose ceiling the completed Fabro run observed, if any."""
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
    """Persist a short dispatcher-owned hold from a typed provider limit outcome.

    The record is labelled with the vendor the RUN observed, never with a fixed
    one. The outcome's provider field is the trigger as well as the label, so
    there is no second condition that could disagree with it and no path on
    which a record is written under a vendor nothing was measured against.
    """
    provider = outcome.provider_usage_limit_provider
    if provider is None:
        return
    now = _parse_journal_iso(text=now_iso)
    expires_at = (now + _HOLD_INTERVAL).strftime("%Y-%m-%dT%H:%M:%SZ")
    journal.append(
        record={
            "at": now_iso,
            "stage": _RECORD_STAGE,
            "work_item_id": outcome.work_item_id,
            "provider": provider,
            "governing_condition": _GOVERNING_CONDITION,
            "record_expires_at": expires_at,
        }
    )


def provider_exhaustion_clearance_record(*, provider: str, reason: str) -> dict[str, object]:
    """Build the appended line that retires one provider's newest observation.

    The record carries only what the CLEARANCE itself asserts — the vendor and
    the operator's stated reason. `at`, `invoker` and `invoker_source` are
    stamped by the append layer, which is what makes "who cleared it, and
    when" the same unforgeable claim on this record as on the observation it
    retires.
    """
    return {
        "stage": _CLEARED_STAGE,
        "provider": provider,
        "governing_condition": _GOVERNING_CONDITION,
        "reason": reason,
    }


def active_provider_exhaustion(
    *,
    provider: str,
    journal_path: Path | None,
    now_iso: str,
) -> ProviderExhaustionRecord | None:
    """The newest unexpired record for ONE named provider, if it holds one.

    Selective by construction: a record naming another vendor is skipped, so a
    provider this dispatch holds no record for is never refused on another
    vendor's ceiling.

    The walk is already newest-first, so the operator's early clearance costs
    one branch: a `provider-exhaustion-cleared` line met BEFORE any observation
    for this provider means the newest observation is already retired, and
    nothing is held. Meeting it AFTER an unexpired observation is a clearance
    an operator has since re-observed past, so it retires nothing.
    """
    now = _parse_journal_iso(text=now_iso)
    if journal_path is None or not journal_path.is_file():
        return None
    for record in reversed(_records(text=journal_path.read_text(encoding="utf-8"))):
        if record.get("provider") != provider:
            continue
        if record.get("stage") == _CLEARED_STAGE:
            return None
        parsed = _provider_record(record=record)
        expiry = _parse_journal_iso(text=parsed.record_expires_at)
        if expiry > now:
            return parsed
    return None


def dispatch_provider_exhaustion(
    *,
    journal_path: Path | None,
    now_iso: str,
) -> ProviderExhaustionRecord | None:
    """The unexpired record covering a provider this dispatch would spend."""
    for provider in DISPATCH_PROVIDERS:
        record = active_provider_exhaustion(
            provider=provider,
            journal_path=journal_path,
            now_iso=now_iso,
        )
        if record is not None:
            return record
    return None


def provider_exhaustion_refusal(
    *,
    work_item_id: str,
    journal: _Journal,
    journal_path: Path | None,
    now_iso: str,
) -> DispatchOutcome | None:
    """Refuse this dispatch when a covered provider's ceiling is still held.

    The refusal names the vendor from the RECORD — the one that actually
    refused — so an operator reading the journal is told which allowance is
    gone rather than a constant that may name a vendor nothing was observed
    against.
    """
    record = dispatch_provider_exhaustion(journal_path=journal_path, now_iso=now_iso)
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
        if record.get("stage") in {_RECORD_STAGE, _CLEARED_STAGE}:
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
