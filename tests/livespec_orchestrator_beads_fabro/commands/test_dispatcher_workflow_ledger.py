"""The four arms of the workflow-variant ledger pin, and where the name lands.

`SPECIFICATION/contracts.md` section "Named workflow variants" resolves the
variant most specific first: an explicit `--workflow-name`, then the name a
prior dispatch of the SAME work-item recorded, then
`dispatcher.default_workflow`, then the reserved name. Each arm gets its own
test because each fails invisibly in a different direction:

- explicit losing to a recorded name would silently ignore the operator;
- a recorded name losing to the default would move a half-finished item onto
  a different graph mid-flight, with the item's record saying nothing;
- a STALE recorded name winning would pin an item to a directory the target
  no longer registers, and every retry would refuse identically;
- the default arm is the one every unconfigured target takes.

The non-arm tests pin the things no arm can: that the selector is never read
from the environment, that the args clone is what the dispatch path hands on,
and that a Namespace which never carried the argument still resolves. The CLI
SURFACE feeding this resolution — the `--workflow-name` argument itself, its
re-emission by `drive`, and the `workflow_name` field on the dispatch record —
is covered beside each module that declares it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._store_dispatch_workflow import (
    dispatch_workflow_for,
    record_dispatch_workflow,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_workflow_ledger import (
    args_with_dispatch_workflow_name,
    resolve_dispatch_workflow_name,
)
from livespec_orchestrator_beads_fabro.commands._workflow_variants import (
    RESERVED_WORKFLOW_NAME,
)
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

_VARIANT_DIR = ".fabro/workflows/codex-first"
_OTHER_VARIANT_DIR = ".fabro/workflows/claude-first"


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="livespec-impl-beads",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _item(*, item_id: str) -> WorkItem:
    return WorkItem(
        id=item_id,
        type="task",
        status="ready",
        title="Workflow variant",
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee=None,
        depends_on=(),
        captured_at="2026-09-06T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )


def _repo(*, tmp_path: Path, dispatcher: dict[str, object]) -> Path:
    """A dispatch target whose `dispatcher` block is exactly `dispatcher`."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        json.dumps(
            {
                "livespec-orchestrator-beads-fabro": {
                    "connection": {"prefix": "bd-ib"},
                    "dispatcher": dispatcher,
                }
            }
        ),
        encoding="utf-8",
    )
    return repo


def _registry_repo(*, tmp_path: Path) -> Path:
    """A target registering two variants and defaulting to `codex-first`."""
    return _repo(
        tmp_path=tmp_path,
        dispatcher={
            "workflows": {"codex-first": _VARIANT_DIR, "claude-first": _OTHER_VARIANT_DIR},
            "default_workflow": "codex-first",
        },
    )


def test_an_explicit_name_outranks_the_recorded_one_and_is_recorded_in_turn(
    tmp_path: Path,
) -> None:
    """Arm one: `--workflow-name` wins, and the item is re-pinned to it."""
    repo = _registry_repo(tmp_path=tmp_path)
    append_work_item(path=_config(), item=_item(item_id="li-wfl-explicit"))
    record_dispatch_workflow(path=_config(), work_item_id="li-wfl-explicit", workflow="codex-first")

    resolved = resolve_dispatch_workflow_name(
        args=argparse.Namespace(workflow_name="claude-first"),
        repo=repo,
        work_item_id="li-wfl-explicit",
    )

    assert resolved == "claude-first"
    assert dispatch_workflow_for(path=_config(), work_item_id="li-wfl-explicit") == "claude-first"


def test_a_retry_with_no_explicit_name_reuses_the_recorded_variant(tmp_path: Path) -> None:
    """Arm two: the recorded name outranks a `default_workflow` that has moved.

    The default is `codex-first` and the record says `claude-first`, so a
    result of `claude-first` can only come from the recorded pin.
    """
    repo = _registry_repo(tmp_path=tmp_path)
    append_work_item(path=_config(), item=_item(item_id="li-wfl-retry"))
    record_dispatch_workflow(path=_config(), work_item_id="li-wfl-retry", workflow="claude-first")

    resolved = resolve_dispatch_workflow_name(
        args=argparse.Namespace(workflow_name=None),
        repo=repo,
        work_item_id="li-wfl-retry",
    )

    assert resolved == "claude-first"
    assert dispatch_workflow_for(path=_config(), work_item_id="li-wfl-retry") == "claude-first"


def test_a_recorded_reserved_name_survives_a_target_that_registers_variants(
    tmp_path: Path,
) -> None:
    """The reserved name is always usable, so it is never treated as stale.

    It is defined whether or not a registry exists and is never read from one,
    so an item that last ran the reserved workflow must keep running it even
    once the target declares a default variant.
    """
    repo = _registry_repo(tmp_path=tmp_path)
    append_work_item(path=_config(), item=_item(item_id="li-wfl-reserved"))
    record_dispatch_workflow(
        path=_config(), work_item_id="li-wfl-reserved", workflow=RESERVED_WORKFLOW_NAME
    )

    resolved = resolve_dispatch_workflow_name(
        args=argparse.Namespace(workflow_name=None),
        repo=repo,
        work_item_id="li-wfl-reserved",
    )

    assert resolved == RESERVED_WORKFLOW_NAME


