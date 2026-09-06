"""Tests for the cross-host OTLP receiver-address resolution (bd-ib-25fjk2).

A dispatch routed to a REMOTE factory runs its sandbox on the factory host,
so the committed docker-bridge literal `172.17.0.1` names the SANDBOX's own
host while the receiver is armed on the dispatcher host: every beat is
refused and the dispatcher-local watchdog sink never advances. These tests
pin the remedy — a remote-factory dispatch binds and advertises the
DISPATCHER's tailnet address, a local one keeps the bridge value.

Everything here is hermetic: the tailnet-host resolver is INJECTED (no
`tailscale` subprocess), the command runner behind the production resolver is
a fake, and the two end-to-end endpoint assertions drive the receiver arming
with `ensure_receiver_started` replaced so no socket ever binds.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import pytest
from livespec_orchestrator_beads_fabro.commands import _dispatcher_otel_wiring
from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult
from livespec_orchestrator_beads_fabro.commands._dispatcher_otel_endpoint import (
    DISPATCHER_TAILNET_HOST_ENV_VAR,
    factory_server_host,
    resolve_dispatcher_tailnet_host,
    resolve_receiver_host,
    shell_tailnet_host,
    tailnet_host_from_runner,
)
from livespec_orchestrator_beads_fabro.commands._otel_receive import OtelReceiver

_BRIDGE_HOST = "172.17.0.1"
_TAILNET_HOST = "100.89.189.118"
_REMOTE_FACTORY = FactoryTarget(
    name="hp", server="https://hp-xubuntu.perch-rudd.ts.net:32276", dev_token=None
)
_LOCAL_FACTORY = FactoryTarget(name="default", server=None, dev_token=None)


def _tailnet(host: str | None) -> Callable[[], str | None]:
    return lambda: host


@dataclass(kw_only=True)
class _CountingResolver:
    """A tailnet-host resolver that records whether it was consulted at all."""

    host: str | None
    calls: int = 0

    def __call__(self) -> str | None:
        self.calls += 1
        return self.host


@dataclass(kw_only=True)
class _FakeRunner:
    """A `CommandRunner` that replays one canned result and records the argv."""

    result: CommandResult
    argvs: list[list[str]] = field(default_factory=list)

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env, stdin)
        self.argvs.append(list(argv))
        return self.result


def test_factory_server_host_reads_the_url_hostname() -> None:
    """A configured factory's server URL yields its lowercased hostname."""
    assert factory_server_host(factory=_REMOTE_FACTORY) == "hp-xubuntu.perch-rudd.ts.net"


def test_factory_server_host_is_empty_without_a_server() -> None:
    """The implicit single-factory target names no host at all."""
    assert factory_server_host(factory=_LOCAL_FACTORY) == ""


def test_factory_server_host_is_empty_for_an_unparseable_server() -> None:
    """A server value that is not a URL yields no hostname (never a guess)."""
    unparseable = FactoryTarget(name="odd", server="hp-xubuntu:32276", dev_token=None)
    assert factory_server_host(factory=unparseable) == ""


def test_resolve_dispatcher_tailnet_host_prefers_the_env_lever() -> None:
    """The operator lever wins over the resolver (a sanitized PATH escape)."""
    resolved = resolve_dispatcher_tailnet_host(
        environ={DISPATCHER_TAILNET_HOST_ENV_VAR: f"  {_TAILNET_HOST}  "},
        resolver=_tailnet("100.0.0.1"),
    )
    assert resolved == _TAILNET_HOST


def test_resolve_dispatcher_tailnet_host_falls_back_to_the_resolver() -> None:
    """With no lever set, the injected resolver supplies the address."""
    assert (
        resolve_dispatcher_tailnet_host(environ={}, resolver=_tailnet(f"{_TAILNET_HOST}\n"))
        == _TAILNET_HOST
    )


def test_resolve_dispatcher_tailnet_host_is_none_when_undiscoverable() -> None:
    """No lever and no resolver answer reads as 'this host has no tailnet'."""
    assert resolve_dispatcher_tailnet_host(environ={}, resolver=_tailnet(None)) is None


