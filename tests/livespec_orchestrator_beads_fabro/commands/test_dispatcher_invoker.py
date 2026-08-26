"""Unit tier for the invoker resolution seam (contracts.md v073).

The module import is deferred into the test bodies via `importlib` and the
first assertion is a genuine `is_file()` check on the module path, so the
Red commit of this slice fails on an ASSERTION (the module does not exist yet)
rather than on a collection-time `ModuleNotFoundError`, which would prove only
unimportability.
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Any

import pytest

_MODULE = "livespec_orchestrator_beads_fabro.commands._dispatcher_invoker"
_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec_orchestrator_beads_fabro"
    / "commands"
    / "_dispatcher_invoker.py"
)


def _invoker() -> Any:
    assert _MODULE_PATH.is_file(), f"expected the invoker resolution module at {_MODULE_PATH}"
    return importlib.import_module(_MODULE)


def _repo(*, tmp_path: Path, require_invoker: str | None) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    if require_invoker is not None:
        _ = (repo / ".livespec.jsonc").write_text(
            '{"livespec-orchestrator-beads-fabro": {"dispatcher": '
            f'{{"require_invoker": {require_invoker}}}}}}}',
            encoding="utf-8",
        )
    return repo


def test_the_flag_wins_over_the_environment() -> None:
    invoker = _invoker()

    identity = invoker.resolve_invoker(
        flag="human:cw",
        env={"LIVESPEC_INVOKER": "session:other"},
        hostname="box",
    )

    assert identity.invoker == "human:cw"
    assert identity.invoker_source == "flag"


def test_the_environment_is_used_when_no_flag_is_passed() -> None:
    invoker = _invoker()

    identity = invoker.resolve_invoker(
        flag=None,
        env={"LIVESPEC_INVOKER": "session:drain"},
        hostname="box",
    )

    assert identity.invoker == "session:drain"
    assert identity.invoker_source == "env"


def test_an_unasserted_identity_is_the_marked_fallback() -> None:
    invoker = _invoker()

    identity = invoker.resolve_invoker(flag=None, env={"USER": "cw"}, hostname="box")

    assert identity.invoker == "unattributed:cw@box"
    assert identity.invoker_source == "fallback"


@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_assertion_is_not_an_assertion(blank: str) -> None:
    """An empty `--invoker` must not launder an unattributed act into `flag`."""
    invoker = _invoker()

    identity = invoker.resolve_invoker(
        flag=blank, env={"LIVESPEC_INVOKER": blank, "USER": "cw"}, hostname="box"
    )

    assert identity.invoker == "unattributed:cw@box"
    assert identity.invoker_source == "fallback"


def test_the_fallback_names_the_unknowns_it_could_not_derive() -> None:
    invoker = _invoker()

    identity = invoker.resolve_invoker(flag=None, env={}, hostname="  ")

    assert identity.invoker == "unattributed:unknown-user@unknown-host"


def test_the_default_identity_reads_the_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoker = _invoker()
    monkeypatch.setenv("LIVESPEC_INVOKER", "foreman:seat-1")

    identity = invoker.default_invoker_identity()

    assert identity.invoker == "foreman:seat-1"
    assert identity.invoker_source == "env"


def test_the_default_identity_derives_a_hostname_when_nothing_is_asserted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercises the real `socket.gethostname()` arm of the fallback derivation."""
    invoker = _invoker()
    monkeypatch.delenv("LIVESPEC_INVOKER", raising=False)
    monkeypatch.setenv("USER", "cw")

    identity = invoker.default_invoker_identity()

    assert identity.invoker.startswith("unattributed:cw@")
    assert identity.invoker != "unattributed:cw@"
    assert identity.invoker_source == "fallback"


def test_a_namespace_without_the_flag_resolves_as_unasserted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoker = _invoker()
    monkeypatch.setenv("LIVESPEC_INVOKER", "console:principal")

    identity = invoker.invoker_from_args(args=argparse.Namespace())

    assert identity.invoker == "console:principal"
    assert identity.invoker_source == "env"


def test_the_flag_reaches_the_parser_and_the_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoker = _invoker()
    monkeypatch.setenv("LIVESPEC_INVOKER", "session:ignored")
    parser = argparse.ArgumentParser()
    invoker.add_invoker_argument(parser=parser)

    args = parser.parse_args(["--invoker", "human:cw"])

    assert invoker.invoker_from_args(args=args).invoker_source == "flag"
    assert invoker.invoker_from_args(args=args).invoker == "human:cw"


def test_no_refusal_when_require_invoker_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invoker = _invoker()
    monkeypatch.delenv("LIVESPEC_INVOKER", raising=False)

    refusal = invoker.require_invoker_refusal(
        args=argparse.Namespace(invoker=None),
        repo=_repo(tmp_path=tmp_path, require_invoker=None),
    )

    assert refusal is None


def test_no_refusal_when_require_invoker_is_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invoker = _invoker()
    monkeypatch.delenv("LIVESPEC_INVOKER", raising=False)

    refusal = invoker.require_invoker_refusal(
        args=argparse.Namespace(invoker=None),
        repo=_repo(tmp_path=tmp_path, require_invoker="false"),
    )

    assert refusal is None


def test_no_refusal_when_an_identity_was_asserted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invoker = _invoker()
    monkeypatch.delenv("LIVESPEC_INVOKER", raising=False)

    refusal = invoker.require_invoker_refusal(
        args=argparse.Namespace(invoker="human:cw"),
        repo=_repo(tmp_path=tmp_path, require_invoker="true"),
    )

    assert refusal is None


def test_the_refusal_names_both_accepted_identity_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invoker = _invoker()
    monkeypatch.delenv("LIVESPEC_INVOKER", raising=False)

    refusal = invoker.require_invoker_refusal(
        args=argparse.Namespace(invoker=None),
        repo=_repo(tmp_path=tmp_path, require_invoker="true"),
    )

    assert refusal is not None
    assert "--invoker" in refusal
    assert "LIVESPEC_INVOKER" in refusal
    assert "require_invoker" in refusal
