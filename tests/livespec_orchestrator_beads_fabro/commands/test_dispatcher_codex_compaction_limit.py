"""The Codex compaction token limit as per-node configuration.

Reaching Codex's auto-compaction threshold mid-turn is what made a long
implement turn fatal: at the threshold Codex calls a remote compaction
endpoint that is dead, with no local fallback. A node still backed by Codex
therefore needs that threshold movable WITHOUT an orchestrator code change,
so it resolves from the same per-node `dispatcher.codex_models` surface the
model pins do. Unlike those pins, which moved onto the adapter's `CODEX_CONFIG`
environment channel with the package succession, the limit stays an adapter
ARGUMENT (`-c model_auto_compact_token_limit=`) — which is where contracts.md
section "ACP node timeouts" puts it.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands import _config
from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_argv import (
    CODEX_ADAPTER_BASE,
    codex_adapter,
)

_CONFIG_NAME = ".livespec.jsonc"


def _write_dispatcher_config(*, cwd: Path, dispatcher: dict[str, object]) -> None:
    _ = (cwd / _CONFIG_NAME).write_text(
        json.dumps({"livespec-orchestrator-beads-fabro": {"dispatcher": dispatcher}}),
        encoding="utf-8",
    )


def test_configured_compaction_limit_rides_the_adapter_c_channel(tmp_path: Path) -> None:
    """A configured limit renders as `-c model_auto_compact_token_limit=`.

    The model pin rides `CODEX_CONFIG` while the limit rides the argument
    channel, so this also pins the two apart: a regression that moved the limit
    into `CODEX_CONFIG` alongside the model would change this string.
    """
    _write_dispatcher_config(
        cwd=tmp_path,
        dispatcher={
            "codex_models": {"implementer": {"model": "gpt-5.5", "compaction_token_limit": 300000}}
        },
    )
    tiers = _config.resolve_codex_model_tiers(cwd=tmp_path)
    assert tiers.implementer.compaction_token_limit == 300000
    assert codex_adapter(tier=tiers.implementer) == (
        'CODEX_CONFIG=\'{"approval_policy":"never","model":"gpt-5.5",'
        '"model_reasoning_effort":"low","sandbox_mode":"danger-full-access"}\' '
        "INITIAL_AGENT_MODE=agent-full-access /opt/livespec/codex-acp/bin/codex-acp "
        "-c model_auto_compact_token_limit=300000"
    )


def test_unconfigured_compaction_limit_renders_nothing(tmp_path: Path) -> None:
    """No configured limit leaves the adapter byte-identical to the pin form."""
    tiers = _config.resolve_codex_model_tiers(cwd=tmp_path)
    assert tiers.implementer.compaction_token_limit == 0
    assert "model_auto_compact_token_limit" not in codex_adapter(tier=tiers.implementer)


def test_compaction_limit_survives_the_model_opt_out(tmp_path: Path) -> None:
    """A node opting out of the model pin still carries its own limit.

    Folding the limit into the pinned branch would drop it for exactly this
    configuration — a node letting `codex-acp` pick its model while still
    needing its compaction threshold moved.
    """
    _write_dispatcher_config(
        cwd=tmp_path,
        dispatcher={"codex_models": {"pr": {"model": "", "compaction_token_limit": 120000}}},
    )
    tiers = _config.resolve_codex_model_tiers(cwd=tmp_path)
    assert tiers.pr.pinned is False
    assert codex_adapter(tier=tiers.pr) == (
        f"{CODEX_ADAPTER_BASE} -c model_auto_compact_token_limit=120000"
    )


def test_non_positive_or_non_integer_limits_resolve_to_unset(tmp_path: Path) -> None:
    """A bogus limit is unset, never a one-token threshold that compacts always."""
    for value in (0, -1, True, "300000", 1.5):
        _write_dispatcher_config(
            cwd=tmp_path,
            dispatcher={"codex_models": {"implementer": {"compaction_token_limit": value}}},
        )
        tiers = _config.resolve_codex_model_tiers(cwd=tmp_path)
        assert tiers.implementer.compaction_token_limit == 0
        assert "model_auto_compact_token_limit" not in codex_adapter(tier=tiers.implementer)
