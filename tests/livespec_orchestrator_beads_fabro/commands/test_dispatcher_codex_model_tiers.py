"""Codex model-tier resolution for the factory's Codex ACP nodes.

The factory's implementer adapter carried no `-c model=` override, so the
sandbox's Codex model was whatever `codex-acp` resolved at runtime rather than
anything anyone chose. These tests bind the pin: built-in fleet defaults, the
per-repo `dispatcher.codex_models` override, and the empty-model opt-out.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands import _config

_CONFIG_NAME = ".livespec.jsonc"


def _write_dispatcher_config(*, cwd: Path, dispatcher: dict[str, object]) -> None:
    _ = (cwd / _CONFIG_NAME).write_text(
        json.dumps({"livespec-orchestrator-beads-fabro": {"dispatcher": dispatcher}}),
        encoding="utf-8",
    )


def test_absent_config_resolves_the_builtin_fleet_default_tiers(tmp_path: Path) -> None:
    """No config at all still pins both tiers — the fleet inherits the policy."""
    tiers = _config.resolve_codex_model_tiers(cwd=tmp_path)
    assert tiers.implementer.model == "gpt-5.5"
    assert tiers.implementer.reasoning_effort == "low"
    assert tiers.implementer.pinned is True
    assert tiers.pr.model == "gpt-5.4-mini"
    assert tiers.pr.reasoning_effort == "high"
    assert tiers.pr.pinned is True


def test_configured_tiers_override_the_builtin_defaults(tmp_path: Path) -> None:
    """A repo's own `codex_models` block wins over the built-in defaults."""
    _write_dispatcher_config(
        cwd=tmp_path,
        dispatcher={
            "codex_models": {
                "implementer": {"model": "gpt-5.4", "reasoning_effort": "high"},
                "pr": {"model": "gpt-5.4-mini", "reasoning_effort": "low"},
            }
        },
    )
    tiers = _config.resolve_codex_model_tiers(cwd=tmp_path)
    assert tiers.implementer.model == "gpt-5.4"
    assert tiers.implementer.reasoning_effort == "high"
    assert tiers.pr.reasoning_effort == "low"


def test_partial_tier_entry_falls_back_per_key(tmp_path: Path) -> None:
    """A tier naming only a model keeps the built-in effort for that tier."""
    _write_dispatcher_config(
        cwd=tmp_path,
        dispatcher={"codex_models": {"implementer": {"model": "gpt-5.4"}}},
    )
    tiers = _config.resolve_codex_model_tiers(cwd=tmp_path)
    assert tiers.implementer.model == "gpt-5.4"
    assert tiers.implementer.reasoning_effort == "low"
    assert tiers.pr.model == "gpt-5.4-mini"


def test_empty_model_is_the_explicit_opt_out(tmp_path: Path) -> None:
    """`"model": ""` drops the pin entirely rather than defaulting it back."""
    _write_dispatcher_config(
        cwd=tmp_path,
        dispatcher={"codex_models": {"implementer": {"model": "", "reasoning_effort": "high"}}},
    )
    tiers = _config.resolve_codex_model_tiers(cwd=tmp_path)
    assert tiers.implementer.model == ""
    assert tiers.implementer.reasoning_effort == ""
    assert tiers.implementer.pinned is False
    assert tiers.pr.pinned is True


def test_malformed_tier_entries_fall_back_to_defaults(tmp_path: Path) -> None:
    """A non-table tier entry is ignored rather than crashing the dispatch."""
    _write_dispatcher_config(
        cwd=tmp_path,
        dispatcher={"codex_models": {"implementer": "gpt-5.4", "pr": [1, 2]}},
    )
    tiers = _config.resolve_codex_model_tiers(cwd=tmp_path)
    assert tiers.implementer.model == "gpt-5.5"
    assert tiers.pr.model == "gpt-5.4-mini"
