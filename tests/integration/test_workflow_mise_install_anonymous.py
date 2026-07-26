"""The sandbox `mise install` prepare step runs ANONYMOUSLY (work-item bd-ib-bic7hb).

`mise install` resolves the aqua-backed pins in `.mise.toml` through
api.github.com, and mise's aqua backend automatically uses `GITHUB_TOKEN` (or
`GH_TOKEN` / `GITHUB_API_TOKEN`) when one is present. The Dispatcher's
run-config overlay projects an ephemeral App INSTALLATION token as
`GITHUB_TOKEN`, so leaving that variable in scope makes a third-party
public-repo metadata fetch a consumer of the factory's own App-installation
credit — one 5000/hr primary rate-limit bucket shared fleet-wide. When it
empties, the prepare step exits 1 and the run dies before any agent work,
stranding the admitted work-item in `active`.

Reproduced 2026-07-26 inside the sandbox image: in the same second, the
anonymous request for the release URL returned 200 while the credentialed one
returned 403 `API rate limit exceeded for installation ID ...`.

Injected defect that makes these RED: drop the `env -u` scrub from the
mise-install prepare step, so mise resolves aqua tools with the factory
credential again.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW_TOML = (
    _REPO_ROOT / ".claude-plugin" / ".fabro" / "workflows" / "implement-work-item" / "workflow.toml"
)
_SCRUBBED_VARIABLES = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_API_TOKEN")


def _mise_install_step() -> str:
    """Return the single prepare-step script line that runs `mise install`."""
    lines = [
        line.strip()
        for line in _WORKFLOW_TOML.read_text(encoding="utf-8").splitlines()
        if line.startswith("script = ") and "mise install" in line
    ]
    assert len(lines) == 1, f"expected exactly one mise-install prepare step, got {lines}"
    return lines[0]


def test_mise_install_scrubs_every_github_credential_variable() -> None:
    """No GitHub credential variable survives into the `mise install` environment."""
    step = _mise_install_step()
    for variable in _SCRUBBED_VARIABLES:
        assert f"-u {variable}" in step, f"{variable} is not scrubbed from the mise-install step"


def test_the_scrub_wraps_mise_install_itself() -> None:
    """The scrub is applied to `mise install`, not merely mentioned in the step."""
    step = _mise_install_step()
    scrub_at = step.index("env -u")
    install_at = step.index("mise install")
    assert scrub_at < install_at, "the env scrub must precede `mise install` in the same command"


def test_the_scrub_is_scoped_to_the_mise_install_step_only() -> None:
    """Every OTHER prepare step keeps the full credential environment."""
    other_steps = [
        line.strip()
        for line in _WORKFLOW_TOML.read_text(encoding="utf-8").splitlines()
        if line.startswith("script = ") and "mise install" not in line
    ]
    assert other_steps, "expected other prepare steps to exist"
    assert not [step for step in other_steps if "env -u" in step]
