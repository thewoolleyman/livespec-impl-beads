"""The per-node ACP adapter VALUE, and the two ways configuration spells it.

Split out of `_config` for the same reason `_codex_model_tiers` and
`_node_timeouts` are: the policy -- what a node's adapter IS, how a
configured value is spelled, and how the rendered string is ordered --
belongs next to its own resolver rather than inside the general
connection-resolution module.

WHY AN ADAPTER IS A TRIPLE AND NOT A PROVIDER ENUM. A node's adapter is
`(command, env, args)`, and model and reasoning effort are NOT fields of
their own: they ride in `env` for adapters that read them from the
environment (`ANTHROPIC_MODEL`, `CLAUDE_CODE_EFFORT_LEVEL`) and in `args`
for adapters that read them from the command line (`-c model=...`,
`-c model_reasoning_effort=...`). That is what makes the shape
provider-agnostic BY CONSTRUCTION rather than by enumerating providers:
an Anthropic-Messages endpoint is expressed by putting
`ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_MODEL` in
`env`, and an OpenAI-compatible one by putting `-c model_provider=<name>`
and its provider definition in `args`. Neither needs a code change here,
which is the whole point of the surface
(the adapter-configuration contract in `SPECIFICATION/contracts.md`).

TWO SPELLINGS, AND WHAT EACH ONE SETS. A configured value is either a
whole adapter STRING or a TABLE of the three fields:

- A STRING is a COMPLETE command line: it sets `command` to the whole
  thing and `args` to empty, because arguments meant for a command that
  has been replaced must not survive it.
- A TABLE is a per-FIELD overlay: `command` and `args` replace only when
  present, so a table that sets `env` alone keeps the workflow's adapter.

In BOTH spellings `env` MERGES key by key with the more specific layer
winning. That is what lets `--acp-node implement=ANTHROPIC_MODEL=... <cmd>`
move one variable while the base URL and auth token a repository
configured for that node survive (Scenario 87). The one exception is
internal: the `dispatcher.codex_models` shorthand expands into a whole
rendered Codex command line and REPLACES the environment, because merging
the workflow default's `ANTHROPIC_MODEL` onto a Codex adapter would pin an
Anthropic model on a command that is not Anthropic's.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, cast

__all__: list[str] = [
    "ACP_NODES",
    "NODE_INPUT_CANDIDATES",
    "AcpAdapter",
    "AcpNodeOverlay",
    "overlay_from_string",
    "overlay_from_table",
    "parse_adapter_string",
    "render_adapter",
    "resolve_node_inputs",
]

# Every ACP node of the `implement-work-item` workflow, in graph order.
# `implementation_diff` and `janitor` are deliberately absent: they are
# `script` nodes with no adapter to configure.
ACP_NODES: tuple[str, ...] = (
    "implement",
    "fix",
    "review_fix",
    "pr",
    "review",
    "disposition",
)

# Which workflow input each node's adapter rides, in DESCENDING preference.
#
# The per-node input is listed first and the shared `acp_adapter` second so
# BOTH workflow shapes resolve: this repo's graph gives every implementer
# node its own input, while a dispatch target still carrying the older
# four-input graph has `implement` / `fix` / `review_fix` sharing
# `acp_adapter`. Resolution reads what the workflow ACTUALLY declares
# rather than assuming a shape, so a not-yet-migrated target is never sent
# an `--input` name its own workflow does not define -- which fabro would
# reject outright.
NODE_INPUT_CANDIDATES: Mapping[str, tuple[str, ...]] = {
    "implement": ("implement_adapter", "acp_adapter"),
    "fix": ("fix_adapter", "acp_adapter"),
    "review_fix": ("review_fix_adapter", "acp_adapter"),
    "pr": ("pr_adapter",),
    "review": ("review_adapter",),
    "disposition": ("disposition_adapter",),
}

# A leading `KEY=value` environment assignment, the mechanism fabro already
# parses off the front of an `acp.command`. The key alphabet is deliberately
# conservative (a shell-style identifier): the first token that is not one
# ends the env prefix and begins the command.
_ENV_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


@dataclass(frozen=True, kw_only=True)
class AcpAdapter:
    """One node's fully-resolved ACP adapter."""

    command: str
    env: Mapping[str, str] = field(default_factory=dict)
    args: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class AcpNodeOverlay:
    """One layer's contribution to one node's adapter.

    A field left `None` is NOT SET at this layer and leaves the less
    specific layer's value standing; that is what makes resolution
    per-field. `env_replaces` distinguishes the two spellings described in
    the module docstring: a whole-string layer sets it, a table layer does
    not.

    `from_shorthand` marks an overlay the `dispatcher.codex_models`
    expansion produced rather than one an operator wrote. It changes ONE
    thing: when the workflow declares no adapter input for that node, the
    overlay is DROPPED instead of refusing the dispatch. The distinction
    matters because that expansion is unconditional -- the `pr` tier
    expands even for a target that configured nothing -- so treating it as
    a request would make every workflow that parameterizes no adapter
    undispatchable over a key nobody set.
    """

    command: str | None = None
    env: Mapping[str, str] = field(default_factory=dict)
    args: tuple[str, ...] | None = None
    env_replaces: bool = False
    from_shorthand: bool = False


