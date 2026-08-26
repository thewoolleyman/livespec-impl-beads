"""Dispatcher disposition for failing AI acceptance passes.

Both disposition records route through `JournalFile.append` — the single append
layer of the journal invoker attribution contract in
`SPECIFICATION/contracts.md`. They used to open the journal path directly, which
left the acceptance-rework record — the very provenance carrier that
contract's rework-pending re-dispatch counterpart designates — carrying neither
a timestamp nor an attribution.
"""

from __future__ import annotations

from pathlib import Path

from returns.unsafe import unsafe_perform_io

from livespec_orchestrator_beads_fabro._store_acceptance_rework import (
    update_acceptance_failed_ai_passes,
)
from livespec_orchestrator_beads_fabro._store_mutations import update_work_item_blocked_state
from livespec_orchestrator_beads_fabro.commands._dispatcher_decision_journal import (
    auto_disposition_journal_record,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import store_config
from livespec_orchestrator_beads_fabro.commands._dispatcher_valves import (
    DEFAULT_ACCEPTANCE_REWORK_CAP,
    effective_acceptance_rework_cap,
)
from livespec_orchestrator_beads_fabro.io import write_stderr
from livespec_orchestrator_beads_fabro.store import update_work_item_status
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "AI_DISPOSITIVE_ACCEPTANCE_POLICIES",
    "rework_or_block_failed_acceptance",
]

AI_DISPOSITIVE_ACCEPTANCE_POLICIES = frozenset(("ai-only", "ai-then-human"))
_ACCEPTANCE_REWORK_CAP_LABEL = "acceptance-rework-cap:"


def rework_or_block_failed_acceptance(
    *, repo: Path, item: WorkItem, policy: str, journal: JournalFile
) -> None:
    """Auto-rework a failing AI pass, or block once the item exceeds its cap."""
    config = store_config(repo=repo)
    failure_state = update_acceptance_failed_ai_passes(path=config, item_id=item.id)
    # An unreadable `.livespec.jsonc` falls back to the documented default cap,
    # visibly and here rather than inside the reader. `unsafe_perform_io` is
    # required: `IOResult.value_or` returns `IO[value]`, not the value.
    cap = unsafe_perform_io(
        effective_acceptance_rework_cap(
            item=item,
            cwd=repo,
            raw_labels=failure_state.raw_labels,
        ).value_or(DEFAULT_ACCEPTANCE_REWORK_CAP)
    )
    cap_source = _acceptance_rework_cap_source(raw_labels=failure_state.raw_labels)
    if failure_state.failed_ai_passes > cap:
        update_work_item_blocked_state(
            path=config,
            item_id=item.id,
            status="blocked",
            blocked_reason="needs-human",
        )
        journal.append(
            record={
                "stage": "acceptance-rework-cap-exceeded",
                "work_item_id": item.id,
                "policy": policy,
                "failed_ai_passes": failure_state.failed_ai_passes,
                "acceptance_rework_cap": cap,
                "cap_source": cap_source,
                "blocked_reason": "needs-human",
            },
        )
        journal.append(
            record=auto_disposition_journal_record(
                work_item_id=item.id,
                disposition="cap-exceeded-escalation",
                governing_settings=("acceptance_rework_cap",),
            )
        )
        _ = write_stderr(
            text=(
                f"SURFACE: work-item {item.id} exceeded acceptance_rework_cap {cap} "
                "after a failing AI acceptance pass; blocked with "
                "blocked_reason needs-human for human review.\n"
            )
        )
        return
    update_work_item_status(path=config, item_id=item.id, status="active")
    journal.append(
        record={
            "stage": "acceptance-auto-rework",
            "work_item_id": item.id,
            "policy": policy,
            "failed_ai_passes": failure_state.failed_ai_passes,
            "acceptance_rework_cap": cap,
            "cap_source": cap_source,
        },
    )
    journal.append(
        record=auto_disposition_journal_record(
            work_item_id=item.id,
            disposition="ai-fail-auto-rework",
            governing_settings=("acceptance_mode", "acceptance_rework_cap"),
        )
    )


def _acceptance_rework_cap_source(*, raw_labels: tuple[str, ...]) -> str:
    for label in raw_labels:
        if not label.startswith(_ACCEPTANCE_REWORK_CAP_LABEL):
            continue
        value = label[len(_ACCEPTANCE_REWORK_CAP_LABEL) :]
        if value.isdecimal() and int(value) > 0:
            return "acceptance-rework-cap label"
    return "dispatcher.acceptance_rework_cap"
