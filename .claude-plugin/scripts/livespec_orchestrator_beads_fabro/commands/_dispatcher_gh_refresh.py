"""Sandbox-local refreshing GitHub CLI wrapper projection for Dispatcher runs."""

from __future__ import annotations

import base64
import io
import json
import os
import tarfile
from collections.abc import Mapping
from pathlib import Path

__all__: list[str] = [
    "DEFAULT_SANDBOX_GH_REFRESH_ROOT",
    "SANDBOX_GH_REFRESH_ROOT_ENV_VAR",
    "refreshing_gh_env_lines",
    "refreshing_gh_prepare_steps_block",
    "resolve_sandbox_gh_refresh_root",
]

_GITHUB_APP_ENV_KEYS = (
    "GITHUB_APP_ID",
    "GITHUB_PRIVATE_KEY",
    "GITHUB_APP_INSTALLATION_ID",
    "GITHUB_API_URL",
)
# The in-sandbox bundle root the dispatcher materializes the refreshing `gh`
# wrapper into. `/workspace` is the fabro sandbox's own mount, so this absolute
# path is correct in production and WRONG anywhere else -- on a CI runner it
# resolves to the runner's filesystem root, where `rm -rf` + `mkdir` either is
# refused (uid 1000: `mkdir: Permission denied`) or, worse, succeeds under uid 0
# and destroys a real /workspace. The lever below exists so a test can execute
# the rendered script for real against a temporary root; production never sets
# it. Mirrors `LIVESPEC_SANDBOX_OTEL_ENDPOINT` in `_dispatcher_projection`.
SANDBOX_GH_REFRESH_ROOT_ENV_VAR = "LIVESPEC_SANDBOX_GH_REFRESH_ROOT"
DEFAULT_SANDBOX_GH_REFRESH_ROOT = "/workspace/.livespec-gh-refresh"


def resolve_sandbox_gh_refresh_root(*, environ: Mapping[str, str]) -> str:
    """Resolve the in-sandbox `gh`-wrapper bundle root (override > default)."""
    override = environ.get(SANDBOX_GH_REFRESH_ROOT_ENV_VAR, "").strip()
    return override or DEFAULT_SANDBOX_GH_REFRESH_ROOT


_SUPPORT_ARCHIVE_RELPATHS = (
    Path("_vendor/livespec_runtime/__init__.py"),
    Path("_vendor/livespec_runtime/github_auth"),
    Path("_vendor/returns"),
    Path("_vendor/typing_extensions.py"),
)
_MINT_HELPER_SOURCE = """#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

bundle_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(bundle_root / "_vendor"))

from livespec_runtime.github_auth.config import load_github_app_config
from livespec_runtime.github_auth.errors import GithubAppAuthError
from livespec_runtime.github_auth.provider import InstallationTokenProvider

if len(sys.argv) != 1:
    sys.stderr.write("usage: mint_app_token.py\\n")
    raise SystemExit(2)

try:
    config = load_github_app_config(environ=os.environ)
    token = InstallationTokenProvider(config=config).token()
except GithubAppAuthError as exc:
    sys.stderr.write(f"ERROR: {exc.detail}\\n")
    raise SystemExit(3) from exc

sys.stderr.write("github-token source: github-app-installation-token\\n")
sys.stdout.write(token)
"""


def refreshing_gh_prepare_steps_block() -> str:
    """Install a sandbox-local refreshing `gh` wrapper when App inputs exist."""
    if not github_app_env_present():
        return ""
    bundle_root = resolve_sandbox_gh_refresh_root(environ=os.environ)
    mint_helper = f"{bundle_root}/bin/mint_app_token.py"
    support_archive_literal = json.dumps(github_auth_support_archive_b64())
    helper_source_literal = json.dumps(_MINT_HELPER_SOURCE)
    script = (
        "set -eu\n"
        f'bundle_root="{bundle_root}"\n'
        f'mint="{mint_helper}"\n'
        'rm -rf "$bundle_root"\n'
        'mkdir -p "$bundle_root/bin"\n'
        "python3 - <<'PY'\n"
        "import base64\n"
        "import io\n"
        "import tarfile\n"
        f"payload = base64.b64decode({support_archive_literal})\n"
        f"target = {bundle_root!r}\n"
        'with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:\n'
        "    archive.extractall(target)\n"
        "PY\n"
        "python3 - <<'PY'\n"
        "from pathlib import Path\n"
        f"Path({mint_helper!r}).write_text({helper_source_literal}, encoding='utf-8')\n"
        "PY\n"
        'chmod 755 "$mint"\n'
        'real_gh="$(command -v gh)"\n'
        'case "$real_gh" in\n'
        "  /*) ;;\n"
        '  *) echo "gh did not resolve to an absolute path" >&2; exit 1 ;;\n'
        "esac\n"
        'wrapped_gh="${real_gh}.livespec-real"\n'
        'if [ ! -x "$wrapped_gh" ]; then mv "$real_gh" "$wrapped_gh"; fi\n'
        'cat > "$real_gh" <<EOF\n'
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'mint="$mint"\n'
        'real_gh="$wrapped_gh"\n'
        "EOF\n"
        "cat >> \"$real_gh\" <<'EOF'\n"
        'token="$(python3 "$mint")"\n'
        'export GH_TOKEN="$token"\n'
        'export GITHUB_TOKEN="$token"\n'
        'exec "$real_gh" "$@"\n'
        "EOF\n"
        'chmod 755 "$real_gh"'
    )
    lines = [
        "",
        "# --- Dispatcher-materialized livespec-refreshing-gh-wrapper ---",
        "[[run.prepare.steps]]",
        f"script = '''\n{script}\n'''",
    ]
    return "\n".join(lines) + "\n"


def refreshing_gh_env_lines() -> str:
    """Project GitHub App inputs for the sandbox-local mint helper."""
    if not github_app_env_present():
        return ""
    return "".join(
        f"{key} = {json.dumps(value)}\n"
        for key in _GITHUB_APP_ENV_KEYS
        if (value := os.environ.get(key)) not in (None, "")
    )


def github_app_env_present() -> bool:
    """Whether the minimum GitHub App inputs are present."""
    return all(os.environ.get(key) not in (None, "") for key in _GITHUB_APP_ENV_KEYS[:2])


def github_auth_support_archive_b64(*, scripts_root: Path | None = None) -> str:
    """Return the dispatching plugin build's minimal GitHub auth support bundle."""
    root = scripts_root if scripts_root is not None else Path(__file__).resolve().parents[2]
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for relpath in _SUPPORT_ARCHIVE_RELPATHS:
            source = root / relpath
            if source.is_dir():
                for child in sorted(source.rglob("*.py")):
                    archive.add(child, arcname=str(child.relative_to(root)))
            else:
                archive.add(source, arcname=str(relpath))
    return base64.b64encode(buffer.getvalue()).decode("ascii")
