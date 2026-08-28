"""The loop probe entry point: `probe --item`, the take-never-file cycle demo.

The loop-probe clause of `SPECIFICATION/contracts.md` ratifies a health command
that drives ONE designated, ALREADY-FILED work-item through the whole cycle with
an assertion at each stage. This module is the composition root and nothing
else: the three bracketing refusals live in `_dispatcher_probe_refusals`, the
ordered drive in `_dispatcher_probe_drive`, the grading of what came back in
`_dispatcher_probe_observation`, the verdict and its rendering in
`_dispatcher_probe_report`, and the live machinery behind
`_dispatcher_probe_wiring`.

WHAT THIS FILE IS RESPONSIBLE FOR is the sequence in which the entry point
arms them: every refusal fires BEFORE the run identifier is minted, before the
journal is opened, and before anything is driven. A refusal that fired after any
of those would have performed the act it exists to prevent, and would leave a
journal record attributing a probe that never legitimately started.

`cycle` and `sources` are injectable for the hermetic tier and default to the
live composition. That default is the ONLY route from this command to the live
Dispatcher, which is what lets the whole test suite exercise the probe against
`FakeBeadsClient` without ever reaching it.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_command_common import (
    EXIT_FAILURE,
    EXIT_PRECONDITION_ERROR,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import (
    InvokerIdentity,
    invoker_from_args,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile, utc_now_iso
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import load_items
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import journal_path
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_cycle import ProbeCycle
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_drive import run_probe_cycle
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_refusals import (
    acceptance_policy_refusal,
    designated_item_refusal,
    fallback_invoker_refusal,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_report import (
    emit_probe_result,
    probe_result_record,
    probe_run_identifier,
    probe_start_record,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_residue import ResidueSource
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_wiring import (
    production_cycle,
    production_sources,
)
from livespec_orchestrator_beads_fabro.io import write_stderr
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "run_probe_command",
]


def run_probe_command(
    *,
    args: argparse.Namespace,
    cycle: ProbeCycle | None = None,
    sources: Sequence[ResidueSource] | None = None,
) -> int:
    """The `probe --item` entry point: refuse, journal, drive, and report."""
    repo = Path(args.repo)
    designated = designated_item_refusal(item_id=getattr(args, "item", None))
    if designated is not None:
        _ = write_stderr(text=designated)
        return EXIT_PRECONDITION_ERROR
    identity = invoker_from_args(args=args)
    unattributed = fallback_invoker_refusal(identity=identity)
    if unattributed is not None:
        _ = write_stderr(text=unattributed)
        return EXIT_PRECONDITION_ERROR
    item = next((one for one in load_items(repo=repo) if one.id == args.item), None)
    if item is None:
        _ = write_stderr(text=f"ERROR: work-item {args.item} is not in the tenant at {repo}\n")
        return EXIT_PRECONDITION_ERROR
    policy = acceptance_policy_refusal(item=item, cwd=repo)
    if policy is not None:
        _ = write_stderr(text=policy)
        return EXIT_PRECONDITION_ERROR
    return _journalled_probe(
        args=args,
        repo=repo,
        item=item,
        identity=identity,
        cycle=cycle if cycle is not None else production_cycle(args=args, repo=repo),
        sources=sources if sources is not None else production_sources(repo=repo),
    )


def _journalled_probe(
    *,
    args: argparse.Namespace,
    repo: Path,
    item: WorkItem,
    identity: InvokerIdentity,
    cycle: ProbeCycle,
    sources: Sequence[ResidueSource],
) -> int:
    probe_run_id = probe_run_identifier(work_item_id=item.id, started_at=utc_now_iso())
    journal = JournalFile(path=journal_path(args=args, repo=repo), identity=identity)
    journal.append(record=probe_start_record(work_item_id=item.id, probe_run_id=probe_run_id))
    result = run_probe_cycle(item=item, cycle=cycle, sources=sources, probe_run_id=probe_run_id)
    journal.append(record=probe_result_record(result=result))
    emit_probe_result(result=result, as_json=args.as_json)
    return 0 if result.passed else EXIT_FAILURE
