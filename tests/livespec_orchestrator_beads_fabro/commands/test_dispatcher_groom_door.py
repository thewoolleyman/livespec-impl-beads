"""The groom door: the one route by which a `backlog` item enters `active`.

`SPECIFICATION/contracts.md` section "Grooming and slice-size calibration" ->
"Consensus-gated automated groom cut" makes the groom dispatch a DOOR rather
than a new admission rule. The defined `admit` verb stays `ready -> active`,
the Dispatcher MUST NOT admit a `backlog` item on its own initiative, and the
`groom` front-end's operator is what opens the door.

WHAT IS MEASURED, AND WHY IT IS THE STORE. A groom dispatch's answer is three
persisted facts — the item's status, the claim held over it, and the workflow
pin that decides which graph its next dispatch runs — and the return value is
merely a report of them. So every case here reads all three back through the
store and the lock seam rather than asserting on what the function said, which
is what makes the test capable of catching a door that reports success and
writes nothing.

THE ORDER OF THE TWO WRITES IS ITSELF ASSERTED, in the refusal cases. The pin
is written BEFORE the status move, because an item that reached `active`
carrying no pin would be picked up by the ordinary drain and dispatched under
`dispatcher.default_workflow` — the exact substitution the apply gate exists to
refuse. A refusal therefore has to leave BOTH unwritten, and each refusal case
checks both.

THE LOOP-SELECTION CASE IS THE DOOR'S COUNTERPART. "A groom dispatch is the
ONLY way a backlog item enters active" is two claims, and this file's other
cases only prove the first. The second — that the drain does not open the same
door on its own — is a property of the selection predicate, so it is asserted
against that predicate directly with a `backlog` item that is otherwise
perfectly dispatchable.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from livespec_orchestrator_beads_fabro._beads_client import reset_fake_singleton
from livespec_orchestrator_beads_fabro._store_dispatch_workflow import dispatch_workflow_for
from livespec_orchestrator_beads_fabro.commands._dispatcher_dispatch_lock import (
    live_dispatch_lock,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_selection import ready_items
from livespec_orchestrator_beads_fabro.store import append_work_item, read_work_items
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem
from livespec_runtime.work_items.types import WorkItemStatus

_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._dispatcher_groom_door"
_MODULE_PATH = Path(
    ".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_groom_door.py"
)

_ITEM_ID = "bd-ib-groom-door"
_GROOM_VARIANT = "groom-cut"
_GROOM_DIR = ".fabro/workflows/groom-cut"
_IMPLEMENT_VARIANT = "codex-first"
_IMPLEMENT_DIR = ".fabro/workflows/codex-first"


def _door_module() -> Any:
    """Import the groom-door module, proving the file exists first."""
    assert _MODULE_PATH.is_file()
    return importlib.import_module(_MODULE_NAME)


class _RecordingJournal:
    """Collects journal records so the groom-dispatch row can be asserted on."""

    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="livespec-impl-beads",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _manifest(*, kind: str) -> str:
    return f'[workflow]\ngraph = "workflow.fabro"\n\n[run.inputs]\nworkflow_kind = "{kind}"\n'


def _repo(*, tmp_path: Path) -> Path:
    """A target registering one groom variant and one implement variant."""
    repo = tmp_path / "repo"
    for directory, kind in ((_GROOM_DIR, "groom"), (_IMPLEMENT_DIR, "implement")):
        target = repo / directory
        target.mkdir(parents=True)
        _ = (target / "workflow.toml").write_text(_manifest(kind=kind), encoding="utf-8")
    _ = (repo / ".livespec.jsonc").write_text(
        json.dumps(
            {
                "livespec-orchestrator-beads-fabro": {
                    "connection": {
                        "tenant": "livespec-impl-beads",
                        "prefix": "livespec-impl-beads",
                        "server_user": "livespec-impl-beads",
                        "database": "livespec-impl-beads",
                        "bd_path": "bd",
                        "fake": True,
                    },
                    "dispatcher": {
                        "workflows": {
                            _GROOM_VARIANT: _GROOM_DIR,
                            _IMPLEMENT_VARIANT: _IMPLEMENT_DIR,
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return repo


def _item(
    *,
    item_id: str = _ITEM_ID,
    status: WorkItemStatus = "backlog",
    rank: str = "m",
) -> WorkItem:
    return WorkItem(
        id=item_id,
        type="task",
        status=status,
        title="An epic with more than one coherent done",
        description="It carries more than one coherent done.",
        origin="freeform",
        gap_id=None,
        rank=rank,
        assignee=None,
        depends_on=(),
        captured_at="2026-09-06T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        acceptance_criteria="- The epic is decomposed.",
    )


def _filed(*, status: WorkItemStatus = "backlog") -> WorkItem:
    reset_fake_singleton()
    item = _item(status=status)
    append_work_item(path=_config(), item=item)
    return item


def _stored_status(*, item_id: str) -> str:
    return next(item.status for item in read_work_items(path=_config()) if item.id == item_id)


def test_the_door_takes_a_backlog_item_to_active_under_a_claim_and_a_pin(
    tmp_path: Path,
) -> None:
    """All three facts are read back from the store, never from the return value."""
    module = _door_module()
    repo = _repo(tmp_path=tmp_path)
    item = _filed()
    journal = _RecordingJournal()

    opened = module.groom_dispatch(repo=repo, item=item, variant=_GROOM_VARIANT, journal=journal)

    assert not isinstance(opened, module.GroomDoorRefusal)
    assert _stored_status(item_id=_ITEM_ID) == "active"
    assert live_dispatch_lock(repo=repo, work_item_id=_ITEM_ID) is not None
    assert dispatch_workflow_for(path=_config(), work_item_id=_ITEM_ID) == _GROOM_VARIANT


def test_the_groom_dispatch_journal_row_carries_the_groom_variant_name(
    tmp_path: Path,
) -> None:
    """`workflow_name` is the field a dispatch record already names a variant in.

    The row uses that field rather than a groom-specific one so a reader
    surveying which graph ran for an item does not have to know that grooming
    exists to find the answer.
    """
    module = _door_module()
    repo = _repo(tmp_path=tmp_path)
    journal = _RecordingJournal()

    _ = module.groom_dispatch(repo=repo, item=_filed(), variant=_GROOM_VARIANT, journal=journal)

    rows = [row for row in journal.records if row["stage"] == module.GROOM_DISPATCH_STAGE]
    assert len(rows) == 1
    assert rows[0]["workflow_name"] == _GROOM_VARIANT
    assert rows[0]["work_item_id"] == _ITEM_ID
    assert rows[0]["from_status"] == "backlog"


def test_an_item_that_is_not_in_backlog_is_refused_with_nothing_written(
    tmp_path: Path,
) -> None:
    """The door opens from `backlog` only; `ready -> active` is the admit verb."""
    module = _door_module()
    repo = _repo(tmp_path=tmp_path)
    item = _filed(status="ready")
    journal = _RecordingJournal()

    refusal = module.groom_dispatch(repo=repo, item=item, variant=_GROOM_VARIANT, journal=journal)

    assert isinstance(refusal, module.GroomDoorRefusal)
    assert refusal.cause == module.GROOM_DOOR_NOT_BACKLOG
    assert _stored_status(item_id=_ITEM_ID) == "ready"
    assert live_dispatch_lock(repo=repo, work_item_id=_ITEM_ID) is None
    assert dispatch_workflow_for(path=_config(), work_item_id=_ITEM_ID) is None


def test_a_variant_that_is_not_a_groom_variant_is_refused_with_nothing_written(
    tmp_path: Path,
) -> None:
    """An implement variant must not reach the door, however it is named.

    The refused variant here is REGISTERED and complete — the only thing wrong
    with it is its declared kind — so a door that checked registration alone
    would pass this case.
    """
    module = _door_module()
    repo = _repo(tmp_path=tmp_path)
    journal = _RecordingJournal()

    refusal = module.groom_dispatch(
        repo=repo, item=_filed(), variant=_IMPLEMENT_VARIANT, journal=journal
    )

    assert isinstance(refusal, module.GroomDoorRefusal)
    assert refusal.cause == module.GROOM_DOOR_NOT_A_GROOM_VARIANT
    assert _GROOM_VARIANT in refusal.detail
    assert _stored_status(item_id=_ITEM_ID) == "backlog"
    assert live_dispatch_lock(repo=repo, work_item_id=_ITEM_ID) is None
    assert dispatch_workflow_for(path=_config(), work_item_id=_ITEM_ID) is None


def test_an_unregistered_variant_is_refused_with_nothing_written(tmp_path: Path) -> None:
    module = _door_module()
    repo = _repo(tmp_path=tmp_path)
    journal = _RecordingJournal()

    refusal = module.groom_dispatch(
        repo=repo, item=_filed(), variant="never-registered", journal=journal
    )

    assert isinstance(refusal, module.GroomDoorRefusal)
    assert refusal.cause == module.GROOM_DOOR_NOT_A_GROOM_VARIANT
    assert _stored_status(item_id=_ITEM_ID) == "backlog"


def test_every_refusal_is_journaled_under_its_own_stage(tmp_path: Path) -> None:
    """A refused door still leaves a record; a silent no-op would not.

    The stage differs from the success stage so a reader counting groom
    dispatches cannot accidentally count refusals among them.
    """
    module = _door_module()
    repo = _repo(tmp_path=tmp_path)
    journal = _RecordingJournal()

    _ = module.groom_dispatch(
        repo=repo, item=_filed(status="ready"), variant=_GROOM_VARIANT, journal=journal
    )

    stages = [row["stage"] for row in journal.records]
    assert stages == [module.GROOM_DOOR_REFUSED_STAGE]


def test_the_dispatcher_loop_never_selects_a_backlog_item(tmp_path: Path) -> None:
    """The drain's own predicate is what keeps the door single-entry.

    The `backlog` item here is otherwise fully dispatchable — ranked, typed,
    with acceptance criteria and no blockers — so its exclusion is the STATUS
    and nothing else, which is the claim the contract makes.
    """
    _ = _door_module()
    repo = _repo(tmp_path=tmp_path)
    backlog = _item()
    ready = _item(item_id="bd-ib-ready-peer", status="ready", rank="n")

    selected = ready_items(items=[backlog, ready], repo=repo)

    assert [item.id for item in selected] == [ready.id]
