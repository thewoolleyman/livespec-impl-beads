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
from livespec_orchestrator_beads_fabro._store_blocked_mutations import (
    update_work_item_blocked_state,
)
from livespec_orchestrator_beads_fabro._store_rework_mutations import (
    update_work_item_rework_pending,
)
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
# The under-cap rework return, per the ratified rework-pending re-dispatch
# contract: the item stays `active` and is STAMPED with `rework:pending`, which
# is what makes it reachable — the marker is the drain's selection input, and
# `dispatch --item` accepts a marked item. An earlier build returned the item to
# `ready` because `active` was then reachable by no route at all; the marker is
# that route, so the return status moves back to `active` with it.
_REWORK_RETURN_STATUS = "active"
_MERGED_RECOVERY = "rework-re-dispatch"
_MERGED_RECOVERY_ORDERING = (
    "Fix the acceptance-criteria defect that failed this pass BEFORE the rework "
    "re-dispatch runs: the rework dispatch deliberately reaches acceptance again, so "
    "an unfixed criteria fragment re-fails there and spends another "
    "acceptance_rework_cap attempt — on the last attempt converting a recoverable "
    "state into blocked / needs-human."
)


def rework_or_block_failed_acceptance(
    *, repo: Path, item: WorkItem, policy: str, merged: bool, journal: JournalFile
) -> None:
    """Auto-rework a failing AI pass, or block once the item exceeds its cap.

    `merged` says whether the failed dispatch left merge evidence behind, and it
    changes the RECOVERY the disposition record advertises, never the status:
    already-merged work cannot be re-published by re-implementing it, so the
    record names the fix-forward rework re-dispatch and the ordering an operator
    must follow. It does NOT name `reconcile-merged`, which refuses a marked
    item precisely because this disposition already ran.
    """
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
    update_work_item_status(path=config, item_id=item.id, status=_REWORK_RETURN_STATUS)
    # The stamp rides the SAME disposition as the routing: this entry is one of
    # exactly two the contract permits to stamp the marker, and an unstamped
    # return would park the item where no drain pass can find it.
    update_work_item_rework_pending(path=config, item_id=item.id, value=True)
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
    journal.append(record=_ai_fail_auto_rework_record(work_item_id=item.id, merged=merged))


def _ai_fail_auto_rework_record(*, work_item_id: str, merged: bool) -> dict[str, object]:
    """Build the published rework disposition, naming the merged recovery route.

    An unmerged failure needs no recovery clause: the marked item is picked up
    by the next drain pass or by `dispatch --item`, and that IS the whole route.
    A merged failure does, because the rework is FIX-FORWARD — it patches on top
    of the already-merged change rather than re-publishing it — so the record
    names the route plus the ordering an operator must follow.
    """
    record = auto_disposition_journal_record(
        work_item_id=work_item_id,
        disposition="ai-fail-auto-rework",
        governing_settings=("acceptance_mode", "acceptance_rework_cap"),
    )
    if not merged:
        return record
    record["recovery"] = _MERGED_RECOVERY
    record["recovery_ordering"] = _MERGED_RECOVERY_ORDERING
    return record


def _acceptance_rework_cap_source(*, raw_labels: tuple[str, ...]) -> str:
    for label in raw_labels:
        if not label.startswith(_ACCEPTANCE_REWORK_CAP_LABEL):
            continue
        value = label[len(_ACCEPTANCE_REWORK_CAP_LABEL) :]
        if value.isdecimal() and int(value) > 0:
            return "acceptance-rework-cap label"
    return "dispatcher.acceptance_rework_cap"
