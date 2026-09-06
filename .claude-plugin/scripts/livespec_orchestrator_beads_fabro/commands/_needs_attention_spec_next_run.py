"""Invoke CORE's spec-`next` CLI cross-plane and adapt its top candidate.

Split out of `needs_attention` along its own cohesion seam: composing the
attention snapshot and REACHING A DIFFERENT PLANE'S CLI are two concerns that
change for different reasons. Everything here exists because the spec side lives
in another checkout with another entry point — the seam bundle, the subprocess
runner, the resolution of where CORE even is — and none of it is about which
facts deserve a maintainer's attention.

The whole surface is fail-soft, and deliberately so: an unreachable CORE must
cost the snapshot its spec row, never the snapshot itself.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from livespec_runtime.needs_attention import SpecNextOutput

from livespec_orchestrator_beads_fabro.commands._needs_attention_core_roots import (
    default_core_root_bases,
    resolve_spec_next_command,
)
from livespec_orchestrator_beads_fabro.commands._needs_attention_spec_next_adapt import (
    adapt_top_candidate,
)
from livespec_orchestrator_beads_fabro.effects import AttemptFailure, attempt

__all__: list[str] = [
    "DEFAULT_SPEC_NEXT_SEAM",
    "SpecNextSeam",
    "spec_next",
]

_SPEC_NEXT_TIMEOUT_SECONDS = 60


@dataclass(frozen=True, slots=True, kw_only=True)
class _SpecNextResult:
    """Captured stdout + exit code from the spec-`next` CLI runner seam."""

    stdout: str
    returncode: int


class _ResolveSpecNextCommand(Protocol):
    """Seam: resolve the runnable spec-`next` argv, or None when unresolvable."""

    def __call__(self, *, project_root: Path) -> list[str] | None: ...


class _RunSpecNextCli(Protocol):
    """Seam: run a resolved argv and capture its stdout + exit code."""

    def __call__(self, *, argv: list[str]) -> _SpecNextResult: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class SpecNextSeam:
    """The injectable side-effecting seams of spec-`next` (defaulted to production).

    Mirrors `livespec_runtime.github_auth.mint.MintSeams`: a frozen bundle of
    the impure callables, defaulted to the real ones and overridden in unit
    tests so the adapt / fail-soft logic is covered without a live CORE
    checkout. The production defaults are integration-covered by the live
    `needs-attention` exercise, not by the hermetic unit suite.
    """

    resolve_command: _ResolveSpecNextCommand
    run: _RunSpecNextCli


def _default_resolve_command(*, project_root: Path) -> list[str] | None:  # pragma: no cover
    """The production `resolve_command` seam: resolve over the real HOME bases."""
    return resolve_spec_next_command(project_root=project_root, bases=default_core_root_bases())


def _run_spec_next_cli(*, argv: list[str]) -> _SpecNextResult:  # pragma: no cover
    """Production `run` seam: shell out to CORE's spec-`next` CLI.

    Mirrors `_beads_client._invoke` — the whole body is `# pragma: no cover`
    (integration-covered): it cannot run hermetically without a live CORE
    checkout. Fail-soft — any OS / subprocess error becomes a non-zero result.
    """
    completed = attempt(
        action=lambda: subprocess.run(  # noqa: S603
            argv,
            capture_output=True,
            text=True,
            check=False,
            timeout=_SPEC_NEXT_TIMEOUT_SECONDS,
        ),
        exceptions=(OSError, subprocess.SubprocessError),
    )
    if isinstance(completed, AttemptFailure):
        return _SpecNextResult(stdout="", returncode=1)
    return _SpecNextResult(stdout=completed.stdout, returncode=completed.returncode)


DEFAULT_SPEC_NEXT_SEAM = SpecNextSeam(
    resolve_command=_default_resolve_command,
    run=_run_spec_next_cli,
)


def spec_next(
    *,
    project_root: Path,
    seam: SpecNextSeam = DEFAULT_SPEC_NEXT_SEAM,
) -> SpecNextOutput | None:
    """Invoke CORE's spec-`next` CLI cross-plane and adapt its top candidate.

    Fail-soft by design: when CORE is unresolvable, the runner raises / exits
    non-zero, its stdout is unparseable, or the ranking is empty / only `none`,
    return None so `compose_needs_attention` drops the spec item entirely
    rather than emitting a useless "go run it yourself" pointer. `seam` is
    injectable (mirroring `MintSeams`) so unit tests exercise the adapt /
    fail-soft logic without a live CORE checkout.
    """
    result = attempt(
        action=lambda: _run_resolved_spec_next(seam=seam, project_root=project_root),
        exceptions=(OSError, subprocess.SubprocessError),
    )
    if isinstance(result, AttemptFailure) or result is None:
        return None
    if result.returncode != 0:
        return None
    return adapt_top_candidate(stdout=result.stdout, project_root=project_root)


def _run_resolved_spec_next(*, seam: SpecNextSeam, project_root: Path) -> _SpecNextResult | None:
    command = seam.resolve_command(project_root=project_root)
    if command is None:
        return None
    return seam.run(argv=[*command, "--project-root", str(project_root)])
