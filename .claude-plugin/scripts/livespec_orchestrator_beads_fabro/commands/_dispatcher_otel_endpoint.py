"""Where the dispatcher's OTLP receiver binds for a cross-host factory dispatch.

The receiver's bound address is ALSO the address the sandbox is told to post
to (`_dispatcher_otel_wiring._project_owned_receiver_endpoint` stamps the
endpoint from `server.config.host`), so one decision settles both halves.

The committed default is the Docker bridge gateway `172.17.0.1`, and that
literal names the gateway of whatever host READS it. Inside the sandbox it
therefore resolves to the SANDBOX's host — correct only while the sandbox and
the dispatcher share a machine. A dispatch routed to a remote factory runs the
sandbox there while the receiver is armed here, so every Claude-Code metric is
posted at a bridge address on the factory host where nothing listens: the beats
are refused, the dispatcher-local heartbeat and cost sinks never advance, and
the stall watchdog reads an absence it cannot tell apart from a hung run.

A remote-factory dispatch therefore binds the DISPATCHER's own tailnet address
instead, which names the same machine from either end, so the sandbox exports
straight back over the tailnet and the existing dispatcher-local probe reads
its own sink unchanged. Local dispatches keep the bridge value.

Two absences deliberately keep the bridge rather than guessing: a factory whose
server names no host (the implicit single-factory target), and a dispatcher
whose own tailnet address is undiscoverable. Advertising an address that cannot
be reached is strictly worse than the bridge — it is the same refused-beat
failure with the evidence moved somewhere new.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlsplit

from livespec_orchestrator_beads_fabro.commands._config import FactoryTarget
from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandRunner
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import ShellCommandRunner

__all__: list[str] = [
    "DISPATCHER_TAILNET_HOST_ENV_VAR",
    "TailnetHostResolver",
    "factory_server_host",
    "resolve_dispatcher_tailnet_host",
    "resolve_receiver_host",
    "shell_tailnet_host",
    "tailnet_host_from_runner",
]

# The operator lever, ahead of any discovery: an explicit address is what a
# host whose tailnet name the CLI cannot report still needs to advertise.
DISPATCHER_TAILNET_HOST_ENV_VAR = "LIVESPEC_DISPATCHER_TAILNET_HOST"

TailnetHostResolver = Callable[[], str | None]

_TAILNET_ADDRESS_ARGV: tuple[str, ...] = ("tailscale", "ip", "-4")
_TAILNET_ADDRESS_TIMEOUT_SECONDS = 10.0

# A factory served on a LOOPBACK name runs wherever the dispatcher runs, so the
# bridge gateway already resolves to the right machine from both ends. A
# factory served on this dispatcher's own tailnet address is the same case, but
# it cannot be a committed literal — `resolve_receiver_host` compares for it.
_SELF_SERVED_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def factory_server_host(*, factory: FactoryTarget) -> str:
    """Return the lowercased hostname of a factory target's server URL.

    Empty when the target names no server (the implicit single-factory case)
    and when the value is not a URL a hostname can be read out of — an
    unparseable server is an absence, never a guess at the operator's intent.
    """
    server = (factory.server or "").strip()
    return (urlsplit(server).hostname or "").lower()


def resolve_dispatcher_tailnet_host(
    *, environ: dict[str, str], resolver: TailnetHostResolver
) -> str | None:
    """Resolve this dispatcher's own tailnet address (env lever > resolver).

    None means "this host has no discoverable tailnet address": both a blank
    lever and a resolver answering nothing usable read that way, so a
    whitespace answer can never be advertised as an endpoint.
    """
    lever = environ.get(DISPATCHER_TAILNET_HOST_ENV_VAR, "").strip()
    if lever != "":
        return lever
    return (resolver() or "").strip() or None


def resolve_receiver_host(
    *,
    factory: FactoryTarget,
    bridge_host: str,
    environ: dict[str, str],
    resolver: TailnetHostResolver,
) -> str:
    """Resolve the address the receiver binds AND advertises for one dispatch.

    `bridge_host` is the committed/env-resolved Docker-bridge value, and it is
    the answer for every dispatch whose sandbox runs on this machine. Only a
    genuinely REMOTE factory reaches the resolver, so a local dispatch never
    pays for a tailnet lookup and never changes behaviour.
    """
    server_host = factory_server_host(factory=factory)
    if server_host == "" or server_host in _SELF_SERVED_HOSTS:
        return bridge_host
    tailnet_host = resolve_dispatcher_tailnet_host(environ=environ, resolver=resolver)
    if tailnet_host is None or tailnet_host == server_host:
        return bridge_host
    return tailnet_host


def tailnet_host_from_runner(*, runner: CommandRunner, cwd: Path) -> str | None:
    """Read this host's tailnet IPv4 through an injected command runner.

    `tailscale ip -4` prints one address per line. A non-zero exit (no
    `tailscale` binary, a logged-out daemon) and output with no usable line
    both read as an absence — this seam never raises into the fail-open
    arming path it feeds.
    """
    result = runner.run(
        argv=list(_TAILNET_ADDRESS_ARGV),
        cwd=cwd,
        timeout_seconds=_TAILNET_ADDRESS_TIMEOUT_SECONDS,
    )
    if result.exit_code != 0:
        return None
    for line in result.stdout.splitlines():
        address = line.strip()
        if address != "":
            return address
    return None


def shell_tailnet_host(*, cwd: Path) -> str | None:
    """The production tailnet-host resolver: `tailscale ip -4` over the shell."""
    return tailnet_host_from_runner(runner=ShellCommandRunner(), cwd=cwd)
