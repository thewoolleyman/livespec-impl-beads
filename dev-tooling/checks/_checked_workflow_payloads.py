# pyright: reportMissingImports=none
"""_checked_workflow_payloads — which workflow directories a payload gate reads.

Shared by BOTH payload gates, `seam_equivalence` and
`no_fleet_toolchain_literals`, because the answer is ONE policy and must not come
to differ between them. `SPECIFICATION/contracts.md` section "Self-contained
plugin dispatch", clause "A registered variant is the reserved workflow's peer,
not its exception", requires each gate to read the bundle AND every directory
this repository registers under its own `dispatcher.workflows`, and to FAIL
rather than report clean for a registered directory whose scan yields nothing to
check.

THE REGISTRY IS READ THROUGH ITS OWN PARSER, never re-derived here. What
`dispatcher.workflows` means -- which entries count, and what an unusable value
does -- belongs to `_workflow_variants.workflow_registry`, and a second reading
of that table inside a gate is exactly the drift the resolve-once discipline
retires. A repository that declares no registry gets the bundle alone, which is
what every dispatch target declaring none already has.

ENUMERATION AND VERDICT ARE SEPARATE, deliberately. This module names what MUST
be read; `incompleteness` says why a named directory is not a whole workflow. A
gate therefore reports an unreadable or partial variant as a finding NAMING that
directory, rather than dying on a read or -- far worse -- skipping it and
reporting a clean scan it never performed.

`where` is the directory AS DECLARED, and it is what every finding and control
failure is prefixed with. Naming the declared path rather than a resolved
absolute one is what makes a finding actionable against the registry entry the
operator wrote.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# NO `sys.path` bootstrap here, deliberately -- the same reasoning
# `_seam_equivalence_findings` records. This is a PRIVATE module of the two
# gates, imported only through them, and each owner puts this directory and the
# orchestrator package's root on the path before importing it.
from livespec_orchestrator_beads_fabro.commands._config import dispatcher_block
from livespec_orchestrator_beads_fabro.commands._workflow_variants import (
    RESERVED_WORKFLOW_NAME,
    workflow_registry,
)

__all__: list[str] = [
    "BUNDLE_RELPATH",
    "REQUIRED_FILES",
    "CheckedPayload",
    "bundle_payload",
    "checked_payloads",
    "incompleteness",
]

# The bundled reserved workflow, spelled from `RESERVED_WORKFLOW_NAME` rather
# than repeating the literal, so the gates and the resolver cannot drift.
BUNDLE_RELPATH: tuple[str, ...] = (
    ".claude-plugin",
    ".fabro",
    "workflows",
    RESERVED_WORKFLOW_NAME,
)

# What makes a directory a WHOLE workflow rather than a partial overlay, per the
# "Named workflow variants" clause. The prompt files are not listed: a graph may
# legitimately carry no ACP node prompt, while these two are what the gates read.
REQUIRED_FILES: tuple[str, ...] = (
    "workflow.fabro",
    "workflow.toml",
)


@dataclass(frozen=True, kw_only=True)
class CheckedPayload:
    """One workflow directory a payload gate reads, named as its findings name it."""

    where: str
    directory: Path


def bundle_payload(*, repo_root: Path) -> CheckedPayload:
    """The bundled `implement-work-item` payload every dispatch target falls back to."""
    return CheckedPayload(
        where="/".join(BUNDLE_RELPATH),
        directory=repo_root.joinpath(*BUNDLE_RELPATH),
    )


def checked_payloads(*, repo_root: Path) -> list[CheckedPayload]:
    """The bundle, then every directory this repository's `dispatcher.workflows` names.

    Sorted by variant name so the report is deterministic, and the bundle
    always first so a reader sees the reference payload before the variants
    held to it.
    """
    registry = workflow_registry(block=dispatcher_block(cwd=repo_root))
    payloads = [bundle_payload(repo_root=repo_root)]
    payloads.extend(
        CheckedPayload(where=declared, directory=repo_root / declared)
        for _name, declared in sorted(registry.items())
    )
    return payloads


def incompleteness(*, payload: CheckedPayload) -> list[str]:
    """Why this directory is not a whole workflow, if it is not.

    A finding rather than a skip, and that is the whole point of the function:
    an absent or half-written registered directory scans to nothing, and
    nothing is indistinguishable from a conformant payload in every report
    either gate produces.
    """
    tail = "so it is not a complete workflow"
    return [
        f"completeness control: {payload.where}: the directory has no {name}, {tail}"
        for name in REQUIRED_FILES
        if not (payload.directory / name).is_file()
    ]
