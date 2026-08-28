"""Confinement of the loop probe's merged-by-design change to `.livespec-probe/`.

The loop-probe clause of `SPECIFICATION/contracts.md` aims the probe's change at
a REAL default branch, so this directory boundary is the only thing between a
health command and an arbitrary commit on master. Confinement is therefore
asserted TWICE, and the two assertions are not redundant. The PRE-MERGE
verification is what makes the merge safe to perform at all: it runs while
refusing still costs nothing, and an escape there fails the probe WITHOUT
merging. The POST-MERGE backstop covers the case the first one structurally
cannot see -- a change that merged anyway, through machinery the probe did not
interpose on. A single check would have to choose which of the two it defends
against.

The backstop NAMES the merged commit and states the revert obligation rather
than performing the revert. The probe mutates nothing beyond its own cycle, so
the repair is the operator's act; a probe that silently repaired an escape
would be doing exactly the unbounded thing the boundary exists to prevent.

A path is confined only when it sits STRICTLY INSIDE the directory. A bare
`.livespec-probe` entry, an absolute path, and any path traversing `..` all read
as escapes -- fail-closed, because every one of them is a change whose target
this module cannot establish is inside the boundary.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import PurePosixPath

__all__: list[str] = [
    "PROBE_DIRECTORY",
    "escaping_paths",
    "merged_escape_failure",
    "pre_merge_confinement_refusal",
]

# The one sanctioned target directory at the governed repository's root. Probe
# artifacts under it are inert: a single file the next probe's change replaces,
# removable by the operator at any time, and no surface may complain about its
# absence.
PROBE_DIRECTORY = ".livespec-probe"

_MINIMUM_CONFINED_PARTS = 2


def escaping_paths(*, paths: Sequence[str]) -> tuple[str, ...]:
    """Every changed path that leaves the sanctioned probe directory."""
    return tuple(path for path in paths if not _confined(path=path))


def pre_merge_confinement_refusal(*, paths: Sequence[str]) -> str | None:
    """The pre-merge verification's refusal, naming each escaping path.

    `None` means the change is confined and the cycle may proceed to the merge.
    A refusal is returned BEFORE the merge is driven, so the caller's remedy is
    to stop -- there is no merged commit to name yet, and none to revert.
    """
    escaping = escaping_paths(paths=paths)
    if not escaping:
        return None
    return (
        "probe change escapes the sanctioned target path; failing without"
        f" merging. Paths outside {PROBE_DIRECTORY}/: {', '.join(escaping)}"
    )


def merged_escape_failure(*, paths: Sequence[str], merge_commit: str) -> str | None:
    """The post-merge backstop's failure, naming the commit and the revert obligation.

    `None` means the merged diff is confined. Otherwise the probe fails and the
    operator -- never the probe -- reverts the named commit.
    """
    escaping = escaping_paths(paths=paths)
    if not escaping:
        return None
    return (
        f"an escaping probe change merged as commit {merge_commit}; paths outside"
        f" {PROBE_DIRECTORY}/: {', '.join(escaping)}. The operator must revert"
        f" {merge_commit}; the probe reverts nothing itself."
    )


def _confined(*, path: str) -> bool:
    candidate = PurePosixPath(path.strip())
    if candidate.is_absolute():
        return False
    parts = tuple(part for part in candidate.parts if part != ".")
    if ".." in parts or len(parts) < _MINIMUM_CONFINED_PARTS:
        return False
    return parts[0] == PROBE_DIRECTORY
