"""Bearer-credential resolution for the Fabro server API.

Two sources, in a fixed order. The `FABRO_DEV_TOKEN__<factory>` environment
variable wins when it is set, because an operator who exported it for THIS
factory said something more specific than a login file shared by every
client on the host. `_config.resolve_fabro_factory` has already read it into
the target's `dev_token`, so this module reads the target rather than the
environment a second time.

Otherwise the credential comes from `~/.fabro/auth.json`, which is where
`fabro auth login` leaves it and therefore what every operator host actually
has. Its shape is `{"servers": {"<server url>": {"kind": ..., "token":
...}}}`, keyed by the url the CLI was pointed at. A configured url and a
logged-in url that name the same server can still differ by a trailing slash
or by case, so an exact hit is tried first and a scheme/host/port-normalised
comparison second — a normalised-only match would quietly accept a path
suffix the exact form would have rejected.

Resolving to `None` is a legitimate answer, not an error: it means the
caller is about to speak to the server unauthenticated. That is worth
JOURNALLING at the call site rather than raising here, because the visible
symptom — every route failing and the destructive fallback firing — reads
exactly like a healthy server refusing the act.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

from livespec_orchestrator_beads_fabro.commands._fabro_port_types import FabroTarget
from livespec_orchestrator_beads_fabro.effects import (
    AttemptFailure,
    JsonParseFailure,
    attempt,
    parse_json,
)

__all__: list[str] = [
    "FABRO_AUTH_FILE_RELATIVE",
    "fabro_auth_file",
    "resolve_bearer_token",
]

# Relative to the operator's home directory, which is where the `fabro` CLI
# writes it and the only place this module looks for it.
FABRO_AUTH_FILE_RELATIVE = Path(".fabro") / "auth.json"


def fabro_auth_file() -> Path:
    """Where `fabro auth login` left this host's credential.

    A named function rather than an inline `Path.home()` join because it is
    an AMBIENT host dependency: the test suite has to be able to point it at
    a scratch file, or whether a check passes depends on whether the machine
    running it happens to be logged in to a factory.
    """
    return Path.home() / FABRO_AUTH_FILE_RELATIVE


def resolve_bearer_token(*, target: FabroTarget) -> str | None:
    """Resolve one factory's bearer credential, or `None` if it has none."""
    if target.dev_token is not None:
        return target.dev_token
    if target.server_url is None:
        return None
    return _auth_file_token(server_url=target.server_url)


def _auth_file_token(*, server_url: str) -> str | None:
    servers = _logged_in_servers(path=fabro_auth_file())
    exact = _token_of(entry=servers.get(server_url))
    if exact is not None:
        return exact
    wanted = _normalised(url=server_url)
    for url, entry in servers.items():
        token = _token_of(entry=entry)
        if token is not None and _normalised(url=url) == wanted:
            return token
    return None


def _logged_in_servers(*, path: Path) -> dict[str, object]:
    read = attempt(action=lambda: path.read_text(encoding="utf-8"), exceptions=(OSError,))
    if isinstance(read, AttemptFailure):
        return {}
    parsed = parse_json(text=read)
    if isinstance(parsed, JsonParseFailure) or not isinstance(parsed, dict):
        return {}
    servers: object = cast("dict[str, Any]", parsed).get("servers")
    if not isinstance(servers, dict):
        return {}
    return cast("dict[str, object]", servers)


def _token_of(*, entry: object) -> str | None:
    if not isinstance(entry, dict):
        return None
    token: object = cast("dict[str, Any]", entry).get("token")
    if isinstance(token, str) and token != "":
        return token
    return None


def _normalised(*, url: str) -> str:
    trimmed = url.strip().rstrip("/")
    split = urlsplit(trimmed)
    if split.scheme == "" or split.netloc == "":
        return trimmed.lower()
    return f"{split.scheme.lower()}://{split.netloc.lower()}"
