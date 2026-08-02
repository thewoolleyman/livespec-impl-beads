from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AGENT_INSTRUCTIONS = (_REPO_ROOT / "AGENTS.md").read_text()
_IMAGE_RUNBOOK = (_REPO_ROOT / "orchestrator-image" / "README.md").read_text()


def test_host_fabro_runbooks_require_supervised_web_console() -> None:
    runbooks = _AGENT_INSTRUCTIONS + _IMAGE_RUNBOOK

    assert "--no-web" not in runbooks
    assert "sudo systemctl restart fabro-server" in _AGENT_INSTRUCTIONS
    assert "sudo systemctl restart fabro-server" in _IMAGE_RUNBOOK
    assert "cargo clean --release -p fabro-spa" in _AGENT_INSTRUCTIONS
    assert "cargo clean --release -p fabro-spa" in _IMAGE_RUNBOOK
    assert "cargo dev build --release -p fabro-cli" in _AGENT_INSTRUCTIONS
    assert "cargo dev build --release -p fabro-cli" in _IMAGE_RUNBOOK
    assert "ExecStartPost" in _IMAGE_RUNBOOK
    assert "Never invoke `fabro server start`" in _IMAGE_RUNBOOK
