"""Plugin-currency gate for dispatcher builds at dispatch admission.

Ambient release-staleness is SURFACED, never enforced. Running the payload the
operator provisioned is legitimate per the self-update contract in
SPECIFICATION/contracts.md, so this gate has NO blocking authority on the sole
ground that a newer `refs/heads/release` head exists than the executing build.
Plugin builds bind at SESSION START while this
gate probes a MOVING ref at DISPATCH TIME, so a blocking comparison against that
head refused every live session's dispatches the moment a release was published
mid-session — the homelab incident of 2026-08-29, re-based here onto the ratified
v089 contract.

The ONE blocking currency form is the deliberate operator floor in
`_dispatcher_minimum_release_floor.py`.

Currency that cannot be OBSERVED is recorded as UNDETERMINED under its own
journal stage and proceeds. That stage is what keeps "we could not tell" from
being read back as "the build is current" — the contract requires the two to be
distinguishable, and a shared warning stage cannot express the difference.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    RELEASE_REPOSITORY_MASTER_REF,
    RELEASE_REPOSITORY_RELEASE_REF,
    RELEASE_REPOSITORY_URL,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_minimum_release_floor import (
    MinimumReleaseVerdict,
    minimum_release_verdict,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_unreleased_master import (
    unreleased_dispatcher_commits_argv,
    unreleased_master_detail,
)
from livespec_orchestrator_beads_fabro.io import write_stderr

__all__: list[str] = [
    "CURRENCY_UNDETERMINED_STAGE",
    "MINIMUM_RELEASE_REFUSED_STAGE",
    "STALENESS_WARNING_STAGE",
    "DispatcherStalenessDecision",
    "DispatcherStalenessMessage",
    "apply_dispatcher_staleness_gate",
    "dispatcher_staleness_decision",
    "latest_release_ref_argv",
    "master_ref_argv",
    "unreleased_dispatcher_commits_argv",
]

STALENESS_WARNING_STAGE = "dispatcher-staleness-warning"
# The journal stage for a currency verdict that could not be REACHED. Distinct
# from the plain warning stage on purpose: a reader tallying "no refusal" must
# still be able to tell an observed-current build from an unobservable one.
CURRENCY_UNDETERMINED_STAGE = "dispatcher-currency-undetermined"
# The one blocking stage this gate can still journal. Deliberately NOT the
# retired `dispatcher-staleness-refused` name, so nothing can read an ambient
# staleness refusal — which no longer exists — into a deliberate operator floor.
MINIMUM_RELEASE_REFUSED_STAGE = "dispatcher-minimum-release-refused"

_PROBE_TIMEOUT_SECONDS = 60.0
_EXIT_PRECONDITION_ERROR = 3
_BUILD_ID_MINIMUM_LENGTH = 7
_BUILD_ID_MAXIMUM_LENGTH = 40
_HEX_DIGITS = frozenset("0123456789abcdef")
_PLUGIN_UPDATE_REMEDY = (
    "claude plugin update livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro"
)


class _StalenessJournal(Protocol):
    """Append-only journal seam for the pre-admission staleness gate."""

    def append(self, *, record: dict[str, object]) -> None:
        """Persist one journal record."""
        ...


@dataclass(frozen=True, kw_only=True)
class DispatcherStalenessMessage:
    """One operator-facing gate message, carrying the journal stage it records under."""

    detail: str
    stage: str = STALENESS_WARNING_STAGE


@dataclass(frozen=True, kw_only=True)
class DispatcherStalenessDecision:
    """The gate result: at most one refusal plus zero or more warnings."""

    refusal: DispatcherStalenessMessage | None
    warnings: tuple[DispatcherStalenessMessage, ...]


def latest_release_ref_argv() -> tuple[str, ...]:
    """Probe the newest installable release artifact.

    The repository and its ref come from the fleet-defaults module. They name
    THIS PLUGIN's own publishing identity rather than anything about the governed
    repository being dispatched -- but one of them is a bare default-branch name
    used as a ref, and the ratified fleet-toolchain-literal ban admits such a
    literal in exactly one module.
    """
    return ("git", "ls-remote", RELEASE_REPOSITORY_URL, RELEASE_REPOSITORY_RELEASE_REF)


def master_ref_argv() -> tuple[str, ...]:
    """Probe this plugin's own raw master, for the non-blocking unreleased-code warning."""
    return ("git", "ls-remote", RELEASE_REPOSITORY_URL, RELEASE_REPOSITORY_MASTER_REF)


