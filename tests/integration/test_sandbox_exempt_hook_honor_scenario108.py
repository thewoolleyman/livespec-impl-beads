"""A governed repository's commit-blocking hook HONORS the resolved marker.

Binds `SPECIFICATION/scenarios.md` Scenario 108's second and third scenarios and
the `sandbox-exempt-marker` row of `SPECIFICATION/contracts.md`'s
members-and-adopters-identical audit: a fleet member honors
the marker through the canonical commit-refuse hook body, an adopter MUST honor
the same resolved marker in its OWN commit-blocking hooks, and the adopter
fixture fails if it does not.

THE CHECKOUT IS SANDBOX-SHAPED, WHICH IS THE WHOLE DIFFICULTY. A Fabro sandbox is
a fresh full clone, structurally indistinguishable from a primary checkout, so
each fixture's hook refuses a commit here exactly as it would in the repository
it governs. The first case proves that refusal is real -- without it the honor
case would pass against a hook that blocks nothing -- and the second proves the
refusal lifts when the RESOLVED marker key reads `true`, while the gate the hook
delegates still fires.

THE MARKER IS READ OFF THE CONTRACT, NEVER SPELLED HERE. The test sets only the
key `resolve_repo_integration_contract` produced for that fixture, so a hook
reading some other key would not be exempted and the case would fail -- which is
the obligation, rather than a comparison of two strings this file chose.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tests.integration.governed_repo_fixtures import (
    ADOPTER,
    GovernedRepo,
    over_both_fixtures,
)

_GATE_RECEIPT = "red-green-replay-gate.ran"
_REFUSAL = "commits are not made in the primary checkout"


@over_both_fixtures
def test_the_commit_blocking_hook_refuses_a_commit_without_the_marker(
    governed: GovernedRepo, tmp_path: Path
) -> None:
    """The control. Without the marker the hook blocks, so the honor case measures honor."""
    repo = _sandbox_shaped_checkout(governed=governed, tmp_path=tmp_path, hook="pre-commit")

    attempt = _attempt_commit(repo=repo)

    assert attempt.returncode != 0
    assert _REFUSAL in attempt.stderr
    assert not (repo / ".git" / _GATE_RECEIPT).exists()


@over_both_fixtures
def test_the_commit_blocking_hook_honors_the_resolved_marker_and_still_gates(
    governed: GovernedRepo, tmp_path: Path
) -> None:
    """The obligation: the primary-checkout refusal lifts, and the delegated gate runs."""
    repo = _sandbox_shaped_checkout(governed=governed, tmp_path=tmp_path, hook="pre-commit")
    _git(repo, "config", governed.resolved().contract.sandbox_exempt_marker, "true")

    attempt = _attempt_commit(repo=repo)

    assert attempt.returncode == 0, attempt.stderr
    assert _REFUSAL not in attempt.stderr
    assert (repo / ".git" / _GATE_RECEIPT).is_file()


def test_a_non_honoring_adopter_hook_fails_the_sandbox_exemption_obligation(
    tmp_path: Path,
) -> None:
    """Scenario 108's third scenario, on the adopter leg, with the marker set and ignored."""
    repo = _sandbox_shaped_checkout(
        governed=ADOPTER, tmp_path=tmp_path, hook="pre-commit-ignoring-the-marker"
    )
    _git(repo, "config", ADOPTER.resolved().contract.sandbox_exempt_marker, "true")

    attempt = _attempt_commit(repo=repo)

    assert attempt.returncode != 0
    assert _REFUSAL in attempt.stderr
    assert not (repo / ".git" / _GATE_RECEIPT).exists()


def _sandbox_shaped_checkout(*, governed: GovernedRepo, tmp_path: Path, hook: str) -> Path:
    """A fresh full clone of one fixture, with the named hook installed and work staged."""
    repo = tmp_path / governed.name
    shutil.copytree(governed.root, repo)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    # Pinned so a host-level `core.hooksPath` cannot silently route around the
    # hook under test and report a green commit nobody's hook ever saw.
    _git(repo, "config", "core.hooksPath", str(repo / ".git" / "hooks"))
    for name, source in (("pre-commit", hook), ("red-green-replay-gate", "red-green-replay-gate")):
        installed = repo / ".git" / "hooks" / name
        shutil.copy(governed.root / "hooks" / source, installed)
        installed.chmod(0o755)
    (repo / "change.txt").write_text(
        "a Red-Green-Replay commit's worth of work\n", encoding="utf-8"
    )
    _git(repo, "add", "change.txt")
    return repo


def _attempt_commit(*, repo: Path) -> subprocess.CompletedProcess[str]:
    """Attempt the commit the hook stands in the way of, without raising on refusal."""
    return subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-m", "feat: fixture change"],
        cwd=str(repo),
        check=False,
        text=True,
        capture_output=True,
    )


def _git(repo: Path, *argv: str) -> None:
    subprocess.run(["git", *argv], cwd=str(repo), check=True, text=True, capture_output=True)
