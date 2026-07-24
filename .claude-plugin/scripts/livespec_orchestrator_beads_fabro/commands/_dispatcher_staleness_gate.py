"""Release-currency gate for dispatcher plugin builds."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner
from livespec_orchestrator_beads_fabro.io import write_stderr

__all__: list[str] = [
    "DispatcherStalenessDecision",
    "DispatcherStalenessMessage",
    "apply_dispatcher_staleness_gate",
    "dispatcher_staleness_decision",
    "latest_release_ref_argv",
    "master_ref_argv",
    "unreleased_dispatcher_commits_argv",
]

_REPO_URL = "https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro.git"
_RELEASE_REF = "refs/heads/release"
_MASTER_REF = "refs/heads/master"
_PROBE_TIMEOUT_SECONDS = 60.0
_EXIT_PRECONDITION_ERROR = 3
_BUILD_ID_MINIMUM_LENGTH = 7
_BUILD_ID_MAXIMUM_LENGTH = 40
_HEX_DIGITS = frozenset("0123456789abcdef")
_PLUGIN_UPDATE_REMEDY = (
    "claude plugin update livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro"
)
_DISPATCHER_PATHS: tuple[str, ...] = (
    ".claude-plugin/scripts/livespec_orchestrator_beads_fabro/",
    ".claude-plugin/scripts/bin/",
    ".claude-plugin/scripts/_bootstrap.py",
)


class _StalenessJournal(Protocol):
    """Append-only journal seam for the pre-admission staleness gate."""

    def append(self, *, record: dict[str, object]) -> None:
        """Persist one journal record."""
        ...


@dataclass(frozen=True, kw_only=True)
class DispatcherStalenessMessage:
    """One operator-facing staleness gate message."""

    detail: str


@dataclass(frozen=True, kw_only=True)
class DispatcherStalenessDecision:
    """The staleness gate result: at most one refusal plus zero or more warnings."""

    refusal: DispatcherStalenessMessage | None
    warnings: tuple[DispatcherStalenessMessage, ...]


def latest_release_ref_argv() -> tuple[str, ...]:
    """Probe the newest installable release artifact."""
    return ("git", "ls-remote", _REPO_URL, _RELEASE_REF)


def master_ref_argv() -> tuple[str, ...]:
    """Probe raw master only for the non-blocking unreleased-code warning."""
    return ("git", "ls-remote", _REPO_URL, _MASTER_REF)


def unreleased_dispatcher_commits_argv(*, release_sha: str, master_sha: str) -> tuple[str, ...]:
    """List dispatcher-own commits present on master but absent from release."""
    return (
        "git",
        "log",
        "--oneline",
        f"{release_sha}..{master_sha}",
        "--",
        *_DISPATCHER_PATHS,
    )


def dispatcher_staleness_decision(
    *,
    plugin_root: Path,
    runner: CommandRunner,
) -> DispatcherStalenessDecision:
    """Compare the executing build to release; warn separately on unreleased master.

    The gate refuses ONLY when the executing build PROVABLY predates the latest
    release. Identity is established FIRST: a git-checkout plugin root is
    exempt, and a root that is neither a checkout nor a release-cache sha
    prefix has no provable identity — the gate warns and proceeds WITHOUT any
    network probe (the bd-ib-n7ce4n deadlock case: a verdict that cannot be
    established must never block dispatch).
    """
    if _git_checkout_head(plugin_root=plugin_root, runner=runner) is not None:
        return DispatcherStalenessDecision(refusal=None, warnings=())
    build_id = _executing_cache_build_id(plugin_root=plugin_root)
    if build_id is None:
        return DispatcherStalenessDecision(
            refusal=None,
            warnings=(
                DispatcherStalenessMessage(
                    detail=(
                        "WARNING: dispatcher staleness gate could not establish the "
                        f"executing build identity (plugin root {plugin_root.name!r} is "
                        "neither a git checkout nor a release-cache build id); "
                        "dispatch proceeds without a plugin-currency verdict."
                    )
                ),
            ),
        )
    release_sha = _remote_ref_sha(runner=runner, argv=latest_release_ref_argv())
    if release_sha is None:
        return DispatcherStalenessDecision(
            refusal=None,
            warnings=(
                DispatcherStalenessMessage(
                    detail=(
                        "WARNING: dispatcher staleness gate could not inspect latest release; "
                        "dispatch proceeds without a plugin-currency verdict."
                    )
                ),
            ),
        )
    master_sha = _remote_ref_sha(runner=runner, argv=master_ref_argv())
    refusal = _stale_refusal(
        build_id=build_id,
        release_sha=release_sha,
        master_sha=master_sha,
    )
    warnings = (
        ()
        if refusal is not None
        else _master_ahead_warnings(
            runner=runner,
            release_sha=release_sha,
            master_sha=master_sha,
        )
    )
    return DispatcherStalenessDecision(refusal=refusal, warnings=warnings)


def apply_dispatcher_staleness_gate(
    *,
    plugin_root: Path,
    journal: _StalenessJournal,
    runner: CommandRunner | None = None,
) -> int | None:
    """Emit the staleness decision; return an exit code only when dispatch must stop."""
    decision = dispatcher_staleness_decision(
        plugin_root=plugin_root,
        runner=runner if runner is not None else ShellCommandRunner(),
    )
    for warning in decision.warnings:
        _ = write_stderr(text=f"{warning.detail}\n")
        journal.append(
            record={
                "stage": "dispatcher-staleness-warning",
                "detail": warning.detail,
                "blocking": False,
            }
        )
    if decision.refusal is None:
        return None
    _ = write_stderr(text=f"{decision.refusal.detail}\n")
    journal.append(
        record={
            "stage": "dispatcher-staleness-refused",
            "detail": decision.refusal.detail,
            "blocking": True,
        }
    )
    return _EXIT_PRECONDITION_ERROR


def _remote_ref_sha(*, runner: CommandRunner, argv: tuple[str, ...]) -> str | None:
    result = runner.run(
        argv=list(argv),
        cwd=Path.cwd(),
        timeout_seconds=_PROBE_TIMEOUT_SECONDS,
    )
    if result.exit_code != 0:
        return None
    first = result.stdout.strip().split(maxsplit=1)
    return first[0] if first else None


def _executing_cache_build_id(*, plugin_root: Path) -> str | None:
    """The flattened-cache build id, or None when the name is not a sha prefix."""
    name = plugin_root.name.strip()
    if not (_BUILD_ID_MINIMUM_LENGTH <= len(name) <= _BUILD_ID_MAXIMUM_LENGTH):
        return None
    return name if all(char in _HEX_DIGITS for char in name) else None


def _git_checkout_head(*, plugin_root: Path, runner: CommandRunner) -> str | None:
    result = runner.run(
        argv=["git", "-C", str(plugin_root), "rev-parse", "HEAD"],
        cwd=Path.cwd(),
        timeout_seconds=_PROBE_TIMEOUT_SECONDS,
    )
    if result.exit_code != 0:
        return None
    sha = result.stdout.strip()
    return sha if sha else None


def _stale_refusal(
    *,
    build_id: str,
    release_sha: str,
    master_sha: str | None,
) -> DispatcherStalenessMessage | None:
    if _build_matches_ref(build_id=build_id, ref_sha=release_sha) or (
        master_sha is not None and _build_matches_ref(build_id=build_id, ref_sha=master_sha)
    ):
        return None
    return DispatcherStalenessMessage(
        detail=(
            "ERROR: dispatcher plugin build is stale; executing build "
            f"{build_id} predates latest release {release_sha[:12]}. "
            f"Run `{_PLUGIN_UPDATE_REMEDY}` before dispatching."
        )
    )


def _build_matches_ref(*, build_id: str, ref_sha: str) -> bool:
    return ref_sha.startswith(build_id) or build_id.startswith(ref_sha)


def _master_ahead_warnings(
    *,
    runner: CommandRunner,
    release_sha: str,
    master_sha: str | None,
) -> tuple[DispatcherStalenessMessage, ...]:
    if master_sha is None or master_sha == release_sha:
        return ()
    commits = _unreleased_dispatcher_commits(
        runner=runner,
        release_sha=release_sha,
        master_sha=master_sha,
    )
    if commits == ():
        commits = (master_sha[:12],)
    return (
        DispatcherStalenessMessage(
            detail=(
                "WARNING: master contains unreleased dispatcher commit(s): "
                f"{'; '.join(commits)}; a release must be cut before this code takes effect."
            )
        ),
    )


def _unreleased_dispatcher_commits(
    *,
    runner: CommandRunner,
    release_sha: str,
    master_sha: str,
) -> tuple[str, ...]:
    result = runner.run(
        argv=list(
            unreleased_dispatcher_commits_argv(
                release_sha=release_sha,
                master_sha=master_sha,
            )
        ),
        cwd=Path.cwd(),
        timeout_seconds=_PROBE_TIMEOUT_SECONDS,
    )
    if result.exit_code != 0:
        return ()
    return tuple(line for line in result.stdout.splitlines() if line.strip())