def test_resolve_dispatcher_tailnet_host_treats_blank_output_as_none() -> None:
    """A resolver answering whitespace is an absence, not an address."""
    assert resolve_dispatcher_tailnet_host(environ={}, resolver=_tailnet("   ")) is None


def test_resolve_receiver_host_is_the_tailnet_host_for_a_remote_factory() -> None:
    """A remote factory binds the dispatcher's own tailnet address."""
    resolver = _CountingResolver(host=_TAILNET_HOST)
    host = resolve_receiver_host(
        factory=_REMOTE_FACTORY,
        bridge_host=_BRIDGE_HOST,
        environ={},
        resolver=resolver,
    )
    assert host == _TAILNET_HOST
    assert resolver.calls == 1


def test_resolve_receiver_host_keeps_the_bridge_for_a_local_factory() -> None:
    """The implicit local target never consults the resolver."""
    resolver = _CountingResolver(host=_TAILNET_HOST)
    host = resolve_receiver_host(
        factory=_LOCAL_FACTORY,
        bridge_host=_BRIDGE_HOST,
        environ={},
        resolver=resolver,
    )
    assert host == _BRIDGE_HOST
    assert resolver.calls == 0


def test_resolve_receiver_host_keeps_the_bridge_for_a_loopback_factory() -> None:
    """A loopback-served factory runs here; the bridge value still applies."""
    loopback = FactoryTarget(name="local", server="http://127.0.0.1:32276", dev_token=None)
    host = resolve_receiver_host(
        factory=loopback,
        bridge_host=_BRIDGE_HOST,
        environ={},
        resolver=_tailnet(_TAILNET_HOST),
    )
    assert host == _BRIDGE_HOST


def test_resolve_receiver_host_keeps_the_bridge_when_the_factory_is_this_host() -> None:
    """A factory whose server names THIS dispatcher's tailnet address is local."""
    self_served = FactoryTarget(
        name="self", server=f"https://{_TAILNET_HOST}:32276", dev_token=None
    )
    host = resolve_receiver_host(
        factory=self_served,
        bridge_host=_BRIDGE_HOST,
        environ={},
        resolver=_tailnet(_TAILNET_HOST),
    )
    assert host == _BRIDGE_HOST


def test_resolve_receiver_host_keeps_the_bridge_without_a_tailnet_address() -> None:
    """An undiscoverable tailnet address never advertises a broken endpoint."""
    host = resolve_receiver_host(
        factory=_REMOTE_FACTORY,
        bridge_host=_BRIDGE_HOST,
        environ={},
        resolver=_tailnet(None),
    )
    assert host == _BRIDGE_HOST


def test_tailnet_host_from_runner_reads_the_first_address() -> None:
    """`tailscale ip -4` output yields its first non-blank line."""
    runner = _FakeRunner(
        result=CommandResult(exit_code=0, stdout=f"\n{_TAILNET_HOST}\n", stderr="")
    )
    assert tailnet_host_from_runner(runner=runner, cwd=Path("/repo")) == _TAILNET_HOST
    assert runner.argvs == [["tailscale", "ip", "-4"]]


def test_tailnet_host_from_runner_is_none_on_a_failed_command() -> None:
    """A missing `tailscale` binary reads as an absence, never as a crash."""
    runner = _FakeRunner(result=CommandResult(exit_code=127, stdout="", stderr="not found"))
    assert tailnet_host_from_runner(runner=runner, cwd=Path("/repo")) is None


def test_tailnet_host_from_runner_is_none_on_empty_output() -> None:
    """A zero-exit command printing nothing usable is still an absence."""
    runner = _FakeRunner(result=CommandResult(exit_code=0, stdout="  \n\n", stderr=""))
    assert tailnet_host_from_runner(runner=runner, cwd=Path("/repo")) is None