def test_a_recorded_name_that_left_the_registry_falls_through_to_the_default(
    tmp_path: Path,
) -> None:
    """Arm three: a renamed-away variant re-resolves rather than pinning a hole.

    The re-pin is the half worth asserting: leaving the stale name recorded
    would make every later retry re-take this fallback, so the item would
    never converge on the variant it is actually running.
    """
    repo = _registry_repo(tmp_path=tmp_path)
    append_work_item(path=_config(), item=_item(item_id="li-wfl-stale"))
    record_dispatch_workflow(path=_config(), work_item_id="li-wfl-stale", workflow="retired-first")

    resolved = resolve_dispatch_workflow_name(
        args=argparse.Namespace(workflow_name=None),
        repo=repo,
        work_item_id="li-wfl-stale",
    )

    assert resolved == "codex-first"
    assert dispatch_workflow_for(path=_config(), work_item_id="li-wfl-stale") == "codex-first"


def test_an_unpinned_item_takes_the_configured_default(tmp_path: Path) -> None:
    """Arm four: a first dispatch resolves `dispatcher.default_workflow`."""
    repo = _registry_repo(tmp_path=tmp_path)
    append_work_item(path=_config(), item=_item(item_id="li-wfl-default"))

    resolved = resolve_dispatch_workflow_name(
        args=argparse.Namespace(workflow_name=None),
        repo=repo,
        work_item_id="li-wfl-default",
    )

    assert resolved == "codex-first"
    assert dispatch_workflow_for(path=_config(), work_item_id="li-wfl-default") == "codex-first"


def test_a_target_declaring_no_registry_pins_the_reserved_name(tmp_path: Path) -> None:
    """Every dispatch records a name, including the one nobody configured."""
    repo = _repo(tmp_path=tmp_path, dispatcher={})
    append_work_item(path=_config(), item=_item(item_id="li-wfl-bare"))

    resolved = resolve_dispatch_workflow_name(
        args=argparse.Namespace(workflow_name=None),
        repo=repo,
        work_item_id="li-wfl-bare",
    )

    assert resolved == RESERVED_WORKFLOW_NAME
    assert (
        dispatch_workflow_for(path=_config(), work_item_id="li-wfl-bare") == RESERVED_WORKFLOW_NAME
    )


def test_no_environment_variable_selects_the_workflow_variant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The selector is a recorded ARGUMENT, so an ambient shell cannot move it.

    Every name an environment layer could plausibly have been spelled under is
    set to a REGISTERED variant that is not the default, so any one of them
    being read would change the answer. The default arm surviving all of them
    is what proves no such layer exists.
    """
    repo = _registry_repo(tmp_path=tmp_path)
    append_work_item(path=_config(), item=_item(item_id="li-wfl-env"))
    for name in (
        "LIVESPEC_WORKFLOW_NAME",
        "LIVESPEC_FABRO_WORKFLOW",
        "LIVESPEC_WORKFLOW",
        "WORKFLOW_NAME",
    ):
        monkeypatch.setenv(name, "claude-first")

    resolved = resolve_dispatch_workflow_name(
        args=argparse.Namespace(workflow_name=None),
        repo=repo,
        work_item_id="li-wfl-env",
    )

    assert resolved == "codex-first"


def test_the_args_clone_carries_the_pinned_name_without_mutating_the_original(
    tmp_path: Path,
) -> None:
    """The clone is what the dispatch path hands on, exactly as the factory pin is."""
    repo = _registry_repo(tmp_path=tmp_path)
    append_work_item(path=_config(), item=_item(item_id="li-wfl-clone"))
    args = argparse.Namespace(workflow_name=None, keep="value")

    cloned = args_with_dispatch_workflow_name(
        args=args,
        repo=repo,
        work_item_id="li-wfl-clone",
    )

    assert cloned is not args
    assert cloned.keep == "value"
    assert cloned.workflow_name == "codex-first"
    assert args.workflow_name is None


def test_a_namespace_without_the_argument_resolves_rather_than_raising(
    tmp_path: Path,
) -> None:
    """The reconcile and check entry points never carry `--workflow-name`."""
    repo = _registry_repo(tmp_path=tmp_path)
    append_work_item(path=_config(), item=_item(item_id="li-wfl-absent"))

    resolved = resolve_dispatch_workflow_name(
        args=argparse.Namespace(),
        repo=repo,
        work_item_id="li-wfl-absent",
    )

    assert resolved == "codex-first"
