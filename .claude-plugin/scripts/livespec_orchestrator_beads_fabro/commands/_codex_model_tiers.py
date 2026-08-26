"""Codex model pins for the factory's Codex ACP nodes.

Split out of `_config` so the pin policy -- which carries the measurement
record that justifies its values -- lives next to its own resolver rather than
inside the general connection-resolution module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

__all__: list[str] = [
    "CodexModelTier",
    "CodexModelTiers",
    "codex_model_tiers_from_block",
]

_CODEX_MODELS_KEY = "codex_models"
_IMPLEMENTER_TIER_KEY = "implementer"
_PR_TIER_KEY = "pr"
_TIER_MODEL_KEY = "model"
_TIER_EFFORT_KEY = "reasoning_effort"
_TIER_COMPACTION_KEY = "compaction_token_limit"

# Built-in Codex model pins for the factory's ACP nodes. These are FLEET
# defaults: every repo dispatching through this plugin inherits them unless
# its own `dispatcher.codex_models` block overrides them.
#
# WHY THESE VALUES, and why the pin exists at all. Before this pin the
# implementer adapter carried no `-c model=` at all, so the sandbox's Codex
# model was whatever `codex-acp` resolved at runtime. That resolution is NOT
# the current frontier model: the sandbox image bakes
# `@zed-industries/codex-acp@0.16.0`, whose models-manager cannot decode the
# present-day catalog (`unknown variant `max``, the reasoning tier the
# gpt-5.6 line introduced), so it silently falls back to its baked static
# list and lands on `gpt-5.5` at `medium`. Nobody chose that; it was the
# residue of a decode failure.
#
# Measured in the pinned sandbox image against the real projected credential
# (2026-08-22): `gpt-5.6-luna`, `gpt-5.6-terra` and `gpt-5.3-codex` are ALL
# refused by the backend from this adapter (HTTP 400 -- the 5.6 slugs report
# "requires a newer version of Codex", `gpt-5.3-codex` reports "not supported
# when using Codex with a ChatGPT account"). `gpt-5.5` and `gpt-5.4` /
# `gpt-5.4-mini` complete turns normally. So the reachable tiers are 5.5,
# 5.4 and 5.4-mini, and any future move to the 5.6 line REQUIRES bumping
# `CODEX_ACP_VERSION` in the livespec-dev-tooling sandbox image first.
#
# The implementer holds `gpt-5.5` and drops only its reasoning effort: a
# weaker implementer buys token savings at the cost of extra `review_fix`
# rounds, which are themselves Codex turns, so the cut that does not risk
# paying for itself twice is effort rather than model. The `pr` node is a
# scripted `git`/`gh` recipe with no design judgement in it, so it takes the
# cheap model outright.
_DEFAULT_IMPLEMENTER_MODEL = "gpt-5.5"
_DEFAULT_IMPLEMENTER_EFFORT = "low"
_DEFAULT_PR_MODEL = "gpt-5.4-mini"
_DEFAULT_PR_EFFORT = "high"


@dataclass(frozen=True, kw_only=True)
class CodexModelTier:
    """Resolved Codex model pin for one class of factory ACP node.

    An EMPTY `model` is the explicit opt-out: the adapter is emitted with no
    `-c model=` / `-c model_reasoning_effort=` override at all, restoring the
    pre-pin behaviour of letting `codex-acp` resolve its own default. It is
    spelled as an empty string rather than a missing key so an operator can
    disable the pin without deleting the surrounding documentation.

    `compaction_token_limit` is the Codex `model_auto_compact_token_limit`
    for the nodes this tier backs, and ZERO means "unset" -- the same
    "configure nothing, change nothing" shape as the empty `model`. It
    belongs here rather than in a key of its own because THIS is the
    per-node Codex configuration surface, and because the limit rides the
    adapter's `-c key=value` channel exactly as the model pins do.

    WHY THE LIMIT IS WORTH CONFIGURING AT ALL. Reaching Codex's
    auto-compaction threshold mid-turn is what made a long implement turn
    fatal: at the threshold Codex calls a remote compaction endpoint that is
    dead, with no local fallback, so the turn dies rather than compacting.
    A node still backed by Codex can therefore need its threshold moved --
    and moving it must not require an orchestrator code change.
    """

    model: str
    reasoning_effort: str
    compaction_token_limit: int = 0

    @property
    def pinned(self) -> bool:
        """Whether this tier contributes model overrides to the adapter."""
        return self.model != ""


@dataclass(frozen=True, kw_only=True)
class CodexModelTiers:
    """The per-node-class Codex pins resolved for one dispatch."""

    implementer: CodexModelTier
    pr: CodexModelTier


def codex_model_tiers_from_block(*, block: dict[str, Any]) -> CodexModelTiers:
    """Resolve the factory's Codex model pins from a dispatcher config block.

    Reads `dispatcher.codex_models`. Each tier entry is an optional
    `{"model": ..., "reasoning_effort": ...}` table; a missing entry, a
    non-table entry, or a missing key falls back to the built-in default for
    that tier, so a partial override is legal. A tier whose `model` is the
    empty string is the opt-out described on `CodexModelTier` and carries an
    empty effort with it -- an effort without a model would be a pin the
    adapter cannot express.

    There is deliberately NO environment override. The pins are a steady-state
    cost policy read once per dispatch on the orchestrator host; an env-var
    seam would let an ad-hoc shell silently re-tier the whole factory with
    nothing in the record to show for it.
    """
    models_raw = block.get(_CODEX_MODELS_KEY)
    models = cast("dict[str, Any]", models_raw) if isinstance(models_raw, dict) else {}
    return CodexModelTiers(
        implementer=_codex_model_tier(
            entry=models.get(_IMPLEMENTER_TIER_KEY),
            default_model=_DEFAULT_IMPLEMENTER_MODEL,
            default_effort=_DEFAULT_IMPLEMENTER_EFFORT,
        ),
        pr=_codex_model_tier(
            entry=models.get(_PR_TIER_KEY),
            default_model=_DEFAULT_PR_MODEL,
            default_effort=_DEFAULT_PR_EFFORT,
        ),
    )


def _codex_model_tier(
    *,
    entry: object,
    default_model: str,
    default_effort: str,
) -> CodexModelTier:
    if not isinstance(entry, dict):
        return CodexModelTier(model=default_model, reasoning_effort=default_effort)
    table = cast("dict[str, Any]", entry)
    compaction = _tier_compaction_token_limit(value=table.get(_TIER_COMPACTION_KEY))
    model_raw = table.get(_TIER_MODEL_KEY)
    model = model_raw if isinstance(model_raw, str) else default_model
    if model == "":
        return CodexModelTier(model="", reasoning_effort="", compaction_token_limit=compaction)
    return CodexModelTier(
        model=model,
        reasoning_effort=_tier_effort(value=table.get(_TIER_EFFORT_KEY), default=default_effort),
        compaction_token_limit=compaction,
    )


def _tier_compaction_token_limit(*, value: object) -> int:
    """The configured compaction token limit, or 0 when none is configured.

    `bool` is excluded explicitly: it is an `int` subclass, so `true` would
    otherwise resolve to a one-token compaction threshold -- a value that
    reads as configured and makes every turn compact immediately.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return max(0, value)


def _tier_effort(*, value: object, default: str) -> str:
    return value if isinstance(value, str) and value != "" else default
