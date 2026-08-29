"""The non-blocking "master carries unreleased dispatcher code" surfacing.

A distinct concern from the executing build's CURRENCY: this says nothing about
which payload is running, only that dispatcher-own code has landed on master and
has not been released yet, so it cannot take effect on the dispatch path until a
release is cut. It has never had blocking authority and does not acquire any
here.

Reports a plain string so the currency gate owns the message vocabulary without
this module having to import it back.
"""

from __future__ import annotations

from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandRunner

__all__: list[str] = [
    "unreleased_dispatcher_commits_argv",
    "unreleased_master_detail",
]

_PROBE_TIMEOUT_SECONDS = 60.0
_DISPATCHER_PATHS: tuple[str, ...] = (
    ".claude-plugin/scripts/livespec_orchestrator_beads_fabro/",
    ".claude-plugin/scripts/bin/",
    ".claude-plugin/scripts/_bootstrap.py",
)


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


def unreleased_master_detail(
    *,
    runner: CommandRunner,
    release_sha: str,
    master_sha: str | None,
) -> str | None:
    """The warning text, or `None` when master carries nothing release lacks."""
    if master_sha is None or master_sha == release_sha:
        return None
    commits = _unreleased_dispatcher_commits(
        runner=runner,
        release_sha=release_sha,
        master_sha=master_sha,
    )
    if commits == ():
        commits = (master_sha[:12],)
    return (
        "WARNING: master contains unreleased dispatcher commit(s): "
        f"{'; '.join(commits)}; a release must be cut before this code takes effect."
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
