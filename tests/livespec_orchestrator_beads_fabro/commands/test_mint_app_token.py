"""`mint-app-token` CLI over the vendored fleet GitHub App-token primitive.

FAIL-CLOSED per the github-app-auth design record (Pillar 2 —
tenant-scoped resolution): the credential env (GITHUB_APP_ID +
GITHUB_PRIVATE_KEY, optional GITHUB_APP_INSTALLATION_ID /
GITHUB_API_URL) is injected ONLY by the calling tenant's
credential_wrapper, and the retired fleet PAT
(LIVESPEC_FAMILY_GITHUB_TOKEN) is NEVER read — not even as a fallback.
The signing / mint / provider logic lives in the vendored
`livespec_runtime.github_auth` (tested upstream in livespec-runtime);
these tests cover ONLY this repo's CLI wiring: the env → config →
provider → stdout railway and the expected-failure exit mapping.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from livespec_orchestrator_beads_fabro.commands import mint_app_token as cli
from livespec_runtime.github_auth.config import GithubAppConfig
from livespec_runtime.github_auth.errors import GithubAppAuthError

_GITHUB_ENV_VARS = (
    "GITHUB_APP_ID",
    "GITHUB_PRIVATE_KEY",
    "GITHUB_APP_INSTALLATION_ID",
    "GITHUB_API_URL",
    "LIVESPEC_FAMILY_GITHUB_TOKEN",
)


@pytest.fixture(autouse=True)
def _scrub_github_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start every test from a credential-free environment (hermetic)."""
    for name in _GITHUB_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


class _StubProvider:
    """Provider stand-in: captures the config, never touches the network."""

    built_with: GithubAppConfig | None = None

    def __init__(self, *, config: GithubAppConfig) -> None:
        type(self).built_with = config

    def token(self) -> str:
        return "ghs_stub-installation-token"


class _MintFailingProvider:
    """Provider stand-in whose mint raises the expected domain error."""

    def __init__(self, *, config: GithubAppConfig) -> None:
        _ = config

    def token(self) -> str:
        raise GithubAppAuthError(detail="the App API rejected the JWT")


@pytest.fixture
def no_mint_spy(monkeypatch: pytest.MonkeyPatch) -> Callable[[], bool]:
    """Install `_StubProvider` and report whether a mint was ever ATTEMPTED.

    The safe-introspection guards are only worth anything if they short-circuit
    BEFORE the network mint. Asserting on stdout alone cannot show that — a
    token could be minted (and so exist, and so be billable and revocable) and
    merely not printed, so the assertion has to be about CONSTRUCTION.

    A stub whose `__init__` raises would express this too, but its body would
    never execute — uncoverable by construction, and this repo gates per-file
    coverage at 100%. A spy over the shared stub proves the same property with
    no unreachable lines.
    """
    _StubProvider.built_with = None
    monkeypatch.setattr(cli, "InstallationTokenProvider", _StubProvider)
    return lambda: _StubProvider.built_with is None


def test_main_mints_via_the_vendored_provider_and_prints_only_the_token(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("GITHUB_APP_ID", " 42 ")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "stub-pem")
    monkeypatch.setattr(cli, "InstallationTokenProvider", _StubProvider)
    assert cli.main(argv=[]) == 0
    captured = capsys.readouterr()
    assert captured.out == "ghs_stub-installation-token"
    assert "github-token source: github-app-installation-token" in captured.err
    built = _StubProvider.built_with
    assert built is not None
    assert built.app_id == "42"
    assert built.installation_id is None


def test_main_threads_the_optional_installation_pin_and_api_url(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("GITHUB_APP_ID", "42")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "stub-pem")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "131208965")
    monkeypatch.setenv("GITHUB_API_URL", "https://ghe.example/api/v3")
    monkeypatch.setattr(cli, "InstallationTokenProvider", _StubProvider)
    # argv is passed explicitly, as in every sibling command test: `main` now
    # PARSES argv, so a bare `main()` would fall through to argparse's default
    # of reading the real `sys.argv` — i.e. pytest's own arguments.
    assert cli.main(argv=[]) == 0
    _ = capsys.readouterr()
    built = _StubProvider.built_with
    assert built is not None
    assert built.installation_id == "131208965"
    assert built.api_url == "https://ghe.example/api/v3"


