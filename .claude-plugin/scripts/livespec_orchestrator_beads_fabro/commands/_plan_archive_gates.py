"""Plan-archive refusal type and the working-tree reference gate.

`_plan_archive_review` owns the two LEDGER-side archive gates: child
disposition and completeness-review evidence. Neither reads the working
tree, so an archive could rename `plan/<slug>/` out from under code that
addresses that directory by path. Archiving `beads-v1-1-2-upgrade` on
2026-09-04 moved a rehearsal package two live test modules held as
hardcoded path constants: the archive pull request came back with 33
`FileNotFoundError`s and a red per-file-coverage leg, on a move whose
epic the same call had already closed and stamped.

This module owns the third, WORKING-TREE gate. It sweeps everything
outside `plan/` for files that address `plan/<slug>/` and refuses the
move while any exist, naming every one, so the driving session repoints
or retires each hit in the same pull request as the move.

Two path spellings reach the same directory and both must be caught: the
posix literal `plan/<slug>/…` and the segment-join form
`ROOT / "plan" / "<slug>" / …` — the shape BOTH measured instances used.
The sweep therefore collapses each separator together with the quoting
and whitespace around it before matching, so one pattern covers both. The
match is bounded on its right so that a longer slug sharing the prefix
(`plan/<slug>-successor`) is not a hit, and label strings of the form
`origin:<slug>` never match because they carry no separator at all.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__: list[str] = [
    "PlanArchiveRefusedError",
    "outside_plan_path_references",
]

EXCLUDED_DIRECTORY_NAMES: tuple[str, ...] = (
    ".git",
    ".venv",
    "_vendor",
    "node_modules",
)

_PLAN_DIR = "plan"
# A separator plus the quoting and whitespace hugging it, so a segment-join
# path renders as the posix path it builds.
_SEPARATOR_NOISE = re.compile(r"[\"'\s]*/[\"'\s]*")


class PlanArchiveRefusedError(Exception):
    """Expected refusal raised when a plan cannot be archived."""

    @classmethod
    def missing_completeness_review(cls) -> PlanArchiveRefusedError:
        return cls("independent completeness-review evidence is required")

    @classmethod
    def undisposed_children(cls, *, child_ids: list[str]) -> PlanArchiveRefusedError:
        return cls(f"undisposed child work-items: {', '.join(child_ids)}")

    @classmethod
    def outside_path_references(
        cls,
        *,
        slug: str,
        paths: tuple[str, ...],
    ) -> PlanArchiveRefusedError:
        joined = ", ".join(paths)
        return cls(f"files outside plan/ reference plan/{slug}/: {joined}")


def outside_plan_path_references(*, project_root: Path, slug: str) -> tuple[str, ...]:
    """Return repo-relative paths outside `plan/` that address `plan/<slug>/`."""
    pattern = re.compile(rf"{_PLAN_DIR}/{re.escape(slug)}(?![0-9A-Za-z_-])")
    return tuple(
        sorted(
            path.relative_to(project_root).as_posix()
            for path in _swept_files(root=project_root, plan_tree=project_root / _PLAN_DIR)
            if _addresses_plan_path(path=path, pattern=pattern)
        )
    )


def _swept_files(*, root: Path, plan_tree: Path) -> list[Path]:
    found: list[Path] = []
    for entry in sorted(root.iterdir()):
        if entry.is_dir():
            # Pruned rather than filtered afterwards: descending into `.git`
            # or a `node_modules` costs more than the archive it guards.
            if entry != plan_tree and entry.name not in EXCLUDED_DIRECTORY_NAMES:
                found.extend(_swept_files(root=entry, plan_tree=plan_tree))
        else:
            found.append(entry)
    return found


def _addresses_plan_path(*, path: Path, pattern: re.Pattern[str]) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # A binary artifact or an unreadable entry addresses nothing a test
        # could import; it is skipped rather than reported as a hit.
        return False
    return pattern.search(_SEPARATOR_NOISE.sub("/", text)) is not None