def dispatcher_staleness_decision(
    *,
    plugin_root: Path,
    runner: CommandRunner,
    cwd: Path | None = None,
) -> DispatcherStalenessDecision:
    """Refuse ONLY below a committed floor; surface every other currency finding.

    Identity is established FIRST: a git-checkout plugin root is exempt, and a
    root that is neither a checkout nor a release-cache sha prefix has no
    provable identity — currency is recorded UNDETERMINED and dispatch proceeds
    WITHOUT any network probe (the bd-ib-n7ce4n deadlock case: a verdict that
    cannot be established must never block dispatch).

    `cwd` is where the committed `dispatcher.minimum_release` floor is read
    from — the dispatch target repo, not the plugin root.
    """
    if _git_checkout_head(plugin_root=plugin_root, runner=runner) is not None:
        return DispatcherStalenessDecision(refusal=None, warnings=())
    floor = minimum_release_verdict(
        plugin_root=plugin_root,
        cwd=cwd if cwd is not None else Path.cwd(),
    )
    if floor is not None:
        decided = _floor_decision(floor=floor)
        if decided is not None:
            return decided
    return _ambient_currency_decision(plugin_root=plugin_root, runner=runner)


def apply_dispatcher_staleness_gate(
    *,
    plugin_root: Path,
    journal: _StalenessJournal,
    runner: CommandRunner | None = None,
    cwd: Path | None = None,
) -> int | None:
    """Emit the currency decision; return an exit code only when dispatch must stop.

    The precondition exit code is reachable ONLY through a committed
    `dispatcher.minimum_release` floor. Ambient release-staleness returns `None`
    here however far behind the executing build is.
    """
    decision = dispatcher_staleness_decision(
        plugin_root=plugin_root,
        runner=runner if runner is not None else ShellCommandRunner(),
        cwd=cwd,
    )
    for warning in decision.warnings:
        _ = write_stderr(text=f"{warning.detail}\n")
        journal.append(
            record={
                "stage": warning.stage,
                "detail": warning.detail,
                "blocking": False,
            }
        )
    if decision.refusal is None:
        return None
    _ = write_stderr(text=f"{decision.refusal.detail}\n")
    journal.append(
        record={
            "stage": decision.refusal.stage,
            "detail": decision.refusal.detail,
            "blocking": True,
        }
    )
    return _EXIT_PRECONDITION_ERROR


def _floor_decision(*, floor: MinimumReleaseVerdict) -> DispatcherStalenessDecision | None:
    """Map the floor's verdict into a gate decision; `None` when the floor cleared."""
    if floor.refusal_detail is not None:
        return DispatcherStalenessDecision(
            refusal=DispatcherStalenessMessage(
                detail=floor.refusal_detail,
                stage=MINIMUM_RELEASE_REFUSED_STAGE,
            ),
            warnings=(),
        )
    if floor.undetermined_detail is not None:
        return _undetermined(reason=floor.undetermined_detail)
    return None


def _ambient_currency_decision(
    *,
    plugin_root: Path,
    runner: CommandRunner,
) -> DispatcherStalenessDecision:
    """Surface how the executing build compares to release — never refuse on it."""
    build_id = _executing_cache_build_id(plugin_root=plugin_root)
    if build_id is None:
        return _undetermined(
            reason=(
                "the gate could not establish the executing build identity (plugin root "
                f"{plugin_root.name!r} is neither a git checkout nor a release-cache build id)"
            )
        )
    release_sha = _remote_ref_sha(runner=runner, argv=latest_release_ref_argv())
    if release_sha is None:
        return _undetermined(reason="the gate could not inspect latest release")
    master_sha = _remote_ref_sha(runner=runner, argv=master_ref_argv())
    unreleased = unreleased_master_detail(
        runner=runner,
        release_sha=release_sha,
        master_sha=master_sha,
    )
    return DispatcherStalenessDecision(
        refusal=None,
        warnings=(
            _lag_warnings(build_id=build_id, release_sha=release_sha, master_sha=master_sha)
            + (() if unreleased is None else (DispatcherStalenessMessage(detail=unreleased),))
        ),
    )


def _undetermined(*, reason: str) -> DispatcherStalenessDecision:
    return DispatcherStalenessDecision(
        refusal=None,
        warnings=(
            DispatcherStalenessMessage(
                detail=(
                    f"WARNING: dispatcher plugin currency could not be determined: {reason}. "
                    "Dispatch proceeds."
                ),
                stage=CURRENCY_UNDETERMINED_STAGE,
            ),
        ),
    )


def _lag_warnings(
    *,
    build_id: str,
    release_sha: str,
    master_sha: str | None,
) -> tuple[DispatcherStalenessMessage, ...]:
    """The ambient-staleness surfacing that replaced the retired blocking refusal."""
    if _build_matches_ref(build_id=build_id, ref_sha=release_sha) or (
        master_sha is not None and _build_matches_ref(build_id=build_id, ref_sha=master_sha)
    ):
        return ()
    return (
        DispatcherStalenessMessage(
            detail=(
                f"WARNING: dispatcher plugin build {build_id} lags latest release "
                f"{release_sha[:12]}; dispatch proceeds because ambient staleness is "
                f"surfaced, not enforced. Run `{_PLUGIN_UPDATE_REMEDY}` and restart to adopt it."
            )
        ),
    )


def _build_matches_ref(*, build_id: str, ref_sha: str) -> bool:
    return ref_sha.startswith(build_id) or build_id.startswith(ref_sha)


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
