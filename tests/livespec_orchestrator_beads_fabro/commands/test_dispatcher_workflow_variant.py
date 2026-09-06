"""The three pre-run refusals a workflow-variant registry can earn.

`_workflow_variants` is total by design; `_dispatcher_workflow_variant` is
where a registry the Dispatcher cannot honour becomes a REFUSAL — one carrying
its own journal stage, in the same shape the ACP-node and node-timeout
refusals already take, and every one of them raised BEFORE any Fabro run
exists.

The three causes, and what each test has to prove is NOT happening instead:

- an unregistered selected name — must not quietly run the reserved graph;
- a registered directory missing `workflow.toml` or `workflow.fabro` — must
  not be merged with the bundle to fill the gap;
- a registry entry named `implement-work-item` — must not be silently inert.

The last one is checked FIRST in the implementation because it is a fault of
the table rather than of the selection, so it holds however the selection
resolves; the test that pins that ordering is the one where BOTH faults are
present at once.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_materialize import (
    MaterializationRefusal,
    materialize_dispatch,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_workflow_variant import (
    WORKFLOW_VARIANT_INCOMPLETE_STAGE,
    WORKFLOW_VARIANT_RESERVED_NAME_STAGE,
    WORKFLOW_VARIANT_UNREGISTERED_STAGE,
    WorkflowVariantRefusal,
    prepare_workflow_variant,
)
from livespec_orchestrator_beads_fabro.commands._workflow_variants import (
    RESERVED_WORKFLOW_NAME,
    WorkflowVariant,
)

_VARIANT_DIR = ".fabro/workflows/codex-first"
_REPO_ROOT = Path(__file__).resolve().parents[3]
_COMMITTED_WORKFLOW = (
    _REPO_ROOT / ".claude-plugin" / ".fabro" / "workflows" / "implement-work-item" / "workflow.toml"
)


class _RecordingJournal:
    """Collects journal records so the dispatch record can be asserted on."""

    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


def _write_dispatcher_config(*, repo: Path, block: dict[str, object]) -> None:
    _ = (repo / ".livespec.jsonc").write_text(
        json.dumps({"livespec-orchestrator-beads-fabro": {"dispatcher": block}}),
        encoding="utf-8",
    )


def _registered_repo(*, tmp_path: Path, files: tuple[str, ...]) -> Path:
    """A target registering `codex-first` whose directory holds only `files`."""
    repo = tmp_path / "repo"
    variant = repo / _VARIANT_DIR
    variant.mkdir(parents=True)
    for name in files:
        _ = (variant / name).write_text(f"# {name}\n", encoding="utf-8")
    _write_dispatcher_config(
        repo=repo,
        block={"workflows": {"codex-first": _VARIANT_DIR}, "default_workflow": "codex-first"},
    )
    return repo


def test_a_target_declaring_no_registry_selects_the_reserved_variant(tmp_path: Path) -> None:
    """The unconfigured case reaches the reserved workflow with nothing refused."""
    assert prepare_workflow_variant(repo=tmp_path) == WorkflowVariant(
        name=RESERVED_WORKFLOW_NAME, directory=None
    )


def test_a_complete_registered_variant_resolves(tmp_path: Path) -> None:
    """A directory holding both the manifest and the graph is honoured."""
    repo = _registered_repo(tmp_path=tmp_path, files=("workflow.toml", "workflow.fabro"))

    assert prepare_workflow_variant(repo=repo) == WorkflowVariant(
        name="codex-first", directory=_VARIANT_DIR
    )


def test_an_unregistered_name_is_refused_naming_the_variant(tmp_path: Path) -> None:
    """Refusal one: the selected name matches no registry entry."""
    repo = _registered_repo(tmp_path=tmp_path, files=("workflow.toml", "workflow.fabro"))

    refusal = prepare_workflow_variant(repo=repo, name="typo-first")

    assert isinstance(refusal, WorkflowVariantRefusal)
    assert refusal.stage == WORKFLOW_VARIANT_UNREGISTERED_STAGE
    assert "typo-first" in refusal.detail
    assert "codex-first" in refusal.detail


def test_an_unregistered_name_against_an_empty_registry_says_so(tmp_path: Path) -> None:
    """The refusal names what IS registered, including when that is nothing."""
    refusal = prepare_workflow_variant(repo=tmp_path, name="codex-first")

    assert isinstance(refusal, WorkflowVariantRefusal)
    assert refusal.stage == WORKFLOW_VARIANT_UNREGISTERED_STAGE
    assert "registered: none" in refusal.detail


def test_a_directory_missing_the_graph_is_refused_naming_the_file(tmp_path: Path) -> None:
    """Refusal two: a registered directory that is not a complete workflow."""
    repo = _registered_repo(tmp_path=tmp_path, files=("workflow.toml",))

    refusal = prepare_workflow_variant(repo=repo)

    assert isinstance(refusal, WorkflowVariantRefusal)
    assert refusal.stage == WORKFLOW_VARIANT_INCOMPLETE_STAGE
    assert "workflow.fabro" in refusal.detail
    assert "codex-first" in refusal.detail


def test_a_directory_missing_the_manifest_is_refused_naming_the_file(tmp_path: Path) -> None:
    """The manifest half of refusal two, so neither file is the only one checked."""
    repo = _registered_repo(tmp_path=tmp_path, files=("workflow.fabro",))

    refusal = prepare_workflow_variant(repo=repo)

    assert isinstance(refusal, WorkflowVariantRefusal)
    assert refusal.stage == WORKFLOW_VARIANT_INCOMPLETE_STAGE
    assert "workflow.toml" in refusal.detail
    assert "workflow.fabro" not in refusal.detail


def test_an_empty_registered_directory_names_every_missing_file(tmp_path: Path) -> None:
    """One refusal enumerating every applicable cause, not the first one found."""
    repo = _registered_repo(tmp_path=tmp_path, files=())

    refusal = prepare_workflow_variant(repo=repo)

    assert isinstance(refusal, WorkflowVariantRefusal)
    assert refusal.stage == WORKFLOW_VARIANT_INCOMPLETE_STAGE
    assert "workflow.toml, workflow.fabro" in refusal.detail


def test_a_registry_entry_claiming_the_reserved_name_is_refused(tmp_path: Path) -> None:
    """Refusal three: the reserved name cannot be redefined by a registry entry."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_dispatcher_config(
        repo=repo, block={"workflows": {RESERVED_WORKFLOW_NAME: ".fabro/workflows/hijacked"}}
    )

    refusal = prepare_workflow_variant(repo=repo)

    assert isinstance(refusal, WorkflowVariantRefusal)
    assert refusal.stage == WORKFLOW_VARIANT_RESERVED_NAME_STAGE
    assert RESERVED_WORKFLOW_NAME in refusal.detail


