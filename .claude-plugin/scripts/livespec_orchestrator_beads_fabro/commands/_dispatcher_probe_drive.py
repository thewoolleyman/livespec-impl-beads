"""Driving the loop probe's cycle in the contract's order, confinement included.

THE ORDER IS THE CONTRACT, not a convenience. The before-snapshot is taken
before anything is driven, so an unreadable source fails the probe rather than
being read as a clean surface after the fact. Effective criteria are asserted
before dispatch, because criteria that cannot be graded make the eventual
acceptance verdict meaningless and a factory run has already burned by then.

And confinement is verified BETWEEN `publish` and `merge`. An escaping change
therefore fails with `merge` NEVER CALLED -- "fails without merging" is a
property of this module's control flow, which a test can observe, rather than a
promise in prose. The already-merged case is routed to the backstop instead:
when the factory's own publish node has merged upstream before the probe could
interpose, the honest report is the commit and the revert obligation, not a
refusal claiming nothing merged.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_confinement import (
    merged_escape_failure,
    pre_merge_confinement_refusal,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_cycle import (
    ProbeCycle,
    ProbePublish,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_observation import (
    graded_observation,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_report import (
    CONFINEMENT_ESCAPE_OUTCOME,
    MERGED_ESCAPE_OUTCOME,
    REVERT_REMEDY,
    SOURCE_REMEDY,
    STOP_REMEDY,
    ProbeResult,
    probe_failure,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_residue import (
    SOURCE_UNAVAILABLE_OUTCOME,
    ResidueSnapshot,
    ResidueSource,
    unavailable_detail,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_stages import (
    CONFINEMENT_STAGE,
    CRITERIA_STAGE,
    MERGE_STAGE,
    PUBLISH_STAGE,
    RESIDUE_STAGE,
    criteria_stage_failure,
)

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "run_probe_cycle",
]

_UNKNOWN_COMMIT = "<unknown commit>"


def run_probe_cycle(
    *,
    item: WorkItem,
    cycle: ProbeCycle,
    sources: Sequence[ResidueSource],
    probe_run_id: str,
) -> ProbeResult:
    """Drive the designated item through the cycle, asserting each stage in order."""
    before = tuple(source.snapshot() for source in sources)
    unreadable = _unreadable(snapshots=before)
    if unreadable is not None:
        return _source_unavailable(
            cycle=cycle, item=item, probe_run_id=probe_run_id, detail=unreadable
        )
    criteria = criteria_stage_failure(item=item)
    if criteria is not None:
        return probe_failure(
            probe_run_id=probe_run_id,
            stage=CRITERIA_STAGE,
            detail=criteria,
            item_status=cycle.item_status(work_item_id=item.id),
        )
    return _drive_verified_cycle(
        item=item, cycle=cycle, before=before, sources=sources, probe_run_id=probe_run_id
    )


def _drive_verified_cycle(
    *,
    item: WorkItem,
    cycle: ProbeCycle,
    before: Sequence[ResidueSnapshot],
    sources: Sequence[ResidueSource],
    probe_run_id: str,
) -> ProbeResult:
    published = cycle.publish(work_item_id=item.id)
    if not published.readable:
        return _source_unavailable(
            cycle=cycle,
            item=item,
            probe_run_id=probe_run_id,
            detail=published.detail,
            stage=PUBLISH_STAGE,
        )
    escape = _escape_before_merge(
        cycle=cycle, item=item, probe_run_id=probe_run_id, published=published
    )
    if escape is not None:
        return escape
    merged = cycle.merge(published=published)
    if not merged.merged:
        return probe_failure(
            probe_run_id=probe_run_id,
            stage=MERGE_STAGE,
            detail=merged.detail,
            item_status=cycle.item_status(work_item_id=item.id),
        )
    backstop = merged_escape_failure(
        paths=merged.merged_paths, merge_commit=merged.merge_commit or _UNKNOWN_COMMIT
    )
    if backstop is not None:
        return _merged_escape(cycle=cycle, item=item, probe_run_id=probe_run_id, detail=backstop)
    return graded_observation(
        work_item_id=item.id,
        observation=cycle.observe(work_item_id=item.id),
        before=before,
        sources=sources,
        probe_run_id=probe_run_id,
    )


def _escape_before_merge(
    *,
    cycle: ProbeCycle,
    item: WorkItem,
    probe_run_id: str,
    published: ProbePublish,
) -> ProbeResult | None:
    """Verify confinement BEFORE `merge` is called, so an escape never merges."""
    paths = published.paths
    already_merged = published.merge_commit
    if already_merged is not None:
        backstop = merged_escape_failure(paths=paths, merge_commit=already_merged)
        if backstop is None:
            return None
        return _merged_escape(cycle=cycle, item=item, probe_run_id=probe_run_id, detail=backstop)
    refusal = pre_merge_confinement_refusal(paths=paths)
    if refusal is None:
        return None
    return probe_failure(
        probe_run_id=probe_run_id,
        stage=CONFINEMENT_STAGE,
        detail=refusal,
        item_status=cycle.item_status(work_item_id=item.id),
        outcome=CONFINEMENT_ESCAPE_OUTCOME,
        remedy=STOP_REMEDY,
    )


def _merged_escape(
    *, cycle: ProbeCycle, item: WorkItem, probe_run_id: str, detail: str
) -> ProbeResult:
    return probe_failure(
        probe_run_id=probe_run_id,
        stage=CONFINEMENT_STAGE,
        detail=detail,
        item_status=cycle.item_status(work_item_id=item.id),
        outcome=MERGED_ESCAPE_OUTCOME,
        remedy=REVERT_REMEDY,
    )


def _unreadable(*, snapshots: Sequence[ResidueSnapshot]) -> str | None:
    unavailable = tuple(
        f"{snapshot.source}: {snapshot.detail}" for snapshot in snapshots if not snapshot.available
    )
    if not unavailable:
        return None
    return unavailable_detail(unavailable=unavailable)


def _source_unavailable(
    *,
    cycle: ProbeCycle,
    item: WorkItem,
    probe_run_id: str,
    detail: str,
    stage: str = RESIDUE_STAGE,
) -> ProbeResult:
    return probe_failure(
        probe_run_id=probe_run_id,
        stage=stage,
        detail=detail,
        item_status=cycle.item_status(work_item_id=item.id),
        outcome=SOURCE_UNAVAILABLE_OUTCOME,
        remedy=SOURCE_REMEDY,
    )
