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


def test_host_fabro_runbook_documents_run_turn_absence_guard() -> None:
    assert "### Fabro `run_turn` absence guard" in _IMAGE_RUNBOOK
    assert "`run-turn-telemetry-absent`" in _IMAGE_RUNBOOK
    assert "critical\nreflection finding" in _IMAGE_RUNBOOK
    assert "not yet provisioned in the livespec" in _IMAGE_RUNBOOK
    assert "Honeycomb environment" in _IMAGE_RUNBOOK
    assert "bd-ib-jb7rzr.3" in _IMAGE_RUNBOOK
    assert "only the per-dispatch guard layer exists" in _IMAGE_RUNBOOK
    assert "Real Fabro `run_turn` spans do not" in _IMAGE_RUNBOOK
    assert "timestamp-bounded global Fabro `run_turn` marker" in _IMAGE_RUNBOOK
    assert "if a future span shape carries them" in _IMAGE_RUNBOOK
    assert "zero `run_turn` spans over the" in _IMAGE_RUNBOOK
    assert "orchestrator-image/provision-honeycomb-run-turn-trigger.sh" in _IMAGE_RUNBOOK
    assert "`COUNT` filtered to `name = run_turn`" in _IMAGE_RUNBOOK
    assert "threshold `<= 0`" in _IMAGE_RUNBOOK
    assert "`operator-alert` recipient" in _IMAGE_RUNBOOK
    assert "10-minute" in _IMAGE_RUNBOOK
    assert "DRY_RUN=1" in _IMAGE_RUNBOOK