def test_the_reserved_name_conflict_outranks_a_selection_fault(tmp_path: Path) -> None:
    """A table fault is reported as a table fault, whatever the selection does.

    Both faults are present: the registry claims the reserved name AND the
    selected name is unregistered. Reporting the selection would name an entry
    the operator never wrote while leaving the one they did write unmentioned.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_dispatcher_config(
        repo=repo, block={"workflows": {RESERVED_WORKFLOW_NAME: ".fabro/workflows/hijacked"}}
    )

    refusal = prepare_workflow_variant(repo=repo, name="typo-first")

    assert isinstance(refusal, WorkflowVariantRefusal)
    assert refusal.stage == WORKFLOW_VARIANT_RESERVED_NAME_STAGE


def test_materialize_dispatch_routes_a_variant_refusal_to_its_own_stage(
    tmp_path: Path,
) -> None:
    """The refusal reaches the dispatch record before any Fabro run exists.

    The payload and adapter steps share this call site, so the assertion that
    NOTHING was journaled is the load-bearing half: it proves the refusal
    happened at the first step rather than after a payload was materialized.
    """
    repo = _registered_repo(tmp_path=tmp_path, files=("workflow.toml",))
    journal = _RecordingJournal()

    refusal = materialize_dispatch(
        args=argparse.Namespace(workflow=None, repo=str(repo)),
        repo=repo,
        work_item_id="bd-ib-27puvv",
        journal=journal,
    )

    assert isinstance(refusal, MaterializationRefusal)
    assert refusal.stage == WORKFLOW_VARIANT_INCOMPLETE_STAGE
    assert journal.records == []


def test_materialize_dispatch_materializes_the_selected_variant_directory(
    tmp_path: Path,
) -> None:
    """The payload, graph render and adapter layers all read the SELECTED variant.

    The registered directory is a real copy of the shipped workflow, so the
    whole downstream chain genuinely runs against it. Its `workflow.toml` is
    then the file the dispatch materialized — which is what makes the existing
    `acp_nodes` / `node_timeouts` refusals apply to a variant as a peer of the
    reserved workflow rather than being evaluated against a bundle it is not
    running.
    """
    repo = tmp_path / "repo"
    variant = repo / _VARIANT_DIR
    variant.parent.mkdir(parents=True)
    _ = shutil.copytree(_COMMITTED_WORKFLOW.parent, variant)
    _write_dispatcher_config(
        repo=repo,
        block={"workflows": {"codex-first": _VARIANT_DIR}, "default_workflow": "codex-first"},
    )
    journal = _RecordingJournal()

    materialized = materialize_dispatch(
        args=argparse.Namespace(workflow=None, repo=str(repo)),
        repo=repo,
        work_item_id="bd-ib-27puvv",
        journal=journal,
    )

    assert not isinstance(materialized, MaterializationRefusal), materialized
    assert materialized.committed_workflow == variant / "workflow.toml"
    assert [record["stage"] for record in journal.records] == ["node-timeouts", "acp-nodes"]