def test_main_never_falls_back_to_the_retired_fleet_pat(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A present fleet PAT with no App env is a REFUSAL, never a credential.

    The pre-github-app-auth CLI silently downgraded to the
    LIVESPEC_FAMILY_GITHUB_TOKEN PAT when no App was configured — the
    exact fleet fallback Pillar 2 forbids. The PAT must never reach
    stdout, and the diagnostic must route the operator to the calling
    tenant's credential_wrapper.
    """
    monkeypatch.setenv("LIVESPEC_FAMILY_GITHUB_TOKEN", "github_pat_retired")
    assert cli.main(argv=[]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "credential_wrapper" in captured.err
    assert "github_pat_retired" not in captured.err


def test_main_maps_missing_app_env_to_exit_3_with_actionable_detail(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(argv=[]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "ERROR:" in captured.err
    assert "GITHUB_APP_ID" in captured.err


def test_main_maps_a_mint_failure_to_exit_3(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("GITHUB_APP_ID", "42")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "stub-pem")
    monkeypatch.setattr(cli, "InstallationTokenProvider", _MintFailingProvider)
    assert cli.main(argv=[]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "the App API rejected the JWT" in captured.err


def test_help_prints_usage_and_never_mints(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    no_mint_spy: Callable[[], bool],
) -> None:
    """`--help` must answer with help text, never with a live credential.

    Regression for the 2026-08-02 incident: an operator ran the command with
    `--help` and received a live installation token. `main` discarded argv and
    the wrapper passed none, so the flag never reached a parser — there was no
    parser. Help is served with full App env present and the no-mint spy
    watching, so passing REQUIRES short-circuiting before the mint rather than
    merely suppressing stdout.
    """
    monkeypatch.setenv("GITHUB_APP_ID", "42")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "stub-pem")
    with pytest.raises(SystemExit) as excinfo:
        _ = cli.main(argv=["--help"])
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "mint-app-token" in captured.out
    assert "ghs_" not in captured.out
    assert no_mint_spy(), "help must short-circuit BEFORE the mint"


def test_an_unrecognised_argument_is_a_usage_error_and_never_mints(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    no_mint_spy: Callable[[], bool],
) -> None:
    """Any argument resolves before minting, not just `--help`.

    The defect class was "argv is ignored and we mint anyway", so a fix that
    special-cased `--help` would leave `--dry-run`, `--check`, or a typo still
    emitting a credential.
    """
    monkeypatch.setenv("GITHUB_APP_ID", "42")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "stub-pem")
    with pytest.raises(SystemExit) as excinfo:
        _ = cli.main(argv=["--dry-run"])
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unrecognized arguments" in captured.err
    assert no_mint_spy(), "a usage error must short-circuit BEFORE the mint"


def test_a_terminal_stdout_refuses_to_mint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    no_mint_spy: Callable[[], bool],
) -> None:
    """A credential must never be written to a terminal.

    The documented contract is `GH_TOKEN="$(mint-app-token)"`, where stdout is
    a pipe. A terminal means a human is watching, and the token would land in
    scrollback and any session transcript — which is how the 2026-08-02 value
    outlived its revocation.
    """
    monkeypatch.setenv("GITHUB_APP_ID", "42")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "stub-pem")
    monkeypatch.setattr(cli, "_stdout_isatty", lambda: True)
    assert cli.main(argv=[]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "stdout is a terminal" in captured.err
    assert 'GH_TOKEN="$(mint-app-token)"' in captured.err
    assert no_mint_spy(), "the terminal guard must short-circuit BEFORE the mint"


def test_a_piped_stdout_still_mints(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The terminal guard must not break the documented capture path.

    Pairs with the refusal test above: together they show the guard
    discriminates rather than simply always refusing.
    """
    monkeypatch.setenv("GITHUB_APP_ID", "42")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "stub-pem")
    monkeypatch.setattr(cli, "InstallationTokenProvider", _StubProvider)
    monkeypatch.setattr(cli, "_stdout_isatty", lambda: False)
    assert cli.main(argv=[]) == 0
    captured = capsys.readouterr()
    assert captured.out == "ghs_stub-installation-token"
