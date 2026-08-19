"""Contracts for the Honeycomb run_turn trigger provisioner."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "orchestrator-image" / "provision-honeycomb-run-turn-trigger.sh"


def _write_curl_stub(*, bin_dir: Path, recipients_json: str) -> None:
    stub = bin_dir / "curl"
    _ = stub.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'printf \'%s\\n\' "$*" >> "${CURL_ARGV_LOG}"\n'
        "url=''\n"
        "while (($#)); do\n"
        '  if [[ "$1" == "--url" ]]; then\n'
        "    shift\n"
        '    url="$1"\n'
        "  fi\n"
        "  shift || true\n"
        "done\n"
        'case "$url" in\n'
        "  */1/recipients)\n"
        '    cat "${RECIPIENTS_JSON}"\n'
        "    ;;\n"
        "  *)\n"
        "    printf 'unexpected URL: %s\\n' \"$url\" >&2\n"
        "    exit 64\n"
        "    ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    _ = (bin_dir / "recipients.json").write_text(recipients_json, encoding="utf-8")


def _run_script(
    *,
    tmp_path: Path,
    recipient_selector: str | None,
    recipients: list[dict[str, object]],
) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    recipients_path = bin_dir / "recipients.json"
    curl_argv_log = tmp_path / "curl-argv.log"
    curl_argv_log.touch()
    _write_curl_stub(bin_dir=bin_dir, recipients_json=json.dumps(recipients))

    env = {
        **os.environ,
        "CURL_ARGV_LOG": str(curl_argv_log),
        "DRY_RUN": "1",
        "HONEYCOMB_API_BASE": "https://honeycomb.test",
        "HONEYCOMB_CONFIG_KEY_LIVESPEC": "not-a-real-key",
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "RECIPIENTS_JSON": str(recipients_path),
    }
    if recipient_selector is not None:
        env["HONEYCOMB_OPERATOR_ALERT_RECIPIENT"] = recipient_selector
    else:
        env.pop("HONEYCOMB_OPERATOR_ALERT_RECIPIENT", None)

    return subprocess.run(
        ["bash", str(_SCRIPT)],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def test_provisioner_resolves_email_recipient_by_email_address(tmp_path: Path) -> None:
    result = _run_script(
        tmp_path=tmp_path,
        recipient_selector="operator@example.test",
        recipients=[
            {
                "id": "email-recipient-1",
                "type": "email",
                "details": {"email_address": "operator@example.test"},
            }
        ],
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recipients"] == [{"id": "email-recipient-1"}]


def test_provisioner_failed_match_lists_redacted_available_recipients(tmp_path: Path) -> None:
    result = _run_script(
        tmp_path=tmp_path,
        recipient_selector="missing@example.test",
        recipients=[
            {
                "id": "email-recipient-1",
                "type": "email",
                "details": {"email_address": "operator@example.test"},
            }
        ],
    )

    assert result.returncode == 1
    assert "no Honeycomb recipient matched 'missing@example.test'" in result.stderr
    assert "available Honeycomb recipients:" in result.stderr
    assert "id=email-recipient-1 type=email email_address=o***r@example.test" in result.stderr
    assert "operator@example.test" not in result.stderr


def test_provisioner_requires_recipient_selector_and_lists_choices(tmp_path: Path) -> None:
    result = _run_script(
        tmp_path=tmp_path,
        recipient_selector=None,
        recipients=[
            {
                "id": "email-recipient-1",
                "type": "email",
                "details": {"email_address": "operator@example.test"},
            }
        ],
    )

    assert result.returncode == 1
    assert "HONEYCOMB_OPERATOR_ALERT_RECIPIENT is required." in result.stderr
    assert "id=email-recipient-1 type=email email_address=o***r@example.test" in result.stderr
