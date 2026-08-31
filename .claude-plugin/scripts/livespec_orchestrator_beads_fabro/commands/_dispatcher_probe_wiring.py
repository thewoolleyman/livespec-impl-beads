"""Production composition of the loop probe's cycle and its residue sources.

Kept apart from `_dispatcher_probe` so the probe's REFUSALS and its STAGE
ORDERING can be read, and tested, without the production seams in the way. This
module is the only place that names the live surfaces, which is what makes the
hermetic tier's guarantee checkable: the tests inject their own cycle and
sources, so nothing under test reaches the live Dispatcher, and any future
attempt to smuggle a live call into the probe's own logic would have to move it
out of here first.

BOTH residue sources fail LOUD. `attempt` converts a store or filesystem error
into an unavailable snapshot rather than an empty one, because the whole point
of the residue contract is that an unread surface must never be reported as a
clear one. An exception swallowed into `identifiers=()` would produce the
probe's best-looking possible output from its worst possible input.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from livespec_runtime.attention_item import AttentionItem

from livespec_orchestrator_beads_fabro.commands._dispatcher_default_branch import (
    resolve_default_branch as resolve_repository_default_branch,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    UNRESOLVED_NAME,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import load_items
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import journal_path
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_cycle import DispatchProbeCycle
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_residue import (
    DONE_STATUS,
    ResidueSnapshot,
    ResidueSource,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_reconcile_merged import (
    run_reconcile_merged_command,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_run_commands import (
    run_dispatch_command,
)
from livespec_orchestrator_beads_fabro.commands.needs_attention import build_attention
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt
from livespec_orchestrator_beads_fabro.errors import (
    BeadsCommandError,
    BeadsConnectionError,
    BeadsMappingError,
    BeadsTenantMissingError,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "ATTENTION_SOURCE",
    "LEDGER_SOURCE",
    "AttentionResidueSource",
    "LedgerResidueSource",
    "item_status_of",
    "production_cycle",
    "production_sources",
    "resolve_default_branch",
]

ATTENTION_SOURCE = "attention"
LEDGER_SOURCE = "ledger"

_MISSING_STATUS = "<absent from the tenant>"
_READ_ERRORS = (
    OSError,
    BeadsCommandError,
    BeadsConnectionError,
    BeadsMappingError,
    BeadsTenantMissingError,
)


@dataclass(frozen=True, kw_only=True)
class AttentionResidueSource:
    """The needs-attention surface, snapshotted by attention-item identifier."""

    repo: Path
    read: Callable[..., Sequence[AttentionItem]]

    def snapshot(self) -> ResidueSnapshot:
        gathered = attempt(
            action=lambda: self.read(project_root=self.repo, repo_name=self.repo.name),
            exceptions=_READ_ERRORS,
        )
        if isinstance(gathered, AttemptFailure):
            return ResidueSnapshot(
                source=ATTENTION_SOURCE, available=False, detail=str(gathered.error)
            )
        return ResidueSnapshot(
            source=ATTENTION_SOURCE,
            available=True,
            identifiers=tuple(one.id for one in gathered),
        )


@dataclass(frozen=True, kw_only=True)
class LedgerResidueSource:
    """The ledger's LIVE rows, snapshotted by work-item id.

    Closed rows are excluded on purpose: a `done` item is settled state, not
    residue, so including it would make every completed probe report its own
    designated item as leftover.
    """

    repo: Path
    read: Callable[..., Sequence[WorkItem]]

    def snapshot(self) -> ResidueSnapshot:
        gathered = attempt(action=lambda: self.read(repo=self.repo), exceptions=_READ_ERRORS)
        if isinstance(gathered, AttemptFailure):
            return ResidueSnapshot(
                source=LEDGER_SOURCE, available=False, detail=str(gathered.error)
            )
        return ResidueSnapshot(
            source=LEDGER_SOURCE,
            available=True,
            identifiers=tuple(one.id for one in gathered if one.status != DONE_STATUS),
        )


def production_sources(*, repo: Path) -> tuple[ResidueSource, ...]:
    """The two live residue surfaces the probe snapshots before and after."""
    return (
        AttentionResidueSource(repo=repo, read=build_attention),
        LedgerResidueSource(repo=repo, read=load_items),
    )


def item_status_of(*, repo: Path, work_item_id: str) -> str:
    """The designated item's current lifecycle state, or an explicit absence mark."""
    found = next((one for one in load_items(repo=repo) if one.id == work_item_id), None)
    return _MISSING_STATUS if found is None else found.status


def resolve_default_branch(*, repo: Path, runner: CommandRunner) -> str:
    """The governed repository's default branch, or the name sentinel when silent.

    A THIN PROJECTION OF THE ONE SHARED RESOLUTION, not a second probe. This
    module used to carry its own `git symbolic-ref` read and its own branch-name
    fallback -- a second answer to a question the ratified
    default-branch-resolution clause gives one resolver, and the constant that
    clause retires. An adopter whose primary branch is not this fleet's got a
    clean, plausible, wrong answer from it, and the probe's `git diff` then
    compared against a range that is not theirs.

    The sentinel is what a silent probe answers, exactly as the resolved contract
    renders an unresolvable REQUIRED field. Nothing is guessed: the probe's own
    diff then fails on a ref nobody could name and reports itself unreadable,
    which is the outcome its residue contract is built around.
    """
    resolved = resolve_repository_default_branch(repo=repo, runner=runner)
    return UNRESOLVED_NAME if resolved is None else resolved


def production_cycle(*, args: argparse.Namespace, repo: Path) -> DispatchProbeCycle:
    """The live cycle: the published dispatch and reconcile surfaces, in order."""
    runner = ShellCommandRunner()

    def status_lookup(*, work_item_id: str) -> str:
        return item_status_of(repo=repo, work_item_id=work_item_id)

    return DispatchProbeCycle(
        args=args,
        repo=repo,
        runner=runner,
        journal_path=journal_path(args=args, repo=repo),
        default_branch=resolve_default_branch(repo=repo, runner=runner),
        drive=run_dispatch_command,
        complete=run_reconcile_merged_command,
        item_status_lookup=status_lookup,
    )