def parse_adapter_string(*, text: str) -> AcpAdapter:
    """Split an adapter command line into its env prefix and its command.

    Leading `KEY=value` tokens become `env`; everything after them is the
    `command`, and `args` stays empty. The decomposition is deliberately
    NOT clever about where a command ends and its arguments begin -- a flat
    string carries no such boundary, and inventing one would make
    `render_adapter(parse_adapter_string(...))` return something other than
    what was written. Round-tripping matters because this is how a
    workflow's own declared default enters resolution.
    """
    tokens = text.split()
    env: dict[str, str] = {}
    index = 0
    for token in tokens:
        if _ENV_ASSIGNMENT_RE.match(token) is None:
            break
        key, _, value = token.partition("=")
        env[key] = value
        index += 1
    return AcpAdapter(command=" ".join(tokens[index:]), env=env)


def render_adapter(*, adapter: AcpAdapter) -> str:
    """Render one adapter to the exact string a node's `acp.command` takes.

    The order is contractual: `env` pairs in SORTED KEY ORDER, then
    `command`, then `args`, single-space separated. Sorting is what makes
    the rendered string a function of the resolved value alone -- two
    dispatches that resolve the same adapter render byte-identical
    commands regardless of which layer contributed which key, so a
    journaled string can be compared across runs.
    """
    pairs = [f"{key}={adapter.env[key]}" for key in sorted(adapter.env)]
    return " ".join([*pairs, adapter.command, *adapter.args])


def overlay_from_string(
    *, text: str, replaces_env: bool = False, from_shorthand: bool = False
) -> AcpNodeOverlay:
    """A COMPLETE-adapter overlay from one adapter command line.

    `command` and `args` are always set -- the whole command line lives in
    `command`, so `args` becomes empty rather than inheriting arguments
    meant for a command that is no longer there.

    `env` MERGES by default, which is the ratified behaviour: an operator
    who moves one node's model with `--acp-node` keeps the base URL and
    auth token the repository layer configured for it, instead of having to
    restate the whole environment on the command line
    (`SPECIFICATION/scenarios.md` Scenario 87).

    `replaces_env` is the ONE exception and it is not user-facing: the
    `dispatcher.codex_models` shorthand expands into a whole rendered Codex
    command line, and merging the workflow default's `ANTHROPIC_MODEL` onto
    a Codex adapter would prefix an Anthropic model pin onto a command that
    is not Anthropic's. That expansion replaces the environment for the
    same reason the pre-existing whole-input override did.
    """
    adapter = parse_adapter_string(text=text)
    return AcpNodeOverlay(
        command=adapter.command,
        env=adapter.env,
        args=(),
        env_replaces=replaces_env,
        from_shorthand=from_shorthand,
    )


def overlay_from_table(*, entry: Mapping[str, Any], key: str) -> AcpNodeOverlay | str:
    """A per-FIELD overlay from one `command` / `env` / `args` table.

    Returns the overlay, or an actionable refusal NAMING THE KEY when a
    field is the wrong type. `key` is the fully-qualified configuration
    path so the message points at the line the operator has to edit rather
    than at the node name alone.
    """
    command_raw = entry.get("command")
    if command_raw is not None and not isinstance(command_raw, str):
        return f"{key}.command must be a string; got {command_raw!r}"
    args = _string_tuple(value=entry.get("args"))
    if args is None and entry.get("args") is not None:
        return f"{key}.args must be an array of strings; got {entry.get('args')!r}"
    env = _string_map(value=entry.get("env"))
    if env is None:
        return f"{key}.env must be a table of string to string; got {entry.get('env')!r}"
    return AcpNodeOverlay(command=command_raw, env=env, args=args)


def resolve_node_inputs(*, declared: Mapping[str, str]) -> Mapping[str, str]:
    """Map each ACP node onto the workflow input its adapter rides.

    `declared` is the workflow's own `[run.inputs]` adapter table. A node
    whose every candidate input is undeclared is simply ABSENT from the
    result: there is no input to override, so the dispatch passes none and
    the workflow runs whatever it declares. Refusing outright would break
    every workflow that parameterizes no adapter, and the case actually
    worth refusing -- a layer CONFIGURING such a node -- is caught by the
    caller, which can then name the node the operator actually wrote.
    """
    resolved: dict[str, str] = {}
    for node in ACP_NODES:
        declared_name = next(
            (name for name in NODE_INPUT_CANDIDATES[node] if name in declared), None
        )
        if declared_name is not None:
            resolved[node] = declared_name
    return resolved


def _string_tuple(*, value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        return None
    items = cast("list[object]", value)
    if not all(isinstance(item, str) for item in items):
        return None
    return tuple(cast("list[str]", items))


def _string_map(*, value: object) -> Mapping[str, str] | None:
    if value is None:
        return {}
    if not isinstance(value, dict):
        return None
    table = cast("dict[str, object]", value)
    if not all(isinstance(item, str) for item in table.values()):
        return None
    return {key: str(item) for key, item in table.items()}
