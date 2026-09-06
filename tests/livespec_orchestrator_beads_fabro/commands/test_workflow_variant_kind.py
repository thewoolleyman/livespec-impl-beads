"""What KIND of work a registered workflow variant does, read off its own file.

`SPECIFICATION/contracts.md` section "Consensus-gated automated groom cut"
rules that the reserved `implement-work-item` workflow MUST NOT groom and that
a groom variant MUST NOT implement. The kind therefore has to travel with the
VARIANT rather than with the registry line that names its directory, and this
is the reader for it.

TWO DEFAULTS ARE ASSERTED HERE RATHER THAN LEFT IMPLICIT, because each is the
direction a wrong guess would break something silently:

- an undeclared kind reads as `implement`, so every variant registered before
  this key existed keeps dispatching instead of being refused by a build it
  never saw;
- an UNREADABLE manifest also reads as `implement`, so a directory fault
  cannot promote a variant through the groom door. The completeness refusal in
  `_dispatcher_workflow_variant` is what reports that fault; this reader must
  not answer `groom` on the way there.

The module is imported through `importlib` behind a file-existence assertion
so the red half of the ritual fails on a genuine assertion rather than on an
unimportable module.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from livespec_orchestrator_beads_fabro.commands._workflow_variants import (
    RESERVED_WORKFLOW_NAME,
    WorkflowVariant,
)

_MODULE_NAME = "livespec_orchestrator_beads_fabro.commands._workflow_variant_kind"
_MODULE_PATH = Path(
    ".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_workflow_variant_kind.py"
)

_GROOM_DIR = ".fabro/workflows/groom-cut"
_IMPLEMENT_DIR = ".fabro/workflows/codex-first"
_ABSENT_DIR = ".fabro/workflows/never-created"


def _kind_module() -> Any:
    """Import the variant-kind reader, proving the file exists first."""
    assert _MODULE_PATH.is_file()
    return importlib.import_module(_MODULE_NAME)


def _manifest(*, kind: str | None) -> str:
    """A run config whose `[run.inputs]` table declares the kind, or does not."""
    declaration = "" if kind is None else f'workflow_kind = "{kind}"\n'
    return (
        '[workflow]\ngraph = "workflow.fabro"\n\n[run.inputs]\n'
        f"{declaration}"
        'pr_adapter = "npx -y @agentclientprotocol/claude-agent-acp"\n'
    )


def _write_variant(*, repo: Path, directory: str, kind: str | None) -> None:
    target = repo / directory
    target.mkdir(parents=True)
    _ = (target / "workflow.toml").write_text(_manifest(kind=kind), encoding="utf-8")


def _write_registry(*, repo: Path, workflows: dict[str, str]) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _ = (repo / ".livespec.jsonc").write_text(
        json.dumps({"livespec-orchestrator-beads-fabro": {"dispatcher": {"workflows": workflows}}}),
        encoding="utf-8",
    )


def test_the_declared_kind_is_read_off_the_variants_own_run_config() -> None:
    """The kind is a value in the variant's `workflow.toml`, not in the registry."""
    module = _kind_module()

    assert module.declared_workflow_kind(committed_text=_manifest(kind="groom")) == "groom"
    assert module.declared_workflow_kind(committed_text=_manifest(kind="implement")) == "implement"


def test_a_run_config_declaring_no_kind_declares_nothing() -> None:
    """An absent declaration is absent, not an empty-string kind.

    Kept separate from the defaulting cases below so the READER's answer and
    the RESOLVER's default cannot be conflated: one says the file is silent,
    the other says what silence means.
    """
    module = _kind_module()

    assert module.declared_workflow_kind(committed_text=_manifest(kind=None)) is None
    assert module.declared_workflow_kind(committed_text=_manifest(kind="")) is None
    assert module.declared_workflow_kind(committed_text="[workflow]\n") is None


def test_the_reserved_workflow_is_an_implement_variant_without_reading_a_file(
    tmp_path: Path,
) -> None:
    """The reserved name resolves no registry directory, so its kind is structural.

    The contract says outright that `implement-work-item` MUST NOT groom. That
    is not a fact about any file on disk — the reserved name is never read from
    the registry at all — so the resolver answers it without one, which is what
    this case proves by giving it a repository holding nothing.
    """
    module = _kind_module()

    kind = module.variant_kind(
        repo=tmp_path,
        variant=WorkflowVariant(name=RESERVED_WORKFLOW_NAME, directory=None),
    )

    assert kind == module.WORKFLOW_KIND_IMPLEMENT


def test_a_variant_declaring_the_groom_kind_resolves_as_a_groom_variant(
    tmp_path: Path,
) -> None:
    module = _kind_module()
    _write_variant(repo=tmp_path, directory=_GROOM_DIR, kind="groom")
    variant = WorkflowVariant(name="groom-cut", directory=_GROOM_DIR)

    assert module.variant_kind(repo=tmp_path, variant=variant) == module.WORKFLOW_KIND_GROOM
    assert module.is_groom_variant(repo=tmp_path, variant=variant)


def test_a_variant_declaring_no_kind_resolves_as_an_implement_variant(
    tmp_path: Path,
) -> None:
    """Silence means `implement`, so an existing registry keeps dispatching."""
    module = _kind_module()
    _write_variant(repo=tmp_path, directory=_IMPLEMENT_DIR, kind=None)
    variant = WorkflowVariant(name="codex-first", directory=_IMPLEMENT_DIR)

    assert module.variant_kind(repo=tmp_path, variant=variant) == module.WORKFLOW_KIND_IMPLEMENT
    assert not module.is_groom_variant(repo=tmp_path, variant=variant)


def test_a_variant_whose_manifest_cannot_be_read_resolves_as_an_implement_variant(
    tmp_path: Path,
) -> None:
    """A directory fault must not promote a variant through the groom door.

    The failing direction is the one that matters: answering `groom` here would
    let an unreadable directory satisfy the apply gate, and the completeness
    refusal that reports the real fault fires later.
    """
    module = _kind_module()
    variant = WorkflowVariant(name="never-created", directory=_ABSENT_DIR)

    assert module.variant_kind(repo=tmp_path, variant=variant) == module.WORKFLOW_KIND_IMPLEMENT


def test_the_registry_reports_which_of_its_entries_are_groom_variants(
    tmp_path: Path,
) -> None:
    """The registry reads each entry's own declared kind, one file per entry."""
    module = _kind_module()
    repo = tmp_path / "repo"
    _write_registry(
        repo=repo,
        workflows={
            "groom-cut": _GROOM_DIR,
            "codex-first": _IMPLEMENT_DIR,
            "never-created": _ABSENT_DIR,
        },
    )
    _write_variant(repo=repo, directory=_GROOM_DIR, kind="groom")
    _write_variant(repo=repo, directory=_IMPLEMENT_DIR, kind="implement")

    assert module.groom_variant_names(repo=repo) == ("groom-cut",)


def test_a_repository_registering_no_variants_names_no_groom_variants(
    tmp_path: Path,
) -> None:
    module = _kind_module()
    repo = tmp_path / "repo"
    _write_registry(repo=repo, workflows={})

    assert module.groom_variant_names(repo=repo) == ()
