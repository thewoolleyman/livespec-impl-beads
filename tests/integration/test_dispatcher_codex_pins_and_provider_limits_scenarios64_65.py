"""Integration coverage for Codex pins and provider-limit permanence."""

from __future__ import annotations

import json
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import (
    dispatch_fabro_run_inputs,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import (
    CODEX_ADAPTER_BASE,
    build_plan,
)
from livespec_orchestrator_beads_fabro.commands._fabro_port import (
    fabro_failure_detail_from_payload,
)

_CONFIG_NAME = ".livespec.jsonc"
_ACP_WRAPPER = "ACP protocol error"
_CODEX_PROVIDER_LIMIT = (
    'Internal error: {"data": {"message": "You\'ve hit your usage limit. '
    "Visit https://chatgpt.com/codex/settings/usage to purchase more credits "
    'or try again at Aug 20th, 2026 3:33 AM.", '
    '"codex_error_info": "usage_limit_exceeded"}}'
)
_CLAUDE_OPUS_5_ADAPTER = (
    "ANTHROPIC_MODEL=claude-opus-5 CLAUDE_CODE_EFFORT_LEVEL=high "
    "npx -y @agentclientprotocol/claude-agent-acp"
)


def _plan(*, repo: Path):
    return build_plan(
        repo=repo,
        work_item_id="bd-ib-cxv3",
        workflow_toml=repo / "workflow.toml",
        goal_file=repo / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=repo / "janitor",
    )


def _input_value(*, inputs: tuple[str, ...], name: str) -> str:
    prefix = f"{name}="
    matches = [value.removeprefix(prefix) for value in inputs if value.startswith(prefix)]
    assert len(matches) == 1
    return matches[0]


def _write_dispatcher_config(*, repo: Path, codex_models: dict[str, object]) -> None:
    config = {"livespec-orchestrator-beads-fabro": {"dispatcher": {"codex_models": codex_models}}}
    (repo / _CONFIG_NAME).write_text(json.dumps(config), encoding="utf-8")


def _failure_payload(*, cause: str) -> list[object]:
    return [
        {
            "status": {"kind": "failed"},
            "failure": {
                "category": "transient_infra",
                "signature": "fabro|transient_infra|acp",
                "causes": [_ACP_WRAPPER, cause],
            },
        }
    ]


def test_scenario64_dispatcher_renders_pinned_codex_adapters_and_true_opt_out(
    tmp_path: Path,
) -> None:
    """Scenario 64: dispatch inputs carry explicit Codex pins and the PR tier."""
    default_inputs = dispatch_fabro_run_inputs(plan=_plan(repo=tmp_path))
    default_implementer = _input_value(inputs=default_inputs, name="acp_adapter")
    default_pr = _input_value(inputs=default_inputs, name="pr_adapter")

    assert default_implementer == _CLAUDE_OPUS_5_ADAPTER
    assert default_pr.startswith(CODEX_ADAPTER_BASE)
    assert " -c model=" in default_pr
    assert " -c model_reasoning_effort=" in default_pr
    assert default_implementer != default_pr

    _write_dispatcher_config(
        repo=tmp_path,
        codex_models={
            "implementer": {"model": "repo-implementer", "reasoning_effort": "high"},
            "pr": {"model": "repo-publish", "reasoning_effort": "low"},
        },
    )
    override_inputs = dispatch_fabro_run_inputs(plan=_plan(repo=tmp_path))
    assert _input_value(inputs=override_inputs, name="acp_adapter").endswith(
        " -c model=repo-implementer -c model_reasoning_effort=high"
    )
    assert _input_value(inputs=override_inputs, name="pr_adapter").endswith(
        " -c model=repo-publish -c model_reasoning_effort=low"
    )

    _write_dispatcher_config(
        repo=tmp_path,
        codex_models={"implementer": {"model": "", "reasoning_effort": "high"}},
    )
    opt_out_inputs = dispatch_fabro_run_inputs(plan=_plan(repo=tmp_path))
    assert _input_value(inputs=opt_out_inputs, name="acp_adapter") == _CLAUDE_OPUS_5_ADAPTER

    _write_dispatcher_config(repo=tmp_path, codex_models={"implementer": "repo-implementer"})
    malformed_inputs = dispatch_fabro_run_inputs(plan=_plan(repo=tmp_path))
    assert _input_value(inputs=malformed_inputs, name="acp_adapter") == _CLAUDE_OPUS_5_ADAPTER


def test_scenario65_provider_usage_ceiling_is_permanent_and_transients_stay_transient() -> None:
    """Scenario 65: provider ceilings are typed permanent failures; transients are not."""
    provider_limit = fabro_failure_detail_from_payload(
        payload=_failure_payload(cause=_CODEX_PROVIDER_LIMIT)
    )
    assert provider_limit is not None
    assert provider_limit.provider_usage_limit is True
    assert provider_limit.category == "deterministic"
    assert provider_limit.signature == "fabro|deterministic|acp"
    assert provider_limit.cause is not None
    assert provider_limit.cause.startswith("You've hit your usage limit.")
    assert "try again at Aug 20th, 2026 3:33 AM." in provider_limit.cause

    transient = fabro_failure_detail_from_payload(
        payload=_failure_payload(cause="connection reset by peer")
    )
    assert transient is not None
    assert transient.provider_usage_limit is False
    assert transient.category == "transient_infra"
    assert transient.signature == "fabro|transient_infra|acp"
    assert transient.cause == "connection reset by peer"
