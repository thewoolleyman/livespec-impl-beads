"""Path and config-resolution helpers for the Dispatcher."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._config import resolve_store_config
from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "calibration_spans_path",
    "cost_report_spans_path",
    "cost_sink_path",
    "heartbeat_path",
    "journal_path",
    "plugin_root",
    "reflector_oob_spans_path",
    "run_turn_sink_path",
    "spans_path",
    "state_root",
    "store_config",
    "workflow_toml",
]

# Where a Fabro workflow config sits under whichever root carries it — the
# plugin root for the bundled default, or a dispatch target's own checkout
# for the repo-local override.
_WORKFLOW_SUBPATH = (".fabro", "workflows", "implement-work-item", "workflow.toml")
_RUN_TURN_DATASET = "fabro"


def store_config(*, repo: Path) -> StoreConfig:
    return resolve_store_config(cwd=repo, work_items_arg=None)


def workflow_toml(*, args: argparse.Namespace) -> Path:
    """The committed Fabro workflow config this dispatch runs, by precedence.

    1. An explicit `--workflow <path>` always wins.
    2. Otherwise the DISPATCH TARGET's own committed
       `<repo>/.fabro/workflows/implement-work-item/workflow.toml`, when it
       exists. The workflow config carries the sandbox image pin, so a
       consumer repo whose toolchain differs from the orchestrator's own
       (a Rust repo needing the `python-rust-agent-` layer, against the
       orchestrator's Python-only pin) governs its own execution substrate
       rather than silently inheriting one that cannot build it.
    3. Otherwise the plugin's bundled workflow — the default for every
       dispatch target that commits none.

    `args` is not guaranteed to carry a `repo` attribute: only the
    dispatch-common subparsers define `--repo`, so the repo-local probe
    reads it defensively and degrades to the bundled default.
    """
    if args.workflow is not None:
        return Path(args.workflow)
    repo: object = getattr(args, "repo", None)
    if repo is not None:
        repo_local = Path(str(repo)).joinpath(*_WORKFLOW_SUBPATH)
        if repo_local.is_file():
            return repo_local
    return plugin_root().joinpath(*_WORKFLOW_SUBPATH)


def journal_path(*, args: argparse.Namespace, repo: Path) -> Path:
    if args.journal is not None:
        return Path(args.journal)
    return repo / "tmp" / "fabro-dispatch-journal.jsonl"


def spans_path(*, args: argparse.Namespace, repo: Path) -> Path:
    """Where the mechanical reflection stage appends its OTLP/JSON spans.

    Co-located with the journal (one `<base>-reflection-spans.jsonl`
    sibling) so a future one-shot replay finds both in the same place;
    one `ExportTraceServiceRequest` per line (the family capture format).
    """
    journal = journal_path(args=args, repo=repo)
    return journal.with_name(f"{journal.stem}-reflection-spans.jsonl")


def reflector_oob_spans_path(*, args: argparse.Namespace, repo: Path) -> Path:
    """Where the out-of-band reflector appends its `gen_ai.evaluation.result` spans.

    Co-located with the journal (a `<base>-reflector-oob-spans.jsonl`
    sibling next to the mechanical-reflection spans file) so the verdict
    spans ride the SAME established local-span-file -> enrich egress path;
    one `ExportTraceServiceRequest` per line (the family capture format).
    """
    journal = journal_path(args=args, repo=repo)
    return journal.with_name(f"{journal.stem}-reflector-oob-spans.jsonl")


def heartbeat_path(*, args: argparse.Namespace, repo: Path) -> Path:
    """Where the live receiver writes the per-run metrics heartbeat.

    Co-located with the journal (a `<base>-otel-heartbeat.json` sibling) so
    the liveness probe reads it out of process next to the rest of the
    dispatch's tmp artifacts.
    """
    journal = journal_path(args=args, repo=repo)
    return journal.with_name(f"{journal.stem}-otel-heartbeat.json")


def cost_sink_path(*, args: argparse.Namespace, repo: Path) -> Path:
    """Where the live receiver writes the per-dispatch CC-token cost.

    Co-located with the journal (a `<base>-otel-cost.json` sibling next to
    the heartbeat file) so the cost gate reads the derived per-dispatch
    cost out of process, exactly as the liveness probe reads the heartbeat.
    The receiver accrues each per-API-call token vector here keyed by
    `work.item.id` / `livespec.dispatch.id`.
    """
    journal = journal_path(args=args, repo=repo)
    return journal.with_name(f"{journal.stem}-otel-cost.json")


def run_turn_sink_path(*, args: argparse.Namespace, repo: Path) -> Path:
    """Where any host receiver records successful Fabro `run_turn` exports.

    The OTLP receiver binds one host-global port, so a different repo's
    dispatcher may own the live receiver that successfully exports this repo's
    Fabro spans. Keep the marker host-global and dataset-scoped so the
    timestamp-bounded guard reads the same signal whichever repo owns :4318.
    """
    _ = (args, repo)
    return (
        state_root()
        / "livespec-orchestrator-beads-fabro"
        / "run-turn-exports"
        / f"{_RUN_TURN_DATASET}.json"
    )


def state_root() -> Path:
    """The per-user root for host-local dispatcher state, repo-independent.

    `XDG_STATE_HOME` when set, else `~/.local/state` — the freedesktop
    convention. PUBLIC because more than one surface needs the SAME root
    resolved the same way: the run-turn export marker above, and the
    tenant-checkout registry that makes the WIP-cap counted-claim bound
    tenant-scoped rather than per-checkout. Two checkouts of one tenant
    resolve an identical root, which is the whole point — a per-repo root
    could not be shared between a worktree and a fresh clone.
    """
    state_home = os.environ.get("XDG_STATE_HOME")
    return Path(state_home) if state_home else Path.home() / ".local" / "state"


def cost_report_spans_path(*, args: argparse.Namespace, repo: Path) -> Path:
    """Where report mode appends its `cost.report` OTLP spans."""
    journal = journal_path(args=args, repo=repo)
    return journal.with_name(f"{journal.stem}-cost-report-spans.jsonl")


def calibration_spans_path(*, args: argparse.Namespace, repo: Path) -> Path:
    """Where calibration emission appends its `dispatcher.calibration` OTLP spans."""
    journal = journal_path(args=args, repo=repo)
    return journal.with_name(f"{journal.stem}-calibration-spans.jsonl")


def plugin_root() -> Path:
    """The plugin root, resolving in BOTH the source tree and the flattened cache.

    In source this module lives at
    `.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_paths.py`,
    so the plugin root is `parents[3]` (the `.claude-plugin/` dir). The Claude
    install flattens that dir to the cache root and exports
    `CLAUDE_PLUGIN_ROOT`; when that env var is set and non-empty it wins. Both
    the `.fabro/` workflow payload and the `scripts/bin/` wrappers ship UNDER
    this root, so a cache-installed plugin resolves them with no repo checkout
    present.
    """
    env_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_root:
        return Path(env_root)
    return Path(__file__).resolve().parents[3]