def test_shell_tailnet_host_delegates_to_the_runner_seam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The production resolver is the runner seam bound to the real shell."""
    seen: list[Path] = []

    def _from_runner(*, runner: object, cwd: Path) -> str | None:
        _ = runner
        seen.append(cwd)
        return _TAILNET_HOST

    monkeypatch.setattr(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_otel_endpoint"
        ".tailnet_host_from_runner",
        _from_runner,
    )
    assert shell_tailnet_host(cwd=Path("/repo")) == _TAILNET_HOST
    assert seen == [Path("/repo")]


def _arm_without_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Build the real receiver but never start it (so no socket binds)."""

    def _without_starting(*, holder: dict[str, object], factory: Callable[[], object]) -> object:
        _ = holder
        # The endpoint projection reads `bound_port`, which a live `start()`
        # would set; stamping it here keeps the assertion on the ADDRESS.
        built = cast("OtelReceiver", factory())
        built.bound_port = 4318
        return built

    monkeypatch.setattr(_dispatcher_otel_wiring, "ensure_receiver_started", _without_starting)


def _endpoint_after_arming(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    factory: FactoryTarget,
) -> str:
    _arm_without_binding(monkeypatch)
    monkeypatch.delenv("LIVESPEC_SANDBOX_OTEL_ENDPOINT", raising=False)
    monkeypatch.delenv("LIVESPEC_OTEL_RECEIVER_HOST", raising=False)
    monkeypatch.delenv(DISPATCHER_TAILNET_HOST_ENV_VAR, raising=False)
    args = argparse.Namespace(
        repo=str(tmp_path),
        journal=str(tmp_path / "j.jsonl"),
        fabro_factory_target=factory,
    )
    receiver = _dispatcher_otel_wiring.ensure_otel_receiver(
        args=args,
        repo=tmp_path,
        holder={},
        tailnet_resolver=_tailnet(_TAILNET_HOST),
    )
    assert isinstance(receiver, OtelReceiver)
    return os.environ["LIVESPEC_SANDBOX_OTEL_ENDPOINT"]


def test_remote_factory_dispatch_advertises_the_dispatcher_tailnet_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A remote-factory dispatch tells the sandbox to post over the tailnet."""
    endpoint = _endpoint_after_arming(
        monkeypatch=monkeypatch, tmp_path=tmp_path, factory=_REMOTE_FACTORY
    )
    assert endpoint == f"http://{_TAILNET_HOST}:4318"
    assert _BRIDGE_HOST not in endpoint


def test_local_dispatch_advertises_the_docker_bridge_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A local dispatch keeps the committed docker-bridge endpoint."""
    endpoint = _endpoint_after_arming(
        monkeypatch=monkeypatch, tmp_path=tmp_path, factory=_LOCAL_FACTORY
    )
    assert endpoint == f"http://{_BRIDGE_HOST}:4318"


def test_arming_falls_back_to_the_configured_factory_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Entry-time arming, before an item pins a target, reads the repo config."""
    _arm_without_binding(monkeypatch)
    monkeypatch.delenv("LIVESPEC_SANDBOX_OTEL_ENDPOINT", raising=False)
    monkeypatch.delenv("LIVESPEC_OTEL_RECEIVER_HOST", raising=False)
    monkeypatch.delenv(DISPATCHER_TAILNET_HOST_ENV_VAR, raising=False)

    def _configured_factory(*, cwd: Path, factory: str | None = None) -> FactoryTarget:
        _ = (cwd, factory)
        return _REMOTE_FACTORY

    monkeypatch.setattr(_dispatcher_otel_wiring, "resolve_fabro_factory", _configured_factory)
    args = argparse.Namespace(repo=str(tmp_path), journal=str(tmp_path / "j.jsonl"))
    receiver = _dispatcher_otel_wiring.ensure_otel_receiver(
        args=args,
        repo=tmp_path,
        holder={},
        tailnet_resolver=_tailnet(_TAILNET_HOST),
    )
    assert isinstance(receiver, OtelReceiver)
    assert receiver.config.host == _TAILNET_HOST
